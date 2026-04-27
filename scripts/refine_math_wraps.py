"""
Find $..$ blocks that contain prose words (likely false-positive wraps from
the bulk script). Unwrap those.

Heuristic: if math content contains a word matching [a-z]{3,} (3+ lowercase
letters in a row) that's NOT a recognized math command (like \text, \frac,
\sin, \cos, \ln, \log, \exp, \mathrm, \infty, \alpha-\omega), it's probably
prose that got wrapped. Unwrap by removing surrounding $..$.
"""
import re, psycopg2
conn = psycopg2.connect("dbname=bri610 user=tutor password=tutor610 host=localhost")

# Recognized math commands / Greek
KNOWN = {'frac','sin','cos','tan','sec','csc','cot','ln','log','exp','sqrt',
         'sum','prod','int','lim','to','infty','partial','nabla','approx',
         'leq','geq','neq','equiv','sim','propto','cdot','times','div','pm','mp',
         'alpha','beta','gamma','delta','epsilon','zeta','eta','theta','iota',
         'kappa','lambda','mu','nu','xi','omicron','pi','rho','sigma','tau',
         'upsilon','phi','chi','psi','omega','varepsilon','varphi','vartheta',
         'mathrm','mathbf','mathit','mathcal','mathbb','text','textit','textbf',
         'left','right','big','Big','bigg','Bigg','quad','qquad','small','large',
         'Delta','Gamma','Lambda','Sigma','Theta','Omega','Phi','Psi','Pi','Xi',
         'inj','ext','rest','syn','tot','open','close','in','out',
         'min','max','arg','sup','inf','case','cases',
         'Na','Cl','Ca','Mg','Cu','Fe','Zn','Co','Ni','Ag','Au','Hg','As'}  # ions

PROSE_RE = re.compile(r'\b([a-zA-Z]{3,})\b')

def has_prose(math_inner):
    # Strip backslash commands first
    no_cmd = re.sub(r'\\[a-zA-Z]+', '', math_inner)
    # Strip subscript content {...}
    no_sub = re.sub(r'_\{[^}]*\}|_\w', '', no_cmd)
    no_sub = re.sub(r'\^\{[^}]*\}|\^\w', '', no_sub)
    # Find words 3+ letters that aren't known math
    for m in PROSE_RE.finditer(no_sub):
        w = m.group(1)
        if w in KNOWN:
            continue
        if len(w) >= 3:
            return True
    return False

def unwrap(m):
    inner = m.group(1)
    if has_prose(inner):
        return inner  # remove the surrounding $..$
    return m.group(0)  # keep as is

with conn.cursor() as cur:
    cur.execute("SELECT lecture, summary FROM lecture_summaries ORDER BY lecture")
    rows = cur.fetchall()

total = 0
for lec, body in rows:
    new = re.sub(r'\$([^$\n]{2,200})\$', unwrap, body)
    diff = body.count('$') - new.count('$')
    if new != body:
        with conn.cursor() as cur:
            cur.execute("UPDATE lecture_summaries SET summary=%s WHERE lecture=%s", (new, lec))
        conn.commit()
        total += diff // 2
        print(f'  {lec}: {diff//2} false-positive wraps unwrapped')
    else:
        print(f'  {lec}: clean')
print(f'\nTotal unwraps: {total}')
