#!/usr/bin/env python3
"""
ingest_lecture_pdf.py — render a lecture PDF into the v0.4 `slides` schema.

For each page in the PDF:
  - Rasterize to data/L<N>/p<NN>.jpg @ 150 DPI
  - Extract page text via PyMuPDF
  - UPSERT a row into `slides` (lecture, page_num, content, topics, img_path)

Embedding is a SEPARATE step (use pipeline_harness.py embed --book ... or call
the OpenRouter embed endpoint directly). This script only handles page-level
ingestion so the new lecture appears in the lecture dropdown + Slides tab + SRS
citations immediately.

Usage:
    python scripts/ingest_lecture_pdf.py L7 \
        "/Users/joonoh/Downloads/Lecture 7 Different types of models (2026).pdf" \
        --title "Different types of models"

    python scripts/ingest_lecture_pdf.py L8 \
        "/Users/joonoh/Downloads/Lecture 8 Neural Codes.pdf" \
        --title "Neural Codes"
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "backend"))

from db_pool import acquire, release  # noqa: E402

import fitz  # PyMuPDF


def render_and_ingest(lecture: str, pdf_path: Path, lecture_title: str,
                       data_root: Path, dpi: int = 150) -> int:
    out_dir = data_root / lecture
    out_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_path))
    print(f"[{lecture}] {pdf_path.name} — {doc.page_count} pages → {out_dir}")

    rows: list[tuple] = []
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)

    for i, page in enumerate(doc, start=1):
        # 1) rasterize
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img_name = f"p{i:02d}.jpg"
        img_full = out_dir / img_name
        pix.save(str(img_full), jpg_quality=85)

        # 2) extract text
        text = page.get_text("text") or ""
        # cheap topic guess: first 90 chars first non-empty line, title-cased headers
        first_line = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
        topics = first_line[:120]

        # img_path stored relative to data/ root (matches existing slide rows)
        rel_img = f"{lecture}/{img_name}"

        rows.append((lecture, lecture_title, i, text.strip(), topics, rel_img))

    doc.close()

    # 3) UPSERT into slides
    conn = acquire()
    inserted = updated = 0
    try:
        with conn.cursor() as cur:
            for r in rows:
                cur.execute("""
                    INSERT INTO slides (lecture, lecture_title, page_num, content, topics, img_path, qc_status)
                    VALUES (%s,%s,%s,%s,%s,%s,'passed')
                    ON CONFLICT (lecture, page_num) DO UPDATE
                      SET lecture_title = EXCLUDED.lecture_title,
                          content       = EXCLUDED.content,
                          topics        = EXCLUDED.topics,
                          img_path      = EXCLUDED.img_path,
                          qc_status     = 'passed'
                    RETURNING (xmax = 0) AS inserted
                """, r)
                was_insert = cur.fetchone()[0]
                if was_insert:
                    inserted += 1
                else:
                    updated += 1
        conn.commit()
    finally:
        release(conn)

    print(f"  ↳ inserted {inserted} / updated {updated} rows in `slides`")
    return inserted + updated


def main():
    p = argparse.ArgumentParser()
    p.add_argument("lecture", help="lecture id, e.g. L7")
    p.add_argument("pdf", help="path to source PDF")
    p.add_argument("--title", required=True, help="lecture title (no 'Lecture N' prefix)")
    p.add_argument("--data-root", default=str(ROOT / "data"))
    p.add_argument("--dpi", type=int, default=150)
    args = p.parse_args()

    data_root = Path(args.data_root)
    pdf = Path(args.pdf)
    if not pdf.is_file():
        sys.exit(f"PDF not found: {pdf}")

    n = render_and_ingest(args.lecture, pdf, args.title, data_root, dpi=args.dpi)
    print(f"DONE — {n} pages.")


if __name__ == "__main__":
    main()
