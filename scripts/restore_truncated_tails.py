#!/usr/bin/env python3
"""
EMERGENCY RESTORATION — 7 lecture summaries got truncated mid-sentence by
panel R3 (max_tokens=12000 hit on Opus integration).

Strategy: for each lecture, identify the truncation point + missing sections,
then ask Opus (via OpenRouter, max_tokens=8000) to generate ONLY the missing
tail. Append the result to existing summary, fixing mid-sentence break.

Each lecture originally had sections through §10 or §11 + "흔한 오해와 시험
함정" + 한 줄 요약 footer. The truncated state visible last:
  L2 §8 → needs §9 (or end), §10 footer
  L3 §9 (intro only) → §9.1-§9.5, §10, §11 흔한 오해
  L4 §9 → §10, §11 흔한 오해
  L5 §9 → §10, §11 흔한 오해
  L6 §9 → §10, §11 흔한 오해
  L7 §9 → §10, §11 흔한 오해
  L8 §9 → §10, §11 흔한 오해, §12 한 줄 요약
"""
from __future__ import annotations
import os, sys, json, re, time, urllib.request, psycopg2
from pathlib import Path

DB_DSN = os.environ.get('DATABASE_URL', 'dbname=bri610 user=tutor password=tutor610 host=localhost')
KEY = os.environ['OPENROUTER_API_KEY']
OPUS = 'anthropic/claude-opus-4-7'

LECTURES = ['L2', 'L3', 'L4', 'L5', 'L6', 'L7', 'L8']

EXPECTED_TAIL_SECTIONS = {
    # lecture: list of section markers that should exist after the visible cutoff
    'L2': ['§9. 추가 학습 자료 — D&A Preface 핵심 표현', '§10. 한 줄 요약'],
    'L3': ['§9.1 $C_m$ — 정전용량은 변화에서만 보인다',
           '§9.2 $R_m$ — 정상상태에서만 보인다',
           '§9.3 $\\tau_m$ — 시간 척도 그 자체',
           '§9.4 $E_K$ (또는 일반 $E_X$) — *반전 전위* 가 답이다',
           '§9.5 표로 요약 (참조용)',
           '§10. 흔한 오해와 시험 함정',
           '§11. 한 줄 요약'],
    'L4': ['§9 후속 — AMPA/NMDA/GABA reversal 표 완성',
           '§10. PSP의 시간 모양 — Alpha function 의 두 시간 척도',
           '§11. 흔한 오해와 시험 함정',
           '§12. 한 줄 요약'],
    'L5': ['§9 후속 — HH 수치 시뮬레이션 완성',
           '§10. 활동전위의 4 phase 와 ionic 흐름 매핑',
           '§11. 흔한 오해와 시험 함정',
           '§12. 한 줄 요약'],
    'L6': ['§9 후속 — Cable PDE dissipation 항 완성',
           '§10. 무수초 vs 수초 propagation 차이',
           '§11. 흔한 오해와 시험 함정',
           '§12. 한 줄 요약'],
    'L7': ['§9 후속 — 모델 선택 = 지도 축척 선택 완성',
           '§10. LIF / Izhikevich / HH 의 식별성 비교',
           '§11. 흔한 오해와 시험 함정',
           '§12. 한 줄 요약'],
    'L8': ['§9 후속 — 보편 부호는 없다 완성',
           '§10. Phase precession + multiplexed code',
           '§11. 흔한 오해와 시험 함정',
           '§12. 한 줄 요약'],
}


def call_opus(system: str, user: str, max_tokens: int = 9000, retries: int = 2, timeout: int = 400) -> str:
    body = json.dumps({
        'model': OPUS,
        'messages': [{'role':'system','content':system},{'role':'user','content':user}],
        'max_tokens': max_tokens, 'temperature': 0.3,
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
            time.sleep(2 ** attempt + 1)
    return ''


SYS = """당신은 BRI610 (computational neuroscience) 강의 요약의 *truncated tail*
부분을 복원하는 작가입니다. 받은 입력은 (1) 요약의 *현재까지 보존된 본문*, (2) *복원해야
할 섹션 목록*. 당신의 임무는 *이미 작성된 본문 다음 줄부터* 시작해서 표시된 섹션을 모두
완성하는 것이다.

## 작성 원칙
- *현재 본문이 끝난 mid-sentence* 가 있으면 자연스럽게 **이어 쓰기**.
- 나머지 섹션은 §X.Y 헤더 + 본문으로 새로 작성.
- 같은 lecture 의 톤·표기·용어 일관성 유지 (English-original 학술어 + Korean 설명).
- 모든 KaTeX `$..$` `$$..$$` 보존.
- Slide 인용 `[Slide L# p.N]` 사용.
- Cross-summary hyperlinks `[L3 §3.5](#summary?lecture=L3)` 형식 유지.
- 목록·표·`<details>` 토글 자유롭게 사용.
- **흔한 오해와 시험 함정** 섹션은 5-7개 항목 (각 항목 = 잘못된 가정 + 왜 틀린지 + 슬라이드 근거).
- **한 줄 요약** 섹션은 blockquote 형식 (`> ...`) 으로 lecture 핵심 1-2 문장.

## 출력 형식
오직 *복원해야 할 tail 만* 출력한다. 기존 본문 prefix 는 출력 금지. 메타 코멘트, "여기부터 추가합니다" 등 안내 금지. 첫 줄부터 바로 mid-sentence 이어 쓰기 또는 새 §X.Y 헤더 시작."""


def restore(conn, lec):
    print(f'\n=== {lec} restoring tail ===')
    with conn.cursor() as cur:
        cur.execute("SELECT summary FROM lecture_summaries WHERE lecture=%s", (lec,))
        row = cur.fetchone()
    if not row:
        print('  no summary, skip')
        return
    current = row[0]
    print(f'  current length: {len(current)} chars')
    print(f'  last 100 chars: ...{current[-100:]!r}')

    expected = EXPECTED_TAIL_SECTIONS.get(lec, [])
    if not expected:
        print('  no expected tail; skip')
        return

    user = (
        f"## 현재까지 보존된 본문 (mid-sentence 끝남)\n"
        f"---\n{current[-2500:]}\n---\n\n"
        f"## 복원해야 할 섹션\n" +
        '\n'.join(f"- {s}" for s in expected) +
        f"\n\n## 복원 작성"
    )
    raw = call_opus(SYS, user, max_tokens=9000)
    tail = re.sub(r'^```(?:markdown|md)?\s*', '', raw.strip())
    tail = re.sub(r'\s*```\s*$', '', tail)
    if len(tail) < 800:
        print(f'  ⚠ tail too short ({len(tail)} chars), skip')
        return

    # Append tail with clean newline boundary
    if not current.endswith('\n'):
        current += '\n'
    new_text = current + tail.lstrip('\n')

    with conn.cursor() as cur:
        cur.execute("UPDATE lecture_summaries SET summary=%s, generated_at=NOW() WHERE lecture=%s",
                    (new_text, lec))
    conn.commit()
    print(f'  ✓ appended {len(tail)} chars → total {len(new_text)} chars')


def main():
    conn = psycopg2.connect(DB_DSN)
    try:
        for lec in LECTURES:
            restore(conn, lec)
    finally:
        conn.close()
    print('\n=== restoration complete ===')


if __name__ == '__main__':
    main()
