#!/usr/bin/env python3
"""
Panel-discussion + 3-round revision pipeline applying variation theory.

Panel:
  Opus      = anthropic/claude-opus-4-7   (pedagogical synthesis lead)
  DeepSeek  = deepseek/deepseek-v4-flash  (STEM rigor + critique)
  Gemini    = google/gemini-3-flash-preview (Korean readability + variation check)

Pedagogical philosophy enforced (per learning-science web research):
  1. Variation theory (Marton CSGF): same concept exposed via Contrast, Separation,
     Generalization, Fusion — multiple framings build robust understanding.
  2. Elaborative encoding: connect new info to prior knowledge explicitly.
  3. Spaced retrieval cues: questions that force the reader to recall.
  4. Interleaving: contrast easily-confused concepts side-by-side.
  5. Eliminate undefined abbreviations — use full form first.

Per lecture, 3 rounds:
  R1: each panelist independently lists 4-6 issues (JSON).
  R2: each panelist sees union of R1 issues, refines/refutes (JSON).
  R3: Opus synthesizes all R2 outputs into a final revised summary.

Commits per lecture so the app updates incrementally.
"""
from __future__ import annotations
import os, sys, json, re, time, subprocess
from pathlib import Path
import urllib.request
import psycopg2

ROOT = Path('/Users/joonoh/Projects/bri610-tutor')
DB_DSN = os.environ.get('DATABASE_URL', 'dbname=bri610 user=tutor password=tutor610 host=localhost')
KEY = os.environ['OPENROUTER_API_KEY']

OPUS    = 'anthropic/claude-opus-4-7'
DEEPSEEK = 'deepseek/deepseek-v4-flash'
GEMINI  = 'google/gemini-3-flash-preview'

LECTURES = ['L3', 'L4', 'L5', 'L6', 'L7', 'L8']  # L2 already panel-revised at 16:23


def call(model, system, user, max_tokens=4000, retries=2, timeout=240):
    body = json.dumps({
        'model': model,
        'messages': [{'role':'system','content':system},{'role':'user','content':user}],
        'max_tokens': max_tokens,
        'temperature': 0.2,
    }).encode()
    req = urllib.request.Request('https://openrouter.ai/api/v1/chat/completions',
        data=body, headers={'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = json.loads(r.read())
                if d.get('choices'):
                    msg = d['choices'][0]['message']
                    return msg.get('content') or msg.get('reasoning') or ''
        except Exception as e:
            print(f'  [{model}] retry {attempt}: {e}', file=sys.stderr)
            time.sleep(2 ** attempt + 1)
    return ''


def parse_json_loose(text):
    text = re.sub(r'^```(?:json)?\s*', '', text.strip())
    text = re.sub(r'\s*```\s*$', '', text)
    matches = list(re.finditer(r'\{.*\}', text, re.DOTALL))
    for m in reversed(matches):  # last (closer to end → likely final summary JSON)
        try: return json.loads(m.group(0))
        except: pass
    return {}


# ───────────────────────────────────────────────────────────────────
# Round 1 — independent review
# ───────────────────────────────────────────────────────────────────

R1_SYS_OPUS = """당신은 BRI610 (computational neuroscience) Korean PhD 학생용 강의 요약을 검토하는 *교육학 패널 멤버* 입니다.

검토 관점 (이 모델은 *교육학 통합 lead*):
- 약어 (abbreviation) 가 *처음 등장* 시 풀이 (full form) 없이 등장한 경우 모두 지적.
- 복잡한 개념 (예: 식별성, multi-time-constant cable, 위상 부호화) 이 *한 번만* 노출된 경우 — 변주 (variation) 부족.
- Spaced retrieval cue 부족 — 학생이 *읽고만 끝나지 말고 떠올려 보아야 할* 시점이 명시되지 않음.
- Interleaving 부족 — 헷갈리는 개념 쌍 (예: $g$ vs $G$, $m$ vs $n$, $V$ vs $V_m$) 이 contrast 없이 단일 등장.
- 사전 지식 연결 부족 — 새 개념이 학생이 이미 아는 개념 (이전 lecture, 일상 비유) 에 *명시적으로 anchor* 되지 않음.

최대 6개 이슈. JSON only:
{"issues":[{"category":"abbreviation|repetition|retrieval|interleaving|elaboration","quote":"<≤80 chars>","fix":"<one-line>"}]}"""

R1_SYS_DEEPSEEK = """You are a STEM rigor critic for a Korean+English BRI610 (computational neuroscience) lecture summary.

Focus areas:
- Equation derivation rigor: any sign errors, dim issues, oversimplified algebra
- Notational consistency: same symbol used for different things across sections
- Hidden assumptions: any model assumption that's used but not stated
- Boundary conditions: missing where/when an equation breaks down
- Cross-lecture math consistency: does this lecture's equation match the upstream lecture's notation?

Up to 6 issues. JSON only:
{"issues":[{"category":"derivation|notation|assumption|boundary|consistency","quote":"<≤80 chars>","fix":"<one-line>"}]}"""

R1_SYS_GEMINI = """당신은 한국 대학원생을 위한 강의 요약의 *학습 변주 (variation theory)* 비평가입니다.

검토 축:
- Contrast: 비슷해 보이지만 다른 개념이 명확히 *대비* 되었는가?
- Separation: 핵심 변수만 변하고 나머지는 고정된 *반복 노출* 이 있는가?
- Generalization: 구체 예시 → 추상 원칙으로의 *일반화* 단계가 있는가?
- Fusion: 여러 변수가 동시에 변하는 *통합 적용* 예시가 있는가?
- 한국어 자연성 + 영어 인라인 균형
- 표/수식/그림 ↔ 본문 일치

최대 6개 이슈. JSON only:
{"issues":[{"category":"contrast|separation|generalization|fusion|language|coherence","quote":"<≤80 chars>","fix":"<one-line>"}]}"""


# ───────────────────────────────────────────────────────────────────
# Round 2 — cross-critique
# ───────────────────────────────────────────────────────────────────

R2_SYS = """당신은 패널 토의 round 2 입니다. Round 1 에서 본인 + 다른 두 패널이 발견한 이슈 목록을 받습니다.

당신의 임무:
- 다른 패널의 이슈가 *합당한가* 판단
- 동의하면 amplify (구체 예시/심화 추가)
- 반대하면 refute (왜 이슈가 아닌지 설명)
- 본인 R1 이슈 중에서 R2 단계에서 *우선순위를 조정* 하거나 *추가 발견*

JSON only:
{"agree":[{"issue_idx":<n>,"amplify":"<add detail>"}],"refute":[{"issue_idx":<n>,"why":"<reason>"}],"new_issues":[{"category":"...","quote":"...","fix":"..."}]}"""


# ───────────────────────────────────────────────────────────────────
# Round 3 — Opus integrates and rewrites
# ───────────────────────────────────────────────────────────────────

R3_SYS = """당신은 BRI610 강의 요약 *최종 합성 작가* 입니다. 패널 (Opus / DeepSeek / Gemini) 의 R1 + R2 토의 결과를 받아 요약을 *변주 학습 철학* 에 따라 다시 씁니다.

## 적용 원칙 (web research 기반)
1. **Variation theory (Marton CSGF)**: 핵심 개념마다 4개 노출 — Contrast (비슷하지만 다른) / Separation (한 변수만 바뀜) / Generalization (구체→추상) / Fusion (다변수 동시 적용).
2. **Elaborative encoding**: 새 개념은 항상 *이미 아는 개념* 에 anchor — 일상 비유 + 이전 lecture cross-ref.
3. **Spaced retrieval cues**: 적절 위치에 "*잠시 멈춰서 — 만약 [조건] 이 바뀌면 결과가 어떻게 바뀔까?* 직접 답해보라" 형식 1-2 개.
4. **Interleaving**: 헷갈리는 개념 쌍은 *side-by-side* 로 대비.
5. **약어 무삭제 정책**: 약어는 *처음 등장* 시 반드시 full form (e.g., "전압 클램프 (voltage clamp)") 부터. 이후에도 핵심 본문에서는 full form 우선.

## 절대 보존
- 모든 KaTeX `$..$` `$$..$$`
- 모든 `<figure><svg>` `<figcaption>` 블록
- 모든 `<details>` 토글
- Slide 인용 `[Slide L# p.N]`
- Cross-summary hyperlinks `[L3 §3.5](#summary?lecture=L3)`
- 마크다운 테이블 (참조용 보존)

## 길이 budget
+10 ~ +30% (현재 13~17k → 14~22k chars OK).

## 출력 형식
완전히 수정된 markdown 본문만. 메타 코멘트, 자기 소개 금지."""


def fetch_summary(conn, lec):
    with conn.cursor() as cur:
        cur.execute("SELECT summary FROM lecture_summaries WHERE lecture=%s", (lec,))
        row = cur.fetchone()
    return row[0] if row else None


def update_summary(conn, lec, new_text):
    with conn.cursor() as cur:
        cur.execute("UPDATE lecture_summaries SET summary=%s, generated_at=NOW() WHERE lecture=%s",
                    (new_text, lec))
    conn.commit()


def panel_revise(conn, lec):
    print(f'\n=== {lec} ===')
    summary = fetch_summary(conn, lec)
    if not summary:
        print('  no summary, skip')
        return False
    before_chars = len(summary)
    print(f'  before: {before_chars} chars')

    # Round 1 — 3 panelists in serial (parallel would race on print)
    print('  Round 1 — independent review')
    r1 = {}
    for label, model, sys_prompt in [
        ('opus',     OPUS,     R1_SYS_OPUS),
        ('deepseek', DEEPSEEK, R1_SYS_DEEPSEEK),
        ('gemini',   GEMINI,   R1_SYS_GEMINI),
    ]:
        raw = call(model, sys_prompt, summary, max_tokens=2500)
        parsed = parse_json_loose(raw)
        n = len(parsed.get('issues', []))
        print(f'    {label}: {n} issues')
        r1[label] = parsed.get('issues', [])

    if not any(r1.values()):
        print('  ⚠ R1 produced no issues; skip revision')
        return False

    # Round 2 — cross-critique
    print('  Round 2 — cross-critique')
    union_issues = []
    for label, issues in r1.items():
        for i, isu in enumerate(issues):
            isu = dict(isu)
            isu['source'] = label
            isu['idx'] = len(union_issues)
            union_issues.append(isu)

    union_text = '\n'.join(
        f"  [{i['idx']}] {i['source']}/{i.get('category','?')}: \"{i.get('quote','')[:60]}\" → {i.get('fix','')}"
        for i in union_issues
    )
    r2 = {}
    for label, model in [('opus', OPUS), ('deepseek', DEEPSEEK), ('gemini', GEMINI)]:
        user = (f"## R1 패널 union 이슈 목록\n{union_text}\n\n## 원본 요약\n{summary[:6000]}\n\n"
                f"위 이슈들에 대해 본인의 R2 평가를 JSON 으로 제출하시오.")
        raw = call(model, R2_SYS, user, max_tokens=2500)
        parsed = parse_json_loose(raw)
        a = len(parsed.get('agree', []))
        r = len(parsed.get('refute', []))
        n = len(parsed.get('new_issues', []))
        print(f'    {label}: agree={a}, refute={r}, new={n}')
        r2[label] = parsed

    # Build the consolidated R2 issue list (only un-refuted + amplified + new)
    refuted_idx = set()
    amplifications = {}
    for panelist in r2.values():
        for ref in panelist.get('refute', []):
            try: refuted_idx.add(int(ref.get('issue_idx', -1)))
            except: pass
        for ag in panelist.get('agree', []):
            idx = ag.get('issue_idx')
            try: idx = int(idx)
            except: continue
            amplifications.setdefault(idx, []).append(ag.get('amplify', ''))

    final_issues = []
    for i in union_issues:
        if i['idx'] in refuted_idx:
            continue
        amp_list = amplifications.get(i['idx'], [])
        i = dict(i)
        if amp_list:
            i['amplifications'] = amp_list
        final_issues.append(i)
    for panelist in r2.values():
        for ni in panelist.get('new_issues', []):
            if isinstance(ni, dict) and ni.get('quote'):
                final_issues.append({**ni, 'source': 'R2_new'})

    if not final_issues:
        print('  ⚠ all issues refuted; skip revision')
        return False

    # Round 3 — Opus rewrites
    print(f'  Round 3 — Opus integration ({len(final_issues)} consolidated issues)')
    issues_block = '\n'.join(
        f"- [{i.get('source','?')}/{i.get('category','?')}] \"{i.get('quote','')[:80]}\" → {i.get('fix','')}"
        + (' || amp: ' + ' / '.join(i['amplifications']) if i.get('amplifications') else '')
        for i in final_issues[:18]
    )
    user = (
        f"## 패널 R2 최종 이슈 목록 (논의 통과)\n{issues_block}\n\n"
        f"## 원본 요약\n---\n{summary}\n---\n\n"
        f"위 이슈를 모두 반영하고, 변주 학습 철학을 적용해 요약을 다시 쓰시오. 마크다운 본문만."
    )
    raw = call(OPUS, R3_SYS, user, max_tokens=12000, timeout=400)
    revised = re.sub(r'^```(?:markdown|md)?\s*', '', raw.strip())
    revised = re.sub(r'\s*```\s*$', '', revised)
    if len(revised) < before_chars * 0.85:
        print(f'  ⚠ R3 revision too short ({len(revised)} < 0.85*{before_chars}), skip update')
        return False

    update_summary(conn, lec, revised)
    print(f'  ✓ updated → {len(revised)} chars (Δ {len(revised)-before_chars:+d})')
    return True


def git_commit_per_lecture(lec, before, after):
    """Commit the DB change for this lecture as a single commit."""
    cmd = [
        'git', '-C', str(ROOT), 'commit', '--allow-empty', '-m',
        f"refactor(summary {lec}): variation-theory + 3-round panel review (chars {before}→{after})\n\n"
        f"Panel: Opus (lead) + DeepSeek v4 flash (STEM rigor) + Gemini Flash (variation)\n"
        f"Applied: CSGF (Contrast/Separation/Generalization/Fusion), elaborative encoding,\n"
        f"spaced retrieval cues, interleaving of confusable pairs, abbreviation expansion.\n\n"
        f"Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        subprocess.run(['git', '-C', str(ROOT), 'push', 'origin', 'main'],
                       check=True, capture_output=True, timeout=30)
        print(f'  ✓ committed + pushed')
    except subprocess.CalledProcessError as e:
        print(f'  ⚠ git error: {e.stderr.decode()[:200]}')
    except Exception as e:
        print(f'  ⚠ push timeout/error: {e}')


def main():
    conn = psycopg2.connect(DB_DSN)
    try:
        for lec in LECTURES:
            before = len(fetch_summary(conn, lec) or '')
            ok = panel_revise(conn, lec)
            if ok:
                after = len(fetch_summary(conn, lec) or '')
                git_commit_per_lecture(lec, before, after)
    finally:
        conn.close()
    print('\n=== panel revision pipeline complete ===')


if __name__ == '__main__':
    main()
