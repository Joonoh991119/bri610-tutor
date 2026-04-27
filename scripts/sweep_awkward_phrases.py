#!/usr/bin/env python3
"""
Sweep awkward translated/meta phrases from lecture_summaries.

Replacements (target → replacement):
  - "이 핸드아웃을 다 읽은 직후" → "다 읽은 직후"
  - "BRI610 박사과정 세미나 핸드아웃" prefix → drop entire prefix line
  - "$V_\text{rest}$ 붕괴" → "$V_\text{rest}$ 가 휴지값에서 이탈"
  - "식별성 깨짐" → "식별 불가능"
  - "본 강의는", "이 강의는" → drop / rephrase
  - "여러분은" → drop (academic register)
  - " 한다.\n\n " orphan period - cleanup whitespace
"""
import re
import psycopg2

DB_DSN = "dbname=bri610 user=tutor password=tutor610 host=localhost"

REPLACEMENTS = [
    # Meta-headers (drop entirely)
    (r'^# BRI610[^\n]*\n+', ''),
    (r'\bBRI610 박사과정 세미나 핸드아웃[: ]?', ''),
    (r'\bBRI610 박사과정 세미나\b', ''),

    # Handout self-references
    (r'이 핸드아웃을 다 읽은 직후', '다 읽은 직후'),
    (r'본 핸드아웃', '본 요약'),
    (r'\b핸드아웃\b', '요약'),

    # Lecture self-references (academic register: don't talk about the lecture itself)
    (r'본 강의에서는', '여기서는'),
    (r'이 강의에서는', '여기서는'),
    (r'본 강의는 ', ''),
    (r'이 강의는 ', ''),

    # Awkward translated verbs
    (r'\$V_\\text\{rest\}\$ 붕괴', r'$V_\\text{rest}$ 가 휴지값에서 이탈'),
    (r'\b식별성 깨짐\b', '식별 불가능'),
    (r'\b가정이 깨진다\b', '가정이 성립하지 않는다'),
    (r'\b가정은 깨진다\b', '가정이 성립하지 않는다'),
    (r'\b해체된다\b', '성립하지 않는다'),

    # Reader address (drop in academic register)
    (r'\b여러분은\b', ''),
    (r'\b여러분이\b', '학생이'),

    # Excess whitespace cleanup
    (r'\n{3,}', '\n\n'),
    (r' {2,}', ' '),
]


def clean(text: str) -> tuple[str, int]:
    n = 0
    for pat, repl in REPLACEMENTS:
        text, k = re.subn(pat, repl, text, flags=re.MULTILINE)
        n += k
    return text.strip() + '\n', n


def main():
    conn = psycopg2.connect(DB_DSN)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT lecture, summary FROM lecture_summaries WHERE lecture IN ('L2','L3','L4','L5','L6','L7','L8') ORDER BY lecture")
            rows = cur.fetchall()

            for L, before in rows:
                after, n = clean(before)
                if n > 0:
                    cur.execute("UPDATE lecture_summaries SET summary=%s, generated_at=NOW() WHERE lecture=%s", (after, L))
                    print(f"  {L}: {n} replacements ({len(before)} → {len(after)} chars)")
                else:
                    print(f"  {L}: clean")
            conn.commit()

            # Final verification
            print('\n=== verification: meta/awkward phrases remaining ===')
            cur.execute("""
                SELECT lecture, summary FROM lecture_summaries
                WHERE lecture IN ('L2','L3','L4','L5','L6','L7','L8')
            """)
            BAD = ['BRI610', '핸드아웃', '박사과정 세미나', '붕괴', '깨짐', '여러분', '본 강의', '이 강의']
            any_bad = False
            for L, s in cur.fetchall():
                for term in BAD:
                    if term in s:
                        any_bad = True
                        # Show context
                        for m in re.finditer(rf'.{{0,40}}{re.escape(term)}.{{0,40}}', s):
                            print(f"  [{L}] {term}: ...{m.group()}...")
                            break  # one per term
            if not any_bad:
                print('  ✓ all clean')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
