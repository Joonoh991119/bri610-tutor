#!/usr/bin/env python3
"""
Finalize DB:
  1. Embed remaining title-only / empty slides using lecture_title + topics
  2. Drop legacy vector(2048) columns: slides.embedding,
     textbook_pages.{text_embedding, image_embedding}
  3. Pre-generate lecture narration for all 48 steps and cache in
     `lecture_narrations` table.

Run as: python3 scripts/finalize_db.py
"""
from __future__ import annotations
import os, sys, json, time, asyncio
import urllib.request
from pathlib import Path
import psycopg2

ROOT = Path('/Users/joonoh/Projects/bri610-tutor')
sys.path.insert(0, str(ROOT / 'backend'))

DB_DSN = os.environ.get('DATABASE_URL', 'dbname=bri610 user=tutor password=tutor610 host=localhost')
OLLAMA = 'http://localhost:11434/api/embeddings'
MODEL = 'bge-m3:latest'
DIM = 1024


def embed(text: str):
    body = json.dumps({'model': MODEL, 'prompt': text[:8000]}).encode()
    req = urllib.request.Request(OLLAMA, data=body, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())['embedding']


def vec_lit(v):
    return '[' + ','.join(f'{x:.6f}' for x in v) + ']'


# ─────────────────────────────────────────────────────────────────
# 1. Embed remaining short slides (title + topics fallback)
# ─────────────────────────────────────────────────────────────────
def embed_short_slides(conn):
    print('=== Step 1: Embed remaining short slides ===')
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, lecture, page_num,
                   COALESCE(content, '') AS content,
                   COALESCE(lecture_title, '') AS lt,
                   COALESCE(topics, '') AS tp
            FROM slides
            WHERE embedding_v2 IS NULL
            ORDER BY lecture, page_num
        """)
        rows = cur.fetchall()
    print(f'  {len(rows)} slides to embed (title-only/empty)')
    done = 0
    for sid, lec, pn, content, lt, tp in rows:
        # Build a meaningful text: lecture title + page + content + topics
        parts = [f'[{lec} p.{pn}]', lt, content.strip(), tp.strip()]
        text = ' • '.join(p for p in parts if p)
        if not text:
            text = f'[{lec} p.{pn}]'
        try:
            v = embed(text)
            if len(v) != DIM:
                print(f'  SKIP {lec} p.{pn} (wrong dim)')
                continue
            with conn.cursor() as cur:
                cur.execute('UPDATE slides SET embedding_v2 = %s::vector WHERE id = %s', (vec_lit(v), sid))
            done += 1
        except Exception as e:
            print(f'  SKIP {lec} p.{pn}: {e}')
    conn.commit()
    print(f'  ✓ embedded {done}/{len(rows)}')

    # Final per-lecture check
    with conn.cursor() as cur:
        cur.execute("""
            SELECT lecture, COUNT(*) AS total, COUNT(embedding_v2) AS bge
            FROM slides GROUP BY lecture ORDER BY lecture
        """)
        for lec, t, b in cur.fetchall():
            print(f'  {lec}: {b}/{t} ({100.0*b/t:.1f}%)')


# ─────────────────────────────────────────────────────────────────
# 2. Drop legacy 2048-dim columns
# ─────────────────────────────────────────────────────────────────
def drop_legacy_columns(conn):
    print('\n=== Step 2: Drop legacy 2048-dim embedding columns ===')
    # Need to be done by table owner (joonoh). Do this via a separate psql command
    # outside this script if running as `tutor`. We'll attempt and note any failure.
    legacy_drops = [
        "ALTER TABLE slides DROP COLUMN IF EXISTS embedding CASCADE",
        "ALTER TABLE textbook_pages DROP COLUMN IF EXISTS text_embedding CASCADE",
        "ALTER TABLE textbook_pages DROP COLUMN IF EXISTS image_embedding CASCADE",
        "DROP INDEX IF EXISTS idx_slides_embedding CASCADE",
        "DROP INDEX IF EXISTS idx_textbook_text_embedding CASCADE",
        "DROP INDEX IF EXISTS idx_textbook_image_embedding CASCADE",
    ]
    for sql in legacy_drops:
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
            print(f'  ✓ {sql[:80]}')
        except psycopg2.errors.InsufficientPrivilege as e:
            conn.rollback()
            print(f'  ⚠ {sql[:60]} → needs table-owner privilege; run as joonoh')
        except Exception as e:
            conn.rollback()
            print(f'  ⚠ {sql[:60]} → {e}')


# ─────────────────────────────────────────────────────────────────
# 3. Pre-generate lecture narration into DB
# ─────────────────────────────────────────────────────────────────
async def pregen_narrations(conn):
    print('\n=== Step 3: Pre-generate 48 lecture narrations ===')
    # Create cache table if missing
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS lecture_narrations (
                id SERIAL PRIMARY KEY,
                lecture VARCHAR(10) NOT NULL,
                step_id INT NOT NULL,
                step_kind VARCHAR(32) NOT NULL,
                title_ko TEXT,
                slide_refs TEXT[],
                instruction_md TEXT,
                narration_md TEXT NOT NULL,
                model TEXT,
                generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                UNIQUE (lecture, step_id)
            )
        """)
        conn.commit()

    from agents import lecture as lecture_mod
    from harness import call_llm

    # Loop over all plans → all steps
    plans = [(getattr(lecture_mod, n), n) for n in dir(lecture_mod)
             if n.startswith('_L') and n.endswith('_PLAN')]
    plans = [(p, n) for p, n in plans if hasattr(p, 'steps')]
    plans.sort(key=lambda x: x[0].lecture_id)

    total = sum(len(p.steps) for p, _ in plans)
    print(f'  {len(plans)} plans, {total} total steps')

    sys_prompt = (
        "당신은 BRI610 박사과정 강의 가이드입니다. 학생이 이 강의를 24시간 안에 마스터하도록 "
        "각 단계를 박사 세미나 톤으로 풀어 설명합니다. 인용은 슬라이드만 사용하고, 영어 전문용어는 "
        "한국어 본문 안에 괄호로 병기. 학부 친절체 금지. 5-8 문장 / 600-1200자 분량."
    )

    done = 0
    for plan, _ in plans:
        for step in plan.steps:
            # Skip if already cached
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM lecture_narrations WHERE lecture=%s AND step_id=%s",
                            (plan.lecture_id, step.step_id))
                if cur.fetchone():
                    done += 1
                    continue

            slide_list = ", ".join(f"[Slide {r}]" for r in step.slide_refs)
            user_prompt = (
                f"강의: {plan.lecture_id} — {plan.title_ko}\n"
                f"단계 {step.step_id}/{len(plan.steps)} ({step.kind}): {step.title_ko}\n"
                f"관련 슬라이드: {slide_list}\n"
                f"학습 목표 / 지침: {step.instruction_md}\n\n"
                "위 지침을 박사 세미나 톤으로 풀어 600-1200자 narration 으로 작성하라. "
                "수식은 KaTeX $..$ 형식. 각 핵심 포인트는 *italic* 강조. "
                "마지막 줄에 '다음 단계' 한 줄 예고."
            )
            try:
                res = await call_llm(role='lecturer', system=sys_prompt, user=user_prompt,
                                     temperature=0.4, max_tokens=2000, cache=False)
                narration = (res.get('text') or '').strip()
                model = res.get('route_used', '?')
                if not narration or len(narration) < 200:
                    print(f'  SKIP {plan.lecture_id} step {step.step_id}: short/empty narration')
                    continue
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO lecture_narrations (lecture, step_id, step_kind, title_ko,
                            slide_refs, instruction_md, narration_md, model)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (lecture, step_id) DO UPDATE SET
                            narration_md = EXCLUDED.narration_md,
                            model = EXCLUDED.model,
                            generated_at = NOW()
                    """, (plan.lecture_id, step.step_id, step.kind, step.title_ko,
                          step.slide_refs, step.instruction_md, narration, model))
                conn.commit()
                done += 1
                print(f'  ✓ {plan.lecture_id} step {step.step_id} ({step.kind}, {len(narration)} chars, via {model})')
            except Exception as e:
                print(f'  ⚠ {plan.lecture_id} step {step.step_id}: {e}')

    print(f'\n  Pre-generated: {done}/{total}')


def main():
    conn = psycopg2.connect(DB_DSN)
    try:
        # 1. Short slides
        embed_short_slides(conn)
        # 2. Drop legacy
        drop_legacy_columns(conn)
        # 3. Pre-generate narrations (async)
        asyncio.run(pregen_narrations(conn))
    finally:
        conn.close()


if __name__ == '__main__':
    main()
