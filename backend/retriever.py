"""
Hybrid Retriever v0.3 — PostgreSQL + pgvector + Full-Text Search with RRF Fusion

Retrieval strategy (accuracy-first):
- Slides: image embedding (Nemotron VL 2048-dim) via pgvector cosine
- Textbook pages: DUAL retrieval
  * text_embedding: primary (semantic text search)
  * image_embedding: supplementary for equation/mixed/figure pages
  * Final score = max(text_sim, image_sim) per page
- Full-text search via PostgreSQL tsvector (GIN index)
- RRF fusion merges vector + FTS results

Model: nvidia/llama-nemotron-embed-vl-1b-v2:free (2048-dim, OpenRouter)

v0.5: connections borrowed from shared db_pool (ThreadedConnectionPool).
"""
import psycopg2, psycopg2.extras
import re, requests, time, logging, os
from typing import Optional

from db_pool import acquire as _pool_acquire, release as _pool_release, DB_DSN

log = logging.getLogger(__name__)

EMBED_DIM = 2048


class HybridRetriever:
    def __init__(self, openrouter_key: str,
                 embed_model: str = "nvidia/llama-nemotron-embed-vl-1b-v2:free",
                 db_dsn: str = None):
        self.db_dsn = db_dsn or DB_DSN
        self.api_key = openrouter_key
        self.embed_model = embed_model
        self.embed_url = "https://openrouter.ai/api/v1/embeddings"
        self.dim = EMBED_DIM

    def _conn(self):
        conn = _pool_acquire()
        # Per-conn statement timeout (cheap; idempotent across borrows)
        with conn.cursor() as c:
            c.execute("SET statement_timeout = '30s'")
        return conn

    @staticmethod
    def _close(conn):
        _pool_release(conn)

    # ─── Embedding ───

    def _post_embed(self, payload, retries=3):
        for attempt in range(retries):
            try:
                r = requests.post(self.embed_url,
                    headers={"Authorization": f"Bearer {self.api_key}",
                             "Content-Type": "application/json"},
                    json={"model": self.embed_model, **payload},
                    timeout=60)
                if r.status_code == 429:
                    time.sleep(min(30, 2 ** (attempt + 2)))
                    continue
                r.raise_for_status()
                return r.json()["data"][0]["embedding"]
            except (requests.exceptions.RequestException, KeyError) as e:
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    log.error(f"Embedding failed: {e}")
                    raise

    def embed_text(self, text: str) -> list:
        return self._post_embed({"input": [text[:8000]]})

    # ─── FTS helper ───

    @staticmethod
    def sanitize_fts(query: str, op: str = "&") -> str:
        """Build a safe tsquery string. op='&' = AND (strict), op='|' = OR (lenient)."""
        tokens = query.split()
        safe = []
        for t in tokens:
            c = re.sub(r'[^\w]', '', t)
            if c and len(c) > 1:
                safe.append(c)
        return f' {op} '.join(safe) if safe else ''

    # ─── Vector Search (pgvector brute-force cosine) ───

    def _vector_search_slides(self, query_vec, lecture=None, limit=15):
        """Cosine similarity search on slides.embedding. Honors lecture filter."""
        conn = self._conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if lecture:
            cur.execute("""
                SELECT id, lecture, lecture_title, page_num, content, img_path, topics,
                       1 - (embedding <=> %s::vector) AS similarity
                FROM slides
                WHERE embedding IS NOT NULL AND lecture = %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """, (query_vec, lecture, query_vec, limit))
        else:
            cur.execute("""
                SELECT id, lecture, lecture_title, page_num, content, img_path, topics,
                       1 - (embedding <=> %s::vector) AS similarity
                FROM slides
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """, (query_vec, query_vec, limit))
        rows = cur.fetchall()
        self._close(conn)
        return [(r['similarity'], dict(r)) for r in rows]

    def _vector_search_textbook(self, query_vec, limit=15):
        """
        Dual-vector search on textbook_pages:
        - text_embedding <=> query (primary)
        - image_embedding <=> query (supplementary for visual pages)
        Score = max(text_sim, image_sim) — ensures no information loss
        """
        conn = self._conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT id, book, page_num, chapter, chapter_title, section_title,
                   content, page_type, has_equations, has_figures,
                   CASE WHEN text_embedding IS NOT NULL
                        THEN 1 - (text_embedding <=> %(vec)s::vector) ELSE 0 END AS text_sim,
                   CASE WHEN image_embedding IS NOT NULL
                        THEN 1 - (image_embedding <=> %(vec)s::vector) ELSE 0 END AS img_sim
            FROM textbook_pages
            WHERE qc_status = 'passed'
              AND (text_embedding IS NOT NULL OR image_embedding IS NOT NULL)
            ORDER BY GREATEST(
                COALESCE(1 - (text_embedding <=> %(vec)s::vector), 0),
                COALESCE(1 - (image_embedding <=> %(vec)s::vector), 0)
            ) DESC
            LIMIT %(limit)s
        """, {'vec': query_vec, 'limit': limit})
        rows = cur.fetchall()
        self._close(conn)
        return [(max(r['text_sim'] or 0, r['img_sim'] or 0), dict(r)) for r in rows]

    # ─── Full-Text Search (PostgreSQL tsvector) ───

    def _fts_slides(self, query, lecture=None, limit=15):
        # Strict AND first; if 0 hits, fall back to OR (lenient).
        for op in ("&", "|"):
            q = self.sanitize_fts(query, op=op)
            if not q:
                return []
            conn = self._conn()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            sql = """
                SELECT id, lecture, lecture_title, page_num, content, img_path, topics,
                       ts_rank_cd(to_tsvector('english', COALESCE(content,'') || ' ' || COALESCE(topics,'')),
                                  to_tsquery('english', %s)) AS rank
                FROM slides
                WHERE to_tsvector('english', COALESCE(content,'') || ' ' || COALESCE(topics,''))
                      @@ to_tsquery('english', %s)
            """
            params = [q, q]
            if lecture:
                sql += " AND lecture = %s"
                params.append(lecture)
            sql += " ORDER BY rank DESC LIMIT %s"
            params.append(limit)
            cur.execute(sql, params)
            rows = cur.fetchall()
            self._close(conn)
            if rows:
                return [(r['rank'], dict(r)) for r in rows]
        return []

    def _fts_textbook(self, query, limit=15):
        for op in ("&", "|"):
            q = self.sanitize_fts(query, op=op)
            if not q:
                return []
            conn = self._conn()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("""
                SELECT id, book, page_num, chapter, chapter_title, section_title,
                       content, page_type, has_equations, has_figures,
                       ts_rank_cd(to_tsvector('english', COALESCE(content,'') || ' ' || COALESCE(section_title,'')),
                                  to_tsquery('english', %s)) AS rank
                FROM textbook_pages
                WHERE qc_status = 'passed'
                  AND to_tsvector('english', COALESCE(content,'') || ' ' || COALESCE(section_title,''))
                      @@ to_tsquery('english', %s)
                ORDER BY rank DESC LIMIT %s
            """, (q, q, limit))
            rows = cur.fetchall()
            self._close(conn)
            if rows:
                return [(r['rank'], dict(r)) for r in rows]
        return []

    # ─── RRF Fusion ───

    def search(self, query: str, lecture: Optional[str] = None,
               source: str = "all", limit: int = 8, alpha: float = 0.6):
        """
        Hybrid search with Reciprocal Rank Fusion.
        alpha: weight for vector search (1-alpha for FTS)
        source: "all" | "slides" | "textbook" — restricts which corpus is searched
        """
        want_slides = source in ("all", "slides")
        want_textbook = source in ("all", "textbook")

        # Check if any embeddings exist
        conn = self._conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM slides WHERE embedding IS NOT NULL")
        has_vec = cur.fetchone()[0] > 0
        cur.execute("SELECT COUNT(*) FROM textbook_pages WHERE text_embedding IS NOT NULL OR image_embedding IS NOT NULL")
        has_tb_vec = cur.fetchone()[0] > 0
        self._close(conn)

        # Vector search (lecture-scoped on slides)
        vs, vb = [], []
        if (want_slides and has_vec) or (want_textbook and has_tb_vec):
            try:
                qvec = self.embed_text(query)
                if want_slides and has_vec:
                    vs = self._vector_search_slides(qvec, lecture=lecture, limit=15)
                if want_textbook and has_tb_vec:
                    vb = self._vector_search_textbook(qvec, 15)
            except Exception as e:
                log.warning(f"Vector search failed, falling back to FTS: {e}")
                alpha = 0.0

        if not ((want_slides and has_vec) or (want_textbook and has_tb_vec)):
            alpha = 0.0

        # FTS search
        fs = self._fts_slides(query, lecture, 15) if want_slides else []
        fb = self._fts_textbook(query, 15) if want_textbook else []

        # RRF merge
        k, rrf = 60, {}

        def add(results, w, tbl):
            for rank, (_, doc) in enumerate(results):
                key = (tbl, doc["id"])
                if key not in rrf:
                    rrf[key] = {"score": 0, "doc": doc, "table": tbl}
                rrf[key]["score"] += w / (k + rank + 1)

        if alpha > 0:
            if want_slides:
                add(vs, alpha, "slide")
            if want_textbook:
                add(vb, alpha, "textbook")
        if want_slides:
            add(fs, 1 - alpha, "slide")
        if want_textbook:
            add(fb, 1 - alpha, "textbook")

        merged = sorted(rrf.values(), key=lambda x: -x["score"])
        results = []
        for item in merged[:limit]:
            doc = item["doc"]
            # Clean up internal fields
            for k_remove in ('rank', 'similarity', 'text_sim', 'img_sim',
                             'text_embedding', 'image_embedding', 'embedding'):
                doc.pop(k_remove, None)

            if item["table"] == "slide":
                results.append({
                    "source": "slide", "id": doc["id"],
                    "lecture": doc["lecture"], "page": doc["page_num"],
                    "title": doc.get("lecture_title", ""),
                    "content": (doc.get("content") or "")[:800],
                    "img": doc.get("img_path", ""),
                    "score": round(item["score"], 4),
                })
            else:
                results.append({
                    "source": "textbook", "id": doc["id"],
                    "book": doc.get("book", ""),
                    "chapter": doc.get("chapter", ""),
                    "chapter_title": doc.get("chapter_title", ""),
                    "section": "",  # page-level, no section_num
                    "section_title": doc.get("section_title", ""),
                    "pages": str(doc.get("page_num", "")),
                    "content": (doc.get("content") or "")[:800],
                    "page_type": doc.get("page_type", ""),
                    "has_equations": doc.get("has_equations", False),
                    "score": round(item["score"], 4),
                })

        return results
