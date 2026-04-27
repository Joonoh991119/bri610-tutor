#!/usr/bin/env python3
"""
DeepSeek-only coherence reviews for all 6 summaries (parallel).
Saves results to JSON for the session-Opus Agent to consume.

Run: python3 scripts/deepseek_coherence_review.py
"""
from __future__ import annotations
import json, os, sys, re, time
from datetime import datetime
from pathlib import Path
import urllib.request, urllib.error
import threading

ROOT = Path('/Users/joonoh/Projects/bri610-tutor')
DB_DSN = os.environ.get('DATABASE_URL', 'dbname=bri610 user=tutor password=tutor610 host=localhost')
OPENROUTER_KEY = os.environ['OPENROUTER_API_KEY']
DEEPSEEK = 'deepseek/deepseek-v4-pro'
LECTURES = ['L3', 'L4', 'L5', 'L6', 'L7', 'L8']

import psycopg2

REVIEW_SYSTEM = """You are reviewing a graduate-level Korean+English BRI610 (computational neuroscience) summary that contains:
- KaTeX equations ($..$ and $$..$$)
- Inline SVG figures (`<figure><svg>..</svg></figure>`)
- Pedagogical analogies in Korean
- Sequential numbered derivation steps
- `<details>` toggles for prerequisite reminders

Your job: judge whether the figures, text, and analogies form a *coherent* knowledge-delivery package for a Korean PhD student rusty on differential equations.

Score 0-10 on:
- figure_text_alignment (does the surrounding text accurately describe what each figure shows? are figure numerical callouts matched in the text?)
- analogy_accuracy (does each analogy faithfully map to the underlying physics/math? no misleading shortcuts?)
- pedagogical_flow (intuition → formalization → connection — present and well-sequenced?)
- bilingual_clarity (Korean primary text natural for native readers? English terms inline appropriately?)
- derivation_completeness (numbered steps mathematically correct AND each step clearly motivated?)

List up to 6 specific issues. Each issue: short EXACT quote (≤80 chars), category, concrete fix.

OUTPUT STRICT JSON only:
{
  "scores": {
    "figure_text_alignment": <0-10>,
    "analogy_accuracy": <0-10>,
    "pedagogical_flow": <0-10>,
    "bilingual_clarity": <0-10>,
    "derivation_completeness": <0-10>,
    "overall": <average>
  },
  "issues": [
    {"quote": "<≤80 chars>", "category": "figure|analogy|flow|korean|math", "fix": "<one-line>"}
  ]
}"""


def call(model, system, user, max_tokens=4000, retries=2, timeout=240):
    body = json.dumps({
        'model': model,
        'messages': [{'role':'system','content':system},{'role':'user','content':user}],
        'max_tokens': max_tokens,
        'temperature': 0.0,
    }).encode()
    req = urllib.request.Request(
        'https://openrouter.ai/api/v1/chat/completions',
        data=body,
        headers={'Authorization': f'Bearer {OPENROUTER_KEY}', 'Content-Type': 'application/json'},
    )
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = json.loads(r.read())
                if d.get('choices'):
                    msg = d['choices'][0]['message']
                    return msg.get('content') or msg.get('reasoning') or ''
                return ''
        except urllib.error.HTTPError as e:
            print(f'  [{model}] HTTP {e.code}: {e.read().decode()[:150]}', file=sys.stderr)
            if e.code in (429, 502, 503): time.sleep(2 ** attempt + 1); continue
            break
        except Exception as e:
            print(f'  [{model}] {e}', file=sys.stderr)
            time.sleep(2 ** attempt + 1)
    return ''


def parse_json_loose(text):
    text = re.sub(r'^```(?:json)?\s*', '', text.strip())
    text = re.sub(r'\s*```\s*$', '', text)
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if not m: return {}
    try: return json.loads(m.group(0))
    except: return {}


def review_one(lecture, summary, results):
    print(f'  [{lecture}] DeepSeek reviewing...')
    raw = call(DEEPSEEK, REVIEW_SYSTEM, summary, max_tokens=4000)
    parsed = parse_json_loose(raw)
    score = parsed.get('scores', {}).get('overall', 0)
    issues = parsed.get('issues', [])
    print(f'  [{lecture}] DeepSeek score={score:.1f}, issues={len(issues)}')
    results[lecture] = {
        'lecture': lecture,
        'scores': parsed.get('scores', {}),
        'overall': score,
        'issues': issues,
        'raw_len': len(raw),
    }


def main():
    conn = psycopg2.connect(DB_DSN)
    summaries = {}
    with conn.cursor() as cur:
        cur.execute('SELECT lecture, summary FROM lecture_summaries WHERE lecture = ANY(%s)', (LECTURES,))
        for row in cur.fetchall():
            summaries[row[0]] = row[1]
    conn.close()

    print(f'Reviewing {len(summaries)} summaries with DeepSeek v4 pro (parallel threads)...')
    results = {}
    threads = []
    for L in LECTURES:
        s = summaries.get(L)
        if not s:
            print(f'  [{L}] no cached summary')
            continue
        t = threading.Thread(target=review_one, args=(L, s, results))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    out = ROOT / 'logs' / f'deepseek_review_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(f'\n✓ DeepSeek reviews saved → {out}')

    # Also write a stable name for the Opus Agent to consume
    stable = ROOT / 'logs' / 'deepseek_review_latest.json'
    stable.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(f'✓ Stable copy → {stable}')

    print('\n=== Summary ===')
    for L in LECTURES:
        r = results.get(L)
        if r:
            print(f'  {L}: overall={r["overall"]:.1f}, {len(r["issues"])} issues')


if __name__ == '__main__':
    main()
