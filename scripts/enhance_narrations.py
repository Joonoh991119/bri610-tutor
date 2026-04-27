#!/usr/bin/env python3
"""
Enhance lecture_narrations via DeepSeek V4 Pro:
  - Insert relevant figures from /frontend/public/figures/*.svg
  - Add 1-2 variation re-explanations (different angles on same concept)
  - Add 1-2 Q&A pairs (Socratic check-points)

Per user mandate (2026-04-27):
  "강의 나레이션 내에 서머리에 있는 이미지를 삽입하고, 독자가 이해할 수 있도록
   변주 설명과 여러가지 질의응답을 던지자. 슬라이드를 줘봤자 이해하기 어려움."

Run as a background script — each narration step takes ~30-90s. 48 total steps
(L3..L8 × 8 steps each) → ~30-60 min.
"""
from __future__ import annotations
import os, sys, json, urllib.request, time, re, pathlib, psycopg2

DB_DSN = os.environ.get('DATABASE_URL', 'dbname=bri610 user=tutor password=tutor610 host=localhost')


def _load_openrouter_key() -> str:
    """Find OPENROUTER_API_KEY: env first, then user shell rc files (user-authorized)."""
    k = os.environ.get('OPENROUTER_API_KEY')
    if k:
        return k
    for rc in ('.zshrc', '.bashrc', '.bash_profile', '.zprofile', '.profile'):
        p = pathlib.Path.home() / rc
        if not p.exists():
            continue
        try:
            for line in p.read_text().splitlines():
                m = re.match(r'\s*export\s+OPENROUTER_API_KEY\s*=\s*[\"\']?([^\"\'\s]+)', line)
                if m:
                    return m.group(1)
        except Exception:
            continue
    raise SystemExit('OPENROUTER_API_KEY not in env or shell rc — set and retry.')


KEY = _load_openrouter_key()

MODEL = 'deepseek/deepseek-v4-pro'

# Figure inventory mapped to lectures by topic (curated — per Markdown.jsx
# /figures/ inventory). Enhancement prompt picks 0-2 figures per step.
FIGURE_TOPICS = {
    'L3': [
        ('bilayer_capacitor.svg',    'Lipid bilayer as parallel-plate capacitor; C_m ≈ εε₀/d'),
        ('membrane_rc_circuit.svg',  'Membrane equivalent circuit: C_m, R_m, E_L, I_inj — KCL form'),
        ('rc_charging_curve.svg',    'Step-current charging: V(t) = V_∞(1−e^(−t/τ)); 63% at t=τ'),
        ('ohmic_iv.svg',             'Single channel I-V line: I = g(V−E_X); slope=g, x-intercept=E_X'),
        ('nernst_diffusion_balance.svg','Nernst balance: diffusion ↔ electric drift at E_X'),
        ('ghk_weighted_log.svg',     'GHK relative permeability bars; K dominates → V_rest near E_K'),
    ],
    'L4': [
        ('ion_channel_subunit.svg',  'K_v 4-subunit symmetry vs Na_v 4-domain asymmetry'),
        ('ohmic_iv.svg',             'I-V line; slope/intercept reading'),
        ('driving_force.svg',        'Driving force (V−E_X): direction flips at reversal'),
        ('synapse_chemical.svg',     'Chemical synapse 6-step cascade'),
        ('conductance_weighted_avg.svg','V_∞ as g-weighted average between E_K and E_Na'),
    ],
    'L5': [
        ('action_potential_phases.svg','AP voltage trace, four phases bounded by E_Na, E_K'),
        ('hh_gating_variables.svg',  'Three sigmoidal gating curves m_∞, h_∞, n_∞'),
        ('voltage_clamp_protocol.svg','Voltage clamp: V step → I_Na transient + I_K plateau'),
        ('ion_channel_subunit.svg',  'K_v vs Na_v structural difference (gating exponents)'),
    ],
    'L6': [
        ('cable_decay_spatial.svg',  'V(x) = V_0 e^(−x/λ); 37% at x=λ, 14% at x=2λ'),
        ('ap_propagation_unmyelinated.svg','Continuous AP propagation along unmyelinated axon'),
        ('ap_propagation_myelinated.svg', 'Saltatory AP jumps between nodes of Ranvier'),
    ],
    'L7': [
        ('f_i_curve_rheobase.svg',   'LIF f-I curve: rheobase + 1/τ_ref saturation'),
        ('action_potential_phases.svg','Real AP vs LIF reset comparison reference'),
    ],
    'L8': [
        ('rate_vs_temporal_codes.svg','Same spike count, different timing patterns'),
        ('psth_construction.svg',    'PSTH = trial-aligned spike density'),
        ('mainen_sejnowski_trial_reliability.svg', 'DC vs frozen-noise reliability paradox'),
        ('hippocampal_phase_precession.svg','Phase precession scatter (place field traversal)'),
    ],
}

SYSTEM = """당신은 BRI610 (computational neuroscience) 강의의 *narration enhancer*.
입력: 한 narration step (10-15 줄). 출력: *같은 핵심 메시지* 를 유지하되, 다음 3 요소가
모두 포함된 enhanced markdown.

## 출력 구성 (순서 고정)
1. **Original narration** (≥80% 보존): 1️⃣..N️⃣ 번호 매김 유지. KaTeX `$..$`, slide refs `[Slide L# p.N]` 보존.
2. **🖼 Figure (0-2 개)**: 입력으로 받은 *FIGURES_AVAILABLE* 중 *이 step 의 핵심 개념* 에 가장 직접 연결되는 1-2 개를 선택. `<figure><img src="/figures/X.svg" alt="..." /><figcaption>그림: ... (간단한 설명 1-2줄)</figcaption></figure>` 형식.
3. **🔁 변주 (2 개)**: 같은 개념을 *다른 각도* 로 재설명. 각 200-400 자.
   - 변주 1: 일상 비유 (댐, 호수, 호스 등) 또는 회로 비유.
   - 변주 2: 수식 → 그림 → 문장 중 *원본과 다른* 표현 형식.
4. **❓ 점검 Q&A (1-2 쌍)**: Socratic check.
   - **Q:** 한 문장 질문 (직관 점검 / 흔한 오해 노출).
   - **A:** 2-4 줄 답변 (오해 → 수정 + 한 문장 일반화).

## 제약
- 출력은 *오로지 enhanced markdown*. prefix/suffix 금지.
- KaTeX 수식 `$...$` `$$...$$` 보존. 한국어 + 영어 학술어 병기 유지.
- Figure 는 FIGURES_AVAILABLE 외 새로 만들 수 없음.
- "변주" 는 *내용 반복* 이 아니라 *표현 변경*. 수식/도식/일상비유 중 다른 형식.
- 원본 ≥ 80% 보존하되, 끝 부분 "→ 다음:" 같은 cliffhanger 가 있으면 enhanced 에서도 마지막에 유지.
"""


def call_deepseek(system: str, user: str, max_tokens: int = 5000, retries: int = 2) -> str:
    body = json.dumps({
        'model': MODEL,
        'messages': [{'role':'system','content':system},{'role':'user','content':user}],
        'max_tokens': max_tokens,
        'temperature': 0.4,
    }).encode()
    req = urllib.request.Request(
        'https://openrouter.ai/api/v1/chat/completions',
        data=body,
        headers={'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'},
    )
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=420) as r:
                d = json.loads(r.read())
                if d.get('choices'):
                    msg = d['choices'][0]['message']
                    return msg.get('content') or msg.get('reasoning') or ''
        except Exception as e:
            print(f'  retry {attempt} after {e}', file=sys.stderr)
            time.sleep(2 ** attempt + 1)
    return ''


def enhance_one(conn, lecture: str, step_id: int) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT step_kind, title_ko, slide_refs, narration_md FROM lecture_narrations "
            "WHERE lecture=%s AND step_id=%s",
            (lecture, step_id),
        )
        row = cur.fetchone()
    if not row:
        print(f'{lecture}/step {step_id}: not found, skip')
        return False
    step_kind, title_ko, slide_refs, narration = row

    # If already enhanced (contains <figure> tag and 변주 marker), skip — idempotent
    if '<figure' in narration and '🔁' in narration and '❓' in narration:
        print(f'{lecture}/step {step_id}: already enhanced — skip')
        return False

    figs = FIGURE_TOPICS.get(lecture, [])
    fig_list = '\n'.join(f'  - /figures/{name}: {desc}' for name, desc in figs)

    user_prompt = (
        f"## Step metadata\n"
        f"- lecture: {lecture}\n"
        f"- step_id: {step_id}\n"
        f"- step_kind: {step_kind}\n"
        f"- title: {title_ko}\n"
        f"- slide_refs: {slide_refs}\n\n"
        f"## FIGURES_AVAILABLE (lecture {lecture})\n"
        f"{fig_list or '  (none — text-only enhancement)'}\n\n"
        f"## Original narration\n"
        f"---\n{narration}\n---\n\n"
        f"## 작업\n"
        f"위 narration 을 시스템 규칙대로 enhanced markdown 으로 출력. "
        f"FIGURES_AVAILABLE 중 이 step 핵심 개념과 가장 직접 연결되는 0-2 개를 선택 (관련 없으면 생략 OK)."
    )

    enhanced = call_deepseek(SYSTEM, user_prompt, max_tokens=4500)
    if not enhanced or len(enhanced) < len(narration) * 0.7:
        print(f'{lecture}/step {step_id}: enhancement too short ({len(enhanced)} vs {len(narration)}) — skip')
        return False

    with conn.cursor() as cur:
        cur.execute(
            "UPDATE lecture_narrations SET narration_md=%s, model=%s, generated_at=now() "
            "WHERE lecture=%s AND step_id=%s",
            (enhanced, f'deepseek/deepseek-v4-pro|enhanced', lecture, step_id),
        )
    conn.commit()
    print(f'{lecture}/step {step_id}: enhanced ({len(narration)} → {len(enhanced)} chars)')
    return True


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None  # e.g., "L3" to limit
    conn = psycopg2.connect(DB_DSN)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT lecture, step_id FROM lecture_narrations "
                "WHERE (%s IS NULL OR lecture = %s) "
                "ORDER BY lecture, step_id",
                (only, only),
            )
            steps = cur.fetchall()
        print(f'enhancing {len(steps)} steps...')
        n_ok = 0
        for lec, sid in steps:
            try:
                if enhance_one(conn, lec, sid):
                    n_ok += 1
            except Exception as e:
                print(f'{lec}/step {sid}: ERROR {type(e).__name__}: {e}', file=sys.stderr)
        print(f'\nDone: {n_ok}/{len(steps)} steps enhanced.')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
