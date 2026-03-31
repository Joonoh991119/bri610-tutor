#!/usr/bin/env python3
"""
Build textbook chunks in SQLite FTS5 from PDF.
Usage: python build_textbook_db.py <pdf_path> <book_name> [--db ../data/bri610_lectures.db]
"""
import fitz
import sqlite3
import re
import argparse

def ensure_schema(conn):
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS textbook_chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book TEXT NOT NULL,
        chapter TEXT,
        chapter_title TEXT,
        section TEXT,
        section_title TEXT NOT NULL,
        page_start INTEGER,
        page_end INTEGER,
        content TEXT NOT NULL,
        topics TEXT DEFAULT ''
    )""")
    # Check if FTS table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='textbook_chunks_fts'")
    if not c.fetchone():
        c.execute("""
        CREATE VIRTUAL TABLE textbook_chunks_fts USING fts5(
            book, chapter, chapter_title, section, section_title, content, topics,
            content=textbook_chunks, content_rowid=id
        )""")
        for sql in [
            """CREATE TRIGGER IF NOT EXISTS tc_ai AFTER INSERT ON textbook_chunks BEGIN
                INSERT INTO textbook_chunks_fts(rowid, book, chapter, chapter_title, section, section_title, content, topics)
                VALUES (new.id, new.book, new.chapter, new.chapter_title, new.section, new.section_title, new.content, new.topics);
            END""",
            """CREATE TRIGGER IF NOT EXISTS tc_au AFTER UPDATE ON textbook_chunks BEGIN
                INSERT INTO textbook_chunks_fts(textbook_chunks_fts, rowid, book, chapter, chapter_title, section, section_title, content, topics)
                VALUES ('delete', old.id, old.book, old.chapter, old.chapter_title, old.section, old.section_title, old.content, old.topics);
                INSERT INTO textbook_chunks_fts(rowid, book, chapter, chapter_title, section, section_title, content, topics)
                VALUES (new.id, new.book, new.chapter, new.chapter_title, new.section, new.section_title, new.content, new.topics);
            END""",
            """CREATE TRIGGER IF NOT EXISTS tc_ad AFTER DELETE ON textbook_chunks BEGIN
                INSERT INTO textbook_chunks_fts(textbook_chunks_fts, rowid, book, chapter, chapter_title, section, section_title, content, topics)
                VALUES ('delete', old.id, old.book, old.chapter, old.chapter_title, old.section, old.section_title, old.content, old.topics);
            END""",
        ]:
            c.execute(sql)
    conn.commit()

def build(pdf_path, book_name, db_path, max_chunk=4000):
    doc = fitz.open(pdf_path)
    toc = doc.get_toc()
    
    sections = sorted([{"level": l, "title": t, "page": p} for l, t, p in toc], key=lambda x: x["page"])
    for i in range(len(sections)):
        sections[i]["page_end"] = sections[i+1]["page"] - 1 if i+1 < len(sections) else len(doc)

    conn = sqlite3.connect(db_path)
    ensure_schema(conn)
    c = conn.cursor()

    # Remove existing entries for this book
    c.execute("DELETE FROM textbook_chunks WHERE book=?", (book_name,))

    current_chapter = ""
    current_chapter_title = ""
    inserted = 0

    for sec in sections:
        title = sec["title"]
        m_ch = re.match(r'^(\d+)\.\s+(.+)', title)
        m_sec = re.match(r'^(\d+)\.(\d+)\s+(.+)', title)

        if m_ch and not m_sec:
            current_chapter = m_ch.group(1)
            current_chapter_title = m_ch.group(2)

        section_id = f"{m_sec.group(1)}.{m_sec.group(2)}" if m_sec else ""
        section_title = m_sec.group(3) if m_sec else title

        full_text = ""
        for p in range(max(0, sec["page"] - 1), min(len(doc), sec["page_end"])):
            full_text += doc[p].get_text() + "\n"
        full_text = full_text.strip()
        if len(full_text) < 20:
            continue

        if len(full_text) <= max_chunk:
            chunks = [full_text]
        else:
            paragraphs = re.split(r'\n\s*\n', full_text)
            chunks, current = [], ""
            for para in paragraphs:
                if len(current) + len(para) > max_chunk and current:
                    chunks.append(current.strip())
                    current = para
                else:
                    current += "\n\n" + para if current else para
            if current.strip():
                chunks.append(current.strip())

        for i, chunk in enumerate(chunks):
            chunk_sec = section_id if len(chunks) == 1 else f"{section_id}[{i+1}/{len(chunks)}]"
            c.execute("""INSERT INTO textbook_chunks 
                (book, chapter, chapter_title, section, section_title, page_start, page_end, content, topics)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (book_name, current_chapter, current_chapter_title, chunk_sec, section_title,
                 sec["page"], sec["page_end"], chunk, ""))
            inserted += 1

    conn.commit()
    c.execute("SELECT COUNT(*) FROM textbook_chunks WHERE book=?", (book_name,))
    print(f"Inserted {c.fetchone()[0]} chunks for '{book_name}'")
    conn.close()
    doc.close()

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("pdf", help="Path to textbook PDF")
    p.add_argument("book_name", help="Short book identifier (e.g. Dayan_Abbott)")
    p.add_argument("--db", default="../data/bri610_lectures.db")
    p.add_argument("--max-chunk", type=int, default=4000)
    args = p.parse_args()
    build(args.pdf, args.book_name, args.db, args.max_chunk)
