#!/usr/bin/env python3
"""
Fix KaTeX syntax errors across all markdown text columns in the bri610 DB.

Patterns fixed (all idempotent):
1. Multi-char chemical subscripts without braces inside math:
   Na_v → \text{Na}_v, Ca_v → \text{Ca}_v, etc.
2. Multi-char subscripts needing braces: g_Na → g_{Na}, V_th → V_{th}, etc.
3. Bare chemical/ion notation outside math → wrap in $..$
4. Raw LaTeX commands outside $..$  → wrap in $..$
5. Nested dollar signs: $X($Y$)Z$ → $X(Y)Z$
6. Multi-char subscript in display math ($$...$$) same rules.

Tables covered:
- lecture_summaries.summary
- lecture_narrations.narration_md
- core_summaries.summary_md  +  must_memorize (jsonb, fact field)
- quiz_items.prompt_md, rationale_md, choices_json (jsonb, text field)
- take_home_exam.prompt_md, model_answer_md, rubric_md
- recall_quiz.prompt, answer
"""
import re
import json
import os
import psycopg2

DB_DSN = os.environ.get('DATABASE_URL', 'dbname=bri610 user=tutor password=tutor610 host=localhost')

# ──────────────────────────────────────────────────────────────────────────────
# REGEX HELPERS
# ──────────────────────────────────────────────────────────────────────────────

# Split text into alternating (plain, math/code/svg) segments.
# Index 0, 2, 4 … are plain; 1, 3, 5 … are protected spans.
PROTECT_PATTERN = re.compile(
    r'(\$\$[\s\S]+?\$\$'           # display math
    r'|\$(?=[^\s$])(?:[^$\n]|\\\$)+?(?<=[^\s\\])\$'  # inline math
    r'|<svg[\s\S]*?</svg>'         # SVG blocks
    r'|```[\s\S]*?```'             # fenced code
    r'|`[^`\n]*?`'                 # inline code
    r'|<code[\s\S]*?</code>)',     # HTML code
    re.DOTALL,
)


def split_protected(text: str):
    """Return list of (is_math_or_code: bool, segment: str)."""
    parts = PROTECT_PATTERN.split(text)
    result = []
    for i, part in enumerate(parts):
        result.append((i % 2 == 1, part))
    return result


def rejoin(parts):
    return ''.join(seg for _, seg in parts)


# ──────────────────────────────────────────────────────────────────────────────
# FIXES INSIDE MATH SPANS (inline $..$ and display $$..$$)
# ──────────────────────────────────────────────────────────────────────────────

def _fix_inside_math(math_text: str) -> str:
    """Apply brace / \\text fixes INSIDE a math span (including the delimiters)."""
    # Detect whether this is display or inline to strip/restore delimiters
    if math_text.startswith('$$'):
        delim = '$$'
        inner = math_text[2:-2]
    elif math_text.startswith('$'):
        delim = '$'
        inner = math_text[1:-1]
    else:
        return math_text  # not math (code/svg), skip

    # --- 1. Chemical multi-char base: Na_x → \text{Na}_x (not already wrapped)
    # Only when Na/Ca appear as base of subscript without \text already
    # Pattern: (?<!\\text{)(?<!\w)(Na|Ca)_([A-Za-z0-9]+)
    # We need to be careful: \text{Na} is already fixed.
    # Also fix Na^{2+} style — those are fine as-is inside math.

    # Fix Na_v, Na_V, Ca_v, Ca_V, Na_K etc. → \text{Na}_{...}, \text{Ca}_{...}
    inner = re.sub(
        r'(?<!\\text\{)(?<![A-Za-z\\])(Na|Ca)_\{([^}]+)\}',
        r'\\text{\1}_{\2}',
        inner,
    )
    inner = re.sub(
        r'(?<!\\text\{)(?<![A-Za-z\\])(Na|Ca)_([A-Za-z0-9]+)',
        lambda m: r'\text{' + m.group(1) + '}_{' + m.group(2) + '}' if len(m.group(2)) > 1 else r'\text{' + m.group(1) + '}_' + m.group(2),
        inner,
    )

    # --- 2. Multi-char subscripts that need braces
    # Patterns: g_Na, g_K, g_L, g_syn, g_th, g_sra, g_Ca, g_AMPA, g_GABA, g_NMDA
    #           E_Na, E_K, E_L, E_Cl, E_Ca, E_syn, E_AMPA, E_GABA, E_NMDA
    #           I_inj, I_ext, I_thr, I_syn, I_Na, I_K, I_Ca, I_L
    #           V_th, V_thr, V_reset, V_rest, V_clamp, V_inj, V_ext, V_max
    #           t_peak, t_isi, t_th
    #           tau_m, tau_n, tau_h, tau_r, tau_d, tau_ref, tau_sra, tau_syn
    #           Also: m_inf, h_inf, n_inf, V_inf

    MULTI_SUB_SPECS = [
        # (base_pattern, subscript_words_requiring_braces)
        # base_pattern is the regex for the base letter(s); subscripts are strings
        (r'g',      ['Na', 'Ca', 'Cl', 'syn', 'th', 'sra', 'AMPA', 'GABA', 'NMDA', 'leak', 'ext', 'inh', 'exc']),
        (r'E',      ['Na', 'Ca', 'Cl', 'syn', 'AMPA', 'GABA', 'NMDA', 'rev', 'leak']),
        (r'I',      ['inj', 'ext', 'thr', 'syn', 'Na', 'Ca', 'Cl', 'leak', 'ref', 'sra', 'app', 'hyp', 'stim', 'exc', 'inh']),
        (r'V',      ['th', 'thr', 'reset', 'rest', 'clamp', 'inj', 'ext', 'max', 'min', 'rev', 'inf', 'mem', 'peak']),
        (r't',      ['peak', 'isi', 'th', 'ref', 'syn', 'rise', 'fall', 'decay']),
        (r'\\tau',  ['ref', 'sra', 'syn', 'rise', 'fall', 'decay', 'mem', 'exc', 'inh']),
        (r'\\alpha',['m', 'h', 'n']),
        (r'\\beta', ['m', 'h', 'n']),
        (r'm',      ['inf']),
        (r'h',      ['inf']),
        (r'n',      ['inf']),
    ]

    for base, subs in MULTI_SUB_SPECS:
        for sub in subs:
            # Already braced: base_{sub} → skip
            # Not braced: base_sub (without {}) → brace
            # Use negative lookbehind for { and lookahead to avoid partial match
            pattern = re.compile(
                rf'({re.escape(base)})_(?!\{{)({re.escape(sub)})(?![A-Za-z0-9])'
            )
            inner = pattern.sub(r'\1_{\2}', inner)

    return delim + inner + delim


# ──────────────────────────────────────────────────────────────────────────────
# FIXES OUTSIDE MATH SPANS (plain prose)
# ──────────────────────────────────────────────────────────────────────────────

# Ion / channel names that appear bare in plain text and should be wrapped in math
# These are multi-char subscript cases that appear WITHOUT surrounding $
BARE_ION_PATTERNS = [
    # Na_v, Na_V → $\text{Na}_v$
    (re.compile(r'(?<!\$)(?<![A-Za-z\\])(Na)_(v|V)(?![A-Za-z0-9{])'), r'$\\text{Na}_\2$'),
    (re.compile(r'(?<!\$)(?<![A-Za-z\\])(Ca)_(v|V)(?![A-Za-z0-9{])'), r'$\\text{Ca}_\2$'),
    # K_v, K_V → $K_v$ (single-char base is fine)
    (re.compile(r'(?<!\$)(?<![A-Za-z\\])(K)_(v|V)(?![A-Za-z0-9{])'), r'$K_\2$'),
    # Ion species outside math: Na^{2+}, Ca^{2+}, Mg^{2+}, K^+, Cl^-
    # Only when NOT inside $ already (checked by split_protected)
    (re.compile(r'(?<![\\$])(Na\^?\{?2\+\}?|Na\+)'), r'$\\text{Na}^+$'),
    (re.compile(r'(?<![\\$])(Ca\^?\{?2\+\}?)'), r'$\\text{Ca}^{2+}$'),
    (re.compile(r'(?<![\\$])(Mg\^?\{?2\+\}?)'), r'$\\text{Mg}^{2+}$'),
    (re.compile(r'(?<![\\$])(?<![A-Za-z])(K\^?\+)(?![A-Za-z0-9])'), r'$K^+$'),
    (re.compile(r'(?<![\\$])(?<![A-Za-z])(Cl\^?-)(?![A-Za-z0-9])'), r'$\\text{Cl}^-$'),
    # Raw LaTeX outside math
    (re.compile(r'(?<!\$)\\tau(?!_|\{|\w)'), r'$\\tau$'),
    (re.compile(r'(?<!\$)\\to(?!\w)'), r'$\\to$'),
    (re.compile(r'(?<!\$)\\equiv(?!\w)'), r'$\\equiv$'),
    (re.compile(r'(?<!\$)\\propto(?!\w)'), r'$\\propto$'),
    (re.compile(r'(?<!\$)\\sqrt\{([^}]+)\}'), r'$\\sqrt{\1}$'),
    (re.compile(r'(?<!\$)\\frac\{([^}]+)\}\{([^}]+)\}'), r'$\\frac{\1}{\2}$'),
    (re.compile(r'(?<!\$)\\infty(?!\w)'), r'$\\infty$'),
    (re.compile(r'(?<!\$)\\partial(?!\w)'), r'$\\partial$'),
    (re.compile(r'(?<!\$)\\alpha(?!\w)'), r'$\\alpha$'),
    (re.compile(r'(?<!\$)\\beta(?!\w)'), r'$\\beta$'),
    (re.compile(r'(?<!\$)\\gamma(?!\w)'), r'$\\gamma$'),
    (re.compile(r'(?<!\$)\\lambda(?!\w)'), r'$\\lambda$'),
    (re.compile(r'(?<!\$)\\mu(?!\w)'), r'$\\mu$'),
]

# Nested dollar signs: $X($Y$)Z$ or $..($..$..)$  (common bug where inner parens had math tags)
NESTED_DOLLAR_RE = re.compile(
    r'\$([^$]*)\(\$([^$]*)\$\)([^$]*)\$'
)


def fix_nested_dollars(text: str) -> tuple[str, int]:
    """Collapse nested $..($Y$)..$ → $..(Y)..$"""
    count = 0
    def repl(m):
        nonlocal count
        count += 1
        return f'${m.group(1)}({m.group(2)}){m.group(3)}$'
    new = NESTED_DOLLAR_RE.sub(repl, text)
    return new, count


def fix_plain_segment(seg: str) -> tuple[str, int]:
    """Apply bare-ion and raw-latex fixes to a plain (non-math) segment."""
    count = 0
    for pat, repl in BARE_ION_PATTERNS:
        new_seg, n = pat.subn(repl, seg)
        count += n
        seg = new_seg
    return seg, count


# ──────────────────────────────────────────────────────────────────────────────
# MASTER FIX FUNCTION
# ──────────────────────────────────────────────────────────────────────────────

def fix_text(text: str) -> tuple[str, int]:
    """Apply all KaTeX fixes to a markdown text string. Returns (new_text, n_changes)."""
    if not text:
        return text, 0

    total = 0

    # Pass 1: fix nested dollars first (before splitting)
    text, n = fix_nested_dollars(text)
    total += n

    # Pass 2: split into protected/plain segments and process each
    parts = split_protected(text)
    new_parts = []
    for is_protected, seg in parts:
        if is_protected:
            # It's a math or code span — fix inside math, leave code untouched
            if seg.startswith('$'):
                fixed = _fix_inside_math(seg)
                if fixed != seg:
                    total += 1
                new_parts.append((True, fixed))
            else:
                new_parts.append((True, seg))  # code/svg untouched
        else:
            # Plain prose — fix bare ions/LaTeX
            fixed, n = fix_plain_segment(seg)
            total += n
            new_parts.append((False, fixed))

    return rejoin(new_parts), total


# ──────────────────────────────────────────────────────────────────────────────
# TABLE HANDLERS
# ──────────────────────────────────────────────────────────────────────────────

def fix_jsonb_list(data, field: str) -> tuple[any, int]:
    """Fix a field named `field` inside a list of JSON objects."""
    if not isinstance(data, list):
        return data, 0
    total = 0
    new_data = []
    for item in data:
        if isinstance(item, dict) and field in item:
            fixed, n = fix_text(item[field])
            total += n
            new_item = dict(item)
            new_item[field] = fixed
            new_data.append(new_item)
        else:
            new_data.append(item)
    return new_data, total


def process_table(conn, table: str, pk: str, text_cols: list, jsonb_cols: list) -> dict:
    """Process all rows in a table. Returns per-column change counts."""
    counts = {c: 0 for c in text_cols + [jc for jc, _ in jsonb_cols]}

    with conn.cursor() as cur:
        all_cols = [pk] + text_cols + [jc for jc, _ in jsonb_cols]
        cur.execute(f"SELECT {', '.join(all_cols)} FROM {table}")
        rows = cur.fetchall()

    for row in rows:
        pk_val = row[0]
        updates = {}
        idx = 1

        for col in text_cols:
            val = row[idx]
            idx += 1
            if val:
                fixed, n = fix_text(val)
                if n > 0:
                    updates[col] = fixed
                    counts[col] += n

        for col, field in jsonb_cols:
            val = row[idx]
            idx += 1
            if val:
                # psycopg2 returns jsonb as Python dict/list already
                fixed_data, n = fix_jsonb_list(val, field)
                if n > 0:
                    updates[col] = json.dumps(fixed_data, ensure_ascii=False)
                    counts[col] += n

        if updates:
            set_clause = ', '.join(f"{col} = %s" for col in updates)
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE {table} SET {set_clause} WHERE {pk} = %s",
                    list(updates.values()) + [pk_val],
                )
    conn.commit()
    return counts


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

TABLES = [
    # (table, pk, [text_cols], [(jsonb_col, jsonb_field)])
    ('lecture_summaries',  'lecture', ['summary'],                                          []),
    ('lecture_narrations', 'id',      ['narration_md'],                                     []),
    ('core_summaries',     'id',      ['summary_md'],                                       [('must_memorize', 'fact')]),
    ('quiz_items',         'id',      ['prompt_md', 'rationale_md'],                        [('choices_json', 'text')]),
    ('take_home_exam',     'id',      ['prompt_md', 'model_answer_md', 'rubric_md'],        []),
    ('recall_quiz',        'id',      ['prompt', 'answer'],                                 []),
]


def main():
    conn = psycopg2.connect(DB_DSN)
    print('Connected to DB. Running KaTeX syntax fixes...\n')

    grand_total = 0
    for table, pk, text_cols, jsonb_cols in TABLES:
        counts = process_table(conn, table, pk, text_cols, jsonb_cols)
        table_total = sum(counts.values())
        grand_total += table_total
        print(f'  {table}: {table_total} fixes')
        for col, n in counts.items():
            if n > 0:
                print(f'    {col}: {n}')

    conn.close()
    print(f'\nGrand total KaTeX fixes applied: {grand_total}')


if __name__ == '__main__':
    main()
