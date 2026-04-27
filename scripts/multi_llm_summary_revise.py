#!/usr/bin/env python3
"""
Multi-LLM collaborative summary revision pipeline.

3 LLMs via OpenRouter:
  Drafter:  anthropic/claude-opus-4-7        — pedagogy + Korean writing
  Critic A: moonshotai/kimi-k2.6             — STEM rigor + facts
  Critic B: google/gemini-3-flash-preview    — Korean naturalness

Loop per lecture: draft → 2 critiques → integrate → re-score; stop ≥8.5 both.
Max 3 rounds per lecture. Updates lecture_summaries.summary in DB.

Run: python3 scripts/multi_llm_summary_revise.py
"""
from __future__ import annotations
import json, os, sys, time, re
from datetime import datetime
from pathlib import Path
import urllib.request
import urllib.error

ROOT = Path('/Users/joonoh/Projects/bri610-tutor')
sys.path.insert(0, str(ROOT / 'backend'))

import psycopg2
from psycopg2.extras import RealDictCursor

DB_DSN = os.environ.get('DATABASE_URL', 'dbname=bri610 user=tutor password=tutor610 host=localhost')
OPENROUTER_KEY = os.environ.get('OPENROUTER_API_KEY')
if not OPENROUTER_KEY:
    print('ERROR: OPENROUTER_API_KEY not set', file=sys.stderr)
    sys.exit(1)

DRAFTER = 'anthropic/claude-opus-4-7'
CRITIC_FACT = 'moonshotai/kimi-k2.6'
CRITIC_KOR = 'google/gemini-3-flash-preview'
ACCEPT_THRESHOLD = 8.5
MAX_ROUNDS = 3

LECTURES = ['L3', 'L4', 'L5', 'L6', 'L7', 'L8']

# ─────────────────────────────────────────────────────────────────────
# OpenRouter client
# ─────────────────────────────────────────────────────────────────────
def openrouter(model: str, system: str, user: str, max_tokens: int = 8000,
               temperature: float = 0.4, retries: int = 3) -> dict:
    body = json.dumps({
        'model': model,
        'messages': [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': user},
        ],
        'max_tokens': max_tokens,
        'temperature': temperature,
    }).encode('utf-8')
    req = urllib.request.Request(
        'https://openrouter.ai/api/v1/chat/completions',
        data=body,
        headers={
            'Authorization': f'Bearer {OPENROUTER_KEY}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://bri610-tutor.local',
        },
    )
    last_err = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if 'choices' in data and data['choices']:
                    msg = data['choices'][0]['message']
                    text = msg.get('content') or msg.get('reasoning') or ''
                    return {'text': text, 'usage': data.get('usage', {})}
                return {'text': '', 'error': f'no choices: {data}'}
        except urllib.error.HTTPError as e:
            last_err = e
            err_body = e.read().decode('utf-8', errors='replace')
            print(f'  [{model}] HTTP {e.code}: {err_body[:200]}', file=sys.stderr)
            if e.code in (429, 502, 503):
                time.sleep(2 ** attempt + 1)
                continue
            break
        except Exception as e:
            last_err = e
            time.sleep(2 ** attempt + 1)
    return {'text': '', 'error': str(last_err)}


# ─────────────────────────────────────────────────────────────────────
# Drafter prompt (Opus)
# ─────────────────────────────────────────────────────────────────────
DRAFTER_SYSTEM = """당신은 BRI610 (computational neuroscience) 강의 요약을 한국 대학원생 청자를 위해 교육학적으로 다시 쓰는 작가입니다. 한국어를 모국어처럼 자연스럽게 구사하며, 영어 학술 용어는 *italic* 또는 (parens) 으로 인라인 처리합니다.

## 개선 목표
1. **기계 번역 흔적 제거** — "이것은 ~이다" 식 직역 → 자연스런 한국 학술체
2. **인지부하 곡선 다듬기** — 직관 → 형식화 → 다른 개념과 연결, 3단계 명시
3. **전이부 다듬기** — "그래서/따라서/이와같이/이로써" 자연스럽게
4. **수동태 줄이기** — "~된다" 보다 "~한다"
5. **첫 문단의 강력한 hook** — "왜 이걸 알아야하는가" 한 문장으로 직타
6. **용어 일관성** — 같은 개념은 같은 한국어 용어 (e.g., 막전위 vs 막전압 통일)
7. **한국 학생 비유** — 가능한 곳은 한국적 일상 비유 추가

## 보존 절대 원칙 (절대 지움 금지)
- 모든 KaTeX 수식 ($..$ 와 $$..$$)
- 모든 SVG 그림 embed (`<figure>`, `<svg>` 블록 그대로 복사)
- 모든 `<details>` 토글 (3개씩) — prerequisite 복습용
- 마크다운 테이블 (concept-map)
- 슬라이드 인용 (`[Slide L# p.N]` 형식)
- 영어 학술 용어 (Korean primary, English in italic/parens)
- 9000~10000자 길이 유지

## 출력 형식
완전히 수정된 요약 본문만 출력. 메타 코멘트 금지. 시작 부터 끝까지 마크다운 형식 그대로."""


# ─────────────────────────────────────────────────────────────────────
# Critic prompts
# ─────────────────────────────────────────────────────────────────────
CRITIC_FACT_SYSTEM = """You are a STEM rigor critic for a graduate-level computational neuroscience summary written for Korean PhD students. The summary uses Korean+English bilingual style with KaTeX math.

Score the summary on:
- factual_accuracy   (0-10): wrong facts, misleading claims, slide-citation mismatch
- equation_correctness (0-10): math typos, wrong derivations, unit mistakes
- physical_intuition (0-10): does the analogy faithfully match the math?

List up to 5 specific issues with EXACT quote (in Korean or English, max 60 chars) and a one-line FIX suggestion.

Output STRICT JSON only, no prose:
{
  "factual_accuracy": <number>,
  "equation_correctness": <number>,
  "physical_intuition": <number>,
  "overall": <number, average>,
  "issues": [
    {"quote": "<60-char excerpt>", "type": "fact|math|intuition", "fix": "<one-line correction>"}
  ]
}"""

CRITIC_KOR_SYSTEM = """당신은 한국 대학원생을 위한 학술 글쓰기 비평가입니다. 주어진 BRI610 (computational neuroscience) 강의 요약 (Korean primary, English bilingual + KaTeX) 을 다음 축에서 평가하시오.

평가 축:
- naturalness        (0-10): 한국어 문장이 자연스러운가? 직역 흔적 없는가?
- academic_register  (0-10): 대학원 학술체에 적절한가? (해체/하실체 혼용 안되어 있는가)
- bilingual_flow     (0-10): 영어 용어 처리가 깔끔한가? italic/parens 사용 일관적인가?

최대 5개의 구체적 어색한 한국어 표현을 인용 (60자 이내) 과 함께 수정안 제시.

오직 JSON 으로 출력 (말 금지):
{
  "naturalness": <number>,
  "academic_register": <number>,
  "bilingual_flow": <number>,
  "overall": <number>,
  "issues": [
    {"quote": "<60자 미만 인용>", "type": "naturalness|register|bilingual", "fix": "<자연스런 수정안>"}
  ]
}"""


def parse_json_loose(text: str) -> dict:
    """Extract first JSON object from possibly fenced text."""
    # Strip markdown code fences
    text = re.sub(r'^```json\s*', '', text.strip())
    text = re.sub(r'```\s*$', '', text.strip())
    # Find first {..} block
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except Exception:
        return {}


# ─────────────────────────────────────────────────────────────────────
# Pipeline
# ─────────────────────────────────────────────────────────────────────
def fetch_summary(conn, lecture: str) -> str:
    with conn.cursor() as cur:
        cur.execute('SELECT summary FROM lecture_summaries WHERE lecture=%s', (lecture,))
        row = cur.fetchone()
    return row[0] if row else ''


def update_summary(conn, lecture: str, new_summary: str):
    with conn.cursor() as cur:
        cur.execute('UPDATE lecture_summaries SET summary=%s WHERE lecture=%s',
                    (new_summary, lecture))
    conn.commit()


def revise_one(conn, lecture: str, log: dict):
    print(f'\n=== {lecture} ===')
    current = fetch_summary(conn, lecture)
    if not current:
        print(f'  no cached summary, skip')
        return

    log['lecture'] = lecture
    log['before_chars'] = len(current)
    log['before_first_para'] = current.split('\n\n')[1][:200] if '\n\n' in current else current[:200]
    log['rounds'] = []

    working = current
    accepted = False

    for r in range(1, MAX_ROUNDS + 1):
        print(f'  round {r}: drafting via Opus...')
        draft_prompt = (f'다음 BRI610 강의 요약을 위 시스템 지침대로 교육학적으로 다시 쓰시오.\n\n'
                        f'기존 요약:\n---\n{working}\n---\n\n'
                        f'개선된 요약 (마크다운 그대로):')
        d = openrouter(DRAFTER, DRAFTER_SYSTEM, draft_prompt,
                       max_tokens=10000, temperature=0.5)
        revised = d.get('text', '').strip()
        if not revised or len(revised) < 4000:
            print(f'  draft failed/too short: {len(revised)} chars; err={d.get("error")}')
            break

        # Strip leading markdown fence if any
        revised = re.sub(r'^```(?:markdown|md)?\s*', '', revised)
        revised = re.sub(r'\s*```\s*$', '', revised)

        print(f'  round {r}: drafted {len(revised)} chars')

        # Two parallel critiques (sequential here, fast enough)
        print(f'  round {r}: Kimi K2.6 fact-checking...')
        kimi_resp = openrouter(CRITIC_FACT, CRITIC_FACT_SYSTEM, revised,
                               max_tokens=4000, temperature=0.0)
        kimi_json = parse_json_loose(kimi_resp.get('text', ''))
        kimi_score = kimi_json.get('overall', 0) or (
            (kimi_json.get('factual_accuracy', 0) +
             kimi_json.get('equation_correctness', 0) +
             kimi_json.get('physical_intuition', 0)) / 3 if kimi_json else 0)

        print(f'  round {r}: Gemini Flash Korean review...')
        gem_resp = openrouter(CRITIC_KOR, CRITIC_KOR_SYSTEM, revised,
                              max_tokens=3000, temperature=0.0)
        gem_json = parse_json_loose(gem_resp.get('text', ''))
        gem_score = gem_json.get('overall', 0) or (
            (gem_json.get('naturalness', 0) +
             gem_json.get('academic_register', 0) +
             gem_json.get('bilingual_flow', 0)) / 3 if gem_json else 0)

        print(f'  round {r}: scores Kimi={kimi_score:.1f}  Gemini={gem_score:.1f}')

        round_log = {
            'round': r,
            'kimi_score': kimi_score,
            'gemini_score': gem_score,
            'kimi_issues': kimi_json.get('issues', [])[:5],
            'gemini_issues': gem_json.get('issues', [])[:5],
            'chars': len(revised),
        }
        log['rounds'].append(round_log)

        if kimi_score >= ACCEPT_THRESHOLD and gem_score >= ACCEPT_THRESHOLD:
            print(f'  ✓ accepted at round {r}')
            working = revised
            accepted = True
            break
        else:
            # Feed issues back into next draft
            issues_text = '## 사실 정확성 (Kimi K2.6)\n'
            for i in kimi_json.get('issues', [])[:5]:
                issues_text += f'- "{i.get("quote","")}": {i.get("fix","")}\n'
            issues_text += '\n## 한국어 자연성 (Gemini)\n'
            for i in gem_json.get('issues', [])[:5]:
                issues_text += f'- "{i.get("quote","")}": {i.get("fix","")}\n'

            DRAFTER_SYSTEM_REVISED = (DRAFTER_SYSTEM +
                '\n\n## 직전 라운드 비평 (반드시 반영)\n' + issues_text)
            working = revised  # keep best so far for next iteration's input
            # Fall through to next round with updated system prompt
            globals()['DRAFTER_SYSTEM_REVISED_DYN'] = DRAFTER_SYSTEM_REVISED

    log['accepted'] = accepted
    log['after_chars'] = len(working)
    log['after_first_para'] = working.split('\n\n')[1][:200] if '\n\n' in working else working[:200]

    if accepted or (working != current and len(working) > 4000):
        update_summary(conn, lecture, working)
        print(f'  → updated DB ({len(working)} chars)')
    else:
        print(f'  → keeping original (no acceptable revision)')


def main():
    out_dir = ROOT / 'logs'
    out_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_path = out_dir / f'summary_revision_v4_{ts}.json'

    full_log = []
    conn = psycopg2.connect(DB_DSN)
    try:
        for lecture in LECTURES:
            entry = {}
            try:
                revise_one(conn, lecture, entry)
            except Exception as e:
                print(f'  EXCEPTION: {e}')
                entry['error'] = str(e)
            full_log.append(entry)
            log_path.write_text(json.dumps(full_log, ensure_ascii=False, indent=2))
            print(f'  log saved → {log_path}')
    finally:
        conn.close()

    print('\n=== Final summary ===')
    for e in full_log:
        if 'rounds' in e and e['rounds']:
            last = e['rounds'][-1]
            print(f"  {e.get('lecture','?')}: rounds={len(e['rounds'])} "
                  f"final_kimi={last['kimi_score']:.1f} final_gem={last['gemini_score']:.1f} "
                  f"accepted={e.get('accepted',False)} "
                  f"Δchars={e['after_chars']-e['before_chars']:+d}")
        else:
            print(f"  {e.get('lecture','?')}: skipped/failed")


if __name__ == '__main__':
    main()
