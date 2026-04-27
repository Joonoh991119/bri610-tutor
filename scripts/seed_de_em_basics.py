#!/usr/bin/env python3
"""
seed_de_em_basics.py — 12 DE/EM zero-knowledge foundation cards for BRI610.

Bridges "no math / no EM background" → "ready for L3-L8".
Topic: de_em_basics
Card shape matches existing `foundations` cards (recall/concept/application/proof,
difficulty 1-3, slide-grounded citations referencing where each concept is first used).

Coverage: 12 of 15 possible cards selected for maximal BRI610 relevance:
  DE (6):  derivative_meaning, separation_of_variables, exponential_decay_intuition,
            first_order_ode_general, integral_as_area, dimensional_analysis
  EM (6):  charge_intuition, current_definition, voltage_definition,
            conductors_insulators_membrane, kirchhoff_current_law, ohms_law_water

Idempotent: re-running skips duplicates by (topic, card_type, mastery_target).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "backend"))

from db_pool import acquire, release  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# SVG SCHEMATICS — academic ink palette, 480px wide, < 200 lines each
# ─────────────────────────────────────────────────────────────────────────────

SVG_SLOPE_LINE = """<figure>
<svg viewBox="0 0 400 200" xmlns="http://www.w3.org/2000/svg" style="font-family:var(--font-sans);font-size:12px;max-width:100%;">
  <!-- Axes -->
  <line x1="50" y1="170" x2="370" y2="170" stroke="#1a1a20" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="50" y1="170" x2="50"  y2="20"  stroke="#1a1a20" stroke-width="1.5" marker-end="url(#arr)"/>
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#1a1a20"/>
    </marker>
  </defs>
  <!-- V(t) line: slope = 5 mV/ms -->
  <line x1="70" y1="155" x2="340" y2="35" stroke="#1a5c8e" stroke-width="2.5"/>
  <!-- Tangent triangle at t=1 ms -->
  <line x1="130" y1="125" x2="230" y2="125" stroke="#8a2a3b" stroke-width="1.2" stroke-dasharray="4,3"/>
  <line x1="230" y1="125" x2="230" y2="75"  stroke="#8a2a3b" stroke-width="1.2" stroke-dasharray="4,3"/>
  <!-- Labels -->
  <text x="350" y="178" fill="#1a1a20">t (ms)</text>
  <text x="55" y="15" fill="#1a1a20">V (mV)</text>
  <text x="165" y="142" fill="#8a2a3b" font-size="11">Δt=1 ms</text>
  <text x="235" y="102" fill="#8a2a3b" font-size="11">ΔV=5 mV</text>
  <text x="200" y="60" fill="#1a5c8e" font-weight="700">dV/dt = 5 mV/ms</text>
</svg>
<figcaption>그림: 기울기로서의 도함수. 접선의 기울기 = dV/dt = ΔV/Δt 극한 (슬라이드 L3 p.20 막전위 방정식의 기반).</figcaption>
</figure>"""

SVG_EXPONENTIAL_DECAY = """<figure>
<svg viewBox="0 0 400 200" xmlns="http://www.w3.org/2000/svg" style="font-family:var(--font-sans);font-size:12px;max-width:100%;">
  <!-- Axes -->
  <defs>
    <marker id="arr2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#1a1a20"/>
    </marker>
  </defs>
  <line x1="40" y1="175" x2="380" y2="175" stroke="#1a1a20" stroke-width="1.5" marker-end="url(#arr2)"/>
  <line x1="40" y1="175" x2="40"  y2="15"  stroke="#1a1a20" stroke-width="1.5" marker-end="url(#arr2)"/>
  <!-- Exponential decay curve (approximate via polyline) -->
  <polyline points="40,25 80,47 120,73 160,95 200,112 240,126 280,137 320,145 360,151 380,154"
            fill="none" stroke="#1a5c8e" stroke-width="2.5"/>
  <!-- y0 label -->
  <line x1="35" y1="25" x2="45" y2="25" stroke="#1a1a20" stroke-width="1"/>
  <text x="5" y="29" fill="#1a1a20" font-size="11">y₀</text>
  <!-- 1/e level -->
  <line x1="35" y1="83" x2="120" y2="83" stroke="#8a2a3b" stroke-width="1" stroke-dasharray="4,3"/>
  <line x1="120" y1="83" x2="120" y2="175" stroke="#8a2a3b" stroke-width="1" stroke-dasharray="4,3"/>
  <text x="42" y="79" fill="#8a2a3b" font-size="10">≈37% y₀</text>
  <text x="105" y="188" fill="#8a2a3b" font-size="11">τ</text>
  <!-- Axis labels -->
  <text x="365" y="188" fill="#1a1a20" font-size="11">t</text>
  <text x="45" y="12" fill="#1a1a20" font-size="11">y(t)=y₀e^{−t/τ}</text>
</svg>
<figcaption>그림: y(t)=y₀e^{-t/τ}. τ에서 37%(=1/e) 남음. 이 곡선이 L3 p.20~23의 막전위 충방전 및 L5 p.22의 게이팅 변수 n(t) 기반.</figcaption>
</figure>"""

SVG_PIPE_FLOW = """<figure>
<svg viewBox="0 0 400 160" xmlns="http://www.w3.org/2000/svg" style="font-family:var(--font-sans);font-size:12px;max-width:100%;">
  <!-- High pressure side -->
  <rect x="20" y="40" width="60" height="80" fill="#d4e9f7" stroke="#1a5c8e" stroke-width="1.5" rx="4"/>
  <text x="50" y="75" text-anchor="middle" fill="#1a5c8e" font-weight="700">고압</text>
  <text x="50" y="92" text-anchor="middle" fill="#1a5c8e" font-size="10">V₁</text>
  <!-- Low pressure side -->
  <rect x="320" y="60" width="60" height="60" fill="#edf7d4" stroke="#3b6b22" stroke-width="1.5" rx="4"/>
  <text x="350" y="88" text-anchor="middle" fill="#3b6b22" font-weight="700">저압</text>
  <text x="350" y="105" text-anchor="middle" fill="#3b6b22" font-size="10">V₂</text>
  <!-- Pipe -->
  <rect x="80" y="70" width="240" height="20" fill="#f0e8d4" stroke="#1a1a20" stroke-width="1.5" rx="3"/>
  <!-- Flow arrows -->
  <text x="160" y="84" fill="#8a2a3b" font-size="18">→→→</text>
  <!-- Resistance label -->
  <text x="200" y="105" text-anchor="middle" fill="#1a1a20" font-size="11">저항 R (파이프 좁기)</text>
  <!-- Ohm label -->
  <text x="200" y="125" text-anchor="middle" fill="#8a2a3b" font-weight="700">I = (V₁−V₂)/R</text>
</svg>
<figcaption>그림: 물 흐름 비유. 압력차(voltage) → 흐름(current), 파이프 좁기(resistance). L3 p.21–22의 막 저항 개념 직관.</figcaption>
</figure>"""

SVG_KCL_NODE = """<figure>
<svg viewBox="0 0 360 200" xmlns="http://www.w3.org/2000/svg" style="font-family:var(--font-sans);font-size:12px;max-width:100%;">
  <defs>
    <marker id="aw" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#1a1a20"/>
    </marker>
    <marker id="ab" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#1a5c8e"/>
    </marker>
    <marker id="ar" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8a2a3b"/>
    </marker>
  </defs>
  <!-- Node circle -->
  <circle cx="180" cy="100" r="14" fill="#f5f0e8" stroke="#1a1a20" stroke-width="2"/>
  <text x="180" y="105" text-anchor="middle" fill="#1a1a20" font-weight="700">V</text>
  <!-- I_inj arrow in from left -->
  <line x1="60" y1="100" x2="162" y2="100" stroke="#1a5c8e" stroke-width="2" marker-end="url(#ab)"/>
  <text x="95" y="88" fill="#1a5c8e" font-weight="700">I_inj</text>
  <!-- I_C arrow out upward -->
  <line x1="180" y1="86" x2="180" y2="25" stroke="#8a2a3b" stroke-width="2" marker-end="url(#ar)"/>
  <text x="188" y="60" fill="#8a2a3b" font-weight="700">I_C</text>
  <!-- I_R arrow out downward -->
  <line x1="180" y1="114" x2="180" y2="175" stroke="#1a1a20" stroke-width="2" marker-end="url(#aw)"/>
  <text x="188" y="155" fill="#1a1a20" font-weight="700">I_R</text>
  <!-- KCL equation -->
  <text x="270" y="100" fill="#8a2a3b" font-size="13" font-weight="700">I_inj</text>
  <text x="315" y="100" fill="#1a1a20" font-size="13">=</text>
  <text x="328" y="100" fill="#8a2a3b" font-size="13" font-weight="700">I_C+I_R</text>
</svg>
<figcaption>그림: KCL 노드. 유입 전류(I_inj) = 커패시터 전류(I_C) + 저항 전류(I_R). 이것이 L3 p.20의 막 방정식 출발점이다.</figcaption>
</figure>"""


# ─────────────────────────────────────────────────────────────────────────────
# 12 DE/EM BASICS CARDS
# ─────────────────────────────────────────────────────────────────────────────

SEEDS: list[dict] = [

    # ─── DE 1: derivative_meaning ─────────────────────────────────────────────
    {
        "topic": "de_em_basics",
        "card_type": "recall",
        "difficulty": 1,
        "bloom": "Understand",
        "mastery_target": "derivative_meaning",
        "prompt_md": (
            "**Setup.** 슬라이드 L3 p.20은 $I_C = C_m \\, dV_m/dt$를 도입한다. "
            "이 식의 핵심은 $dV/dt$ — **도함수(derivative)** — 의 의미를 이해하는 것이다.\n\n"
            + SVG_SLOPE_LINE + "\n\n"
            "(a) $dV/dt = 5\\ \\mathrm{mV/ms}$가 물리적으로 의미하는 바를 **두 가지 방식**으로 서술하시오: "
            "(i) 순간적(instantaneous) 기울기로서의 해석, "
            "(ii) 짧은 시간 $\\Delta t = 1\\ \\mathrm{ms}$가 지났을 때의 근사적 변화량.\n"
            "(b) 위 그림에서 접선 삼각형(tangent triangle)의 두 변 $\\Delta V$와 $\\Delta t$를 식별하고, "
            "평균 변화율과 순간 변화율의 차이를 설명하시오.\n"
            "(c) **타당성 영역 힌트**: '$1\\ \\mathrm{ms}$ 후 V가 5 mV 변한다'는 근사가 정확하지 않은 이유는 "
            "무엇인가? (힌트: 막전위는 지수적으로 변한다)"
        ),
        "answer_md": (
            "(a) **$dV/dt = 5\\ \\mathrm{mV/ms}$의 두 가지 해석**\n\n"
            "① **순간 기울기**: 시각 $t$에서 $V(t)$ 곡선의 접선(tangent)의 기울기가 5 mV/ms. "
            "즉, 그 순간 막전위가 '얼마나 빠르게 변하고 있는가'를 나타내는 순간 변화율이다.\n\n"
            "② **근사적 변화량**: $\\Delta t \\to 0$ 극한의 정의이므로, 충분히 짧은 $\\Delta t$ 동안:\n"
            "$$\\Delta V \\approx \\frac{dV}{dt} \\cdot \\Delta t = 5\\ \\mathrm{mV/ms} \\times 1\\ \\mathrm{ms} = 5\\ \\mathrm{mV}$$\n"
            "즉, '지금 이 순간의 변화율로 1 ms 동안 유지된다면 약 5 mV 변한다'는 뜻.\n\n"
            "(b) **접선 삼각형 해석**\n\n"
            "그림의 빨간 삼각형: 가로변 $\\Delta t$ (시간), 세로변 $\\Delta V$ (전압 변화).\n"
            "- **평균 변화율**: 두 점 사이 직선의 기울기 $\\Delta V / \\Delta t$ (할선, secant).\n"
            "- **순간 변화율** $dV/dt$: $\\Delta t \\to 0$ 극한 — 접선(tangent)의 기울기.\n\n"
            "(c) **근사의 타당성 영역**\n\n"
            "막전위는 지수 함수 $V(t) = V_\\infty + (V_0 - V_\\infty)e^{-t/\\tau_m}$로 변한다 "
            "(L3 p.20–23). 이 경우 $dV/dt$는 시간에 따라 변하므로, 1 ms 동안 '5 mV 변한다'는 "
            "근사는 $1\\ \\mathrm{ms} \\ll \\tau_m$ (막 시간 상수)일 때만 좋다. "
            "$\\tau_m \\sim 10\\text{–}100\\ \\mathrm{ms}$이므로 1 ms는 충분히 짧아 근사가 유효하지만, "
            "10 ms 이상에서는 오차가 커진다."
        ),
        "rationale_md": (
            "**흔한 학생 오개념**: $dV/dt$를 '1 ms 후의 정확한 전압 변화'로 이해하는 것. "
            "도함수는 **순간** 변화율이므로 특정 시간 동안의 변화는 적분해야 정확하다: "
            "$\\Delta V = \\int_{t_0}^{t_0 + \\Delta t} (dV/dt)\\, dt$. "
            "단, $\\Delta t$가 충분히 짧으면 $dV/dt$가 거의 상수로 근사되어 $\\approx (dV/dt)\\Delta t$가 된다.\n\n"
            "**또 다른 오해**: '도함수'가 복잡한 개념이라는 막연한 두려움. "
            "L3 p.20 슬라이드 예시가 정확히 이것을 설명: 1 nF 뉴런에 1 nA를 주입하면 "
            "$dV/dt = 1\\ \\mathrm{nA}/1\\ \\mathrm{nF} = 1\\ \\mathrm{mV/ms}$ — "
            "도함수가 측정 가능한 물리량임을 보여준다.\n\n"
            "**연결**: L5 p.21의 $dn/dt = \\alpha_n(1-n) - \\beta_n n$도 동일한 '순간 변화율' 개념 — "
            "게이팅 변수 $n$이 지금 이 순간 얼마나 빠르게 변하는가를 나타낸다."
        ),
        "source_citation": {"kind": "slide", "lecture": "L3", "page": 20,
                             "note": "dV/dt 막전위 변화율 개념 첫 사용"},
        "priority_score": 0.95,
        "info_density": 0.90,
    },

    # ─── DE 2: separation_of_variables ────────────────────────────────────────
    {
        "topic": "de_em_basics",
        "card_type": "proof",
        "difficulty": 2,
        "bloom": "Apply",
        "mastery_target": "separation_of_variables",
        "prompt_md": (
            "**Setup.** 슬라이드 L3 p.23의 막 시간 상수 $\\tau_m$, "
            "L5 p.22의 게이팅 변수 ODE $dn/dt = (n_\\infty - n)/\\tau_n$, "
            "L7 p.12의 LIF 방정식이 모두 동일한 수학 구조를 가진다: "
            "$\\tau \\frac{dy}{dt} = -y + B$ (상수 $B$, 시상수 $\\tau$).\n\n"
            "(a) 가장 단순한 형태 $\\frac{dy}{dt} = -\\frac{y}{\\tau}$를 변수 분리법(separation of variables)으로 풀어 "
            "$y(t) = y_0 e^{-t/\\tau}$를 유도하시오. 단계: (i) $dy/y = ?$, (ii) 양변 적분, (iii) 초기 조건 적용.\n"
            "(b) 왜 변수 분리법이 이 ODE에 적용 가능한가? (어떤 수학적 구조가 분리를 허용하는가?)\n"
            "(c) $\\tau \\frac{dy}{dt} = -y + B$ (비동질 형태, $B \\neq 0$)를 풀기 위한 변수 치환 전략: "
            "$u = y - B$로 치환하면 어떤 동질(homogeneous) ODE가 되는가? 그 해를 원래 변수로 돌아와 쓰시오."
        ),
        "answer_md": (
            "(a) **변수 분리법 단계별 유도**\n\n"
            "시작: $\\frac{dy}{dt} = -\\frac{y}{\\tau}$\n\n"
            "(i) 변수 분리 ($y \\neq 0$):\n"
            "$$\\frac{dy}{y} = -\\frac{dt}{\\tau}$$\n\n"
            "(ii) 양변 적분:\n"
            "$$\\int \\frac{dy}{y} = \\int -\\frac{dt}{\\tau}$$\n"
            "$$\\ln|y| = -\\frac{t}{\\tau} + C_0$$\n\n"
            "(iii) 지수 취하기:\n"
            "$$y(t) = A e^{-t/\\tau}, \\quad A = e^{C_0}$$\n\n"
            "초기 조건 $y(0) = y_0$: $A = y_0$. 따라서:\n"
            "$$\\boxed{y(t) = y_0 \\, e^{-t/\\tau}}$$\n\n"
            "(b) **분리 가능성의 수학적 구조**\n\n"
            "ODE $dy/dt = f(t) \\cdot g(y)$ 형태일 때 변수 분리 가능.\n"
            "$dy/dt = -y/\\tau$에서: $f(t) = -1/\\tau$ (상수), $g(y) = y$.\n"
            "핵심: 우변이 $t$의 함수 × $y$의 함수의 곱 → $dy/y$와 $dt$ 각각의 변수로 분리 가능.\n"
            "이것이 **가산(multiplicative) ODE**의 핵심 구조이다.\n\n"
            "(c) **비동질 ODE 해: 변수 치환**\n\n"
            "치환: $u = y - B$ (정상 상태 $B$로부터의 편차).\n"
            "그러면 $du/dt = dy/dt$이고 $y = u + B$를 대입:\n"
            "$$\\tau \\frac{du}{dt} = -(u + B) + B = -u$$\n"
            "→ 동질 ODE: $\\tau du/dt = -u$ → $u(t) = u_0 e^{-t/\\tau}$.\n\n"
            "원래 변수로 환원 ($u_0 = y_0 - B$):\n"
            "$$\\boxed{y(t) = B + (y_0 - B)\\,e^{-t/\\tau}}$$\n\n"
            "해석: $t \\to \\infty$이면 $y \\to B$ (정상 상태), $t=0$이면 $y = y_0$ ✓."
        ),
        "rationale_md": (
            "**흔한 학생 오개념**: 비동질 ODE $\\tau dy/dt = -y + B$에서 변수 분리를 시도하다 실패하는 것. "
            "비동질 형태는 직접 분리 불가 — 먼저 $u = y - B$ 치환으로 동질 형태로 만들어야 한다. "
            "이 '정상 상태로부터의 편차' 치환이 BRI610 전반에 걸쳐 핵심 기법이다.\n\n"
            "**또 다른 오해**: 적분 상수 $C_0$를 마지막에 아무 값으로 정하는 것. "
            "$C_0$는 초기 조건 $y(0) = y_0$에 의해 정확히 결정되어야 한다. "
            "이 단계를 빠뜨리면 특수해(particular solution)가 아닌 일반해(general solution)에 머문다.\n\n"
            "**연결**: L5 p.22의 $dn/dt = \\alpha_n(1-n) - \\beta_n n$은 "
            "$n_\\infty = \\alpha_n/(\\alpha_n+\\beta_n)$, $\\tau_n = 1/(\\alpha_n+\\beta_n)$으로 "
            "쓰면 $dn/dt = (n_\\infty - n)/\\tau_n$이 되어 정확히 비동질 1차 ODE 형태. "
            "해: $n(t) = n_\\infty + (n_0 - n_\\infty)e^{-t/\\tau_n}$."
        ),
        "source_citation": {"kind": "slide", "lecture": "L3", "page": 23,
                             "note": "τ_m = R_m C_m 도입; 이 ODE 구조가 L5 p.22, L7 p.12에서 사용"},
        "priority_score": 0.98,
        "info_density": 0.95,
    },

    # ─── DE 3: exponential_decay_intuition ────────────────────────────────────
    {
        "topic": "de_em_basics",
        "card_type": "concept",
        "difficulty": 1,
        "bloom": "Understand",
        "mastery_target": "exponential_decay_intuition",
        "prompt_md": (
            "**Setup.** $y(t) = y_0 e^{-t/\\tau}$ 형태의 지수 감쇠(exponential decay)는 "
            "L3 p.23의 막 시간 상수, L5 p.22의 게이팅 변수, L7 p.16의 LIF ISI 계산 등 "
            "BRI610 전반에 나타난다.\n\n"
            + SVG_EXPONENTIAL_DECAY + "\n\n"
            "(a) **'37% 규칙'**: $t = \\tau$에서 $y(\\tau)/y_0$를 정확히 계산하시오. "
            "$e \\approx 2.718$을 이용하여 소수점 첫째 자리까지 답하라.\n"
            "(b) **'63% 규칙' (충전 곡선)**: $y_0 = 0$에서 출발하여 $y_\\infty$로 상승하는 경우 "
            "$y(t) = y_\\infty(1 - e^{-t/\\tau})$에서 $t = \\tau$일 때 목표값의 몇 %에 도달하는가?\n"
            "(c) 두 관점을 대조하라: (i) 지수 감쇠를 '매 $\\tau$ 마다 지수적으로 작아진다'는 관점과 "
            "(ii) '각 순간 남은 거리의 $1/\\tau$씩 줄어든다'는 속도 관점. "
            "어느 관점이 $dy/dt = -y/\\tau$ ODE에서 더 직접적으로 읽히는가?"
        ),
        "answer_md": (
            "(a) **37% 규칙 계산**\n\n"
            "$$\\frac{y(\\tau)}{y_0} = e^{-\\tau/\\tau} = e^{-1} = \\frac{1}{e} \\approx \\frac{1}{2.718} \\approx 0.368 = 36.8\\%$$\n\n"
            "즉, 시간 상수 $\\tau$ 후에는 초기값의 약 37%만 남는다 — 또는 63%가 '소멸'했다.\n\n"
            "(b) **충전 곡선에서 63% 도달**\n\n"
            "$$y(\\tau) = y_\\infty(1 - e^{-1}) \\approx y_\\infty \\times 0.632 = 63.2\\% \\cdot y_\\infty$$\n\n"
            "즉, 충전 곡선에서는 $\\tau$ 후에 목표값의 63%에 도달한다. "
            "이 값이 슬라이드 L3 p.20 그래프의 '63%' 표시이다.\n\n"
            "(c) **두 관점 비교**\n\n"
            "| 관점 | 서술 | ODE와의 연결 |\n"
            "|---|---|---|\n"
            "| 전역적(global) | 매 $\\tau$마다 $1/e \\approx 37\\%$씩 곱해짐 | 유한 시간 후 결과를 계산하기 좋음 |\n"
            "| 속도(local) | 현재값의 $1/\\tau$씩 감소: $dy/dt = -(1/\\tau)\\cdot y$ | ODE에서 **직접** 읽힘 |\n\n"
            "속도 관점이 ODE $dy/dt = -y/\\tau$에서 더 직접적: 우변 $-y/\\tau$가 "
            "'현재 $y$값에 비례한 속도로 감소'임을 명시적으로 나타낸다. "
            "이 자기조절(self-referential) 구조가 지수 함수를 유일하게 결정한다."
        ),
        "rationale_md": (
            "**흔한 학생 오개념**: $\\tau$ 후에 $y = 0$이 된다고 생각하는 것. "
            "지수 함수는 수학적으로 절대 0에 도달하지 않는다 ($e^{-x} > 0$ for all finite $x$). "
            "실용적으로는 $5\\tau$ 후에 $e^{-5} \\approx 0.67\\%$ 남아 '거의 완료'로 취급한다.\n\n"
            "**또 다른 오해**: '37%'와 '63%'가 다른 현상이라고 생각하는 것. "
            "두 값은 동일한 수 $1-1/e \\approx 0.632$의 두 면 — 감쇠에서 63% 소멸했고, "
            "충전에서 63% 도달했다. 같은 시간 상수 $\\tau$로 기술된다.\n\n"
            "**연결**: L5 p.22 $n_\\infty$로의 수렴, L7 p.15 LIF $V(t)$ 충전, "
            "L6 p.11 케이블의 공간 감쇠 $V(x) = V_0 e^{-x/\\lambda}$ (시간 대신 공간 변수) 모두 "
            "이 37%/63% 개념의 변형이다."
        ),
        "source_citation": {"kind": "slide", "lecture": "L3", "page": 23,
                             "note": "τ_m 개념; 지수 감쇠가 L5 p.22, L6 p.11, L7 p.15에서 사용"},
        "priority_score": 0.96,
        "info_density": 0.92,
    },

    # ─── DE 4: first_order_ode_general ────────────────────────────────────────
    {
        "topic": "de_em_basics",
        "card_type": "concept",
        "difficulty": 2,
        "bloom": "Analyze",
        "mastery_target": "first_order_ode_general",
        "prompt_md": (
            "**Setup.** 슬라이드 L7 p.11 주석: BRI610의 거의 모든 방정식이 "
            "$\\tau \\frac{dy}{dt} = -y + B(t)$ 하나의 템플릿으로 요약된다 (단, $B$가 상수이거나 시간 의존일 수 있음).\n\n"
            "(a) 다음 네 BRI610 방정식 각각에서 $y$, $\\tau$, $B$에 해당하는 양이 무엇인지 표를 채우시오:\n"
            "  (i) L3 p.20 막 방정식: $\\tau_m dV/dt = -(V - E_L) + R_m I_e$\n"
            "  (ii) L5 p.21 게이팅 변수: $dn/dt = \\alpha_n(1-n) - \\beta_n n$\n"
            "  (iii) L6 p.8 정상 케이블: $\\lambda^2 d^2V/dx^2 - V = 0$ (시간 대신 공간 변수)\n"
            "  (iv) L7 p.23 $g_{sra}$ 방정식: $\\tau_{sra} dg_{sra}/dt = -g_{sra}$\n"
            "(b) 이 템플릿이 '끌개(attractor) + 이완(relaxation)' 구조를 갖는다고 설명하시오. "
            "$B$가 끌어당기는 목표(target)라는 점에서.\n"
            "(c) $B$가 **시간 의존**일 때 ($B = B(t)$) 해가 어떻게 달라지는가? "
            "(정성적 설명; 복잡한 경우 적분인자(integrating factor) 방법 언급 충분)"
        ),
        "answer_md": (
            "(a) **BRI610 방정식 분류표**\n\n"
            "| 방정식 | $y$ | $\\tau$ | $B$ | 정상 상태 $y_\\infty = B$ |\n"
            "|---|---|---|---|---|\n"
            "| L3 막 방정식 | $V$ | $\\tau_m = R_m C_m$ | $E_L + R_m I_e$ | $V_{\\infty} = E_L + R_m I_e$ |\n"
            "| L5 게이팅 변수 | $n$ | $\\tau_n(V)$ | $n_\\infty(V)$ | 고정 $V$에서 $n_\\infty$ |\n"
            "| L6 정상 케이블 | $V(x)$ | $\\lambda$ (공간 스케일) | 0 (경계 조건에 의존) | 0 (무한대에서) |\n"
            "| L7 $g_{sra}$ | $g_{sra}$ | $\\tau_{sra}$ | 0 | 0 (스파이크 없을 때) |\n\n"
            "(b) **끌개 + 이완 구조**\n\n"
            "템플릿 $\\tau dy/dt = -(y - B)$를 보면:\n"
            "- $y > B$일 때: $dy/dt < 0$ → $y$가 $B$를 향해 감소.\n"
            "- $y < B$일 때: $dy/dt > 0$ → $y$가 $B$를 향해 증가.\n"
            "- $y = B$일 때: $dy/dt = 0$ → 정상 상태.\n\n"
            "$B$가 **끌개(attractor)** = 시스템이 항상 향해가는 목표. "
            "$\\tau$는 '얼마나 빠르게 끌리는가' = 이완 속도. "
            "이 구조가 안정(stable) 정점(fixed point)을 만든다.\n\n"
            "(c) **$B = B(t)$ (시간 의존) 일 때**\n\n"
            "정상 상태가 시간에 따라 움직이므로 시스템이 '움직이는 목표'를 쫓는다. "
            "해는 더 이상 단순한 지수 형태가 아니며, 적분인자(integrating factor) 방법:\n"
            "$$y(t) = e^{-t/\\tau}\\left[y_0 + \\frac{1}{\\tau}\\int_0^t B(t')e^{t'/\\tau}\\, dt'\\right]$$\n"
            "이 공식은 LIF 뉴런의 임의 전류 $I_e(t)$에 대한 막전위 $V(t)$의 일반해이다 (L7 p.12–14)."
        ),
        "rationale_md": (
            "**흔한 학생 오개념**: 각 BRI610 방정식이 서로 다른 수학 구조를 갖는다고 생각하는 것. "
            "실제로는 모두 동일한 1차 선형 ODE 템플릿의 변형이다. "
            "이 패턴을 인식하면 새 방정식을 볼 때마다 '$y$, $\\tau$, $B$가 뭐지?'라고 물으면 된다.\n\n"
            "**또 다른 오해**: $B$가 항상 상수라고 가정하는 것. "
            "게이팅 변수에서 $B = n_\\infty(V)$는 전압에 의존하므로 비선형 — "
            "V가 변하면 $B$도 변하여 시스템이 복잡해진다. 이것이 HH 모델 비선형성의 근원이다.\n\n"
            "**연결**: L6 p.8 케이블 방정식은 동일 템플릿이지만 '시간' 대신 '공간'이 독립 변수. "
            "이것이 시간 상수 $\\tau_m$과 공간 상수 $\\lambda$가 수학적으로 유사한 이유이다."
        ),
        "source_citation": {"kind": "slide", "lecture": "L7", "page": 11,
                             "note": "LIF 도출에서 1차 ODE 템플릿 명시; L3 p.23, L5 p.22에서도 사용"},
        "priority_score": 0.97,
        "info_density": 0.95,
    },

    # ─── DE 5: integral_as_area ───────────────────────────────────────────────
    {
        "topic": "de_em_basics",
        "card_type": "application",
        "difficulty": 2,
        "bloom": "Apply",
        "mastery_target": "integral_as_area",
        "prompt_md": (
            "**Setup.** 적분(integration)은 '누적(accumulation)'이다. "
            "$Q = \\int I(t)\\, dt$는 L3 p.19 $I_C = C\\, dV/dt$의 역방향 — "
            "전류가 흐르면 전하가 쌓이고, 전하가 쌓이면 막전위가 변한다.\n\n"
            "(a) **직사각형 펄스 예시**: $I(t) = 1\\ \\mathrm{nA}$ (0 ≤ t ≤ 2 ms), 그 외 0이라 하자. "
            "이 펄스 동안 흐른 총 전하 $Q = \\int_0^{2\\,\\mathrm{ms}} I\\, dt$를 계산하시오 "
            "(단위 확인 포함).\n"
            "(b) 위에서 구한 $Q$가 뉴런의 막전위 변화 $\\Delta V$에 어떻게 연결되는가? "
            "$Q = C_m \\Delta V$ ($C_m = 0.5\\ \\mathrm{nF}$)를 이용하여 $\\Delta V$를 계산하시오 "
            "(단, 누설이 없다고 가정).\n"
            "(c) '전류의 시간 적분 = 면적'이라는 기하학적 해석을 사용하여, "
            "동일한 총 전하를 주입하되 펄스 폭이 짧을수록($\\Delta t$ 감소, $I$ 증가) "
            "뉴런이 느끼는 전압 변화가 같다고 설명하시오. 이것이 왜 신경과학에서 중요한가?"
        ),
        "answer_md": (
            "(a) **펄스 전하 계산**\n\n"
            "$I(t) = 1\\ \\mathrm{nA}$ = 상수 (0–2 ms 동안)이므로 적분 = 면적 = 상수 × 폭:\n"
            "$$Q = \\int_0^{2\\,\\mathrm{ms}} 1\\ \\mathrm{nA}\\, dt = 1\\ \\mathrm{nA} \\times 2\\ \\mathrm{ms} = 2\\ \\mathrm{nA\\cdot ms}$$\n\n"
            "단위 변환: $1\\ \\mathrm{nA\\cdot ms} = 1\\times 10^{-9}\\ \\mathrm{A} \\times 10^{-3}\\ \\mathrm{s} = 10^{-12}\\ \\mathrm{C} = 1\\ \\mathrm{pC}$.\n"
            "따라서 $Q = 2\\ \\mathrm{pC}$.\n\n"
            "(b) **전하 → 막전위 변화**\n\n"
            "$Q = C_m \\Delta V$에서:\n"
            "$$\\Delta V = \\frac{Q}{C_m} = \\frac{2\\ \\mathrm{pC}}{0.5\\ \\mathrm{nF}} = \\frac{2\\times10^{-12}\\ \\mathrm{C}}{0.5\\times10^{-9}\\ \\mathrm{F}} = 4\\times10^{-3}\\ \\mathrm{V} = 4\\ \\mathrm{mV}$$\n\n"
            "(c) **면적 불변 = 동일 $\\Delta V$**\n\n"
            "면적 $Q = I \\times \\Delta t$가 같으면 $\\Delta V = Q/C_m$도 같다. "
            "예: $I = 2\\ \\mathrm{nA}$, $\\Delta t = 1\\ \\mathrm{ms}$ → $Q = 2\\ \\mathrm{pC}$로 동일.\n\n"
            "신경과학적 중요성: 시냅스 입력(EPSC)의 **총 전하(charge)**가 막전위 변화를 결정한다 "
            "(전류의 최대값이 아니라). 이것이 시냅스 전달(synaptic transmission) 효율의 기준이 되며, "
            "패치 클램프 실험에서 EPSC 면적으로 시냅스 강도를 측정하는 근거이다."
        ),
        "rationale_md": (
            "**흔한 학생 오개념**: 전류(nA)와 전하(pC)를 혼동하는 것. "
            "전류는 단위 시간당 전하의 흐름 ($I = dQ/dt$)이므로, "
            "전하를 구하려면 전류를 시간에 대해 적분해야 한다. "
            "1 nA = 1 pC/ms이라는 단위 관계를 기억하면 편하다.\n\n"
            "**또 다른 오해**: 적분이 항상 복잡한 계산을 필요로 한다는 생각. "
            "상수 전류의 경우 적분 = 면적 = 직사각형 넓이 = $I \\times \\Delta t$로 바로 계산 가능.\n\n"
            "**연결**: L3 p.19의 $I_C = C\\, dV/dt$를 시간에 대해 적분하면 $\\Delta V = (1/C)\\int I_C\\, dt$. "
            "이것이 뉴런이 '입력을 적분(integrate)한다'는 LIF 모델 명칭(integrate-and-fire)의 유래이다 (L7 p.9)."
        ),
        "source_citation": {"kind": "slide", "lecture": "L3", "page": 19,
                             "note": "I_C = C dV/dt; 역방향 적분이 L7 p.9 LIF 'integrate' 개념 근거"},
        "priority_score": 0.93,
        "info_density": 0.90,
    },

    # ─── DE 6: dimensional_analysis ───────────────────────────────────────────
    {
        "topic": "de_em_basics",
        "card_type": "application",
        "difficulty": 2,
        "bloom": "Apply",
        "mastery_target": "dimensional_analysis",
        "prompt_md": (
            "**Setup.** 차원 분석(dimensional analysis)은 수식 오류를 잡는 가장 빠른 도구이다. "
            "슬라이드 L3 p.23은 $\\tau_m = R_m C_m$이 시간 단위를 갖는다고 명시한다.\n\n"
            "(a) **$\\tau_m = R_m C_m$ 차원 확인**: "
            "$R_m$의 단위를 $\\Omega \\cdot \\mathrm{cm}^2$ (specific membrane resistance), "
            "$C_m$의 단위를 $\\mathrm{F/cm}^2$ (specific membrane capacitance)라 할 때, "
            "곱 $R_m \\times C_m$의 단위가 초(second)임을 단계별로 확인하시오. "
            "($1\\ \\Omega = 1\\ \\mathrm{V/A}$, $1\\ \\mathrm{F} = 1\\ \\mathrm{C/V}$, $1\\ \\mathrm{A} = 1\\ \\mathrm{C/s}$ 이용)\n"
            "(b) **$I_C = C_m \\, dV/dt$ 차원 확인**: "
            "$[C_m] = \\mathrm{nF}$, $[dV/dt] = \\mathrm{mV/ms}$라 할 때 "
            "$[I_C]$의 단위를 계산하고 전류 단위(nA)와 일치하는지 확인하시오.\n"
            "(c) **실수 탐지 문제**: 한 학생이 $\\tau_m = R_m / C_m$으로 적었다. "
            "차원 분석으로 이것이 틀렸음을 보이시오."
        ),
        "answer_md": (
            "(a) **$\\tau_m = R_m C_m$ 차원 확인**\n\n"
            "$$[R_m] = \\Omega\\cdot\\mathrm{cm}^2, \\quad [C_m] = \\frac{\\mathrm{F}}{\\mathrm{cm}^2}$$\n\n"
            "$$[R_m C_m] = \\Omega\\cdot\\mathrm{cm}^2 \\times \\frac{\\mathrm{F}}{\\mathrm{cm}^2} = \\Omega\\cdot\\mathrm{F}$$\n\n"
            "단위 분해:\n"
            "$$\\Omega\\cdot\\mathrm{F} = \\frac{\\mathrm{V}}{\\mathrm{A}} \\times \\frac{\\mathrm{C}}{\\mathrm{V}} = \\frac{\\mathrm{C}}{\\mathrm{A}} = \\frac{\\mathrm{C}}{\\mathrm{C/s}} = \\mathrm{s}$$\n\n"
            "면적 단위 cm² 가 분자·분모에서 상쇄되므로 specific 단위(per area)를 써도 $\\tau_m$은 "
            "면적 독립적 (슬라이드 L3 p.23 명시) ✓\n\n"
            "(b) **$I_C = C_m \\, dV/dt$ 차원 확인**\n\n"
            "$$[C_m \\cdot dV/dt] = \\mathrm{nF} \\times \\frac{\\mathrm{mV}}{\\mathrm{ms}}$$\n\n"
            "$$= 10^{-9}\\,\\mathrm{F} \\times \\frac{10^{-3}\\,\\mathrm{V}}{10^{-3}\\,\\mathrm{s}} = 10^{-9}\\,\\mathrm{F}\\cdot\\mathrm{V/s}$$\n\n"
            "$$= 10^{-9}\\,\\mathrm{C/s} \\times \\mathrm{V/(F\\cdot V\\cdot s^{-1}\\cdot s)} = 10^{-9}\\,\\mathrm{A} = 1\\,\\mathrm{nA}$$\n\n"
            "단순화: $[F \\times V/s] = [C/V \\times V/s] = [C/s] = [A]$이므로 "
            "$[\\mathrm{nF} \\times \\mathrm{mV/ms}] = [\\mathrm{nA}]$ ✓\n\n"
            "(c) **$\\tau_m = R_m / C_m$ 오류 탐지**\n\n"
            "$$\\left[\\frac{R_m}{C_m}\\right] = \\frac{\\Omega\\cdot\\mathrm{cm}^2}{\\mathrm{F/cm}^2} = \\Omega\\cdot\\mathrm{cm}^4/\\mathrm{F}$$\n\n"
            "$$= \\frac{\\mathrm{V}}{\\mathrm{A}} \\times \\frac{\\mathrm{cm}^4 \\cdot \\mathrm{V}}{\\mathrm{C}} = \\frac{\\mathrm{V}^2 \\cdot \\mathrm{cm}^4}{\\mathrm{A}\\cdot\\mathrm{C}} \\neq \\mathrm{s}$$\n\n"
            "단위가 초(s)가 아니므로 틀렸다. 정확한 단위가 나오지 않으면 수식 자체가 잘못된 것."
        ),
        "rationale_md": (
            "**흔한 학생 오개념**: 차원 분석이 '옵션'이라고 생각하는 것. "
            "차원 분석은 **필수 검증 단계**이다. 슬라이드 L3 p.23의 'τ_m은 면적에 독립적'이라는 "
            "중요한 사실 자체가 차원 분석(specific 단위의 면적 상쇄)에서 나온다.\n\n"
            "**또 다른 오해**: nF × mV/ms = nA를 즉시 계산하기 어렵다고 생각하는 것. "
            "핵심 기억법: $\\mathrm{F} = \\mathrm{C/V}$이므로 $\\mathrm{F} \\times \\mathrm{V} = \\mathrm{C}$, "
            "그리고 $\\mathrm{C/s} = \\mathrm{A}$. 이 두 관계만 알면 전기 차원 변환이 모두 가능하다.\n\n"
            "**연결**: L5 p.29 HH 막 전류 방정식의 단위 확인, L6 p.8 케이블 방정식에서 "
            "$\\lambda = \\sqrt{R_m/R_i}$ (공간 상수, 단위 cm) 차원 확인에 동일한 기법을 사용한다."
        ),
        "source_citation": {"kind": "slide", "lecture": "L3", "page": 23,
                             "note": "τ_m = R_m C_m 차원 분석; 슬라이드 L3 p.23 명시"},
        "priority_score": 0.94,
        "info_density": 0.91,
    },

    # ─── EM 1: charge_intuition ───────────────────────────────────────────────
    {
        "topic": "de_em_basics",
        "card_type": "recall",
        "difficulty": 1,
        "bloom": "Understand",
        "mastery_target": "charge_intuition",
        "prompt_md": (
            "**Setup.** 슬라이드 L3 p.12는 뉴런 세포질(cytoplasm)에 다량의 이온이 존재하며, "
            "이 이온들이 전하(charge)를 운반한다고 서술한다. "
            "L3 p.27–29의 Nernst 방정식, L3 p.30의 GHK 방정식이 모두 이온 종과 전하에 기반한다.\n\n"
            "(a) 전하(electric charge, $Q$)의 SI 단위는 무엇이며, 기본 전하(elementary charge) $e$의 값을 적으시오. "
            "신경과학에서 자주 쓰이는 스케일(pC, nC)도 명시하라.\n"
            "(b) 주요 이온의 가수(valency, $z$)를 표로 정리하시오: Na⁺, K⁺, Cl⁻, Ca²⁺. "
            "가수가 전하량 및 Nernst 방정식에서 어떤 역할을 하는가?\n"
            "(c) **수치 감각**: 세포막의 전형적 정전용량 $C_m = 100\\ \\mathrm{pF}$이고 "
            "막전위 $V_m = -65\\ \\mathrm{mV}$라면, 막 양쪽에 분리된 총 전하 $Q = C_m V_m$을 계산하고, "
            "이것이 몇 개의 단가 이온(univalent ion)에 해당하는지 구하시오."
        ),
        "answer_md": (
            "(a) **전하 단위와 기본 전하**\n\n"
            "- SI 단위: 쿨롱(Coulomb, C)\n"
            "- 기본 전하: $e \\approx 1.602 \\times 10^{-19}\\ \\mathrm{C}$ (양성자 또는 전자 1개의 전하량)\n"
            "- 신경과학 스케일: $1\\ \\mathrm{pC} = 10^{-12}\\ \\mathrm{C}$, $1\\ \\mathrm{nC} = 10^{-9}\\ \\mathrm{C}$\n"
            "- 단일 이온 채널 전류 ~1 pA가 1 ms 동안 흐르면 $Q \\approx 1\\ \\mathrm{fC} = 10^{-15}\\ \\mathrm{C}$\n\n"
            "(b) **주요 이온 가수표**\n\n"
            "| 이온 | 가수 $z$ | 전하 | Nernst 분모 $zF$ |\n"
            "|---|---|---|---|\n"
            "| Na⁺ | +1 | $+e$ | $+F$ |\n"
            "| K⁺  | +1 | $+e$ | $+F$ |\n"
            "| Cl⁻ | −1 | $-e$ | $-F$ |\n"
            "| Ca²⁺| +2 | $+2e$ | $+2F$ |\n\n"
            "Nernst 방정식 $E = (RT/zF)\\ln([out]/[in])$에서 $z$는:\n"
            "① 가수가 클수록 전기력이 커져 같은 농도 기울기에서 평형 전위가 **절반** ($z=2$).\n"
            "② 부호가 반전되면 ($z<0$, Cl⁻) 분모가 음수 → Nernst 전위의 부호가 반전.\n\n"
            "(c) **막의 총 전하 계산**\n\n"
            "$$Q = C_m \\times V_m = 100\\ \\mathrm{pF} \\times 65\\ \\mathrm{mV} = 100\\times10^{-12}\\ \\mathrm{F} \\times 65\\times10^{-3}\\ \\mathrm{V}$$\n"
            "$$= 6.5\\times10^{-12}\\ \\mathrm{C} = 6.5\\ \\mathrm{pC}$$\n\n"
            "단가 이온 수:\n"
            "$$N = \\frac{Q}{e} = \\frac{6.5\\times10^{-12}}{1.6\\times10^{-19}} \\approx 4\\times10^7 \\text{ 개}$$\n\n"
            "해석: 약 4천만 개의 이온만 막 양쪽에 불균형하게 분포해도 -65 mV 막전위가 형성된다 — "
            "뉴런 전체의 이온 수(~$10^{10}$개/μm³)에 비하면 극히 소수(< 0.01%)."
        ),
        "rationale_md": (
            "**흔한 학생 오개념**: 막전위를 유지하려면 세포 내외의 이온 농도 분포가 크게 달라야 한다고 생각하는 것. "
            "실제로는 매우 소수의 이온(전체의 < 0.01%)만 막 근처에 불균형하게 분포하면 충분하다. "
            "이것이 '활동 전위가 세포 전체의 이온 농도를 크게 바꾸지 않는다'는 사실의 근거이다.\n\n"
            "**또 다른 오해**: Ca²⁺의 $z=+2$가 단순히 Na⁺보다 두 배 강하다는 것. "
            "Nernst 방정식에서 $z$는 분모에 있어 **절반**의 평형 전위 민감도를 준다. "
            "동일한 농도 기울기에서 Ca²⁺의 $E_{Ca}$는 K⁺ $E_K$의 절반 크기.\n\n"
            "**연결**: L3 p.17–19 정전용량 $C_m$, L3 p.27–29 Nernst 방정식의 $z$ 역할, "
            "L5 p.13–14 Ca²⁺ 채널 (슬라이드에서 'Ca later'로 언급)."
        ),
        "source_citation": {"kind": "slide", "lecture": "L3", "page": 12,
                             "note": "이온과 전하 첫 언급; Nernst에서 z 사용은 L3 p.27-29"},
        "priority_score": 0.92,
        "info_density": 0.88,
    },

    # ─── EM 2: current_definition ────────────────────────────────────────────
    {
        "topic": "de_em_basics",
        "card_type": "recall",
        "difficulty": 1,
        "bloom": "Understand",
        "mastery_target": "current_definition",
        "prompt_md": (
            "**Setup.** 전류(electric current)의 정의가 슬라이드 L3 p.19에서 $I_C = C\\,dV/dt$, "
            "L3 p.32–33에서 $I_X = g_X(V-E_X)$로 처음 사용된다. "
            "두 식 모두 전류의 기본 정의 $I = dQ/dt$에서 출발한다.\n\n"
            "(a) $I = dQ/dt$의 물리적 의미를 서술하고, SI 단위가 암페어(A)임을 유도하시오. "
            "신경과학에서 자주 쓰이는 nA, pA 스케일과 대표적 맥락을 예시하라.\n"
            "(b) **부호 규약**: 슬라이드 L3 p.32는 '양전하가 세포 밖으로 나가면 외향 전류(outward)로 양수(+)'라고 정의한다. "
            "이 규약으로 다음 상황의 전류 부호를 판단하시오: "
            "(i) K⁺가 세포 밖으로 이동, (ii) Na⁺가 세포 안으로 이동, (iii) Cl⁻가 세포 밖으로 이동.\n"
            "(c) 전류 $I = 2\\ \\mathrm{nA}$가 $t = 5\\ \\mathrm{ms}$ 동안 흘렀을 때 "
            "이동한 총 전하를 계산하고, 이것이 단가 이온 몇 개에 해당하는지 구하시오."
        ),
        "answer_md": (
            "(a) **전류 정의 및 단위**\n\n"
            "$I = dQ/dt$: 단위 시간당 특정 단면을 통과하는 전하의 양 = '전하 흐름 속도'.\n\n"
            "$$[I] = \\frac{[Q]}{[t]} = \\frac{\\mathrm{C}}{\\mathrm{s}} = \\mathrm{A}$$\n\n"
            "신경과학 스케일:\n"
            "- $\\mathrm{nA} = 10^{-9}\\ \\mathrm{A}$: 전극(electrode)으로 주입하는 전류 (~1–10 nA)\n"
            "- $\\mathrm{pA} = 10^{-12}\\ \\mathrm{A}$: 단일 이온 채널 전류 (~1–100 pA)\n\n"
            "(b) **부호 규약 적용**\n\n"
            "| 상황 | 방향 | 부호 |\n"
            "|---|---|---|\n"
            "| K⁺ (양이온) → 세포 밖 | 양전하 외향 | **+** (외향, outward) |\n"
            "| Na⁺ (양이온) → 세포 안 | 양전하 내향 | **-** (내향, inward) |\n"
            "| Cl⁻ (음이온) → 세포 밖 | 음전하 외향 = 양전하 내향 | **-** (내향으로 간주) |\n\n"
            "Cl⁻가 밖으로 나가는 것 = 양전하가 안으로 들어오는 것과 동등 → 내향 전류 = 음수.\n\n"
            "(c) **총 전하 계산**\n\n"
            "$$Q = I \\cdot \\Delta t = 2\\ \\mathrm{nA} \\times 5\\ \\mathrm{ms} = 10\\ \\mathrm{nA\\cdot ms} = 10\\ \\mathrm{pC}$$\n\n"
            "이온 수:\n"
            "$$N = \\frac{Q}{e} = \\frac{10\\times10^{-12}\\ \\mathrm{C}}{1.6\\times10^{-19}\\ \\mathrm{C}} \\approx 6.25\\times10^7 \\approx 6.3\\times10^7 \\text{ 개}$$"
        ),
        "rationale_md": (
            "**흔한 학생 오개념**: 음이온이 밖으로 나가면 '+전류'라고 생각하는 것. "
            "전류의 부호 규약은 **양전하의 방향** 기준이다. "
            "음이온의 이동은 반대 방향의 양전하 흐름과 동등하므로 부호가 반전된다.\n\n"
            "**또 다른 오해**: nA와 pA의 규모를 직관적으로 느끼지 못하는 것. "
            "기억법: 단일 이온 채널 ≈ 1–100 pA, 뉴런 전체 막전류 ≈ 수 nA, "
            "전극 주입 전류 ≈ 0.1–10 nA. 100개의 열린 채널이 1 nA 정도를 만든다.\n\n"
            "**연결**: 슬라이드 L3 p.32–33의 막 전류 정의($I_m = \\sum I_X$), "
            "L5 p.29의 HH 막 전류 방정식이 모두 이 부호 규약을 따른다. "
            "내향 전류(-) = 탈분극(depolarization) 유발; 외향 전류(+) = 재분극(repolarization) 유발."
        ),
        "source_citation": {"kind": "slide", "lecture": "L3", "page": 19,
                             "note": "I_C = C dV/dt에서 전류 첫 사용; 부호 규약은 L3 p.32"},
        "priority_score": 0.93,
        "info_density": 0.89,
    },

    # ─── EM 3: voltage_definition ────────────────────────────────────────────
    {
        "topic": "de_em_basics",
        "card_type": "concept",
        "difficulty": 1,
        "bloom": "Understand",
        "mastery_target": "voltage_definition",
        "prompt_md": (
            "**Setup.** 슬라이드 L3 p.15는 막전위(membrane potential)를 "
            "$V_m(t) = V_{\\text{interior}}(t) - V_{\\text{exterior}}(t)$로 정의하고, "
            "p.16은 '안정 상태는 동적 평형(dynamical equilibrium)'이라 서술한다.\n\n"
            "(a) 전압(voltage, 전위차)의 물리적 정의: '단위 전하당 일(work per unit charge)'. "
            "이것이 왜 '전위(potential)'가 아닌 '전위**차**(potential **difference**)'인지 설명하시오. "
            "$(1\\ \\mathrm{V} = 1\\ \\mathrm{J/C}$ 관계 사용)\n"
            "(b) 슬라이드 L3 p.15의 정의에서: "
            "(i) 기준 전위(reference potential)를 세포 외부($V_{\\text{exterior}} = 0$)로 설정하는 이유는 무엇인가? "
            "(ii) 안정 막전위가 -65 mV가 아닌 +65 mV가 아닌 이유를 이온 농도로 설명하시오.\n"
            "(c) 두 관점을 대조하라: (i) 전압을 '에너지 저장'으로 보는 관점 vs "
            "(ii) '이온 이동의 구동력(driving force)'으로 보는 관점. "
            "L3 p.31의 구동력 $(V_m - E_K)$ 개념은 어느 관점에서 더 자연스러운가?"
        ),
        "answer_md": (
            "(a) **전압 = 단위 전하당 일 = 전위차**\n\n"
            "전위(potential) $V$는 기준점으로부터 단위 전하를 이동시키는 데 필요한 일:\n"
            "$$V = \\frac{W}{Q} \\quad [\\mathrm{V}] = \\frac{[\\mathrm{J}]}{[\\mathrm{C}]}$$\n\n"
            "왜 '차'인가: 절대 에너지는 기준점(reference) 선택에 따라 달라지므로 물리적으로 의미가 없다. "
            "두 점 사이의 **차이**만이 이온의 이동 방향과 크기를 결정한다. "
            "막전위 $V_m = V_{in} - V_{out}$은 내부와 외부 사이의 전위차.\n\n"
            "(b) **기준 전위 선택과 음의 막전위**\n\n"
            "(i) 기준을 외부 ($V_{ext} = 0$)로 설정: 실험적 편의 — 전극을 세포 외부 용액에 꽂아 "
            "기준(ground)으로 삼고 세포 내부를 측정. 생물학적 의미: 세포 외부가 '정상' 환경.\n\n"
            "(ii) 안정 막전위가 음수인 이유: K⁺가 주요 투과 이온이고, "
            "$[K^+]_{in} = 150\\ \\mathrm{mM} \\gg [K^+]_{out} = 5.5\\ \\mathrm{mM}$. "
            "K⁺가 농도 기울기를 따라 밖으로 나가면 내부에 음전하가 남아 내부가 음(−)이 된다. "
            "$E_K \\approx -83\\ \\mathrm{mV}$ (슬라이드 L3 p.29). 안정 막전위 $V_m \\approx -65\\ \\mathrm{mV}$는 "
            "여러 이온의 GHK 가중 평균.\n\n"
            "(c) **두 관점 비교**\n\n"
            "| 관점 | 서술 | 용도 |\n"
            "|---|---|---|\n"
            "| 에너지 저장 | 막 양쪽 전하 불균형이 에너지를 저장 | 커패시터 에너지 $E = QV/2$, 에너지 대사 분석 |\n"
            "| 구동력 | 이온이 전압 기울기를 따라 이동 | 이온 전류 계산: $I = g(V - E_{ion})$ |\n\n"
            "슬라이드 L3 p.31의 구동력 $(V_m - E_K)$은 **구동력 관점**: "
            "$V_m$이 K⁺ 평형 전위 $E_K$로부터 얼마나 떨어져 있는가 = K⁺가 얼마나 강하게 구동되는가."
        ),
        "rationale_md": (
            "**흔한 학생 오개념**: 음의 막전위(-65 mV)를 '에너지가 낮다'고만 해석하는 것. "
            "이온 이동 관점에서 음의 내부 전위는 Na⁺를 강하게 **끌어당기고**(내향 구동력), "
            "K⁺를 **밀어내는**(외향 구동력) 전기력을 만든다. 부호가 모든 이온 동역학을 결정한다.\n\n"
            "**또 다른 오해**: 막전위가 세포 내부의 '전압'이라고 생각하는 것. "
            "막전위는 항상 **차이**이며, 외부를 기준(0)으로 잡았을 때의 내부 전위이다.\n\n"
            "**연결**: 슬라이드 L3 p.31–33의 구동력 $(V - E_{ion})$이 직접 이온 전류를 결정 → "
            "L5 p.29 HH 방정식에서 $\\bar{g}_{Na} m^3 h (V - E_{Na})$로 이어진다. "
            "활동 전위 상승 = $V_m$이 $E_{Na}$ 방향으로 급격히 이동하는 과정이다."
        ),
        "source_citation": {"kind": "slide", "lecture": "L3", "page": 15,
                             "note": "막전위 정의 V_m = V_in - V_out; 구동력은 L3 p.31"},
        "priority_score": 0.94,
        "info_density": 0.90,
    },

    # ─── EM 4: conductors_insulators_membrane ────────────────────────────────
    {
        "topic": "de_em_basics",
        "card_type": "concept",
        "difficulty": 2,
        "bloom": "Analyze",
        "mastery_target": "conductors_insulators_membrane",
        "prompt_md": (
            "**Setup.** 슬라이드 L3 p.13은 '세포막은 lipid bilayer — 3~4 nm 두께, 대부분의 이하전 분자에 불투과성'이라 서술하고, "
            "p.17은 이 구조를 커패시터로 모델링한다.\n\n"
            "(a) 다음 세 재료를 도체(conductor), 절연체(insulator), 또는 '제어된 게이트(controlled gate)'로 분류하시오: "
            "(i) 세포질(cytoplasm), (ii) 세포 외액(extracellular fluid), (iii) lipid bilayer의 소수성(hydrophobic) 핵, "
            "(iv) 이온 채널(ion channel) 단백질. 각 분류의 근거를 서술하라.\n"
            "(b) Lipid bilayer가 커패시터(capacitor)로 모델링되는 이유를 재료 분류 관점에서 설명하시오: "
            "'두 도체 + 사이의 절연체' 구조가 어떻게 충족되는가?\n"
            "(c) **이온 채널의 역할**: 이온 채널이 없으면 막전위가 변할 수 없다. "
            "이온 채널을 '가변 저항(variable resistor)'으로 모델링할 때, "
            "채널 열림 정도($P_{open}$)와 membrane conductance($g_m$)의 관계를 서술하시오."
        ),
        "answer_md": (
            "(a) **재료 분류**\n\n"
            "| 재료 | 분류 | 근거 |\n"
            "|---|---|---|\n"
            "| 세포질 (cytoplasm) | **도체** | 자유 이온(K⁺, Na⁺, Cl⁻, 단백질 음이온 등)이 풍부 → 전하 이동 가능 |\n"
            "| 세포 외액 | **도체** | 자유 이온(Na⁺, Cl⁻ 등) 풍부 → 전하 이동 가능 |\n"
            "| Lipid bilayer 소수성 핵 | **절연체** | 탄화수소(hydrocarbon) 사슬 — 자유 전하 없음, 이온 통과 극히 어려움 |\n"
            "| 이온 채널 단백질 | **제어된 게이트** | 막 전압, 리간드, 기계적 자극에 의해 열림/닫힘 조절됨 — 선택적 이온 통과 허용 |\n\n"
            "(b) **Bilayer = 커패시터 구조**\n\n"
            "커패시터의 기본 구조: 두 도체 + 사이의 절연체.\n"
            "- **도체 1**: 세포 내부(cytoplasm) — 이온이 자유롭게 이동\n"
            "- **절연체**: Lipid bilayer 소수성 핵 (3–4 nm) — 이온 차단\n"
            "- **도체 2**: 세포 외부(extracellular fluid) — 이온이 자유롭게 이동\n\n"
            "이 구조가 두 도체 사이에 전하 불균형(전위차)을 '저장'하게 해준다 → 커패시터 정의 $Q = CV_m$.\n\n"
            "(c) **이온 채널 = 가변 저항**\n\n"
            "단일 채널 conductance $\\gamma$가 있을 때, 채널이 $N$개 있고 $P_{open}$이 열림 확률:\n"
            "$$g_m = N \\cdot P_{open} \\cdot \\gamma$$\n\n"
            "채널이 더 많이 열리면 ($P_{open}$ 증가) → $g_m$ 증가 → 저항 $R_m = 1/g_m$ 감소 → "
            "같은 구동력에서 더 많은 이온 전류.\n\n"
            "HH 모델에서 $g_K = \\bar{g}_K n^4$, $g_{Na} = \\bar{g}_{Na} m^3 h$는 "
            "정확히 이 $P_{open} \\times \\bar{g}$ 구조이다 (슬라이드 L5 p.14–19)."
        ),
        "rationale_md": (
            "**흔한 학생 오개념**: 세포막을 단순한 장벽(barrier)으로만 이해하는 것. "
            "세포막은 '도체-절연체-도체' 샌드위치 구조로, 이것이 커패시터 기능을 결정한다. "
            "이온 채널은 이 '절연체'를 통한 제어된 통로를 제공한다.\n\n"
            "**또 다른 오해**: 이온 채널이 단순히 '구멍'이라고 생각하는 것. "
            "이온 채널은 선택성(selectivity)과 게이팅(gating) 기능을 갖는 정교한 단백질이다 "
            "(슬라이드 L3 p.26, L5 p.12 참조).\n\n"
            "**연결**: 슬라이드 L3 p.17–18의 $C_m \\approx 1\\ \\mu\\mathrm{F/cm}^2$는 "
            "bilayer 두께 $d \\approx 3\\ \\mathrm{nm}$와 $\\varepsilon \\approx 2.5\\varepsilon_0$에서 "
            "$C = \\varepsilon/d$로 계산된다 — 재료 특성이 정전용량을 결정한다는 구체적 예시."
        ),
        "source_citation": {"kind": "slide", "lecture": "L3", "page": 13,
                             "note": "lipid bilayer = insulator, 커패시터 모델 도입; L3 p.17 커패시턴스"},
        "priority_score": 0.95,
        "info_density": 0.92,
    },

    # ─── EM 5: kirchhoff_current_law ─────────────────────────────────────────
    {
        "topic": "de_em_basics",
        "card_type": "application",
        "difficulty": 2,
        "bloom": "Apply",
        "mastery_target": "kirchhoff_current_law",
        "prompt_md": (
            "**Setup.** 슬라이드 L3 p.19–20의 막 방정식 $C_m dV/dt = I_{inj} - (V-E_L)/R_m$은 "
            "**키르히호프 전류 법칙(Kirchhoff's Current Law, KCL)**에서 직접 유도된다: "
            "노드(node)로 들어오는 전류의 합 = 노드에서 나가는 전류의 합 (전하 보존).\n\n"
            + SVG_KCL_NODE + "\n\n"
            "(a) 위 그림의 단일-구획 뉴런에서 KCL을 적용하시오: "
            "$I_{inj}$가 들어오고 $I_C$(커패시터)와 $I_R$(저항/이온 채널)이 나간다. "
            "KCL 방정식을 쓰고, $I_C = C_m dV/dt$와 $I_R = (V-E_L)/R_m$을 대입하여 막 방정식을 유도하라.\n"
            "(b) HH 모델 (슬라이드 L5 p.4, p.29)에서 막 전류가 세 항으로 구성된다: "
            "K⁺, Na⁺, 누설(leak) 전류. 이것도 KCL인가? 어떤 형태로 쓰이는가?\n"
            "(c) 슬라이드 L6 p.13–14의 다중-구획 모델에서 각 구획이 이웃 구획에 전류를 주고받는다. "
            "단일 구획 $i$에 대한 KCL 방정식에 '인접 구획으로부터의 축 전류(axial current)'가 "
            "어떻게 추가되는지 정성적으로 설명하시오 (케이블 방정식의 $R_i$ 항 언급)."
        ),
        "answer_md": (
            "(a) **단일-구획 막 방정식 KCL 유도**\n\n"
            "KCL (전하 보존): 노드 $V$에서:\n"
            "$$I_{inj} = I_C + I_R$$\n"
            "$$I_{inj} = C_m \\frac{dV}{dt} + \\frac{V - E_L}{R_m}$$\n\n"
            "재정렬:\n"
            "$$C_m \\frac{dV}{dt} = -\\frac{V - E_L}{R_m} + I_{inj}$$\n\n"
            "$R_m$으로 곱하고 $\\tau_m = R_m C_m$ 정의:\n"
            "$$\\boxed{\\tau_m \\frac{dV}{dt} = -(V - E_L) + R_m I_{inj}}$$\n\n"
            "이것이 슬라이드 L3 p.20, L7 p.11의 막 방정식이다.\n\n"
            "(b) **HH 모델의 KCL 형태**\n\n"
            "슬라이드 L5 p.29:\n"
            "$$C_m \\frac{dV_m}{dt} = I_{inj} - i_K - i_{Na} - i_L$$\n"
            "$$= I_{inj} - \\bar{g}_K n^4(V-E_K) - \\bar{g}_{Na}m^3h(V-E_{Na}) - \\bar{g}_L(V-E_L)$$\n\n"
            "네, 이것도 KCL이다. 외부 주입 전류 $I_{inj}$가 들어오고, "
            "세 이온 채널을 통한 전류가 나간다 (또는 들어온다, 부호에 따라). "
            "커패시터 전류 $C_m dV_m/dt$는 나머지 전하를 처리한다.\n\n"
            "(c) **다중 구획에서의 KCL 확장**\n\n"
            "구획 $i$는 자신의 막 전류($I_C, I_R$) 외에 인접 구획 $i-1$과 $i+1$로부터 "
            "**축 전류(axial current)** $I_{ax}$를 받는다:\n"
            "$$I_{ax,i\\leftarrow i-1} = \\frac{V_{i-1} - V_i}{R_{ax}}$$\n"
            "여기서 $R_{ax}$는 구획 사이 세포질의 축 저항(axial resistance).\n\n"
            "KCL 확장:\n"
            "$$C_m \\frac{dV_i}{dt} = I_{ax,\\text{from }i-1} + I_{ax,\\text{from }i+1} - \\frac{V_i - E_L}{R_m} + I_{inj,i}$$\n\n"
            "$R_{ax}$가 케이블 방정식(L6 p.8)의 내부 저항 $R_i$에 해당하며, "
            "연속 극한($\\Delta x \\to 0$)에서 PDE의 $\\lambda^2 \\partial^2 V/\\partial x^2$ 항이 된다."
        ),
        "rationale_md": (
            "**흔한 학생 오개념**: 막 방정식이 '뉴런만의 특수 방정식'이라고 생각하는 것. "
            "실제로는 전기회로의 KCL을 직접 적용한 것이다. "
            "뉴런 특이성은 $E_L$이 0이 아닌 것과 능동 채널의 비선형 conductance뿐이다.\n\n"
            "**또 다른 오해**: KCL에서 '들어오는 전류'와 '나가는 전류'의 부호 관리 혼동. "
            "일관성 있는 규약 (L3 p.32: 외향 = 양수)을 선택하고 모든 전류를 같은 기준으로 표현해야 한다. "
            "HH 방정식에서 $dV/dt$의 우변이 $-g_K(V-E_K)$ 등으로 음수인 이유: "
            "외향 K⁺ 전류는 내부 전하를 감소시켜 $V$를 낮추므로 음의 기여.\n\n"
            "**연결**: L6 p.8 케이블 방정식은 KCL을 공간적으로 무한히 작은 구획에 적용한 것. "
            "L7 p.10의 LIF 유도도 KCL에서 시작 (슬라이드 p.10 명시)."
        ),
        "source_citation": {"kind": "slide", "lecture": "L3", "page": 19,
                             "note": "막 방정식 = KCL 적용; L5 p.29 HH KCL, L6 p.8 케이블 KCL"},
        "priority_score": 0.97,
        "info_density": 0.94,
    },

    # ─── EM 6: ohms_law_water ────────────────────────────────────────────────
    {
        "topic": "de_em_basics",
        "card_type": "concept",
        "difficulty": 1,
        "bloom": "Understand",
        "mastery_target": "ohms_law_water",
        "prompt_md": (
            "**Setup.** 슬라이드 L3 p.21–22는 막 저항(membrane resistance) $R_m$을 도입하고, "
            "L3 p.33은 이온 전류 $I_X = g_X(V_m - E_X)$를 옴의 법칙(Ohm's law)으로 표현한다.\n\n"
            + SVG_PIPE_FLOW + "\n\n"
            "(a) 위 물 흐름 비유에서 각 요소를 전기 회로와 대응시키시오: "
            "압력차 $\\Delta P = P_1 - P_2$ → ?, 흐름 속도 $F$ → ?, 파이프 좁기/저항 $R_{pipe}$ → ?\n"
            "(b) 옴의 법칙 $I = V/R$ (또는 $I = gV$, $g=1/R$)의 두 가지 관점을 서술하시오: "
            "(i) 저항 관점: 전압이 같으면 저항이 클수록 전류가 작다. "
            "(ii) 전도도 관점: '채널이 더 많이 열릴수록 전도도 증가 = 저항 감소 = 더 많은 전류'. "
            "신경과학에서 어느 관점이 더 자주 사용되는가?\n"
            "(c) '더 많은 채널이 열린다'는 것이 막 저항에 어떤 영향을 미치는가? "
            "활동 전위 중 Na⁺ 채널이 대량 개방될 때 막의 $R_{Na}$가 어떻게 변하는지, "
            "이것이 Na⁺ 전류에 어떤 영향을 미치는지 서술하시오."
        ),
        "answer_md": (
            "(a) **물-전기 비유 대응**\n\n"
            "| 물 흐름 | 전기 회로 |\n"
            "|---|---|\n"
            "| 압력차 $\\Delta P$ | 전압(전위차) $V = V_1 - V_2$ [V] |\n"
            "| 흐름 속도 $F$ [vol/s] | 전류 $I$ [C/s = A] |\n"
            "| 파이프 좁기/저항 $R_{pipe}$ | 전기 저항 $R$ [Ω] |\n\n"
            "옴의 법칙: $I = V/R$ ↔ $F = \\Delta P / R_{pipe}$.\n\n"
            "(b) **두 관점 비교**\n\n"
            "| 관점 | 수식 | 강조 |\n"
            "|---|---|---|\n"
            "| 저항 | $I = V/R$ | '얼마나 막는가?' |\n"
            "| 전도도 | $I = gV$, $g = 1/R$ | '얼마나 통하는가?' |\n\n"
            "신경과학에서 **전도도 관점**이 더 자주 사용된다. 이유:\n"
            "- 채널이 열리면 conductance가 더해짐 (병렬 저항 → 전도도 합산).\n"
            "- $g_K = \\bar{g}_K n^4$처럼 conductance가 직접 게이팅 변수로 표현.\n"
            "- 저항 $R = 1/g$는 채널이 조금만 열려도 매우 커져서 다루기 불편.\n\n"
            "(c) **활동 전위 중 Na⁺ 채널 대량 개방 시**\n\n"
            "Na⁺ 채널 대량 개방 → 병렬 Na⁺ conductance 합산 → $g_{Na}$ 급격히 증가 → $R_{Na} = 1/g_{Na}$ 급감.\n\n"
            "Na⁺ 전류:\n"
            "$$I_{Na} = g_{Na}(V_m - E_{Na}) = \\bar{g}_{Na} m^3 h (V_m - E_{Na})$$\n\n"
            "$g_{Na}$ 증가 + 구동력 $(V_m - E_{Na})$이 매우 음수(-123 mV at rest) → 강한 내향 Na⁺ 전류 → 탈분극 → 활동 전위 상승.\n\n"
            "슬라이드 L5 p.7–8의 빠른 양성 순환(fast positive cycle)이 바로 이 과정이다."
        ),
        "rationale_md": (
            "**흔한 학생 오개념**: 저항과 전도도를 단순히 '역수 관계'로만 기억하고, "
            "어느 상황에서 어느 표현을 쓸지 모르는 것. "
            "실용적 기준: 채널 수나 열림 확률에 대해 이야기할 때 → conductance; "
            "'막이 얼마나 저항하는가'를 말할 때 → resistance.\n\n"
            "**또 다른 오해**: 물 비유에서 '압력 = 전압'이 완벽한 비유라고 생각하는 것. "
            "중요한 차이: 이온 전류는 전압 **차이**가 아닌 평형 전위(Nernst)로부터의 편차 "
            "$(V - E_{ion})$에 비례한다 — 이것이 '수정된 옴의 법칙'이다.\n\n"
            "**연결**: L3 p.21–22의 membrane resistance $R_m$, L3 p.33의 이온 전류 $I_X = g_X(V-E_X)$, "
            "L5 p.14의 active conductance 개념이 모두 이 기반 위에 쌓인다."
        ),
        "source_citation": {"kind": "slide", "lecture": "L3", "page": 21,
                             "note": "막 저항 R_m 도입 L3 p.21-22; 이온 전류 g_X(V-E_X) L3 p.33"},
        "priority_score": 0.94,
        "info_density": 0.91,
    },
]


def insert_cards(items: list[dict]) -> list[int]:
    conn = acquire()
    try:
        with conn.cursor() as cur:
            ids = []
            for it in items:
                # Skip if same (topic, card_type, mastery_target) already exists
                cur.execute(
                    """
                    SELECT id FROM question_bank
                    WHERE topic = %s AND card_type = %s AND mastery_target = %s
                    LIMIT 1
                    """,
                    (it["topic"], it["card_type"], it.get("mastery_target")),
                )
                if cur.fetchone():
                    print(f"  skip dup: {it['topic']}/{it['card_type']}/{it.get('mastery_target')}")
                    continue

                cur.execute(
                    """
                    INSERT INTO question_bank
                      (topic, card_type, difficulty, bloom, prompt_md, answer_md,
                       rationale_md, source_citation, priority_score, info_density,
                       mastery_target, status)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,'active')
                    RETURNING id
                    """,
                    (
                        it["topic"], it["card_type"], it["difficulty"], it["bloom"],
                        it["prompt_md"], it["answer_md"], it["rationale_md"],
                        json.dumps(it["source_citation"], ensure_ascii=False),
                        it["priority_score"], it["info_density"],
                        it.get("mastery_target"),
                    ),
                )
                new_id = cur.fetchone()[0]
                ids.append(new_id)
                print(f"  inserted id={new_id}: {it['topic']}/{it['card_type']}/{it.get('mastery_target')}")

                # Also add to srs_cards for user_id=1
                cur.execute(
                    """
                    INSERT INTO srs_cards (user_id, bank_item_id, state)
                    VALUES (1, %s, 'New')
                    ON CONFLICT (user_id, bank_item_id) DO NOTHING
                    """,
                    (new_id,),
                )

        conn.commit()
        return ids
    finally:
        release(conn)


if __name__ == "__main__":
    ids = insert_cards(SEEDS)
    print(f"\nInserted {len(ids)} de_em_basics cards. IDs: {ids}")
    print("\nCard summary:")
    for it in SEEDS:
        print(f"  [{it['card_type']:>11s} / d={it['difficulty']}]  {it['mastery_target']}")
