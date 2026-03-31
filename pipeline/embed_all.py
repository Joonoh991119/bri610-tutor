#!/usr/bin/env python3
"""
BRI610 Embedding Pipeline
Generates Nemotron VL multimodal embeddings for all slides and textbook chunks.

Slides: embedded as images (preserves equations, diagrams)
Textbook chunks: embedded as text

Usage:
  python embed_all.py --key <openrouter_key> [--db ../data/bri610_lectures.db]
  python embed_all.py --key <key> --slides-only   # just slides
  python embed_all.py --key <key> --text-only      # just textbook
  python embed_all.py --key <key> --check          # show progress
"""
import sqlite3, struct, base64, requests, time, argparse, sys
from pathlib import Path

MODEL = "nvidia/llama-nemotron-embed-vl-1b-v2:free"
API_URL = "https://openrouter.ai/api/v1/embeddings"
DIM = 2048

def ensure_schema(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Add embedding column if not exists
    for table in ["slides", "textbook_chunks"]:
        cols = [r[1] for r in c.execute(f"PRAGMA table_info({table})")]
        if "embedding" not in cols:
            c.execute(f"ALTER TABLE {table} ADD COLUMN embedding BLOB")
            print(f"Added embedding column to {table}")
    conn.commit()
    conn.close()

def pack_vec(vec):
    return struct.pack(f'{len(vec)}f', *vec)

def embed_request(api_key, payload, retries=3):
    for attempt in range(retries):
        try:
            r = requests.post(API_URL,
                headers={"Authorization": f"Bearer {api_key}",
                         "Content-Type": "application/json"},
                json={"model": MODEL, **payload}, timeout=90)
            if r.status_code == 429:
                wait = min(30, 2 ** (attempt + 2))
                print(f"  Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r.json()["data"][0]["embedding"]
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"  FAILED: {e}")
                return None

def embed_slides(db_path, api_key, force=False):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    if force:
        rows = c.execute("SELECT id, lecture, page_num, content, img_path FROM slides").fetchall()
    else:
        rows = c.execute("SELECT id, lecture, page_num, content, img_path FROM slides WHERE embedding IS NULL").fetchall()
    
    total = len(rows)
    print(f"\n{'='*50}")
    print(f"Embedding {total} slides as IMAGES (Nemotron VL)")
    print(f"{'='*50}")
    
    done = 0
    for i, (sid, lec, page, content, img_path) in enumerate(rows):
        img_file = Path(img_path) if img_path else None
        
        if img_file and img_file.exists():
            # Multimodal: image + OCR text caption
            with open(img_file, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            input_content = [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
            ]
            # Add OCR text as caption if available
            if content and len(content) > 30 and not content.startswith("[Visual"):
                input_content.append({"type": "text", "text": content[:1500]})
            
            vec = embed_request(api_key, {"input": [input_content]})
        elif content and len(content) > 20:
            # Text-only fallback
            vec = embed_request(api_key, {"input": [content[:4000]]})
        else:
            continue
        
        if vec:
            c.execute("UPDATE slides SET embedding=? WHERE id=?", (pack_vec(vec), sid))
            done += 1
        
        if (i + 1) % 5 == 0 or i == total - 1:
            conn.commit()
            print(f"  [{i+1}/{total}] {lec} p{page} ✓ ({done} embedded)")
        
        time.sleep(0.3)  # rate limit courtesy
    
    conn.commit()
    conn.close()
    print(f"Slides done: {done}/{total}")
    return done

def embed_textbook(db_path, api_key, force=False):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    if force:
        rows = c.execute("SELECT id, book, chapter, section_title, content FROM textbook_chunks").fetchall()
    else:
        rows = c.execute("SELECT id, book, chapter, section_title, content FROM textbook_chunks WHERE embedding IS NULL").fetchall()
    
    total = len(rows)
    print(f"\n{'='*50}")
    print(f"Embedding {total} textbook chunks as TEXT")
    print(f"{'='*50}")
    
    done = 0
    for i, (tid, book, ch, sec, content) in enumerate(rows):
        if not content or len(content) < 30:
            continue
        
        vec = embed_request(api_key, {"input": [content[:8000]]})
        
        if vec:
            c.execute("UPDATE textbook_chunks SET embedding=? WHERE id=?", (pack_vec(vec), tid))
            done += 1
        
        if (i + 1) % 10 == 0 or i == total - 1:
            conn.commit()
            print(f"  [{i+1}/{total}] {book} Ch.{ch} '{sec[:30]}' ({done} embedded)")
        
        time.sleep(0.2)
    
    conn.commit()
    conn.close()
    print(f"Textbook done: {done}/{total}")
    return done

def check_progress(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    total_s = c.execute("SELECT COUNT(*) FROM slides").fetchone()[0]
    emb_s = c.execute("SELECT COUNT(*) FROM slides WHERE embedding IS NOT NULL").fetchone()[0]
    total_t = c.execute("SELECT COUNT(*) FROM textbook_chunks").fetchone()[0]
    emb_t = c.execute("SELECT COUNT(*) FROM textbook_chunks WHERE embedding IS NOT NULL").fetchone()[0]
    
    print(f"Slides:    {emb_s}/{total_s} embedded ({emb_s/total_s*100:.0f}%)" if total_s else "Slides: 0")
    print(f"Textbook:  {emb_t}/{total_t} embedded ({emb_t/total_t*100:.0f}%)" if total_t else "Textbook: 0")
    print(f"Total:     {emb_s+emb_t}/{total_s+total_t}")
    conn.close()

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="BRI610 Embedding Pipeline")
    p.add_argument("--key", required=True, help="OpenRouter API key")
    p.add_argument("--db", default="../data/bri610_lectures.db")
    p.add_argument("--slides-only", action="store_true")
    p.add_argument("--text-only", action="store_true")
    p.add_argument("--force", action="store_true", help="Re-embed everything")
    p.add_argument("--check", action="store_true", help="Show progress only")
    args = p.parse_args()
    
    if args.check:
        check_progress(args.db)
        sys.exit(0)
    
    ensure_schema(args.db)
    
    if not args.text_only:
        embed_slides(args.db, args.key, args.force)
    if not args.slides_only:
        embed_textbook(args.db, args.key, args.force)
    
    print("\n=== Final Status ===")
    check_progress(args.db)
