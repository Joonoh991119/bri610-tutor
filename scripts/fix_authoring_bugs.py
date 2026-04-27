"""
Fix authoring bugs in summaries:
1. $($X$)$  →  $(X)$        (broken nested math-in-paren)
2. $($X$)   →  $(X)$        (missing closing dollar variant)
3. **X<em>Y</em>Z**  →  <strong>X<em>Y</em>Z</strong>  (md bold can't span html elements)
4. orphan $ adjacent to text like `**reversal potential E_X$ 를` — fix common patterns

Run sequentially, idempotently.
"""
import re, psycopg2
conn = psycopg2.connect("dbname=bri610 user=tutor password=tutor610 host=localhost")

def fix1_nested_paren_math(body):
    """`$($X$)$` and `$($X$)` → `$(X)$`"""
    n = 0
    # Variant A: $(\$ ... \$)$ — full match
    new, k = re.subn(r'\$\(\$([^$\n]+?)\$\)\$', r'$($1)$', body)
    n += k
    # Variant B: $(\$ ... \$) — closing $ missing
    new, k = re.subn(r'\$\(\$([^$\n]+?)\$\)', r'$($1)$', new)
    n += k
    return new, n


def fix2_md_bold_with_em(body):
    """**X<em>Y</em>Z** → <strong>X<em>Y</em>Z</strong>"""
    n = 0
    # Match **...** that contains <em> tags
    pattern = re.compile(r'\*\*((?:(?!\*\*).){1,500}?<em>.*?</em>(?:(?!\*\*).){0,500}?)\*\*', re.DOTALL)
    def repl(m):
        nonlocal n
        n += 1
        return f'<strong>{m.group(1)}</strong>'
    new = pattern.sub(repl, body)
    return new, n


def fix3_orphan_dollar_in_em(body):
    """`E_X$ 를` style — orphan $ that should have been `$E_X$` with opening dollar.
       Look for `\b[A-Z][A-Za-z]?_(\w|\{[^}]+\})\$\s` patterns where no opening $ precedes within 50 chars."""
    n = 0
    # Pattern: WordWithSubscript$ followed by space (orphan close)
    # Find orphan $ — odd dollars before this position
    pattern = re.compile(r'(\b[A-Z][A-Za-z]?_(?:[A-Za-z0-9]|\{[^}]+\}))\$(\s)')
    def repl(m):
        # check if even number of $ before this position
        nonlocal n
        # Use start position — count dollars before
        pre = body[:m.start()]
        n_dollars = pre.count('$') - pre.count(r'\$')
        if n_dollars % 2 == 0:
            # opening dollar missing — wrap the symbol
            n += 1
            return f'${m.group(1)}${m.group(2)}'
        return m.group(0)
    new = pattern.sub(repl, body)
    return new, n


with conn.cursor() as cur:
    cur.execute("SELECT lecture, summary FROM lecture_summaries ORDER BY lecture")
    rows = cur.fetchall()

totals = {1:0, 2:0, 3:0}
for lec, body in rows:
    orig = body
    body, n1 = fix1_nested_paren_math(body)
    body, n2 = fix2_md_bold_with_em(body)
    body, n3 = fix3_orphan_dollar_in_em(body)
    if body != orig:
        with conn.cursor() as cur:
            cur.execute("UPDATE lecture_summaries SET summary=%s WHERE lecture=%s", (body, lec))
        conn.commit()
    totals[1] += n1; totals[2] += n2; totals[3] += n3
    print(f'  {lec}: nested-paren={n1}, md-bold-em→html={n2}, orphan-$={n3}')

print(f'\nTotals: nested-paren={totals[1]}, md-bold-em→html={totals[2]}, orphan-$={totals[3]}')
