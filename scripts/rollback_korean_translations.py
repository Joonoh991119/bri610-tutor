#!/usr/bin/env python3
"""
Roll back over-translated Korean terms to English originals.

User mandate: Korean terms that are direct transliterations of English with
NO Korean conceptual identity must be returned to English. First occurrence
in each text gets `English (Korean)` form; subsequent occurrences get plain
English.

Terms rolled back (confirmed direct translations, not established Korean terms):
  내향 (전류)  → inward (current)    — "inward current" 의 직역
  임계          → threshold           — V_th / I_thr 등 — 역치/임계 모두 rollback
  냉각 / 초과 냉각 → undershoot      — wrong translation; context = AP undershoot
  트레이스      → trace               — "trace" 의 직역
  미시변량      → state variable      — "state variable / microscopic variable" 의 직역

Terms KEPT (well-established Korean neuroscience terms — do NOT revert):
  분극, 탈분극, 과분극, 재분극     (standard Korean biophysics)
  막전위, 활동전위, 불응기, etc.   (already handled by preserve_english_terms.py)

Note: 역치 was already mapped to threshold in preserve_english_terms.py,
so we skip it here.  임계 (without 역치 overlap) maps cleanly to threshold.

Tables covered:
  lecture_summaries.summary
  lecture_narrations.narration_md
  core_summaries.summary_md  +  must_memorize (jsonb, fact field)
  quiz_items.prompt_md, rationale_md, choices_json (jsonb, text field)
  take_home_exam.prompt_md, model_answer_md, rubric_md
  recall_quiz.prompt, answer
"""

import re
import json
import os
import psycopg2

DB_DSN = os.environ.get('DATABASE_URL', 'dbname=bri610 user=tutor password=tutor610 host=localhost')

# ──────────────────────────────────────────────────────────────────────────────
# TERM MAP
# Each entry: (Korean_regex_pattern, English_term, Korean_paren_note)
# Ordered from longest/most specific to shortest to avoid partial hits.
# ──────────────────────────────────────────────────────────────────────────────

ROLLBACK_TERMS = [
    # 초과 냉각 / 냉각 → undershoot
    # Context: "V_rest 아래로의 초과 냉각" = "undershoot below V_rest"
    ('초과 냉각',      'undershoot',           'V_rest 아래로의 과냉각'),
    ('냉각',           'undershoot',           'V_rest 아래로의 과냉각'),

    # 내향 → inward
    # "Na 내향 전류" = "inward Na current"
    ('내향 전류',      'inward current',       '세포 안으로 향하는 전류'),
    ('내향전류',       'inward current',       '세포 안으로 향하는 전류'),
    ('내향',           'inward',               '세포 안쪽 방향'),

    # 외향 → outward  (symmetric — add for consistency)
    ('외향 전류',      'outward current',      '세포 밖으로 향하는 전류'),
    ('외향전류',       'outward current',      '세포 밖으로 향하는 전류'),
    ('외향',           'outward',              '세포 바깥쪽 방향'),

    # 임계 → threshold
    # BUT: "임계값" / "임계 전압" may already be handled by preserve_english_terms.py
    # as "threshold voltage" — we handle the bare 임계 that appears as "threshold" usage
    ('임계값',         'threshold',            'AP 발화 조건값'),
    ('임계 도달',      'threshold crossing',   'threshold 도달'),
    ('임계 위로',      'above threshold',      'threshold 이상'),
    ('임계 근처',      'near threshold',       'threshold 근방'),
    ('임계를 넘',      'crosses threshold',    'threshold 초과'),
    ('임계점',         'threshold',            'AP 발화 임계점'),
    # Generic 임계 as standalone noun (but NOT 임계 when part of Korean compounds
    # like 임계상태 in thermodynamics — check context).
    # We use a word-boundary-like approach with Korean.
    ('임계',           'threshold',            'AP 발화 임계'),

    # 트레이스 → trace
    ('트레이스',       'trace',                '실험/모델 파형 기록'),

    # 미시변량 → state variable
    ('미시변량',       'state variable',       '미시 상태를 기술하는 변수'),
]

# ──────────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────────

PROTECT_PATTERN = re.compile(
    r'(\$\$[\s\S]+?\$\$'
    r'|\$(?=[^\s$])(?:[^$\n]|\\\$)+?(?<=[^\s\\])\$'
    r'|<svg[\s\S]*?</svg>'
    r'|```[\s\S]*?```'
    r'|`[^`\n]*?`'
    r'|<code[\s\S]*?</code>)',
    re.DOTALL,
)


def already_converted(text: str, eng: str) -> bool:
    """Check whether the English term already appears with Korean parenthetical."""
    # Pattern: english_term (Korean text)
    pat = re.compile(rf'\b{re.escape(eng)}\s*\([가-힣 ,./·]+\)')
    return bool(pat.search(text))


def rollback(text: str) -> tuple[str, int]:
    """Apply all rollbacks to a markdown string. Returns (new_text, n_changes)."""
    if not text:
        return text, 0
    total = 0
    for kr, eng, kr_paren in ROLLBACK_TERMS:
        kr_re = re.compile(rf'(?<![A-Za-z가-힣]){re.escape(kr)}(?![가-힣A-Za-z])')
        first_done = already_converted(text, eng)
        replacements = 0

        def make_repl(first_flag_list):
            def repl(m):
                replacements_inner = 0
                nonlocal replacements
                replacements += 1
                if not first_flag_list[0]:
                    first_flag_list[0] = True
                    return f'*{eng}* ({kr_paren})'
                return f'*{eng}*'
            return repl

        first_flag = [first_done]

        # Split by protected spans; only replace in plain segments
        chunks = PROTECT_PATTERN.split(text)
        new_chunks = []
        for i, chunk in enumerate(chunks):
            if i % 2 == 0:
                # plain prose
                new_chunk = kr_re.sub(make_repl(first_flag), chunk)
                new_chunks.append(new_chunk)
            else:
                new_chunks.append(chunk)
        text = ''.join(new_chunks)
        total += replacements

    return text, total


def rollback_jsonb_list(data, field: str) -> tuple[any, int]:
    if not isinstance(data, list):
        return data, 0
    total = 0
    new_data = []
    for item in data:
        if isinstance(item, dict) and field in item:
            fixed, n = rollback(item[field])
            total += n
            new_item = dict(item)
            new_item[field] = fixed
            new_data.append(new_item)
        else:
            new_data.append(item)
    return new_data, total


def process_table(conn, table: str, pk: str, text_cols: list, jsonb_cols: list) -> dict:
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
                fixed, n = rollback(val)
                if n > 0:
                    updates[col] = fixed
                    counts[col] += n

        for col, field in jsonb_cols:
            val = row[idx]
            idx += 1
            if val:
                fixed_data, n = rollback_jsonb_list(val, field)
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
    ('lecture_summaries',  'lecture', ['summary'],                                      []),
    ('lecture_narrations', 'id',      ['narration_md'],                                 []),
    ('core_summaries',     'id',      ['summary_md'],                                   [('must_memorize', 'fact')]),
    ('quiz_items',         'id',      ['prompt_md', 'rationale_md'],                    [('choices_json', 'text')]),
    ('take_home_exam',     'id',      ['prompt_md', 'model_answer_md', 'rubric_md'],    []),
    ('recall_quiz',        'id',      ['prompt', 'answer'],                             []),
]


def main():
    conn = psycopg2.connect(DB_DSN)
    print('Connected to DB. Running Korean→English rollback...\n')

    grand_total = 0
    for table, pk, text_cols, jsonb_cols in TABLES:
        counts = process_table(conn, table, pk, text_cols, jsonb_cols)
        table_total = sum(counts.values())
        grand_total += table_total
        print(f'  {table}: {table_total} substitutions')
        for col, n in counts.items():
            if n > 0:
                print(f'    {col}: {n}')

    conn.close()
    print(f'\nGrand total Korean→English rollbacks: {grand_total}')


if __name__ == '__main__':
    main()
