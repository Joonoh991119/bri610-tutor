#!/usr/bin/env python3
"""
BRI610 Unified Search Harness — Slides + Textbooks
Usage:
  python3 search_lectures.py "query" [-n 8] [-l L3] [--source slides|textbook|all]
  python3 search_lectures.py --slide L3:15
  python3 search_lectures.py --list
"""
import sqlite3, argparse, json, re, sys

DB_PATH = "/home/claude/bri610_lectures.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def sanitize_fts(query):
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

def search_slides(query, lecture=None, limit=10):
    conn = get_conn()
    q = sanitize_fts(query)
    params = [q, limit] if not lecture else [q, lecture, limit]
    sql = """
        SELECT s.lecture, s.lecture_title, s.page_num, s.content, s.img_path, s.topics, rank
        FROM slides_fts f JOIN slides s ON f.rowid = s.id
        WHERE slides_fts MATCH ?
    """
    if lecture:
        sql += " AND s.lecture = ?"
    sql += " ORDER BY rank LIMIT ?"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [{"source": "slide", "lecture": r["lecture"], "page": r["page_num"],
             "title": r["lecture_title"], "content": r["content"][:600],
             "img": r["img_path"], "score": round(r["rank"], 3)} for r in rows]

def search_textbook(query, limit=10):
    conn = get_conn()
    q = sanitize_fts(query)
    rows = conn.execute("""
        SELECT t.book, t.chapter, t.chapter_title, t.section, t.section_title,
               t.page_start, t.page_end, t.content, rank
        FROM textbook_chunks_fts f JOIN textbook_chunks t ON f.rowid = t.id
        WHERE textbook_chunks_fts MATCH ?
        ORDER BY rank LIMIT ?
    """, (q, limit)).fetchall()
    conn.close()
    return [{"source": "textbook", "book": r["book"], "chapter": r["chapter"],
             "chapter_title": r["chapter_title"], "section": r["section"],
             "section_title": r["section_title"], "pages": f"{r['page_start']}-{r['page_end']}",
             "content": r["content"][:600], "score": round(r["rank"], 3)} for r in rows]

def search_all(query, lecture=None, limit=10):
    s = search_slides(query, lecture, limit)
    t = search_textbook(query, limit)
    merged = s + t
    merged.sort(key=lambda x: x["score"])
    return merged[:limit]

def get_slide(lecture, page):
    conn = get_conn()
    row = conn.execute("SELECT * FROM slides WHERE lecture=? AND page_num=?", (lecture, page)).fetchone()
    conn.close()
    return dict(row) if row else None

def list_all():
    conn = get_conn()
    print("=== Lecture Slides ===")
    for r in conn.execute("SELECT lecture, lecture_title, COUNT(*) c FROM slides GROUP BY lecture ORDER BY lecture"):
        print(f"  {r[0]}: {r[1]} ({r[2]} slides)")
    print("\n=== Textbooks ===")
    for r in conn.execute("SELECT book, chapter, chapter_title, COUNT(*) c FROM textbook_chunks GROUP BY book, chapter ORDER BY book, CAST(chapter AS INTEGER)"):
        print(f"  [{r[0]}] Ch.{r[1]}: {r[2]} ({r[3]} chunks)")
    conn.close()

def db_stats():
    conn = get_conn()
    slides = conn.execute("SELECT COUNT(*) FROM slides").fetchone()[0]
    chunks = conn.execute("SELECT COUNT(*) FROM textbook_chunks").fetchone()[0]
    conn.close()
    return {"slides": slides, "textbook_chunks": chunks, "total": slides + chunks}

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="BRI610 Unified Search")
    p.add_argument("query", nargs="?")
    p.add_argument("-l", "--lecture", help="Filter slides by lecture (L2-L6)")
    p.add_argument("-n", "--limit", type=int, default=8)
    p.add_argument("-s", "--source", choices=["slides", "textbook", "all"], default="all")
    p.add_argument("--slide", help="Get exact slide, e.g. L3:15")
    p.add_argument("--list", action="store_true")
    p.add_argument("--stats", action="store_true")
    p.add_argument("--json", action="store_true", help="Output as JSON")
    args = p.parse_args()

    if args.list:
        list_all()
    elif args.stats:
        print(json.dumps(db_stats(), indent=2))
    elif args.slide:
        lec, pg = args.slide.split(":")
        r = get_slide(lec, int(pg))
        print(json.dumps(r, indent=2, ensure_ascii=False) if r else "Not found")
    elif args.query:
        fn = {"slides": search_slides, "textbook": search_textbook, "all": search_all}[args.source]
        kw = {"query": args.query, "limit": args.limit}
        if args.source == "slides":
            kw["lecture"] = args.lecture
        results = fn(**kw)
        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            for i, r in enumerate(results):
                if r["source"] == "slide":
                    print(f"\n[{i+1}] SLIDE {r['lecture']} p{r['page']} | {r['title']} (score: {r['score']})")
                    print(f"    {r['content'][:180]}...")
                else:
                    print(f"\n[{i+1}] BOOK [{r['book']}] Ch.{r['chapter']} S{r['section']} '{r['section_title']}' pp.{r['pages']} (score: {r['score']})")
                    print(f"    {r['content'][:180]}...")
    else:
        p.print_help()
