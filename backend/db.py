"""
DB access layer v0.3 — PostgreSQL + pgvector
For BRI610 lecture slides + textbook pages (page-level, not chunk-level)

v0.5: connections are now borrowed from a shared ThreadedConnectionPool
(see backend/db_pool.py) instead of opened per call.
"""
import psycopg2, psycopg2.extras
import re, os, json
from typing import Optional

from db_pool import acquire as _pool_acquire, release as _pool_release, DB_DSN


class DB:
    def __init__(self, dsn: str = None):
        # dsn arg retained for back-compat; pool reads DATABASE_URL env at process start
        self.dsn = dsn or DB_DSN

    def _conn(self):
        return _pool_acquire()

    @staticmethod
    def _close(conn):
        _pool_release(conn)

    @staticmethod
    def sanitize_fts(query: str) -> str:
        tokens = query.split()
        safe = []
        for t in tokens:
            c = re.sub(r'[^\w]', '', t)
            if c and len(c) > 1:
                safe.append(c)
        return ' & '.join(safe) if safe else ''

    def stats(self):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM slides")
        slides = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM textbook_pages WHERE qc_status='passed'")
        pages = cur.fetchone()[0]
        # Prefer v2 (BGE-M3 1024-dim) embeddings; fall back to legacy v1 (Nemotron 2048)
        cur.execute("SELECT COUNT(*) FROM slides WHERE embedding_v2 IS NOT NULL")
        slides_v2 = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM slides WHERE embedding IS NOT NULL")
        slides_v1 = cur.fetchone()[0]
        slides_emb = max(slides_v2, slides_v1)
        cur.execute("SELECT COUNT(*) FROM textbook_pages WHERE text_embedding_v2 IS NOT NULL")
        pages_v2 = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM textbook_pages WHERE text_embedding IS NOT NULL")
        pages_v1 = cur.fetchone()[0]
        pages_emb = max(pages_v2, pages_v1)
        self._close(conn)
        return {
            "slides": slides, "textbook_pages": pages,
            "total": slides + pages,
            "embedded": slides_emb + pages_emb,
            "embedded_v2_bge_m3": slides_v2 + pages_v2,
        }

    def detailed_stats(self):
        conn = self._conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT lecture, lecture_title,
                   COUNT(*) AS total, COUNT(embedding) AS embedded
            FROM slides GROUP BY lecture, lecture_title ORDER BY lecture
        """)
        slides = [dict(r) for r in cur.fetchall()]
        cur.execute("""
            SELECT book,
                   COUNT(*) FILTER (WHERE qc_status='passed') AS total,
                   COUNT(text_embedding) FILTER (WHERE qc_status='passed') AS text_emb,
                   COUNT(image_embedding) FILTER (WHERE qc_status='passed') AS img_emb
            FROM textbook_pages GROUP BY book ORDER BY book
        """)
        books = [dict(r) for r in cur.fetchall()]
        self._close(conn)
        return {"slides": slides, "textbooks": books}

    def list_lectures(self):
        conn = self._conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT lecture AS id, lecture_title AS title, COUNT(*) AS slides
            FROM slides GROUP BY lecture, lecture_title ORDER BY lecture
        """)
        lectures = [dict(r) for r in cur.fetchall()]
        cur.execute("""
            SELECT book, chapter, chapter_title, COUNT(*) AS pages
            FROM textbook_pages
            WHERE qc_status = 'passed'
            GROUP BY book, chapter, chapter_title
            ORDER BY book, CAST(NULLIF(chapter,'') AS INTEGER) NULLS LAST
        """)
        books = [dict(r) for r in cur.fetchall()]
        self._close(conn)
        return {"lectures": lectures, "textbooks": books}

    def search_slides(self, query: str, lecture: Optional[str] = None, limit: int = 10):
        q = self.sanitize_fts(query)
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
        return [{
            "source": "slide", "id": r["id"], "lecture": r["lecture"],
            "page": r["page_num"], "title": r["lecture_title"],
            "content": r["content"], "img": r["img_path"],
            "topics": r["topics"], "score": round(float(r["rank"]), 3)
        } for r in rows]

    def search_textbook(self, query: str, limit: int = 10):
        q = self.sanitize_fts(query)
        if not q:
            return []
        conn = self._conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT id, book, page_num, chapter, chapter_title, section_title, content,
                   page_type, has_equations,
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
        return [{
            "source": "textbook", "id": r["id"], "book": r["book"],
            "chapter": r["chapter"], "chapter_title": r["chapter_title"],
            "section": "", "section_title": r["section_title"],
            "pages": str(r["page_num"]),
            "content": r["content"], "score": round(float(r["rank"]), 3)
        } for r in rows]

    def search_all(self, query: str, lecture: Optional[str] = None, limit: int = 10):
        s = self.search_slides(query, lecture, limit)
        t = self.search_textbook(query, limit)
        merged = s + t
        merged.sort(key=lambda x: -x["score"])
        return merged[:limit]

    def get_summary(self, lecture: str):
        conn = self._conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM lecture_summaries WHERE lecture = %s", (lecture,))
        row = cur.fetchone()
        self._close(conn)
        if row:
            d = dict(row)
            d['generated_at'] = d['generated_at'].isoformat() if d['generated_at'] else None
            d['feedback_at'] = d['feedback_at'].isoformat() if d['feedback_at'] else None
            return d
        return None

    def upsert_summary(self, lecture, title, summary, sources):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO lecture_summaries (lecture, lecture_title, summary, sources, generated_at)
            VALUES (%s, %s, %s, %s, now())
            ON CONFLICT (lecture) DO UPDATE SET
                summary = EXCLUDED.summary, sources = EXCLUDED.sources,
                generated_at = now(), lecture_title = EXCLUDED.lecture_title
        """, (lecture, title, summary, json.dumps(sources)))
        conn.commit()
        self._close(conn)

    def save_feedback(self, lecture, feedback):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute("""
            UPDATE lecture_summaries SET feedback = %s, feedback_at = now()
            WHERE lecture = %s
        """, (feedback, lecture))
        conn.commit()
        self._close(conn)

    def get_slide(self, lecture: str, page: int):
        conn = self._conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM slides WHERE lecture=%s AND page_num=%s", (lecture, page))
        row = cur.fetchone()
        self._close(conn)
        if row:
            d = dict(row)
            d.pop('embedding', None)
            return d
        return None

    def get_slides_range(self, lecture: str, start: int, end: int):
        conn = self._conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT id, lecture, lecture_title, page_num, content, img_path, topics
            FROM slides WHERE lecture=%s AND page_num BETWEEN %s AND %s ORDER BY page_num
        """, (lecture, start, end))
        rows = [dict(r) for r in cur.fetchall()]
        self._close(conn)
        return rows
