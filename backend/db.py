"""
DB access layer v0.3 — PostgreSQL + pgvector
For BRI610 lecture slides + textbook pages (page-level, not chunk-level)
"""
import psycopg2, psycopg2.extras
from pgvector.psycopg2 import register_vector
import re, os
from typing import Optional

DB_DSN = os.environ.get("DATABASE_URL", "dbname=bri610 user=tutor password=tutor610 host=localhost")


class DB:
    def __init__(self, dsn: str = None):
        self.dsn = dsn or DB_DSN

    def _conn(self):
        conn = psycopg2.connect(self.dsn)
        register_vector(conn)
        return conn

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
        cur.execute("SELECT COUNT(*) FROM slides WHERE embedding IS NOT NULL")
        slides_emb = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM textbook_pages WHERE qc_status='passed' AND text_embedding IS NOT NULL")
        pages_emb = cur.fetchone()[0]
        conn.close()
        return {
            "slides": slides, "textbook_pages": pages,
            "total": slides + pages,
            "embedded": slides_emb + pages_emb,
        }

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
        conn.close()
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
        conn.close()
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
        conn.close()
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

    def get_slide(self, lecture: str, page: int):
        conn = self._conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM slides WHERE lecture=%s AND page_num=%s", (lecture, page))
        row = cur.fetchone()
        conn.close()
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
        conn.close()
        return rows
