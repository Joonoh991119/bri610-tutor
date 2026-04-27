#!/usr/bin/env python3
"""
Quick VLM readability + completeness check using Gemini 3 Flash (multimodal).

For each of 6 lectures (L3..L8):
  1. Render embedded figures (SVG → PNG via rsvg-convert)
  2. Send (summary text + PNG figures) to Gemini Flash
  3. Get scores: readability, completeness, figure_caption_match
  4. Issues list

Output: logs/vlm_review_latest.json (consumed by session Opus Agent)
"""
from __future__ import annotations
import json, os, sys, re, time, base64, subprocess
from datetime import datetime
from pathlib import Path
import urllib.request, urllib.error
import threading
import psycopg2

ROOT = Path('/Users/joonoh/Projects/bri610-tutor')
FIG_DIR = ROOT / 'frontend' / 'public' / 'figures'
PNG_DIR = ROOT / 'logs' / 'vlm_pngs'
PNG_DIR.mkdir(parents=True, exist_ok=True)

DB_DSN = os.environ.get('DATABASE_URL', 'dbname=bri610 user=tutor password=tutor610 host=localhost')
OPENROUTER_KEY = os.environ['OPENROUTER_API_KEY']
VLM = 'google/gemini-3-flash-preview'

LECTURES = ['L3', 'L4', 'L5', 'L6', 'L7', 'L8']

# Map of figure file basenames embedded by each lecture summary
# (we'll detect by scanning the summary text for figure URL patterns)


def render_pngs():
    """Convert each SVG → PNG (300×180 — small enough for VLM, big enough to read)."""
    pngs = {}
    for svg in sorted(FIG_DIR.glob('*.svg')):
        if 'backup' in str(svg): continue
        png = PNG_DIR / f'{svg.stem}.png'
        # Skip if already rendered and fresh
        if png.exists() and png.stat().st_mtime > svg.stat().st_mtime:
            pngs[svg.stem] = png
            continue
        try:
            subprocess.run(
                ['rsvg-convert', '-w', '600', '-o', str(png), str(svg)],
                check=True, capture_output=True, timeout=15,
            )
            pngs[svg.stem] = png
        except Exception as e:
            print(f'  ⚠ render fail {svg.name}: {e}', file=sys.stderr)
    print(f'  rendered {len(pngs)} PNGs')
    return pngs


def detect_figures_in_summary(summary):
    """Find which figure files this summary embeds (by URL or filename mentions)."""
    found = set()
    for m in re.finditer(r'/figures/([a-z_]+)\.svg', summary):
        found.add(m.group(1))
    return list(found)


def fetch_summaries():
    conn = psycopg2.connect(DB_DSN)
    summaries = {}
    with conn.cursor() as cur:
        cur.execute('SELECT lecture, summary FROM lecture_summaries WHERE lecture = ANY(%s)', (LECTURES,))
        for row in cur.fetchall():
            summaries[row[0]] = row[1]
    conn.close()
    return summaries


VLM_SYSTEM = """You are a Korean computational neuroscience graduate-level tutor reviewing the readability and completeness of a lecture summary that embeds publication-grade figures.

You are given:
1. The full Korean+English summary text (markdown with KaTeX)
2. PNG renders of the embedded figures (in image_url messages)

Score 0-10 on each axis:
- readability: at-a-glance comprehension; can a Korean PhD student read this in 5 min and grasp the message?
- completeness: does the summary cover the lecture's key teachable points?
- figure_caption_match: does the figure rendering match the surrounding text claims (numerical callouts, axis ranges, semantics)?
- visual_clarity: are the figures themselves visually clean (no overlap, clear hierarchy, color-meaningful)?

List up to 4 specific issues. Each issue: short EXACT quote (≤80 chars) or figure name, category, one-line fix.

OUTPUT STRICT JSON only, no prose:
{
  "scores": {
    "readability": <0-10>,
    "completeness": <0-10>,
    "figure_caption_match": <0-10>,
    "visual_clarity": <0-10>,
    "overall": <average>
  },
  "issues": [
    {"target": "<quote or figure_name>", "category": "readability|completeness|figure-text|visual", "fix": "<one-line>"}
  ]
}"""


def b64_image(png_path):
    return base64.b64encode(png_path.read_bytes()).decode()


def call_vlm(summary, figure_pngs, lecture):
    """Send a multimodal request to VLM with the summary text + figure PNGs."""
    # Build OpenAI-format multimodal user content
    user_content = [
        {'type': 'text', 'text': f'Lecture: {lecture}\n\n## Summary text\n\n{summary[:9000]}'},
    ]
    for name, path in figure_pngs[:6]:  # cap at 6 figures to control payload size
        user_content.append({
            'type': 'text',
            'text': f'\n\nEmbedded figure: {name}.svg',
        })
        user_content.append({
            'type': 'image_url',
            'image_url': {'url': f'data:image/png;base64,{b64_image(path)}'},
        })

    body = json.dumps({
        'model': VLM,
        'messages': [
            {'role': 'system', 'content': VLM_SYSTEM},
            {'role': 'user', 'content': user_content},
        ],
        'max_tokens': 3000,
        'temperature': 0.0,
    }).encode()

    req = urllib.request.Request(
        'https://openrouter.ai/api/v1/chat/completions',
        data=body,
        headers={'Authorization': f'Bearer {OPENROUTER_KEY}', 'Content-Type': 'application/json'},
    )
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                d = json.loads(r.read())
                if d.get('choices'):
                    msg = d['choices'][0]['message']
                    return msg.get('content') or msg.get('reasoning') or ''
        except urllib.error.HTTPError as e:
            print(f'  [{lecture}] HTTP {e.code}: {e.read().decode()[:200]}', file=sys.stderr)
            if e.code in (429, 502, 503): time.sleep(2 ** attempt + 1); continue
            break
        except Exception as e:
            print(f'  [{lecture}] {e}', file=sys.stderr)
            time.sleep(2 ** attempt + 1)
    return ''


def parse_json_loose(text):
    text = re.sub(r'^```(?:json)?\s*', '', text.strip())
    text = re.sub(r'\s*```\s*$', '', text)
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if not m: return {}
    try: return json.loads(m.group(0))
    except: return {}


def review_one(lecture, summary, all_pngs, results):
    embedded = detect_figures_in_summary(summary)
    figure_pngs = [(n, all_pngs[n]) for n in embedded if n in all_pngs]
    print(f'  [{lecture}] {len(figure_pngs)} figures detected, calling VLM...')
    raw = call_vlm(summary, figure_pngs, lecture)
    parsed = parse_json_loose(raw)
    score = parsed.get('scores', {}).get('overall', 0)
    issues = parsed.get('issues', [])
    print(f'  [{lecture}] VLM overall={score:.1f}, issues={len(issues)}')
    results[lecture] = {
        'lecture': lecture,
        'figures_reviewed': [n for n, _ in figure_pngs],
        'scores': parsed.get('scores', {}),
        'overall': score,
        'issues': issues,
        'raw_len': len(raw),
    }


def main():
    print(f'== VLM readability check via {VLM} ==\n')
    print('Step 1: Rendering SVG → PNG...')
    pngs = render_pngs()

    print('\nStep 2: Fetching summaries from DB...')
    summaries = fetch_summaries()
    print(f'  {len(summaries)} cached summaries')

    print('\nStep 3: VLM review (parallel)...')
    results = {}
    threads = []
    for L in LECTURES:
        s = summaries.get(L)
        if not s:
            print(f'  [{L}] no summary, skip')
            continue
        t = threading.Thread(target=review_one, args=(L, s, pngs, results))
        t.start(); threads.append(t)
    for t in threads:
        t.join()

    out_ts = ROOT / 'logs' / f'vlm_review_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    out_stable = ROOT / 'logs' / 'vlm_review_latest.json'
    out_ts.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    out_stable.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(f'\n✓ VLM review saved → {out_ts}')

    print('\n=== VLM Summary ===')
    for L in LECTURES:
        r = results.get(L)
        if r:
            print(f'  {L}: overall={r["overall"]:.1f}, {len(r["issues"])} issues')


if __name__ == '__main__':
    main()
