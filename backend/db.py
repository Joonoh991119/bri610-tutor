"""DB access layer for BRI610 lecture slides + textbook chunks"""
import sqlite3
import re
from typing import Optional

class DB:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def sanitize_fts(query: str) -> str:
        tokens = query.split()
        safe = []
        for t in tokens:
            if '-' in t:
                safe.append(f'"{t}"')
            elif re.match(r'^[a-zA-Z0-9_]+$', t):
                safe.append(t)
            else:
                cleaned = re.sub(r'[^\w]', '', t)
                if cleaned:
                    safe.append(cleaned)
        return ' '.join(safe)

    def stats(self):
        conn = self._conn()
        slides = conn.execute("SELECT COUNT(*) FROM slides").fetchone()[0]
        chunks = conn.execute("SELECT COUNT(*) FROM textbook_chunks").fetchone()[0]
        conn.close()
        return {"slides": slides, "textbook_chunks": chunks, "total": slides + chunks}

    def list_lectures(self):
        conn = self._conn()
        lectures = []
        for r in conn.execute("SELECT lecture, lecture_title, COUNT(*) c FROM slides GROUP BY lecture ORDER BY lecture"):
            lectures.append({"id": r[0], "title": r[1], "slides": r[2]})
        books = []
        for r in conn.execute("SELECT book, chapter, chapter_title, COUNT(*) c FROM textbook_chunks GROUP BY book, chapter ORDER BY book, CAST(chapter AS INTEGER)"):
            books.append({"book": r[0], "chapter": r[1], "chapter_title": r[2], "chunks": r[3]})
        conn.close()
        return {"lectures": lectures, "textbooks": books}

    def search_slides(self, query: str, lecture: Optional[str] = None, limit: int = 10):
        conn = self._conn()
        q = self.sanitize_fts(query)
        if not q:
            return []
        params = [q]
        sql = """
            SELECT s.id, s.lecture, s.lecture_title, s.page_num, s.content, s.img_path, s.topics, rank
            FROM slides_fts f JOIN slides s ON f.rowid = s.id
            WHERE slides_fts MATCH ?
        """
        if lecture:
            sql += " AND s.lecture = ?"
            params.append(lecture)
        sql += " ORDER BY rank LIMIT ?"
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()
        conn.close()
        return [{"source": "slide", "id": r["id"], "lecture": r["lecture"], "page": r["page_num"],
                 "title": r["lecture_title"], "content": r["content"],
                 "img": r["img_path"], "topics": r["topics"],
                 "score": round(r["rank"], 3)} for r in rows]

    def search_textbook(self, query: str, limit: int = 10):
        conn = self._conn()
        q = self.sanitize_fts(query)
        if not q:
            return []
        rows = conn.execute("""
            SELECT t.id, t.book, t.chapter, t.chapter_title, t.section, t.section_title,
                   t.page_start, t.page_end, t.content, rank
            FROM textbook_chunks_fts f JOIN textbook_chunks t ON f.rowid = t.id
            WHERE textbook_chunks_fts MATCH ?
            ORDER BY rank LIMIT ?
        """, (q, limit)).fetchall()
        conn.close()
        return [{"source": "textbook", "id": r["id"], "book": r["book"],
                 "chapter": r["chapter"], "chapter_title": r["chapter_title"],
                 "section": r["section"], "section_title": r["section_title"],
                 "pages": f"{r['page_start']}-{r['page_end']}",
                 "content": r["content"], "score": round(r["rank"], 3)} for r in rows]

    def search_all(self, query: str, lecture: Optional[str] = None, limit: int = 10):
        s = self.search_slides(query, lecture, limit)
        t = self.search_textbook(query, limit)
        merged = s + t
        merged.sort(key=lambda x: x["score"])
        return merged[:limit]

    def get_slide(self, lecture: str, page: int):
        conn = self._conn()
        row = conn.execute("SELECT * FROM slides WHERE lecture=? AND page_num=?", (lecture, page)).fetchone()
        conn.close()
        if row:
            d = dict(row)
            return d
        return None

    def get_slides_range(self, lecture: str, start: int, end: int):
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM slides WHERE lecture=? AND page_num BETWEEN ? AND ? ORDER BY page_num",
            (lecture, start, end)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
