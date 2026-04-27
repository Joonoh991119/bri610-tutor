#!/usr/bin/env python3
"""
Phase 2 — adversarial OpenRouter critics on the Phase-1 revised summaries.

Two critics in parallel per lecture:
  - Kimi K2.6 (moonshotai/kimi-k2.6) — science accuracy + ODE/EM correctness
  - Gemini Flash (google/gemini-3-flash-preview) — readability for beginners

Output: logs/adversarial_phase2_<ts>.json + logs/adversarial_phase2_latest.json
The output is consumed by Phase 3 (a session Opus agent that integrates the
issues and applies a final revision pass).
"""
from __future__ import annotations
import os, sys, json, re, time
import urllib.request, urllib.error
import threading
from datetime import datetime
from pathlib import Path
import psycopg2

ROOT = Path('/Users/joonoh/Projects/bri610-tutor')
OPENROUTER_KEY = os.environ['OPENROUTER_API_KEY']
DB_DSN = os.environ.get('DATABASE_URL', 'dbname=bri610 user=tutor password=tutor610 host=localhost')

KIMI = 'moonshotai/kimi-k2.6'
GEMINI = 'google/gemini-3-flash-preview'

LECTURES = ['L2', 'L3', 'L4', 'L5', 'L6', 'L7', 'L8']


KIMI_SYSTEM = """You are a STEM rigor critic for a graduate-level Korean+English BRI610 (computational neuroscience) summary. Korean PhD-student audience, rusty on differential equations and electromagnetism.

Score 0-10 each:
- ode_explanation_quality: are ODE derivations explicit enough that a student who just took DE last semester can follow? (separation of variables, characteristic equation, homogeneous vs forced)
- em_explanation_quality: are circuit / capacitor / Ohm's law concepts adequately motivated for someone weak on EM?
- math_correctness: any sign errors, dimensional issues, wrong constants?
- analogy_fidelity: do analogies match the math without misleading shortcuts?
- citation_validity: every [Slide L# p.N] should reference a real BRI610 slide.

List up to 6 specific issues. Each issue: short EXACT quote (≤80 chars), category, concrete fix.

OUTPUT STRICT JSON only:
{
  "scores": {"ode_explanation_quality": <0-10>, "em_explanation_quality": <0-10>, "math_correctness": <0-10>, "analogy_fidelity": <0-10>, "citation_validity": <0-10>, "overall": <average>},
  "issues": [{"quote": "...", "category": "ode|em|math|analogy|citation", "fix": "..."}]
}"""


GEMINI_SYSTEM = """당신은 한국 대학원생을 위한 학술 글쓰기 비평가입니다. BRI610 (computational neuroscience) 강의 요약을 *초보 독자가 이해할 수 있는가* 의 관점에서 평가합니다.

평가 축 (0-10):
- beginner_accessibility: ODE 나 회로 개념을 처음 접하는 학생도 따라갈 수 있는가?
- structure_signposting: 굵은 글씨 / 번호 / 문단 구분이 *skim* 가능하게 디자인되었는가?
- transition_smoothness: 섹션 간 전이가 자연스러운가? 갑자기 새 개념이 등장하지 않는가?
- pedagogical_scaffolding: 직관 → 형식화 → 연결 의 3 단계가 명시적인가?
- bilingual_balance: 한국어 본문에 영어 용어가 자연스럽게 녹아있는가?

최대 6 개의 구체적 문제점 인용 (≤80자) 과 수정안 제시.

오직 JSON 으로 출력:
{
  "scores": {"beginner_accessibility": <0-10>, "structure_signposting": <0-10>, "transition_smoothness": <0-10>, "pedagogical_scaffolding": <0-10>, "bilingual_balance": <0-10>, "overall": <average>},
  "issues": [{"quote": "...", "category": "accessibility|structure|transition|scaffolding|bilingual", "fix": "..."}]
}"""


def call(model, system, user, max_tokens=4000, retries=2, timeout=180):
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
            if e.code in (429,502,503): time.sleep(2**attempt+1); continue
            break
        except Exception as e:
            print(f'  [{model}] {e}', file=sys.stderr)
            time.sleep(2**attempt+1)
    return ''


def parse_json_loose(t):
    t = re.sub(r'^```(?:json)?\s*', '', t.strip())
    t = re.sub(r'\s*```\s*$', '', t)
    m = re.search(r'\{.*\}', t, re.DOTALL)
    if not m: return {}
    try: return json.loads(m.group(0))
    except: return {}


def review_one(L, summary, results):
    print(f'  [{L}] starting parallel critics...', flush=True)
    sub = {}
    def go(model, key, system):
        raw = call(model, system, summary)
        parsed = parse_json_loose(raw)
        sub[key] = parsed
        score = parsed.get('scores', {}).get('overall', 0)
        n = len(parsed.get('issues', []))
        print(f'  [{L}] {key} score={score:.1f}, issues={n}', flush=True)
    t1 = threading.Thread(target=go, args=(KIMI, 'kimi', KIMI_SYSTEM))
    t2 = threading.Thread(target=go, args=(GEMINI, 'gemini', GEMINI_SYSTEM))
    t1.start(); t2.start()
    t1.join(); t2.join()
    results[L] = sub


def main():
    conn = psycopg2.connect(DB_DSN)
    summaries = {}
    with conn.cursor() as cur:
        cur.execute('SELECT lecture, summary FROM lecture_summaries WHERE lecture = ANY(%s)', (LECTURES,))
        for r in cur.fetchall(): summaries[r[0]] = r[1]
    conn.close()

    print(f'Phase 2: parallel adversarial reviews on {len(summaries)} summaries...')
    results = {}
    threads = []
    for L in LECTURES:
        s = summaries.get(L)
        if not s: continue
        t = threading.Thread(target=review_one, args=(L, s, results))
        t.start(); threads.append(t)
    for t in threads:
        t.join()

    out_dir = ROOT / 'logs'
    out_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_path = out_dir / f'adversarial_phase2_{ts}.json'
    out_stable = out_dir / 'adversarial_phase2_latest.json'
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    out_stable.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(f'\n✓ saved → {out_path}')

    print('\n=== Aggregate scores ===')
    for L in LECTURES:
        r = results.get(L, {})
        ks = r.get('kimi', {}).get('scores', {}).get('overall', 0)
        gs = r.get('gemini', {}).get('scores', {}).get('overall', 0)
        ki = len(r.get('kimi', {}).get('issues', []))
        gi = len(r.get('gemini', {}).get('issues', []))
        print(f'  {L}: Kimi={ks:.1f} ({ki} issues)   Gemini={gs:.1f} ({gi} issues)')


if __name__ == '__main__':
    main()
