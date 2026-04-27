"""
Inside $$..$$ display math, remove inner $..$ delimiters (they're invalid).
Pattern: $$X$Y$Z$$ → $$XYZ$$
"""
import re, psycopg2
conn = psycopg2.connect("dbname=bri610 user=tutor password=tutor610 host=localhost")

def fix_block(m):
    inner = m.group(1)
    # Strip inner $ that aren't escaped
    cleaned = re.sub(r'(?<!\\)\$', '', inner)
    return f'$${cleaned}$$'

with conn.cursor() as cur:
    cur.execute("SELECT lecture, summary FROM lecture_summaries ORDER BY lecture")
    rows = cur.fetchall()

total = 0
for lec, body in rows:
    # Match $$..$$ blocks (single-line for now since multi-line $$$$ not common)
    new, n = re.subn(r'\$\$([^$\n]+(?:\$[^$\n]+\$[^$\n]*)+)\$\$', fix_block, body)
    if new != body:
        with conn.cursor() as cur:
            cur.execute("UPDATE lecture_summaries SET summary=%s WHERE lecture=%s", (new, lec))
        conn.commit()
        # count actual fixes
        before_dollars = body.count('$')
        after_dollars = new.count('$')
        diff = (before_dollars - after_dollars)
        total += diff // 2
        print(f'  {lec}: {diff//2} inner $ pairs removed')
    else:
        print(f'  {lec}: clean')
print(f'\nTotal: {total}')
