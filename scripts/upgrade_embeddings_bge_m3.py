#!/usr/bin/env python3
"""
Upgrade DB embeddings to BGE-M3 (1024 dim, BAAI multilingual top-tier).

What this does:
  1. Adds new vector(1024) columns: slides.embedding_v2, textbook_pages.text_embedding_v2
  2. Embeds every slide + textbook page via Ollama BGE-M3 (/api/embeddings)
  3. Creates HNSW indices on the new columns
  4. Old vector(2048) embedding columns kept as fallback (will be dropped after retriever
     migrated)

BGE-M3 advantages over current nvidia/llama-nemotron-embed-vl-1b:
  - Native multilingual (Korean tokenization much better)
  - Top of MTEB retrieval benchmark
  - 1024 dim is tighter (less storage, faster ANN)
  - Local Ollama → no API rate limit / cost

Run: python3 scripts/upgrade_embeddings_bge_m3.py
"""
from __future__ import annotations
import os, sys, json, time
import urllib.request, urllib.error
import psycopg2
from psycopg2.extras import execute_batch

DB_DSN = os.environ.get('DATABASE_URL', 'dbname=bri610 user=tutor password=tutor610 host=localhost')
OLLAMA = 'http://localhost:11434/api/embeddings'
MODEL = 'bge-m3:latest'
DIM = 1024
BATCH = 32


def embed(text: str, retries: int = 3) -> list[float] | None:
    body = json.dumps({'model': MODEL, 'prompt': text[:8000]}).encode()
    req = urllib.request.Request(OLLAMA, data=body, headers={'Content-Type': 'application/json'})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                d = json.loads(r.read())
                return d.get('embedding')
        except Exception as e:
            print(f'  retry {attempt} after {e}', file=sys.stderr)
            time.sleep(1)
    return None


def vec_literal(v):
    return '[' + ','.join(f'{x:.6f}' for x in v) + ']'


def upgrade_slides(conn):
    print('=== slides ===')
    with conn.cursor() as cur:
        # Schema: add vector(1024) column if missing
        # columns already added by table owner
        conn.commit()

        # Fetch rows that need embedding
        cur.execute("""
            SELECT id, lecture, page_num, content
            FROM slides
            WHERE content IS NOT NULL AND LENGTH(content) > 50
              AND embedding_v2 IS NULL
            ORDER BY id
        """)
        rows = cur.fetchall()
    print(f'  {len(rows)} slides to embed')

    done = 0
    for sid, lec, pn, content in rows:
        v = embed(f'[{lec} p.{pn}] {content}')
        if v is None or len(v) != DIM:
            print(f'  SKIP {lec} p.{pn} (embed failed)')
            continue
        with conn.cursor() as cur:
            cur.execute('UPDATE slides SET embedding_v2 = %s::vector WHERE id = %s', (vec_literal(v), sid))
        done += 1
        if done % 25 == 0:
            conn.commit()
            print(f'  ... {done}/{len(rows)}')
    conn.commit()
    print(f'  ✓ embedded {done}/{len(rows)}')

    # HNSW index — skip if already exists (created out-of-band as table owner)
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_indexes WHERE indexname='idx_slides_embed_v2'")
        if not cur.fetchone():
            try:
                cur.execute("CREATE INDEX idx_slides_embed_v2 ON slides USING hnsw (embedding_v2 vector_cosine_ops) WITH (m=16, ef_construction=64)")
                conn.commit()
                print('  ✓ index built')
            except Exception as e:
                conn.rollback()
                print(f'  ⚠ index creation skipped: {e}')
        else:
            print('  ✓ index already exists')


def upgrade_textbook(conn):
    print('=== textbook_pages ===')
    with conn.cursor() as cur:
        # columns already added by table owner
        conn.commit()

        cur.execute("""
            SELECT id, book, page_num, content
            FROM textbook_pages
            WHERE content IS NOT NULL AND LENGTH(content) > 100
              AND text_embedding_v2 IS NULL
            ORDER BY id
        """)
        rows = cur.fetchall()
    print(f'  {len(rows)} textbook pages to embed')

    done = 0
    for tid, book, pn, content in rows:
        v = embed(f'[{book} p.{pn}] {content}')
        if v is None or len(v) != DIM:
            print(f'  SKIP {book} p.{pn} (embed failed)')
            continue
        with conn.cursor() as cur:
            cur.execute('UPDATE textbook_pages SET text_embedding_v2 = %s::vector WHERE id = %s', (vec_literal(v), tid))
        done += 1
        if done % 50 == 0:
            conn.commit()
            print(f'  ... {done}/{len(rows)}')
    conn.commit()
    print(f'  ✓ embedded {done}/{len(rows)}')

    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_indexes WHERE indexname='idx_textbook_text_embed_v2'")
        if not cur.fetchone():
            try:
                cur.execute("CREATE INDEX idx_textbook_text_embed_v2 ON textbook_pages USING hnsw (text_embedding_v2 vector_cosine_ops) WITH (m=16, ef_construction=64)")
                conn.commit()
                print('  ✓ index built')
            except Exception as e:
                conn.rollback()
                print(f'  ⚠ index skipped: {e}')
        else:
            print('  ✓ index already exists')


def main():
    conn = psycopg2.connect(DB_DSN)
    try:
        # Verify Ollama up
        v = embed('hello world')
        if v is None or len(v) != DIM:
            print(f'BGE-M3 sanity failed: dim={len(v) if v else None}', file=sys.stderr)
            sys.exit(1)
        print(f'BGE-M3 ready (dim={len(v)})\n')

        upgrade_slides(conn)
        upgrade_textbook(conn)

        # Final stats
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 'slides' AS tbl, COUNT(*) AS rows,
                       COUNT(embedding_v2) AS new_embed
                FROM slides
                UNION ALL
                SELECT 'textbook_pages', COUNT(*), COUNT(text_embedding_v2)
                FROM textbook_pages
            """)
            print('\n=== Final ===')
            for tbl, rows, new in cur.fetchall():
                pct = 100.0 * new / rows if rows else 0
                print(f'  {tbl}: {new}/{rows} ({pct:.1f}%) embedded with BGE-M3')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
