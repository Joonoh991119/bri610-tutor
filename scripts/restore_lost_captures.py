"""
Restore math captures lost by fix1 backref bug ($1 instead of \1).

Each `$($1)$` was originally `$(<math>)$`. Reconstruct from context.
"""
import re, psycopg2
conn = psycopg2.connect("dbname=bri610 user=tutor password=tutor610 host=localhost")

# Per-lecture mapping: ordered occurrences and their replacement.
# Identified from context grep above.
RESTORATIONS = {
    'L4': [
        ('$($1)$>0$', '$(V - E_X)>0$'),
        ('$($1)$<0$', '$(V - E_X)<0$'),
        ('Driving force $($1)$ 의', 'Driving force $(V - E_X)$ 의'),
        ('R_m I_0\\,($1 - e^{-t/\\tau_m}$)$', 'R_m I_0\\,(1 - e^{-t/\\tau_m})$'),
        ('Driving force $($1)$ 가', 'Driving force $(V - E_X)$ 가'),
        ('$dg/dt = A($1 - t/t_\\text{peak}$)e^{-t/t_\\text{peak}} = 0$', '$dg/dt = A(1 - t/t_\\text{peak})e^{-t/t_\\text{peak}} = 0$'),
    ],
    'L5': [
        ('driving force $($1)$ 가', 'driving force $(V - E_\\text{Na})$ 가'),
        ('Driving force $($1)$ 는', 'Driving force $(V-E_X)$ 는'),
    ],
    'L6': [
        # L6 has: `R_m / R_i$ 만 결정 — $($1)$ 와 $($1)$ 는 정확히 동일한 $\lambda$ ... 무한히 많은 $($1)$ 조합이 동일`
        # First $($1)$ → (R_m, R_i)
        # Second $($1)$ → (2R_m, 2R_i)
        # Third $($1)$ → (R_m, R_i)
        # Fourth $($1)$ → (R_m, R_i)
        # We do them in order via simple scan.
    ],
}

# L6 is more delicate; do it inline below

with conn.cursor() as cur:
    cur.execute("SELECT lecture, summary FROM lecture_summaries WHERE lecture IN ('L4','L5','L6')")
    rows = cur.fetchall()

for lec, body in rows:
    orig = body
    if lec == 'L6':
        # Sequential replacement
        replacements = [
            '$(R_m, R_i)$',
            '$(2 R_m, 2 R_i)$',
            '$(R_m, R_i)$',
            '$(R_m, R_i)$ \\to (kR_m, kR_i)$',
        ]
        # Simpler: targeted by surrounding context
        body = body.replace('$($1)$ 와 $($1)$ 는 정확히', '$(R_m, R_i)$ 와 $(2 R_m, 2 R_i)$ 는 정확히', 1)
        body = body.replace('무한히 많은 $($1)$ 조합', '무한히 많은 $(R_m, R_i)$ 조합', 1)
        body = body.replace('$($1)$ \\to ($kR_m, kR_i$)$ scaling', '$(R_m, R_i) \\to (kR_m, kR_i)$ scaling', 1)
    else:
        for old, new in RESTORATIONS.get(lec, []):
            body = body.replace(old, new, 1)
    if body != orig:
        with conn.cursor() as cur:
            cur.execute("UPDATE lecture_summaries SET summary=%s WHERE lecture=%s", (body, lec))
        conn.commit()
        # Count remaining $1 occurrences
        remaining = body.count('$($1)$')
        print(f'  {lec}: restored, remaining $($1)$ patterns: {remaining}')
    else:
        print(f'  {lec}: no change')

# Final audit
with conn.cursor() as cur:
    cur.execute("SELECT lecture, summary FROM lecture_summaries ORDER BY lecture")
    print('\nResidual $($1)$ pattern audit:')
    for lec, body in cur.fetchall():
        n = body.count('$($1)$')
        if n: print(f'  {lec}: {n}')
