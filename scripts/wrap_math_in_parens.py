"""
Sweep DB summaries for math-like patterns inside parentheses that aren't
wrapped in $..$ delimiters. Common cases:
  - (V_m), (V_inf), (V_rest), (E_K), (E_Na), etc.
  - (C_m dV/dt = ...)
  - (g_X), (I_inj), (I_C), (I_R)
  - (m^3 h), (n^4)

Apply $..$ wrapping. Idempotent: skip if already wrapped.
"""
import re, psycopg2

conn = psycopg2.connect("dbname=bri610 user=tutor password=tutor610 host=localhost")

# Pattern 1: bare variable like V_m, E_K, I_inj inside paren or italic
# Match `(VAR)` where VAR contains _ or = or / and isn't already in $..$
# Conservative: only match patterns that clearly look like math (contain _, =, /, ^).

# We'll match parentheticals that have:
#  - one or more $..$ already, OR
#  - bare math-looking content
# And rewrite bare ones to $..$.

# Allowed varchars before/after to avoid matching inside existing $..$:
# Skip if surrounded by $ already.

# Strategy: find each `(content)` group. If content has math markers (_,=,/,^,Greek)
# and content doesn't already include $, wrap content in $..$.

MATH_TOKEN_RE = re.compile(r'[A-Za-z](?:_(?:[A-Za-z]|\{[^}]+\}|\d)|\^(?:[A-Za-z]|\{[^}]+\}|\d))')

def contains_math_token(s):
    return bool(MATH_TOKEN_RE.search(s)) or '\\' in s

def rewrite_paren(m):
    inner = m.group(1)
    # already has $..$ ? leave it
    if '$' in inner:
        return m.group(0)
    # contains math?
    if not contains_math_token(inner):
        return m.group(0)
    # contains pure prose markers like ', ', or Korean explanation? Don't wrap if it's mostly prose.
    # Only wrap if the inner is MOSTLY math (>50% non-Hangul non-space ASCII).
    hangul = sum(1 for c in inner if '가' <= c <= '힣')
    if hangul > 4:  # too much Korean text mixed in — skip
        return m.group(0)
    # Wrap it
    return f'(${inner}$)'

# Also handle: `*english (V_m)*` style — V_m inside italic emphasis
# This is the table cell pattern. 

# Plus pattern: bare vars inside narrative sentences like "휴지 V_m"
# We won't auto-wrap bare vars without parens to avoid false positives.

with conn.cursor() as cur:
    cur.execute("SELECT lecture, summary FROM lecture_summaries ORDER BY lecture")
    rows = cur.fetchall()

total_changes = 0
for lec, body in rows:
    new = re.sub(r'\(([^()$\n]{2,80})\)', rewrite_paren, body)
    n = sum(1 for _ in re.finditer(r'\(\$', new)) - sum(1 for _ in re.finditer(r'\(\$', body))
    if new != body:
        with conn.cursor() as cur:
            cur.execute("UPDATE lecture_summaries SET summary=%s WHERE lecture=%s", (new, lec))
        conn.commit()
        # count actual diff
        diff = abs(len(new) - len(body))
        total_changes += n
        print(f'  {lec}: {n} parentheticals wrapped, {diff} char delta')
    else:
        print(f'  {lec}: clean')

print(f'\nTotal $-wraps inserted: {total_changes}')
conn.close()
