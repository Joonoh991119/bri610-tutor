#!/usr/bin/env python3
"""
Retry tail restoration for L5 and L7 — they were rejected because tail was
< 800 chars. Lower threshold for these specific lectures.
"""
import os, sys, json, re, time, urllib.request, psycopg2

DB_DSN = os.environ.get('DATABASE_URL', 'dbname=bri610 user=tutor password=tutor610 host=localhost')
KEY = os.environ['OPENROUTER_API_KEY']
OPUS = 'anthropic/claude-opus-4-7'

TARGETS = {
    'L5': [
        '§9 후속 — 위에서 끝난 mid-sentence 자연스럽게 이어 쓰기 ("불응기는 m·h 가 모두..." 부터 완성)',
        '§10. HH 시뮬레이션 결과 해석 — refractory period, AHP, spike-frequency adaptation',
        '§11. 흔한 오해와 시험 함정 — 5-7 항목',
        '§12. 한 줄 요약 (blockquote)',
    ],
    'L7': [
        '§9 후속 — 위에서 끝난 mid-sentence 자연스럽게 이어 쓰기 ("실제 뉴런은 hyperpolar..." 부터 완성)',
        '§10. LIF / Izhikevich / HH 의 비교 표 (식별성, 표현력, 계산 비용)',
        '§11. 흔한 오해와 시험 함정 — 5-7 항목',
        '§12. 한 줄 요약 (blockquote)',
    ],
}


SYS = """당신은 BRI610 강의 요약의 *truncated tail* 을 복원하는 작가입니다. 입력은
(1) 본문 끝부분 (mid-sentence), (2) 복원해야 할 섹션 목록.

## 작성 원칙
- *현재 mid-sentence* 자연스럽게 **이어 쓰기**.
- 나머지 섹션은 §X.Y 헤더 + 본문으로 새 작성.
- 같은 lecture 톤·표기·용어 일관성 유지.
- KaTeX `$..$` `$$..$$` 보존, slide 인용 `[Slide L# p.N]`, cross-summary
  hyperlinks `[L3 §3.5](#summary?lecture=L3)` 형식.
- "흔한 오해" = 5-7 항목, 각 잘못된 가정 + 왜 틀린지 + 슬라이드 근거.
- "한 줄 요약" = blockquote `> ...` 1-2 문장.
- **분량 풍부하게 작성** (최소 1500-2500 chars).

## 출력
오직 tail 본문만. prefix, 안내 멘트 금지."""


def call_opus(user, max_tokens=8000, retries=2, timeout=400):
    body = json.dumps({
        'model': OPUS,
        'messages': [{'role':'system','content':SYS},{'role':'user','content':user}],
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


def main():
    conn = psycopg2.connect(DB_DSN)
    try:
        for lec, expected in TARGETS.items():
            print(f'\n=== {lec} retry ===')
            with conn.cursor() as cur:
                cur.execute("SELECT summary FROM lecture_summaries WHERE lecture=%s", (lec,))
                current = cur.fetchone()[0]
            print(f'  before: {len(current)} chars; tail: ...{current[-80:]!r}')

            user = (
                f"## 현재까지 본문 (mid-sentence)\n---\n{current[-2500:]}\n---\n\n"
                f"## 복원 섹션\n" + '\n'.join(f'- {s}' for s in expected) +
                "\n\n## 시작"
            )
            tail = call_opus(user, max_tokens=8000)
            tail = re.sub(r'^```(?:markdown|md)?\s*', '', tail.strip())
            tail = re.sub(r'\s*```\s*$', '', tail)
            print(f'  generated tail: {len(tail)} chars')
            if len(tail) < 200:
                print('  ⚠ still too short; skipping')
                continue
            new_text = (current if current.endswith('\n') else current + '\n') + tail.lstrip('\n')
            with conn.cursor() as cur:
                cur.execute("UPDATE lecture_summaries SET summary=%s, generated_at=NOW() WHERE lecture=%s",
                            (new_text, lec))
            conn.commit()
            print(f'  ✓ appended → total {len(new_text)} chars')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
