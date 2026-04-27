#!/usr/bin/env python3
"""
1. Convert markdown emphasis inside <figcaption> to inline HTML so it
   renders properly (rehype-raw doesn't re-parse markdown inside HTML blocks).
   - **bold** → <strong>bold</strong>
   - *italic* → <em>italic</em>
2. Detect content that may not be in BRI610 slides (e.g., TASK / TREK / etc.
   specific K-leak channel families that go beyond slide scope) and replace
   with slide-faithful generalizations.
3. Idempotent — safe to re-run.
"""
import re, os, psycopg2

DB_DSN = os.environ.get('DATABASE_URL', 'dbname=bri610 user=tutor password=tutor610 host=localhost')

# Slide-unfaithful specifics → slide-faithful generalizations
SLIDE_FIDELITY_REPLACEMENTS = [
    # K leak channel families: slides say "leak channel" generically
    (r'\bTASK\s*/\s*TREK\s*류[^.\n]*', '*K leak* 채널 종류 (slides 범위에서는 family-agnostic)'),
    (r'\bTASK\s*류\b',  '*K leak* 채널'),
    (r'\bTREK\s*류\b',  '*K leak* 채널'),
    (r'\bTASK\s*-\s*\d\b', '*K leak* 채널'),
    (r'\bTREK\s*-\s*\d\b', '*K leak* 채널'),
    (r'tandem-pore K [^.\n]*?(?=\.|,|\))', '두-포어 영역 K 채널 (slides 범위 외 분자 정체)'),

    # Other potentially out-of-scope specifics — flag for now (no auto-replace)
    # (handled manually by panel pipeline downstream)
]


def convert_md_in_figcaptions(text: str) -> tuple[str, int]:
    """Inside every <figcaption>...</figcaption> block, convert markdown emphasis to HTML."""
    n_replacements = 0

    def fix(match):
        nonlocal n_replacements
        inner = match.group(1)
        # **bold** → <strong>bold</strong>  (handle ** before *)
        new_inner, k1 = re.subn(r'\*\*([^*\n]+?)\*\*', r'<strong>\1</strong>', inner)
        # *italic* → <em>italic</em>  (avoid nested * already inside HTML)
        new_inner, k2 = re.subn(r'(?<![*<])\*([^*\n]+?)\*(?![*])', r'<em>\1</em>', new_inner)
        n_replacements += k1 + k2
        return f'<figcaption>{new_inner}</figcaption>'

    out = re.sub(r'<figcaption>(.*?)</figcaption>', fix, text, flags=re.DOTALL)
    return out, n_replacements


def apply_slide_fidelity(text: str) -> tuple[str, int]:
    n = 0
    for pat, repl in SLIDE_FIDELITY_REPLACEMENTS:
        text, k = re.subn(pat, repl, text)
        n += k
    return text, n


def main():
    conn = psycopg2.connect(DB_DSN)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT lecture, summary FROM lecture_summaries ORDER BY lecture")
            rows = cur.fetchall()

        for lec, summary in rows:
            new_text, n_md = convert_md_in_figcaptions(summary)
            new_text, n_slide = apply_slide_fidelity(new_text)
            if n_md or n_slide or new_text != summary:
                with conn.cursor() as cur:
                    cur.execute("UPDATE lecture_summaries SET summary=%s WHERE lecture=%s", (new_text, lec))
                conn.commit()
                print(f'  {lec}: md→html {n_md}, slide-fidelity {n_slide} '
                      f'({len(summary)} → {len(new_text)} chars)')
            else:
                print(f'  {lec}: clean')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
