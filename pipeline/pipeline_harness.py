#!/usr/bin/env python3
"""
BRI610 Pipeline Harness — Agent Team for Parse → QC → Embed
PostgreSQL + pgvector backend

Usage:
  python pipeline_harness.py parse --book DA --pdf <path>
  python pipeline_harness.py qc [--book DA] [--fix]
  python pipeline_harness.py embed --key <openrouter_key> [--book DA] [--batch 50]
  python pipeline_harness.py status
  python pipeline_harness.py migrate-slides --sqlite <path>
"""
import psycopg2, psycopg2.extras
from pgvector.psycopg2 import register_vector
import fitz, re, os, base64, struct, json, time, argparse, sys, requests

DB_DSN = os.environ.get("DATABASE_URL", "dbname=bri610 user=tutor password=tutor610 host=localhost")
EMBED_MODEL = "nvidia/llama-nemotron-embed-vl-1b-v2:free"
EMBED_URL = "https://openrouter.ai/api/v1/embeddings"

def get_conn():
    conn = psycopg2.connect(DB_DSN)
    register_vector(conn)
    return conn

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PARSER AGENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def classify_page(text, n_raster, n_drawings):
    """Classify page type with comprehensive heuristics"""
    tlen = len(text.strip())
    
    eq_patterns = [
        r'[=∂∫∑∏τλσμαβγδεθφψω]',
        r'd[A-Z]/d[tx]', r'\bexp\b|\blog\b|\bln\b',
        r'\d+\.\d+\s*[×·]\s*10',
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
    """Build page→(chapter, chapter_title, section_title) from PDF TOC"""
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
    """Parse PDF into page-level records with classification"""
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
        
        # TOC lookup
        ch, ch_title, sec = "", "", ""
        for pg in range(p + 1, 0, -1):
            if pg in toc_map:
                ch, ch_title, sec = toc_map[pg]
                break
        
        # Rasterize (for mixed/figure/equation pages, or all if needed later)
        img_path = os.path.join(img_dir, f"p{p+1:04d}.jpg")
        if ptype in ('mixed', 'figure', 'equation') and not os.path.exists(img_path):
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
            'img_path': img_path if ptype in ('mixed', 'figure', 'equation') else None,
        })
    
    doc.close()
    return pages

def cmd_parse(args):
    book_map = {
        'DA': ('Dayan_Abbott', 
               '/mnt/user-data/uploads/Theoretical_Neuroscience_Computational_and_Mathematical_Modeling_of_Neural_Systems_-__Peter_Dayan__L__F__Abbott__1_.pdf',
               '/home/claude/bri610-tutor/data/textbook_images/DA'),
        'FN': ('Fundamental_Neuroscience',
               '/home/claude/fundamental_neuroscience.pdf', 
               '/home/claude/bri610-tutor/data/textbook_images/FN'),
    }
    
    targets = [args.book] if args.book else ['DA', 'FN']
    conn = get_conn()
    cur = conn.cursor()
    
    for key in targets:
        name, pdf, img_dir = book_map[key]
        print(f"\n{'='*50}")
        print(f"Parsing: {name}")
        print(f"{'='*50}")
        
        pages = parse_textbook(pdf, name, img_dir)
        
        # Insert into PostgreSQL
        inserted = 0
        for pg in pages:
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
        
        conn.commit()
        
        # Print summary
        cur.execute("""
            SELECT page_type, COUNT(*), SUM(CASE WHEN has_equations THEN 1 ELSE 0 END),
                   SUM(CASE WHEN has_figures THEN 1 ELSE 0 END)
            FROM textbook_pages WHERE book=%s GROUP BY page_type ORDER BY page_type
        """, (name,))
        print(f"\n  Inserted {inserted} pages:")
        for r in cur.fetchall():
            print(f"    {r[0]}: {r[1]} pages | {r[2]} with eq | {r[3]} with figs")
    
    conn.close()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# QC AGENT
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
    'image_exists': lambda pg: (
        pg['page_type'] not in ('mixed', 'figure', 'equation') or 
        (pg['img_path'] and os.path.exists(pg['img_path']))
    ),
    'reasonable_length': lambda pg: pg['content_length'] < 15000,  # no garbled extraction
}

def cmd_qc(args):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    sql = "SELECT * FROM textbook_pages WHERE qc_status = 'pending'"
    if args.book:
        book_map = {'DA': 'Dayan_Abbott', 'FN': 'Fundamental_Neuroscience'}
        sql += f" AND book = '{book_map[args.book]}'"
    
    cur.execute(sql)
    pages = cur.fetchall()
    print(f"QC: {len(pages)} pages to check")
    
    passed, failed, skipped = 0, 0, 0
    cur2 = conn.cursor()
    
    for pg in pages:
        results = {}
        all_pass = True
        
        for check_name, check_fn in QC_CHECKS.items():
            try:
                ok = check_fn(pg)
            except:
                ok = False
            results[check_name] = ok
            if not ok:
                all_pass = False
        
        # Skip references and blank pages
        if pg['page_type'] == 'references' or not results.get('not_blank_page', True):
            status = 'skipped'
            skipped += 1
        elif all_pass:
            status = 'passed'
            passed += 1
        else:
            status = 'failed'
            failed += 1
            fails = [k for k, v in results.items() if not v]
            if args.fix:
                # Auto-fix: reclassify or skip
                if 'not_blank_page' in fails:
                    status = 'skipped'
                    skipped += 1
                    failed -= 1
        
        cur2.execute("UPDATE textbook_pages SET qc_status=%s, qc_notes=%s WHERE id=%s",
                     (status, json.dumps(results), pg['id']))
        
        # Log
        cur2.execute("""
            INSERT INTO qc_log (source_table, source_id, check_name, passed, details)
            VALUES ('textbook_pages', %s, 'full_qc', %s, %s)
        """, (pg['id'], all_pass, json.dumps(results)))
    
    conn.commit()
    conn.close()
    print(f"  Passed: {passed} | Failed: {failed} | Skipped: {skipped}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EMBEDDER AGENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def embed_request(api_key, input_data, retries=3):
    hdrs = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    for attempt in range(retries):
        try:
            r = requests.post(EMBED_URL, headers=hdrs,
                json={"model": EMBED_MODEL, "input": input_data}, timeout=60)
            if r.status_code == 429:
                time.sleep(min(30, 2**(attempt+2)))
                continue
            r.raise_for_status()
            return r.json()["data"][0]["embedding"]
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2**attempt)
            else:
                return None

def cmd_embed(args):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Only embed QC-passed pages without embeddings
    sql = """SELECT id, book, page_num, content, page_type, img_path,
                    has_figures, has_equations
             FROM textbook_pages 
             WHERE qc_status = 'passed' AND text_embedding IS NULL"""
    if args.book:
        book_map = {'DA': 'Dayan_Abbott', 'FN': 'Fundamental_Neuroscience'}
        sql += f" AND book = '{book_map[args.book]}'"
    sql += f" ORDER BY id LIMIT {args.batch}"
    
    cur.execute(sql)
    pages = cur.fetchall()
    print(f"Embedding: {len(pages)} QC-passed pages (batch={args.batch})")
    
    cur2 = conn.cursor()
    done_t, done_i = 0, 0
    
    for i, pg in enumerate(pages):
        # Text embedding (always for content > 50 chars)
        tvec = None
        if pg['content'] and len(pg['content']) > 50:
            tvec = embed_request(args.key, [pg['content'][:8000]])
            if tvec:
                cur2.execute("UPDATE textbook_pages SET text_embedding=%s WHERE id=%s",
                             (tvec, pg['id']))
                done_t += 1
            time.sleep(0.3)
        
        # Image embedding (for mixed/figure/equation pages)
        if pg['page_type'] in ('mixed', 'figure', 'equation') and pg['img_path'] and os.path.exists(pg['img_path']):
            with open(pg['img_path'], "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            ivec = embed_request(args.key, [f"data:image/jpeg;base64,{b64}"])
            if ivec:
                cur2.execute("UPDATE textbook_pages SET image_embedding=%s WHERE id=%s",
                             (ivec, pg['id']))
                done_i += 1
            time.sleep(0.3)
        
        if (i+1) % 10 == 0:
            conn.commit()
            print(f"  [{i+1}/{len(pages)}] text={done_t} image={done_i}")
    
    conn.commit()
    conn.close()
    print(f"Done: {done_t} text + {done_i} image embeddings")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STATUS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def cmd_status(args):
    conn = get_conn()
    cur = conn.cursor()
    
    print("=== Slides ===")
    cur.execute("SELECT COUNT(*), SUM(CASE WHEN embedding IS NOT NULL THEN 1 ELSE 0 END) FROM slides")
    r = cur.fetchone()
    print(f"  Total: {r[0] or 0} | Embedded: {r[1] or 0}")
    
    print("\n=== Textbook Pages ===")
    cur.execute("""
        SELECT book, qc_status, COUNT(*),
               SUM(CASE WHEN text_embedding IS NOT NULL THEN 1 ELSE 0 END),
               SUM(CASE WHEN image_embedding IS NOT NULL THEN 1 ELSE 0 END)
        FROM textbook_pages GROUP BY book, qc_status ORDER BY book, qc_status
    """)
    for r in cur.fetchall():
        print(f"  [{r[0][:2]}] {r[1]}: {r[2]} pages | text_emb={r[3]} | img_emb={r[4]}")
    
    print("\n=== QC Log ===")
    cur.execute("SELECT passed, COUNT(*) FROM qc_log GROUP BY passed")
    for r in cur.fetchall():
        print(f"  {'PASS' if r[0] else 'FAIL'}: {r[1]}")
    
    conn.close()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MIGRATE SLIDES FROM SQLITE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def cmd_migrate_slides(args):
    import sqlite3
    sconn = sqlite3.connect(args.sqlite)
    sconn.row_factory = sqlite3.Row
    
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
            ON CONFLICT (lecture, page_num) DO UPDATE SET
                embedding = EXCLUDED.embedding, qc_status = 'passed'
        """, (r['lecture'], r['lecture_title'], r['page_num'], r['content'],
              r['topics'], r['img_path'], emb))
        migrated += 1
    
    conn.commit()
    sconn.close()
    conn.close()
    print(f"Migrated {migrated} slides to PostgreSQL")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="BRI610 Pipeline Harness")
    sub = p.add_subparsers(dest='cmd')
    
    sp = sub.add_parser('parse')
    sp.add_argument('--book', choices=['DA', 'FN'])
    
    sq = sub.add_parser('qc')
    sq.add_argument('--book', choices=['DA', 'FN'])
    sq.add_argument('--fix', action='store_true')
    
    se = sub.add_parser('embed')
    se.add_argument('--key', required=True)
    se.add_argument('--book', choices=['DA', 'FN'])
    se.add_argument('--batch', type=int, default=50)
    
    ss = sub.add_parser('status')
    
    sm = sub.add_parser('migrate-slides')
    sm.add_argument('--sqlite', required=True)
    
    args = p.parse_args()
    
    if args.cmd == 'parse': cmd_parse(args)
    elif args.cmd == 'qc': cmd_qc(args)
    elif args.cmd == 'embed': cmd_embed(args)
    elif args.cmd == 'status': cmd_status(args)
    elif args.cmd == 'migrate-slides': cmd_migrate_slides(args)
    else: p.print_help()
