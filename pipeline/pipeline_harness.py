#!/usr/bin/env python3
"""
BRI610 Pipeline Harness v0.3 — Agent Workflow Orchestrator
Stage-Gate Pipeline: Parse → QC → Embed → Verify → Report

Each stage has a QC gate that must pass before the next stage runs.
Designed for ACCURACY and ZERO information loss over token efficiency.

Usage:
  # Full auto-pipeline (runs all stages sequentially with QC gates)
  python pipeline_harness.py run --key <openrouter_key> [--book DA|FN] [--batch 50]

  # Individual stages
  python pipeline_harness.py parse   --book DA|FN
  python pipeline_harness.py qc      [--book DA|FN] [--fix]
  python pipeline_harness.py embed   --key <key> [--book DA|FN] [--batch 50]
  python pipeline_harness.py verify  [--book DA|FN]
  python pipeline_harness.py status
  python pipeline_harness.py migrate-slides --sqlite <path>
"""
import psycopg2, psycopg2.extras
from pgvector.psycopg2 import register_vector
import fitz, re, os, base64, struct, json, time, argparse, sys, requests
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional, Callable
from enum import Enum

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIG & LOGGING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DB_DSN = os.environ.get("DATABASE_URL", "dbname=bri610 user=tutor password=tutor610 host=localhost")
EMBED_MODEL = "nvidia/llama-nemotron-embed-vl-1b-v2:free"
EMBED_URL = "https://openrouter.ai/api/v1/embeddings"
EMBED_DIM = 2048
# Nemotron VL input limit: 8192 tokens ~ 32000 chars for text
# Send FULL content to minimize information loss
TEXT_EMBED_MAX_CHARS = 32000

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(LOG_DIR, f'pipeline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')),
    ]
)
log = logging.getLogger('pipeline')


def get_conn():
    conn = psycopg2.connect(DB_DSN)
    register_vector(conn)
    return conn


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STAGE GATE — QC Hook System
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Stage(Enum):
    PARSE = "parse"
    QC = "qc"
    EMBED = "embed"
    VERIFY = "verify"
    COMPLETE = "complete"


@dataclass
class StageResult:
    """Result of a pipeline stage execution"""
    stage: str
    success: bool
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: list = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def pass_rate(self) -> float:
        denom = self.total - self.skipped
        return self.passed / denom if denom > 0 else 0.0

    def gate_check(self, min_pass_rate: float = 0.95) -> bool:
        """QC gate: must meet minimum pass rate to proceed"""
        if self.total == 0:
            return False
        return self.pass_rate >= min_pass_rate and self.failed == 0


class StageGate:
    """Orchestrator: runs stages sequentially, each must pass QC gate before next"""

    GATE_THRESHOLDS = {
        Stage.PARSE: 0.90,
        Stage.QC: 0.95,
        Stage.EMBED: 0.98,
        Stage.VERIFY: 0.95,
    }

    def __init__(self):
        self.results: dict = {}
        self.hooks: dict = {
            'pre_stage': [],
            'post_stage': [],
            'gate_pass': [],
            'gate_fail': [],
            'pipeline_complete': [],
        }

    def register_hook(self, event: str, fn: Callable):
        if event in self.hooks:
            self.hooks[event].append(fn)

    def _fire(self, event: str, **kwargs):
        for fn in self.hooks.get(event, []):
            try:
                fn(**kwargs)
            except Exception as e:
                log.warning(f"Hook {event}/{fn.__name__} error: {e}")

    def run_stage(self, stage: Stage, fn: Callable, **kwargs) -> StageResult:
        """Execute a stage function and check its QC gate"""
        log.info(f"\n{'='*60}")
        log.info(f"  STAGE: {stage.value.upper()}")
        log.info(f"{'='*60}")

        self._fire('pre_stage', stage=stage)

        try:
            result = fn(**kwargs)
        except Exception as e:
            log.error(f"Stage {stage.value} CRASHED: {e}")
            result = StageResult(stage=stage.value, success=False, errors=[str(e)])

        self.results[stage.value] = result
        self._fire('post_stage', stage=stage, result=result)

        threshold = self.GATE_THRESHOLDS.get(stage, 0.95)

        if result.gate_check(threshold):
            log.info(f"  GATE PASS -- {stage.value}: {result.passed}/{result.total} "
                     f"({result.pass_rate:.1%}) >= {threshold:.0%}")
            self._fire('gate_pass', stage=stage, result=result)
            return result
        else:
            log.error(f"  GATE FAIL -- {stage.value}: {result.passed}/{result.total} "
                      f"({result.pass_rate:.1%}) < {threshold:.0%}")
            if result.errors:
                for e in result.errors[:5]:
                    log.error(f"    Error: {e}")
            self._fire('gate_fail', stage=stage, result=result)
            return result

    def save_report(self, filepath: str = None):
        """Save pipeline execution report"""
        if filepath is None:
            filepath = os.path.join(LOG_DIR, f'pipeline_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        report = {stage: asdict(r) for stage, r in self.results.items()}
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        log.info(f"Report saved: {filepath}")
        return filepath


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STAGE 1: PARSER AGENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def classify_page(text, n_raster, n_drawings):
    """Classify page type with comprehensive heuristics"""
    tlen = len(text.strip())
    eq_patterns = [
        r'[=\u2202\u222b\u2211\u220f\u03c4\u03bb\u03c3\u03bc\u03b1\u03b2\u03b3\u03b4\u03b5\u03b8\u03c6\u03c8\u03c9]',
        r'd[A-Z]/d[tx]', r'\bexp\b|\blog\b|\bln\b',
        r'\d+\.\d+\s*[\u00d7\u00b7]\s*10',
    ]
    has_eq = any(re.search(p, text) for p in eq_patterns)
    has_caption = bool(re.search(r'(?i)(figure|fig\.)\s+\d+', text))
    has_refs = bool(re.search(r'(?i)^references\s*$', text, re.M)) or \
               (text.count('(') > 10 and bool(re.search(r'\(\d{4}\)', text)))

    if tlen < 30:
        return 'empty', has_eq, has_caption, has_refs
    if has_refs and tlen > 300:
        return 'references', has_eq, has_caption, has_refs
    if tlen < 200 and (n_raster > 0 or n_drawings > 10):
        return 'figure', has_eq, has_caption, has_refs
    if n_raster > 0 or n_drawings > 20:
        return 'mixed', has_eq, has_caption, has_refs
    if has_eq:
        return 'equation', has_eq, has_caption, has_refs
    return 'text', has_eq, has_caption, has_refs


def get_toc_map(doc):
    """Build page->(chapter, chapter_title, section_title) from PDF TOC"""
    toc = doc.get_toc()
    if not toc:
        return {}
    entries = sorted(toc, key=lambda x: x[2])
    mapping = {}
    ch, ch_title, sec = "", "", ""
    for level, title, page in entries:
        m_da = re.match(r'^(\d+)\.\s+(.+)', title)
        m_da_sec = re.match(r'^(\d+)\.(\d+)\s+(.+)', title)
        m_fn = re.match(r'CHAPTER\s+(\d+):\s*(.*)', title)
        if m_fn:
            ch, ch_title = m_fn.group(1), m_fn.group(2).strip()
        elif m_da and not m_da_sec:
            ch, ch_title = m_da.group(1), m_da.group(2)
        elif m_da_sec:
            sec = m_da_sec.group(3)
        elif level >= 3:
            sec = title.strip()
        mapping[page] = (ch, ch_title, sec)
    return mapping


def parse_textbook(pdf_path, book_name, img_dir):
    """Parse PDF into page-level records — rasterize ALL pages for zero info loss"""
    os.makedirs(img_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    toc_map = get_toc_map(doc)

    pages = []
    for p in range(len(doc)):
        text = doc[p].get_text().strip().replace('\x00', '')
        raster = doc[p].get_images()
        drawings = doc[p].get_drawings()
        ptype, has_eq, has_cap, has_refs = classify_page(text, len(raster), len(drawings))

        if ptype == 'empty':
            continue

        ch, ch_title, sec = "", "", ""
        for pg in range(p + 1, 0, -1):
            if pg in toc_map:
                ch, ch_title, sec = toc_map[pg]
                break

        # Rasterize ALL non-empty pages (accuracy > storage)
        img_path = os.path.join(img_dir, f"p{p+1:04d}.jpg")
        if not os.path.exists(img_path):
            pix = doc[p].get_pixmap(dpi=150)
            pix.save(img_path)

        pages.append({
            'book': book_name, 'page_num': p + 1,
            'chapter': ch, 'chapter_title': ch_title, 'section_title': sec,
            'content': text, 'content_length': len(text),
            'has_figures': len(raster) > 0 or len(drawings) > 20,
            'has_equations': has_eq, 'has_references': has_refs,
            'has_captions': has_cap,
            'n_drawings': len(drawings), 'n_raster_images': len(raster),
            'page_type': ptype,
            'img_path': img_path,
        })
    doc.close()
    return pages


def stage_parse(book=None, **kwargs) -> StageResult:
    """STAGE 1: Parse textbooks into PostgreSQL"""
    book_map = {
        'DA': ('Dayan_Abbott',
               os.path.expanduser('~/Downloads/Theoretical Neuroscience Computational and Mathematical Modeling of Neural Systems -  Peter Dayan, L. F. Abbott.pdf'),
               os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'textbook_images', 'DA')),
        'FN': ('Fundamental_Neuroscience',
               os.path.expanduser('~/Zotero/storage/SXYKE54W/2008 - Fundamental neuroscience.pdf'),
               os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'textbook_images', 'FN')),
    }
    targets = [book] if book else ['DA', 'FN']
    result = StageResult(stage='parse', success=True)
    conn = get_conn()
    cur = conn.cursor()
    for key in targets:
        name, pdf, img_dir = book_map[key]
        if not os.path.exists(pdf):
            result.errors.append(f"PDF not found: {pdf}")
            continue
        log.info(f"Parsing: {name} from {pdf}")
        pages = parse_textbook(pdf, name, img_dir)
        inserted = 0
        for pg in pages:
            try:
                cur.execute("""
                    INSERT INTO textbook_pages
                    (book, page_num, chapter, chapter_title, section_title, content,
                     content_length, has_figures, has_equations, has_references, has_captions,
                     n_drawings, n_raster_images, page_type, img_path, qc_status)
                    VALUES (%(book)s, %(page_num)s, %(chapter)s, %(chapter_title)s, %(section_title)s,
                            %(content)s, %(content_length)s, %(has_figures)s, %(has_equations)s,
                            %(has_references)s, %(has_captions)s, %(n_drawings)s, %(n_raster_images)s,
                            %(page_type)s, %(img_path)s, 'pending')
                    ON CONFLICT (book, page_num) DO UPDATE SET
                        content = EXCLUDED.content, content_length = EXCLUDED.content_length,
                        page_type = EXCLUDED.page_type, has_figures = EXCLUDED.has_figures,
                        has_equations = EXCLUDED.has_equations, qc_status = 'pending'
                """, pg)
                inserted += 1
            except Exception as e:
                result.errors.append(f"{name} p{pg['page_num']}: {e}")
                result.failed += 1
        conn.commit()
        result.total += len(pages)
        result.passed += inserted
        cur.execute("""
            SELECT page_type, COUNT(*), SUM(CASE WHEN has_equations THEN 1 ELSE 0 END),
                   SUM(CASE WHEN has_figures THEN 1 ELSE 0 END)
            FROM textbook_pages WHERE book=%s GROUP BY page_type ORDER BY page_type
        """, (name,))
        log.info(f"  Inserted {inserted} pages from {name}:")
        for r in cur.fetchall():
            log.info(f"    {r[0]}: {r[1]} pages | {r[2]} with eq | {r[3]} with figs")
    conn.close()
    result.success = result.failed == 0
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STAGE 2: QC AGENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

QC_CHECKS = {
    'content_not_empty': lambda pg: len(pg['content'] or '') > 30,
    'chapter_assigned': lambda pg: bool(pg['chapter']),
    'type_consistent': lambda pg: (
        (pg['page_type'] != 'text' or pg['content_length'] > 100) and
        (pg['page_type'] != 'figure' or pg['has_figures'] or pg['n_drawings'] > 10) and
        (pg['page_type'] != 'references' or pg['has_references'])
    ),
    'not_blank_page': lambda pg: 'intentionally left blank' not in (pg['content'] or '').lower(),
    'image_exists': lambda pg: pg['img_path'] and os.path.exists(pg['img_path']),
    'reasonable_length': lambda pg: pg['content_length'] < 15000,
}


def stage_qc(book=None, fix=False, **kwargs) -> StageResult:
    """STAGE 2: Quality check all pending pages"""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    sql = "SELECT * FROM textbook_pages WHERE qc_status = 'pending'"
    params = []
    if book:
        book_map = {'DA': 'Dayan_Abbott', 'FN': 'Fundamental_Neuroscience'}
        sql += " AND book = %s"
        params.append(book_map[book])
    cur.execute(sql, params)
    pages = cur.fetchall()
    result = StageResult(stage='qc', success=True, total=len(pages))
    cur2 = conn.cursor()
    for pg in pages:
        check_results = {}
        all_pass = True
        for check_name, check_fn in QC_CHECKS.items():
            try:
                ok = check_fn(pg)
            except Exception:
                ok = False
            check_results[check_name] = ok
            if not ok:
                all_pass = False
        if pg['page_type'] == 'references' or not check_results.get('not_blank_page', True):
            status = 'skipped'
            result.skipped += 1
        elif all_pass:
            status = 'passed'
            result.passed += 1
        else:
            fails = [k for k, v in check_results.items() if not v]
            if fix:
                if 'not_blank_page' in fails:
                    status = 'skipped'
                    result.skipped += 1
                elif 'chapter_assigned' in fails and pg['page_num'] <= 10:
                    status = 'skipped'
                    result.skipped += 1
                else:
                    status = 'failed'
                    result.failed += 1
                    result.errors.append(f"{pg['book']} p{pg['page_num']}: {fails}")
            else:
                status = 'failed'
                result.failed += 1
                result.errors.append(f"{pg['book']} p{pg['page_num']}: {fails}")
        cur2.execute("UPDATE textbook_pages SET qc_status=%s, qc_notes=%s WHERE id=%s",
                     (status, json.dumps(check_results), pg['id']))
        cur2.execute("""
            INSERT INTO qc_log (source_table, source_id, check_name, passed, details)
            VALUES ('textbook_pages', %s, 'full_qc', %s, %s)
        """, (pg['id'], status == 'passed', json.dumps(check_results)))
    conn.commit()
    conn.close()
    log.info(f"  QC: Passed={result.passed} Failed={result.failed} Skipped={result.skipped}")
    result.success = True
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STAGE 3: EMBEDDER AGENT (Zero Information Loss)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def embed_request(api_key, input_data, retries=5):
    """Embedding request with robust retry"""
    hdrs = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    for attempt in range(retries):
        try:
            r = requests.post(EMBED_URL, headers=hdrs,
                json={"model": EMBED_MODEL, "input": input_data}, timeout=120)
            if r.status_code == 429:
                wait = min(60, 2 ** (attempt + 2))
                log.warning(f"  Rate limited, waiting {wait}s (attempt {attempt+1}/{retries})")
                time.sleep(wait)
                continue
            if r.status_code >= 500:
                time.sleep(2 ** attempt)
                continue
            r.raise_for_status()
            data = r.json()
            vec = data["data"][0]["embedding"]
            if len(vec) != EMBED_DIM:
                log.error(f"  Wrong dim: got {len(vec)}, expected {EMBED_DIM}")
                return None
            return vec
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                log.error(f"  Embed FAILED after {retries} attempts: {e}")
                return None
    return None


def stage_embed(key=None, book=None, batch=50, **kwargs) -> StageResult:
    """
    STAGE 3: Generate embeddings — ACCURACY FIRST.

    Strategy:
    - text_embedding: ALL QC-passed pages (full content, up to 32k chars)
    - image_embedding: equation/mixed/figure pages get ADDITIONAL image embedding
    - Dual embedding ensures zero information loss
    """
    if not key:
        return StageResult(stage='embed', success=False, errors=['No API key'])

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Count remaining
    count_sql = """SELECT COUNT(*) FROM textbook_pages
                   WHERE qc_status = 'passed'
                   AND (text_embedding IS NULL OR
                        (page_type IN ('mixed','figure','equation') AND image_embedding IS NULL))"""
    params = []
    if book:
        book_map = {'DA': 'Dayan_Abbott', 'FN': 'Fundamental_Neuroscience'}
        count_sql += " AND book = %s"
        params.append(book_map[book])
    cur.execute(count_sql, params)
    total_remaining = cur.fetchone()['count']
    log.info(f"  Pages needing embedding: {total_remaining}")

    # Fetch batch (prioritize no-embedding pages first)
    sql = """SELECT id, book, page_num, content, content_length, page_type, img_path,
                    has_figures, has_equations,
                    text_embedding IS NOT NULL AS has_text_emb,
                    image_embedding IS NOT NULL AS has_img_emb
             FROM textbook_pages
             WHERE qc_status = 'passed'
               AND (text_embedding IS NULL OR
                    (page_type IN ('mixed','figure','equation') AND image_embedding IS NULL))"""
    if book:
        sql += " AND book = %s"
    sql += " ORDER BY (text_embedding IS NULL) DESC, id ASC LIMIT %s"
    params_fetch = params + [batch]
    cur.execute(sql, params_fetch)
    pages = cur.fetchall()

    result = StageResult(stage='embed', success=True, total=len(pages))
    cur2 = conn.cursor()
    done_t, done_i, failed = 0, 0, 0

    for i, pg in enumerate(pages):
        page_label = f"{pg['book'][:2]} p{pg['page_num']}"

        # TEXT EMBEDDING (all pages with content > 50 chars)
        if not pg['has_text_emb'] and pg['content'] and len(pg['content']) > 50:
            text_input = pg['content'][:TEXT_EMBED_MAX_CHARS]
            tvec = embed_request(key, [text_input])
            if tvec:
                cur2.execute("UPDATE textbook_pages SET text_embedding=%s WHERE id=%s",
                             (tvec, pg['id']))
                done_t += 1
            else:
                result.errors.append(f"{page_label}: text embedding failed")
                failed += 1
            time.sleep(0.3)

        # IMAGE EMBEDDING (equation/mixed/figure pages)
        needs_img = (pg['page_type'] in ('mixed', 'figure', 'equation') and
                     not pg['has_img_emb'] and
                     pg['img_path'] and os.path.exists(pg['img_path']))
        if needs_img:
            with open(pg['img_path'], "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            ivec = embed_request(key, [f"data:image/jpeg;base64,{b64}"])
            if ivec:
                cur2.execute("UPDATE textbook_pages SET image_embedding=%s WHERE id=%s",
                             (ivec, pg['id']))
                done_i += 1
            else:
                result.errors.append(f"{page_label}: image embedding failed")
                failed += 1
            time.sleep(0.3)

        if (i + 1) % 10 == 0:
            conn.commit()
            log.info(f"  [{i+1}/{len(pages)}] text={done_t} image={done_i} failed={failed}")

    conn.commit()
    result.passed = done_t + done_i
    result.failed = failed
    result.metrics = {
        'text_embeddings': done_t,
        'image_embeddings': done_i,
        'total_remaining': total_remaining - len(pages),
        'batch_size': batch,
    }
    conn.close()
    log.info(f"  Embed: {done_t} text + {done_i} image, {failed} failed, ~{total_remaining - len(pages)} remaining")
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STAGE 4: VERIFICATION AGENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def stage_verify(book=None, **kwargs) -> StageResult:
    """STAGE 4: Verify embedding integrity"""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    result = StageResult(stage='verify', success=True)

    # Missing text embeddings
    sql = "SELECT id, book, page_num, page_type FROM textbook_pages WHERE qc_status='passed' AND text_embedding IS NULL"
    params = []
    if book:
        book_map = {'DA': 'Dayan_Abbott', 'FN': 'Fundamental_Neuroscience'}
        sql += " AND book = %s"
        params.append(book_map[book])
    cur.execute(sql, params)
    missing_text = cur.fetchall()
    if missing_text:
        result.errors.append(f"{len(missing_text)} pages missing text_embedding")

    # Missing image embeddings for visual pages
    sql2 = """SELECT id, book, page_num FROM textbook_pages
              WHERE qc_status='passed' AND page_type IN ('mixed','figure','equation')
              AND image_embedding IS NULL"""
    if book:
        sql2 += " AND book = %s"
    cur.execute(sql2, params)
    missing_img = cur.fetchall()
    if missing_img:
        result.errors.append(f"{len(missing_img)} visual pages missing image_embedding")

    # Stats per book
    cur.execute("""
        SELECT book,
               COUNT(*) FILTER (WHERE qc_status='passed') AS passed,
               COUNT(*) FILTER (WHERE qc_status='passed' AND text_embedding IS NOT NULL) AS has_text,
               COUNT(*) FILTER (WHERE qc_status='passed' AND page_type IN ('mixed','figure','equation')) AS visual,
               COUNT(*) FILTER (WHERE qc_status='passed' AND page_type IN ('mixed','figure','equation')
                                AND image_embedding IS NOT NULL) AS has_img
        FROM textbook_pages GROUP BY book ORDER BY book
    """)
    for r in cur.fetchall():
        log.info(f"  [{r['book'][:2]}] passed={r['passed']} text_emb={r['has_text']} "
                 f"visual={r['visual']} img_emb={r['has_img']}")
        result.metrics[r['book']] = dict(r)

    # Slides
    cur.execute("SELECT COUNT(*) AS total, COUNT(*) FILTER (WHERE embedding IS NOT NULL) AS embedded FROM slides")
    s = cur.fetchone()
    log.info(f"  Slides: {s['embedded']}/{s['total']}")
    result.metrics['slides'] = dict(s)

    total_passed = sum(m.get('passed', 0) for k, m in result.metrics.items() if k != 'slides')
    total_text = sum(m.get('has_text', 0) for k, m in result.metrics.items() if k != 'slides')
    result.total = total_passed
    result.passed = total_text
    result.failed = len(missing_text)
    result.metrics['summary'] = {
        'text_coverage': f"{total_text}/{total_passed}",
        'missing_text': len(missing_text),
        'missing_img': len(missing_img),
    }
    conn.close()
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STATUS (standalone)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def cmd_status(args):
    conn = get_conn()
    cur = conn.cursor()

    print("=== Slides ===")
    cur.execute("SELECT COUNT(*), COUNT(*) FILTER (WHERE embedding IS NOT NULL) FROM slides")
    r = cur.fetchone()
    print(f"  Total: {r[0] or 0} | Embedded: {r[1] or 0}")

    print("\n=== Textbook Pages ===")
    cur.execute("""
        SELECT book, qc_status, COUNT(*),
               COUNT(*) FILTER (WHERE text_embedding IS NOT NULL),
               COUNT(*) FILTER (WHERE image_embedding IS NOT NULL)
        FROM textbook_pages GROUP BY book, qc_status ORDER BY book, qc_status
    """)
    for r in cur.fetchall():
        print(f"  [{r[0][:2]}] {r[1]}: {r[2]} pages | text_emb={r[3]} | img_emb={r[4]}")

    print("\n=== Embedding Progress ===")
    cur.execute("""
        SELECT
            COUNT(*) FILTER (WHERE qc_status='passed') AS qc_passed,
            COUNT(*) FILTER (WHERE qc_status='passed' AND text_embedding IS NOT NULL) AS has_text,
            COUNT(*) FILTER (WHERE qc_status='passed' AND page_type IN ('mixed','figure','equation')) AS visual,
            COUNT(*) FILTER (WHERE qc_status='passed' AND page_type IN ('mixed','figure','equation')
                            AND image_embedding IS NOT NULL) AS has_img
        FROM textbook_pages
    """)
    r = cur.fetchone()
    print(f"  Text embeddings: {r[1]}/{r[0]} ({r[1]*100//max(r[0],1)}%)")
    print(f"  Image embeddings: {r[3]}/{r[2]} ({r[3]*100//max(r[2],1)}%)")
    conn.close()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MIGRATE SLIDES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def cmd_migrate_slides(args):
    import sqlite3 as sl3
    sconn = sl3.connect(args.sqlite)
    sconn.row_factory = sl3.Row
    rows = sconn.execute("SELECT * FROM slides").fetchall()
    conn = get_conn()
    cur = conn.cursor()
    migrated = 0
    for r in rows:
        emb = None
        if r['embedding']:
            n = len(r['embedding']) // 4
            emb = list(struct.unpack(f'{n}f', r['embedding']))
        cur.execute("""
            INSERT INTO slides (lecture, lecture_title, page_num, content, topics, img_path, embedding, qc_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'passed')
            ON CONFLICT (lecture, page_num) DO UPDATE SET embedding = EXCLUDED.embedding, qc_status = 'passed'
        """, (r['lecture'], r['lecture_title'], r['page_num'], r['content'],
              r['topics'], r['img_path'], emb))
        migrated += 1
    conn.commit()
    sconn.close()
    conn.close()
    print(f"Migrated {migrated} slides")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FULL PIPELINE ORCHESTRATOR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def cmd_run(args):
    """Full pipeline: Parse -> QC -> Embed (loop) -> Verify"""
    gate = StageGate()

    def on_gate_fail(stage, result, **kw):
        log.error(f"\n{'!'*60}")
        log.error(f"  PIPELINE HALTED at {stage.value} (pass_rate={result.pass_rate:.1%})")
        log.error(f"{'!'*60}")
    gate.register_hook('gate_fail', on_gate_fail)

    # Stage 1: Parse (skip if data exists)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM textbook_pages")
    total_pages = cur.fetchone()[0]
    conn.close()

    if total_pages == 0:
        r = gate.run_stage(Stage.PARSE, stage_parse, book=args.book)
        if not r.gate_check(gate.GATE_THRESHOLDS[Stage.PARSE]):
            gate.save_report()
            return
    else:
        log.info(f"Parse: skipped ({total_pages} pages already in DB)")

    # Stage 2: QC (skip if no pending)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM textbook_pages WHERE qc_status = 'pending'")
    pending = cur.fetchone()[0]
    conn.close()

    if pending > 0:
        r = gate.run_stage(Stage.QC, stage_qc, book=args.book, fix=True)
        if not r.gate_check(gate.GATE_THRESHOLDS[Stage.QC]):
            gate.save_report()
            return
    else:
        log.info(f"QC: skipped (no pending pages)")

    # Stage 3: Embed (loop until done)
    for round_num in range(1, 200):
        log.info(f"\n  -- Embed Round {round_num} --")
        r = gate.run_stage(Stage.EMBED, stage_embed,
                           key=args.key, book=args.book, batch=args.batch)
        remaining = r.metrics.get('total_remaining', 0)
        if remaining <= 0:
            log.info(f"  All embeddings complete after {round_num} rounds")
            break
        if r.failed > max(r.passed * 0.5, 5):
            log.error(f"  Too many failures ({r.failed}), stopping")
            break
        time.sleep(2)

    # Stage 4: Verify
    r = gate.run_stage(Stage.VERIFY, stage_verify, book=args.book)

    report_path = gate.save_report()
    log.info(f"\n{'='*60}")
    log.info(f"  PIPELINE COMPLETE — Report: {report_path}")
    log.info(f"{'='*60}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CLI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="BRI610 Pipeline Harness v0.3")
    sub = p.add_subparsers(dest='cmd')

    sr = sub.add_parser('run', help='Full auto-pipeline with QC gates')
    sr.add_argument('--key', required=True)
    sr.add_argument('--book', choices=['DA', 'FN'])
    sr.add_argument('--batch', type=int, default=50)

    sp = sub.add_parser('parse')
    sp.add_argument('--book', choices=['DA', 'FN'])

    sq = sub.add_parser('qc')
    sq.add_argument('--book', choices=['DA', 'FN'])
    sq.add_argument('--fix', action='store_true')

    se = sub.add_parser('embed')
    se.add_argument('--key', required=True)
    se.add_argument('--book', choices=['DA', 'FN'])
    se.add_argument('--batch', type=int, default=50)

    sv = sub.add_parser('verify')
    sv.add_argument('--book', choices=['DA', 'FN'])

    ss = sub.add_parser('status')

    sm = sub.add_parser('migrate-slides')
    sm.add_argument('--sqlite', required=True)

    args = p.parse_args()

    if args.cmd == 'run': cmd_run(args)
    elif args.cmd == 'parse':
        r = stage_parse(book=args.book)
        print(f"Parse: {r.passed}/{r.total}, {r.failed} failed")
    elif args.cmd == 'qc':
        r = stage_qc(book=args.book, fix=args.fix)
        print(f"QC: {r.passed}/{r.total}, {r.failed} failed, {r.skipped} skipped")
    elif args.cmd == 'embed':
        r = stage_embed(key=args.key, book=args.book, batch=args.batch)
        print(f"Embed: text={r.metrics.get('text_embeddings',0)} img={r.metrics.get('image_embeddings',0)}")
    elif args.cmd == 'verify':
        r = stage_verify(book=args.book)
        print(f"Verify: {r.passed}/{r.total} | {r.metrics.get('summary','')}")
    elif args.cmd == 'status': cmd_status(args)
    elif args.cmd == 'migrate-slides': cmd_migrate_slides(args)
    else: p.print_help()
