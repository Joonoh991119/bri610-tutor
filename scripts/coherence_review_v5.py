#!/usr/bin/env python3
"""
Coherence review v5 — figure × text × analogy joint check.

Reviewers (parallel, then merged):
  Opus       (anthropic/claude-opus-4-7 via OpenRouter)
  DeepSeek   (deepseek/deepseek-v4-pro)

Each reviews: does the surrounding text accurately describe the embedded figures
and do the analogies map cleanly to the math? Output → issues list.

Loop per lecture (max 2 rounds, 30-min total budget):
  1. Both critics review current summary independently.
  2. Merge issues; if combined score ≥ 8.5 → accept.
  3. Else: Opus drafts revision applying both critic issue-lists.
  4. Re-score once. Accept best version → DB.

Run: python3 scripts/coherence_review_v5.py
"""
from __future__ import annotations
import json, os, sys, time, re
from datetime import datetime
from pathlib import Path
import urllib.request, urllib.error
import threading

ROOT = Path('/Users/joonoh/Projects/bri610-tutor')
sys.path.insert(0, str(ROOT / 'backend'))

import psycopg2

DB_DSN = os.environ.get('DATABASE_URL', 'dbname=bri610 user=tutor password=tutor610 host=localhost')
OPENROUTER_KEY = os.environ['OPENROUTER_API_KEY']

LECTURES = ['L3', 'L4', 'L5', 'L6', 'L7', 'L8']
ACCEPT = 8.5
MAX_ROUNDS = 2
TOTAL_BUDGET_S = 1700  # 28 min hard ceiling

OPUS = 'anthropic/claude-opus-4-7'
DEEPSEEK = 'deepseek/deepseek-v4-pro'


def call(model, system, user, max_tokens=6000, temperature=0.3, retries=2, timeout=240):
    body = json.dumps({
        'model': model,
        'messages': [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': user},
        ],
        'max_tokens': max_tokens,
        'temperature': temperature,
    }).encode()
    req = urllib.request.Request(
        'https://openrouter.ai/api/v1/chat/completions',
        data=body,
        headers={'Authorization': f'Bearer {OPENROUTER_KEY}', 'Content-Type': 'application/json'},
    )
    last_err = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = json.loads(r.read())
                if d.get('choices'):
                    msg = d['choices'][0]['message']
                    return msg.get('content') or msg.get('reasoning') or ''
                return ''
        except urllib.error.HTTPError as e:
            last_err = f'HTTP {e.code}: {e.read().decode()[:200]}'
            print(f'    [{model}] {last_err}', file=sys.stderr)
            if e.code in (429, 502, 503): time.sleep(2 ** attempt + 1)
            else: break
        except Exception as e:
            last_err = str(e)
            time.sleep(2 ** attempt + 1)
    print(f'    [{model}] failed: {last_err}', file=sys.stderr)
    return ''


def parse_json(text):
    text = re.sub(r'^```(?:json)?\s*', '', text.strip())
    text = re.sub(r'\s*```\s*$', '', text)
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if not m: return {}
    try: return json.loads(m.group(0))
    except: return {}


# ─────────────────────────────────────────────────────────────────────
# Prompts
# ─────────────────────────────────────────────────────────────────────
REVIEW_SYSTEM = """You are reviewing a graduate-level Korean+English BRI610 (computational neuroscience) summary that contains:
- KaTeX equations ($..$ and $$..$$)
- Inline SVG figures (`<figure><svg>..</svg></figure>`)
- Pedagogical analogies in Korean
- Sequential numbered derivation steps
- `<details>` toggles for prerequisite reminders

YOUR JOB: judge whether the figures, text, and analogies form a *coherent* knowledge-delivery package for a Korean PhD student rusty on differential equations.

Score 0-10 on:
- figure_text_alignment: does the surrounding prose accurately describe what each figure shows? Are figure callouts (e.g. "1/e ≈ 37%") matched in the text?
- analogy_accuracy: does each analogy faithfully map to the underlying physics/math? No misleading shortcuts.
- pedagogical_flow: intuition → formalization → connection — are these three steps present and well-sequenced?
- bilingual_clarity: Korean primary text natural for native readers? English terms inline appropriately?
- derivation_completeness: are the numbered steps mathematically correct AND each step clearly motivated?

List up to 6 specific issues. Each issue: short EXACT quote (≤80 chars), category, concrete fix.

OUTPUT STRICT JSON only:
{
  "scores": {
    "figure_text_alignment": <0-10>,
    "analogy_accuracy": <0-10>,
    "pedagogical_flow": <0-10>,
    "bilingual_clarity": <0-10>,
    "derivation_completeness": <0-10>,
    "overall": <average>
  },
  "issues": [
    {"quote": "<≤80 chars>", "category": "figure|analogy|flow|korean|math", "fix": "<one-line>"}
  ]
}"""


REVISE_SYSTEM = """당신은 BRI610 강의 요약을 다음 비평가들의 지적을 반영하여 다시 쓰는 작가입니다.
입력: 기존 요약 + Opus 비평 + DeepSeek 비평.
출력: 비평을 모두 반영한 개선 요약 (마크다운 형식 그대로).

## 절대 보존 (수정 금지)
- 모든 KaTeX 수식 ($..$, $$..$$)
- 모든 SVG 그림 embed (`<figure>...<svg>...`) — 본문 SVG 코드는 한 글자도 건드리지 마라
- 모든 `<details>` prerequisite 토글 (3개)
- 마크다운 테이블, 슬라이드 인용, 영어 학술 용어 (italic/parens)
- 9000-10000자 길이

## 개선 우선순위
1. 그림과 본문의 정량 일치 — 그림에서 보이는 값/곡선이 본문 설명과 정확히 매칭
2. 비유의 정확성 — 비유가 수식의 본질을 왜곡하지 않는가
3. 한국어 자연성 — 직역 흔적 제거, 학술 어휘 일관성
4. 직관 → 형식화 → 연결 3단계 명시적으로

## 출력 형식
완전한 마크다운 요약. 메타 코멘트, 자기 소개, 변경사항 요약 모두 금지. 본문만."""


# ─────────────────────────────────────────────────────────────────────
# Pipeline
# ─────────────────────────────────────────────────────────────────────
def review_parallel(summary):
    """Both reviewers run in threads, return combined dict."""
    out = {}
    def go(model, key):
        text = call(model, REVIEW_SYSTEM, summary, max_tokens=4000, temperature=0.0)
        out[key] = parse_json(text)
    t1 = threading.Thread(target=go, args=(OPUS, 'opus'))
    t2 = threading.Thread(target=go, args=(DEEPSEEK, 'deepseek'))
    t1.start(); t2.start()
    t1.join(); t2.join()
    return out


def merged_score(rev):
    o = rev.get('opus', {}).get('scores', {}).get('overall', 0)
    d = rev.get('deepseek', {}).get('scores', {}).get('overall', 0)
    o = o or 0; d = d or 0
    return (o + d) / 2 if (o > 0 and d > 0) else max(o, d)


def merged_issues(rev):
    issues = []
    for key in ('opus', 'deepseek'):
        for i in rev.get(key, {}).get('issues', [])[:6]:
            i['source'] = key
            issues.append(i)
    return issues


def revise(summary, issues):
    issue_block = '## 비평가 지적 사항 (전부 반영하시오)\n'
    for i in issues:
        issue_block += f"- [{i.get('source','?')}/{i.get('category','?')}] \"{i.get('quote','')}\" → {i.get('fix','')}\n"
    user = (
        f'기존 요약:\n---\n{summary}\n---\n\n{issue_block}\n\n'
        f'개선된 요약 (마크다운 본문만, SVG/<details>/수식/길이 모두 보존):'
    )
    return call(OPUS, REVISE_SYSTEM, user, max_tokens=10000, temperature=0.4, timeout=300)


def coherence_loop(conn, lecture, log):
    print(f'\n=== {lecture} ===')
    with conn.cursor() as cur:
        cur.execute('SELECT summary FROM lecture_summaries WHERE lecture=%s', (lecture,))
        row = cur.fetchone()
    if not row:
        print('  no cached summary, skip')
        return
    current = row[0]

    log['lecture'] = lecture
    log['before_chars'] = len(current)
    log['rounds'] = []

    best = current
    best_score = 0

    for r in range(1, MAX_ROUNDS + 1):
        print(f'  round {r}: parallel review (Opus + DeepSeek)...')
        rev = review_parallel(best)
        score = merged_score(rev)
        issues = merged_issues(rev)
        opus_s = rev.get('opus', {}).get('scores', {}).get('overall', 0) or 0
        deep_s = rev.get('deepseek', {}).get('scores', {}).get('overall', 0) or 0
        print(f'  round {r}: Opus={opus_s:.1f}  DeepSeek={deep_s:.1f}  merged={score:.1f}  issues={len(issues)}')

        log['rounds'].append({
            'round': r, 'opus_score': opus_s, 'deepseek_score': deep_s,
            'merged': score, 'issues': issues[:8],
        })

        if score >= ACCEPT:
            print(f'  ✓ accepted at round {r}')
            log['accepted_round'] = r
            break

        if r < MAX_ROUNDS:
            print(f'  round {r}: drafting revision...')
            revised = revise(best, issues)
            revised = re.sub(r'^```(?:markdown|md)?\s*', '', revised.strip())
            revised = re.sub(r'\s*```\s*$', '', revised)
            if len(revised) > 5000:
                best = revised
                best_score = score  # last round's pre-revision score; the next round will reassess
            else:
                print(f'    revision too short ({len(revised)}); keeping previous')

    if log['rounds']:
        log['after_chars'] = len(best)
        if best != current:
            with conn.cursor() as cur:
                cur.execute('UPDATE lecture_summaries SET summary=%s WHERE lecture=%s',
                            (best, lecture))
            conn.commit()
            print(f'  → DB updated ({len(best)} chars)')
        else:
            print(f'  → kept original')


def main():
    out = ROOT / 'logs' / f'coherence_v5_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    out.parent.mkdir(exist_ok=True)
    full = []
    conn = psycopg2.connect(DB_DSN)
    t0 = time.time()
    try:
        for L in LECTURES:
            elapsed = time.time() - t0
            if elapsed > TOTAL_BUDGET_S:
                print(f'\n*** budget exceeded ({elapsed:.0f}s), stopping at {L}')
                break
            entry = {}
            try: coherence_loop(conn, L, entry)
            except Exception as e:
                entry['error'] = str(e)
                print(f'  EXCEPTION: {e}')
            full.append(entry)
            out.write_text(json.dumps(full, ensure_ascii=False, indent=2))
    finally:
        conn.close()
    print(f'\n=== Final ===')
    for e in full:
        if e.get('rounds'):
            r = e['rounds'][-1]
            print(f"  {e.get('lecture','?'):4s} merged={r['merged']:.1f} "
                  f"(Opus={r['opus_score']:.1f} DS={r['deepseek_score']:.1f}) "
                  f"accepted_at={e.get('accepted_round','-')} "
                  f"Δchars={e.get('after_chars',e.get('before_chars',0))-e.get('before_chars',0):+d}")


if __name__ == '__main__':
    main()
