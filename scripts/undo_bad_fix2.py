"""
Undo the corruption from the bad fix2 regex.

Corruption pattern:
  Original:  **A**X**B**     (X contained <em>...</em>)
  My regex matched:  **X**  (treating closing of A and opening of B as a pair)
  Replaced with: <strong>X</strong>
  Final corrupt state: **A<strong>X</strong>B**

Detection: `**A<strong>X</strong>B**` where A and B are short prose tokens
and <strong>X</strong> contains an <em>...</em> inside.

Undo: replace `**A<strong>X</strong>B**` with `**A** X **B**`.
"""
import re, psycopg2
conn = psycopg2.connect("dbname=bri610 user=tutor password=tutor610 host=localhost")

# Match the corruption pattern. Constraints:
# - A: 1-30 chars, no ** or newline
# - X: any chars (DOTALL), bounded by </strong>
# - B: 1-30 chars, no ** or newline
# Use non-greedy on X to handle multiple instances.
pat = re.compile(
    r'\*\*([^*\n]{1,40}?)<strong>(.*?)</strong>([^*\n]{1,40}?)\*\*',
    re.DOTALL
)

def repl(m):
    a, x, b = m.group(1), m.group(2), m.group(3)
    # Reconstruct original: **A** X **B**
    # Note: the original had **A** X **B**, and X may have contained <em> which is preserved
    return f'**{a}** {x} **{b}**'

with conn.cursor() as cur:
    cur.execute("SELECT lecture, summary FROM lecture_summaries ORDER BY lecture")
    rows = cur.fetchall()

total = 0
for lec, body in rows:
    new, n = pat.subn(repl, body)
    if n:
        with conn.cursor() as cur:
            cur.execute("UPDATE lecture_summaries SET summary=%s WHERE lecture=%s", (new, lec))
        conn.commit()
        total += n
        print(f'  {lec}: {n} corruptions undone')
    else:
        print(f'  {lec}: clean')

print(f'\nTotal: {total}')
