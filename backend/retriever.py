"""
Hybrid Retriever — Nemotron VL Multimodal Embedding + FTS5 with RRF fusion

Embedding strategy:
- Slides: image embedding via Nemotron VL (preserves equations, diagrams, layout)
- Textbook chunks: text embedding via Nemotron VL
- Queries: text embedding
Model: nvidia/llama-nemotron-embed-vl-1b-v2:free (2048-dim, OpenRouter)
"""
import sqlite3, struct, math, re, base64, requests, time, logging
from typing import Optional
from pathlib import Path

log = logging.getLogger(__name__)
EMBED_DIM = 2048

class HybridRetriever:
    def __init__(self, db_path: str, openrouter_key: str,
                 embed_model: str = "nvidia/llama-nemotron-embed-vl-1b-v2:free"):
        self.db_path = db_path
        self.api_key = openrouter_key
        self.embed_model = embed_model
        self.embed_url = "https://openrouter.ai/api/v1/embeddings"
        self.dim = EMBED_DIM

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ─── Embedding ───

    def _post_embed(self, payload, retries=3):
        for attempt in range(retries):
            try:
                r = requests.post(self.embed_url,
                    headers={"Authorization": f"Bearer {self.api_key}",
                             "Content-Type": "application/json"},
                    json={"model": self.embed_model, **payload},
                    timeout=60)
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

    def embed_image(self, image_path: str, caption: str = "") -> list:
        """Embed slide image — data:image/jpeg;base64 URL string format"""
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        # OpenRouter accepts base64 data URL as plain string input
        return self._post_embed({"input": [f"data:image/jpeg;base64,{b64}"]})

    # ─── Vector packing ───

    @staticmethod
    def pack_vec(vec: list) -> bytes:
        return struct.pack(f'{len(vec)}f', *vec)

    @staticmethod
    def unpack_vec(blob: bytes) -> list:
        n = len(blob) // 4
        return list(struct.unpack(f'{n}f', blob))

    @staticmethod
    def cosine_sim(a, b):
        dot = sum(x*y for x, y in zip(a, b))
        na = math.sqrt(sum(x*x for x in a))
        nb = math.sqrt(sum(x*x for x in b))
        return dot / (na * nb) if na and nb else 0.0

    @staticmethod
    def sanitize_fts(query: str) -> str:
        tokens = query.split()
        safe = []
        for t in tokens:
            if '-' in t: safe.append(f'"{t}"')
            elif re.match(r'^[a-zA-Z0-9_]+$', t): safe.append(t)
            else:
                c = re.sub(r'[^\w]', '', t)
                if c: safe.append(c)
        return ' '.join(safe)

    # ─── Search ───

    def _vector_search(self, query_vec, table, limit=20):
        conn = self._conn()
        if table == "slides":
            rows = conn.execute(
                "SELECT id, lecture, lecture_title, page_num, content, img_path, topics, embedding "
                "FROM slides WHERE embedding IS NOT NULL").fetchall()
        else:
            rows = conn.execute(
                "SELECT id, book, chapter, chapter_title, section, section_title, "
                "page_start, page_end, content, embedding "
                "FROM textbook_chunks WHERE embedding IS NOT NULL").fetchall()
        conn.close()
        scored = []
        for r in rows:
            sim = self.cosine_sim(query_vec, self.unpack_vec(r["embedding"]))
            scored.append((sim, dict(r)))
        scored.sort(key=lambda x: -x[0])
        return scored[:limit]

    def _fts_slides(self, query, lecture=None, limit=20):
        conn = self._conn()
        q = self.sanitize_fts(query)
        if not q: return []
        params = [q]
        sql = ("SELECT s.id, s.lecture, s.lecture_title, s.page_num, s.content, "
               "s.img_path, s.topics, rank "
               "FROM slides_fts f JOIN slides s ON f.rowid = s.id WHERE slides_fts MATCH ?")
        if lecture: sql += " AND s.lecture = ?"; params.append(lecture)
        sql += " ORDER BY rank LIMIT ?"; params.append(limit)
        rows = conn.execute(sql, params).fetchall()
        conn.close()
        return [(abs(r["rank"]), dict(r)) for r in rows]

    def _fts_textbook(self, query, limit=20):
        conn = self._conn()
        q = self.sanitize_fts(query)
        if not q: return []
        rows = conn.execute(
            "SELECT t.id, t.book, t.chapter, t.chapter_title, t.section, "
            "t.section_title, t.page_start, t.page_end, t.content, rank "
            "FROM textbook_chunks_fts f JOIN textbook_chunks t ON f.rowid=t.id "
            "WHERE textbook_chunks_fts MATCH ? ORDER BY rank LIMIT ?", (q, limit)
        ).fetchall()
        conn.close()
        return [(abs(r["rank"]), dict(r)) for r in rows]

    def search(self, query: str, lecture: Optional[str] = None,
               limit: int = 8, alpha: float = 0.6):
        conn = self._conn()
        has_vec = conn.execute(
            "SELECT COUNT(*) FROM slides WHERE embedding IS NOT NULL"
        ).fetchone()[0] > 0
        conn.close()

        if has_vec:
            qvec = self.embed_text(query)
            vs = self._vector_search(qvec, "slides", 15)
            vb = self._vector_search(qvec, "textbook_chunks", 15)
        else:
            vs, vb, alpha = [], [], 0.0

        fs = self._fts_slides(query, lecture, 15)
        fb = self._fts_textbook(query, 15)

        k, rrf = 60, {}
        def add(results, w, tbl):
            for rank, (_, doc) in enumerate(results):
                key = (tbl, doc["id"])
                if key not in rrf: rrf[key] = {"score": 0, "doc": doc, "table": tbl}
                rrf[key]["score"] += w / (k + rank + 1)

        if alpha > 0: add(vs, alpha, "slide"); add(vb, alpha, "textbook")
        add(fs, 1-alpha, "slide"); add(fb, 1-alpha, "textbook")

        merged = sorted(rrf.values(), key=lambda x: -x["score"])
        results = []
        for item in merged[:limit]:
            doc = item["doc"]
            doc.pop("embedding", None); doc.pop("rank", None)
            if item["table"] == "slide":
                results.append({"source":"slide","id":doc["id"],"lecture":doc["lecture"],
                    "page":doc["page_num"],"title":doc["lecture_title"],
                    "content":doc["content"][:800],"img":doc.get("img_path",""),
                    "score":round(item["score"],4)})
            else:
                results.append({"source":"textbook","id":doc["id"],"book":doc["book"],
                    "chapter":doc["chapter"],"chapter_title":doc.get("chapter_title",""),
                    "section":doc.get("section",""),"section_title":doc.get("section_title",""),
                    "pages":f"{doc.get('page_start','')}-{doc.get('page_end','')}",
                    "content":doc["content"][:800],"score":round(item["score"],4)})
        return results
