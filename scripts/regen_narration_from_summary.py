#!/usr/bin/env python3
"""
Pre-generate lecture narration in DB, grounded in lecture_summaries.

Per user spec: narration should feel like the summary content broken into
*step-by-step* pedagogical elaboration — NOT free-form commentary that drifts
from the summary.

Procedure per step:
  1. Read the matching summary section from lecture_summaries.
  2. Pass (step.instruction_md + relevant summary excerpt) to Opus via
     OpenRouter.
  3. Opus generates 3-5 numbered "step" explanations that walk through the
     summary content for THIS step, with KaTeX math preserved.
  4. Cache to lecture_narrations.

Run: python3 scripts/regen_narration_from_summary.py
"""
from __future__ import annotations
import os, sys, json, re, time
import urllib.request
from pathlib import Path
import psycopg2

ROOT = Path('/Users/joonoh/Projects/bri610-tutor')
sys.path.insert(0, str(ROOT / 'backend'))

DB_DSN = os.environ.get('DATABASE_URL', 'dbname=bri610 user=tutor password=tutor610 host=localhost')
KEY = os.environ['OPENROUTER_API_KEY']
MODEL = 'anthropic/claude-opus-4-7'  # session Opus equivalent via OR


def call_or(system, user, max_tokens=2500, retries=2, timeout=200):
    body = json.dumps({
        'model': MODEL,
        'messages': [{'role': 'system', 'content': system},
                     {'role': 'user', 'content': user}],
        'max_tokens': max_tokens,
        'temperature': 0.3,
    }).encode()
    req = urllib.request.Request('https://openrouter.ai/api/v1/chat/completions',
        data=body, headers={'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = json.loads(r.read())
                if d.get('choices'):
                    msg = d['choices'][0]['message']
                    return msg.get('content') or msg.get('reasoning') or ''
        except Exception as e:
            print(f'  retry {attempt} after {e}', file=sys.stderr)
            time.sleep(2 ** attempt)
    return ''


SYS = """당신은 BRI610 강의 가이드입니다. 학생이 *기존 요약 (summary)* 을 step-by-step 으로 풀어서 학습할 수 있도록 narration 을 생성합니다.

## 핵심 원칙
- **요약을 풀어쓰는 것**: 새로운 내용을 만들지 말고, 주어진 요약 발췌 + 이 단계의 instruction 만 가지고 narration 을 작성한다.
- **step-by-step**: 3-5 개의 *번호 매긴 sub-step* 으로 분해하라. 각 sub-step 은 1-2 문장.
- **연속 학습 흐름**: "1️⃣ 우선… 2️⃣ 그 다음… 3️⃣ 마지막으로…" 형태의 전환을 사용. 학생이 *읽는 동안 따라가는 느낌* 이 나야 함.
- **수식**: KaTeX `$..$` 그대로 보존.
- **분량**: 600-1100 자.
- 마지막 줄: `→ 다음:` 한 줄 짧은 anchor.

## 출력 형식
오직 narration 본문 (마크다운). 메타 코멘트, "여기 narration 입니다" 등 안내 문구 금지."""


def main():
    sys.path.insert(0, str(ROOT / 'backend'))
    from agents import lecture as lecture_mod

    conn = psycopg2.connect(DB_DSN)

    # Cache table
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

    # Pull summaries
    summaries = {}
    with conn.cursor() as cur:
        cur.execute("SELECT lecture, summary FROM lecture_summaries")
        for row in cur.fetchall():
            summaries[row[0]] = row[1]
    print(f'Loaded {len(summaries)} summaries')

    plans = [(getattr(lecture_mod, n), n) for n in dir(lecture_mod)
             if n.startswith('_L') and n.endswith('_PLAN')]
    plans = [(p, n) for p, n in plans if hasattr(p, 'steps')]
    plans.sort(key=lambda x: x[0].lecture_id)
    total = sum(len(p.steps) for p, _ in plans)
    print(f'{len(plans)} plans, {total} total steps\n')

    done = 0
    for plan, _ in plans:
        L = plan.lecture_id
        summary = summaries.get(L, '')
        if not summary:
            print(f'[{L}] no summary, skip')
            continue
        for step in plan.steps:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM lecture_narrations WHERE lecture=%s AND step_id=%s",
                            (L, step.step_id))
                if cur.fetchone():
                    done += 1
                    continue

            # Pull a summary excerpt — find paragraphs whose §-header keywords overlap
            # with the step title or instruction. Fallback: take first 2500 chars of summary.
            excerpt = extract_relevant_excerpt(summary, step.title_ko, step.instruction_md, step.slide_refs)

            slide_list = ", ".join(step.slide_refs)
            user = (
                f"강의: {L} — {plan.title_ko}\n"
                f"단계 {step.step_id}/{len(plan.steps)} ({step.kind}): {step.title_ko}\n"
                f"관련 슬라이드: {slide_list}\n\n"
                f"## 단계 instruction (이번 단계의 학습 목표)\n{step.instruction_md}\n\n"
                f"## 강의 요약 발췌 (이 단계와 관련된 부분)\n---\n{excerpt}\n---\n\n"
                "위 발췌를 *3-5 개 step-by-step sub-step* 으로 풀어 narration 을 작성하라. "
                "원문 요약의 사실/수식만 사용하고 외부 사실 추가 금지."
            )
            narration = call_or(SYS, user, max_tokens=2500).strip()
            narration = re.sub(r'^```(?:markdown|md)?\s*', '', narration)
            narration = re.sub(r'\s*```\s*$', '', narration)
            if len(narration) < 250:
                print(f'  ⚠ {L} step {step.step_id}: short narration ({len(narration)}), skip')
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
                """, (L, step.step_id, step.kind, step.title_ko,
                      step.slide_refs, step.instruction_md, narration, MODEL))
            conn.commit()
            done += 1
            print(f'  ✓ {L} step {step.step_id} ({step.kind}, {len(narration)} chars)')

    print(f'\nTotal pre-generated: {done}/{total}')
    conn.close()


def extract_relevant_excerpt(summary: str, title: str, instruction: str, slide_refs: list, max_chars: int = 3500) -> str:
    """Find the most relevant slice of the summary for this step."""
    # Tokenize the step title + instruction into keywords (Korean+English mixed)
    keywords = set()
    for src in (title or '', instruction or ''):
        for tok in re.findall(r'[A-Za-z_]+|[가-힣]{2,}', src):
            t = tok.lower()
            if len(t) >= 2:
                keywords.add(t)
    # Add slide page tokens
    for ref in slide_refs:
        m = re.search(r'p\.?\s*(\d+)', ref)
        if m: keywords.add(f'p.{m.group(1)}')
        keywords.add(ref.lower())

    # Score each section (## §...) by keyword hits
    sections = re.split(r'(?=^## )', summary, flags=re.MULTILINE)
    scored = []
    for sec in sections:
        text = sec[:5000].lower()
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scored.append((score, sec))
    scored.sort(key=lambda x: -x[0])

    # Take top 1-2 sections, capped at max_chars
    excerpt = ''
    for _, sec in scored[:2]:
        if len(excerpt) + len(sec) > max_chars:
            excerpt += sec[: max_chars - len(excerpt)]
            break
        excerpt += sec + '\n'
    if not excerpt:
        # Fallback: first 2500 chars of summary
        excerpt = summary[:max_chars]
    return excerpt.strip()


if __name__ == '__main__':
    main()
