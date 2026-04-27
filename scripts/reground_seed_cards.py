#!/usr/bin/env python3
"""
reground_seed_cards.py — Re-ground 11 hallucinated seed cards (IDs 4,6,8,9-15,17,18)
to actual slide content.

Each card keeps: topic, card_type, difficulty, bloom, mastery_target.
Replaces: prompt_md, answer_md, rationale_md, source_citation.

All citations are kind='slide' only.
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
# 11 REGROUND UPDATES
# ─────────────────────────────────────────────────────────────────────────────

UPDATES: list[dict] = [

    # ─── ID 4: HH proof ───────────────────────────────────────────────────────
    # Original: cited L5 p.25 "5-state Markov chain → n^4 derivation"
    # Fix: L5 p.17–19 actually covers n^k persistent conductance derivation
    # with the 4-subunit argument. Rewrite as a proof of P_open = n^k
    # from the kinetic scheme, showing the intermediate binomial step.
    {
        "id": 4,
        "prompt_md": (
            "**Setup.** 슬라이드 L5 p.17–19는 delayed-rectifier K⁺ 채널의 개방 확률(open probability)을 "
            "$P_{\\text{open}} = n^k$ 형태로 유도한다. 여기서 $n$은 단일 소단위(subunit)의 게이팅 변수이고 "
            "$k$는 소단위 수이다.\n\n"
            "(a) 슬라이드 p.17 모식도를 근거로, **독립적인 $k$개의 동일한 소단위**가 각각 독립적으로 open/closed "
            "전이를 할 때 채널 전체가 열려 있을 확률 $P_{\\text{open}}$을 유도하시오. 이항(binomial) 논리를 "
            "사용하고 중간 단계를 명시하라.\n"
            "(b) $k=4$ 일 때 $g_K = \\bar{g}_K n^4$ 식을 유도하고, $n$이 따르는 1차 ODE "
            "($dn/dt$ 식)를 슬라이드 p.20–21의 kinetic scheme에서 직접 도출하시오 "
            "(opening rate $\\alpha_n$, closing rate $\\beta_n$ 이용).\n"
            "(c) 슬라이드 p.19 주의: $k$는 실험 데이터에 맞춰 선택되는 **정수** 이며 "
            "물리적 소단위 수의 직접적 반영이 아닐 수 있다고 서술한다. "
            "이것이 모델의 어떤 '타당성 영역(regime of validity)'을 제한하는가?"
        ),
        "answer_md": (
            "(a) **독립 소단위 가정에서 $P_{\\text{open}} = n^k$ 유도**\n\n"
            "각 소단위 게이트가 독립적으로 열릴 확률을 $n$ ($0 \\leq n \\leq 1$)이라 하자. "
            "채널이 열리려면 $k$개 소단위 모두 열려야 하므로 (AND 조건):\n"
            "$$P_{\\text{open}} = P(\\text{gate 1 open}) \\times P(\\text{gate 2 open}) \\times \\cdots \\times P(\\text{gate } k \\text{ open}) = n^k$$\n"
            "이 논리는 독립 베르누이 시행의 곱이다. 소단위들이 협동(cooperative)하면 이 식이 성립하지 않는다.\n\n"
            "(b) **$k=4$에서 $g_K = \\bar{g}_K n^4$, 그리고 $dn/dt$ ODE**\n\n"
            "conductance는 최대 conductance × 열릴 확률:\n"
            "$$g_K = \\bar{g}_K \\cdot P_{\\text{open}} = \\bar{g}_K n^4$$\n\n"
            "슬라이드 p.20–21 kinetic scheme: 각 소단위는 닫힘(closed)에서 열림(open)으로 "
            "전압 의존 속도 $\\alpha_n(V)$로, 역방향으로 $\\beta_n(V)$로 전이:\n"
            "$$\\text{closed} \\underset{\\beta_n}{\\overset{\\alpha_n}{\\rightleftharpoons}} \\text{open}$$\n"
            "Master equation에서:\n"
            "$$\\frac{dn}{dt} = \\alpha_n(V)(1 - n) - \\beta_n(V)\\,n$$\n"
            "첫 항: closed($1-n$) → open 전이. 둘째 항: open($n$) → closed 전이.\n"
            "이는 L5 p.21 슬라이드의 수식과 동일하다.\n\n"
            "**안정 값(steady-state)**: $n_\\infty = \\alpha_n / (\\alpha_n + \\beta_n)$, "
            "**시간 상수**: $\\tau_n = 1 / (\\alpha_n + \\beta_n)$.\n\n"
            "(c) **타당성 영역 제한**\n\n"
            "$k$가 실험 데이터 피팅값이면: ① 소단위 수가 실제로 다른 채널에 그대로 이전(transfer) 불가; "
            "② 소단위 협동성(cooperativity)이 있을 때 독립 가정 위반 → $n^k$ 는 open probability의 "
            "현상론적(phenomenological) 기술일 뿐 분자 메커니즘(mechanistic) 모델이 아니다. "
            "따라서 이 모델은 **전체 채널의 매크로스코픽 conductance 재현**에는 유효하지만, "
            "단일 채널(single-channel) 통계나 협동 게이팅 예측에는 적용할 수 없다."
        ),
        "rationale_md": (
            "**흔한 학생 오개념**: $n^4$ 를 그냥 '$n$을 4승한다'고 암기하고 유도 논리를 모른다. "
            "핵심은 **독립 소단위 AND 조건** → 확률의 곱. 이 가정이 틀리면 실제 단일채널 데이터에서 "
            "burst 구조나 협동 게이팅이 보인다 (슬라이드 p.19 주석).\n\n"
            "**또 다른 오해**: $dn/dt$ 식에서 $(1-n)$ 항을 빠뜨리는 것 — 이 항이 없으면 "
            "$n$이 1을 넘어 비물리적이 된다. $(1-n)$은 closed 상태에 있는 소단위의 비율을 나타낸다.\n\n"
            "**연결**: L5 p.25–28에서 다루는 sodium 채널(transient conductance $m^3 h$)은 "
            "동일한 kinetic scheme 구조를 갖되 $m$(활성화)과 $h$(비활성화)가 **반대 전압 의존성**을 가진다는 "
            "차이가 있다. 두 변수가 동시에 커야($m^3 h$ 최대) 채널이 열린다."
        ),
        "source_citation": {"kind": "slide", "lecture": "L5", "page": 17,
                             "note": "n^k derivation spans L5 p.17–21"},
    },

    # ─── ID 6: Cable concept ──────────────────────────────────────────────────
    # Original: claimed Rall 3/2 law — NOT in slides
    # Fix: slides cover multi-compartment model and AP propagation (L6 p.13–14)
    # Rewrite as concept card on multi-compartment approach vs cable PDE,
    # contrasting two viewpoints (continuous PDE vs discrete compartments)
    {
        "id": 6,
        "prompt_md": (
            "**Setup.** 슬라이드 L6 p.13–14는 신경세포를 **다중 구획 모델(multi-compartment model)** 로 "
            "분할하는 접근법을 소개한다. p.8의 cable PDE와 비교하라.\n\n"
            "(a) Cable PDE(편미분 방정식) 접근과 다중 구획 모델 접근의 **핵심 가정 차이**를 "
            "서로 대조하여 서술하시오. (각 접근이 신경세포의 공간적 이질성을 어떻게 처리하는가?)\n"
            "(b) 슬라이드 p.14: '더 많은 구획 = 더 나은 근사(More compartments means better approximation)'. "
            "이 주장의 수렴(convergence) 조건은 무엇이며, 구획 수를 무한히 늘릴 때 어떤 극한에 수렴하는가?\n"
            "(c) 능동적 채널(active conductance)이 포함된 경우 PDE 해석 해(analytical solution)를 구하기 "
            "어려운 이유를 물리적으로 설명하고, 다중 구획 모델이 이 문제를 어떻게 우회하는지 설명하시오."
        ),
        "answer_md": (
            "(a) **케이블 PDE vs 다중 구획 모델의 핵심 가정 차이**\n\n"
            "| 항목 | Cable PDE | 다중 구획 모델 |\n"
            "|---|---|---|\n"
            "| 공간 처리 | 연속(continuous) — $V(x,t)$, $x$는 실수 | 이산(discrete) — $V_i(t)$, $i$는 구획 번호 |\n"
            "| 각 위치 가정 | 원통형 균질 케이블 | 각 구획 내 전위 균일(isopotential) |\n"
            "| 수식 유형 | 편미분 방정식 (PDE) | 연립 상미분 방정식 (ODE system) |\n"
            "| 실제 형태 | 이상화된 케이블에만 해석 가능 | 임의의 신경 형태(morphology)에 적용 |\n\n"
            "(b) **수렴 조건과 극한**\n\n"
            "각 구획의 길이 $\\Delta x$가 공간 상수 $\\lambda$에 비해 작아야 한다: $\\Delta x \\ll \\lambda$. "
            "구획 수 $N \\to \\infty$, $\\Delta x \\to 0$ 극한에서 다중 구획 모델은 "
            "cable PDE의 이산화 근사(finite-difference discretization)와 동일해진다 — "
            "즉, 수치해가 PDE의 연속 해(analytical solution)에 수렴한다.\n\n"
            "(c) **능동 채널이 있을 때 해석 해가 어려운 이유**\n\n"
            "Cable PDE에 HH 형태의 비선형(nonlinear) voltage-dependent conductance $g_K n^4, g_{Na} m^3 h$가 "
            "더해지면 PDE가 **비선형 PDE** 가 된다. 이런 방정식은 일반적으로 해석 해가 존재하지 않는다 "
            "(슬라이드 L6 p.13 명시). 다중 구획 모델은 각 구획을 작은 독립 ODE로 취급하여 "
            "수치 적분(Euler/Runge-Kutta)으로 풀기 때문에 비선형 항도 시간 진행에 따라 계산 가능하다. "
            "NEURON 같은 소프트웨어가 바로 이 전략을 사용한다."
        ),
        "rationale_md": (
            "**흔한 학생 오개념**: '구획 모델이 PDE보다 더 단순하다'고 생각하는 것. "
            "실제로는 다중 구획 모델이 더 복잡한 형태(morphology)를 표현할 수 있고, "
            "비선형 채널 동역학을 수치적으로 다룰 수 있다는 점에서 **더 범용적이고 현실적**이다. "
            "PDE는 수학적으로 우아하지만 단순화된 가정(균질 케이블, 수동 막)에서만 해석 해가 가능하다.\n\n"
            "**또 다른 오해**: 구획 수가 많을수록 항상 좋다. 실제로는 계산 비용이 기하급수적으로 증가하므로, "
            "$\\Delta x \\lesssim \\lambda/10$을 만족하는 최소 구획 수를 선택하는 것이 실용적이다.\n\n"
            "**연결**: L7 p.10–13의 leaky integrate-and-fire(LIF) 모델은 "
            "단일-구획 모델의 극단적 단순화 — 공간 구조 전체를 하나의 막 방정식으로 압축한 것이다."
        ),
        "source_citation": {"kind": "slide", "lecture": "L6", "page": 13,
                             "note": "multi-compartment approach L6 p.13–14"},
    },

    # ─── ID 8: Cable proof ────────────────────────────────────────────────────
    # Original: Green's function for cable PDE — not in slides
    # Fix: Slides show the exponential spatial decay solution (L6 p.10–11)
    # and the Gaussian time-dep solution (L6 p.12). Rewrite as proof of
    # steady-state exponential solution from the cable PDE.
    {
        "id": 8,
        "prompt_md": (
            "**Setup.** 슬라이드 L6 p.10는 반무한 케이블(semi-infinite cable)에서 $x=0$ 위치에 "
            "일정 전류 $I_{inj}$를 주입했을 때, 정상 상태(steady-state) 막전위가 "
            "$V_m(x) = V_0 \\, e^{-x/\\lambda}$ 형태로 공간적으로 감소함을 제시한다.\n\n"
            "(a) Cable PDE (슬라이드 L6 p.8):\n"
            "$$\\lambda^2 \\frac{\\partial^2 V_m}{\\partial x^2} - \\tau_m \\frac{\\partial V_m}{\\partial t} - V_m = -R_m I_{inj}(x,t)$$\n"
            "에서 $I_{inj} = $ constant (위치 $x>0$ 에서 0, $x=0$ 에서 고정)이고 $\\partial V_m / \\partial t = 0$ (정상 상태)이면 "
            "어떤 상미분방정식(ODE)이 되는지 도출하시오.\n"
            "(b) 위 ODE의 일반해를 구하고, 경계 조건 $V_m(\\infty) = 0$ (무한대에서 소멸)와 "
            "$V_m(0) = V_0$을 적용하여 $V_m(x) = V_0 e^{-x/\\lambda}$를 유도하시오. "
            "중간 특성 방정식(characteristic equation) 단계를 명시하라.\n"
            "(c) $\\lambda$의 물리적 의미(슬라이드 L6 p.11)를 서술하고, $\\lambda$가 커질수록 "
            "시냅스 입력의 공간적 통합(spatial summation)에 어떤 영향을 미치는지 설명하시오."
        ),
        "answer_md": (
            "(a) **정상 상태 Cable ODE 도출**\n\n"
            "정상 상태 ($\\partial V_m/\\partial t = 0$)이고 $x > 0$ 영역에서 $I_{inj} = 0$이면 "
            "Cable PDE는:\n"
            "$$\\lambda^2 \\frac{d^2 V_m}{dx^2} - V_m = 0$$\n"
            "이것은 2차 상미분 방정식 (ODE)이다.\n\n"
            "(b) **일반해 유도**\n\n"
            "특성 방정식: $\\lambda^2 r^2 - 1 = 0 \\implies r = \\pm \\frac{1}{\\lambda}$.\n\n"
            "따라서 일반해:\n"
            "$$V_m(x) = A e^{x/\\lambda} + B e^{-x/\\lambda}$$\n\n"
            "**경계 조건 적용**:\n"
            "- $V_m(\\infty) = 0$: $A e^{\\infty/\\lambda} \\to \\infty$ 이므로 $A = 0$.\n"
            "- $V_m(0) = V_0$: $B e^0 = B = V_0$.\n\n"
            "따라서:\n"
            "$$\\boxed{V_m(x) = V_0 \\, e^{-x/\\lambda}}$$\n\n"
            "이것이 슬라이드 L6 p.10–11에 나타난 지수적 공간 감쇠 해이다.\n\n"
            "(c) **$\\lambda$의 물리적 의미 (슬라이드 L6 p.11)**\n\n"
            "$\\lambda$는 **공간 상수(length constant, 또는 space constant)**: "
            "전위가 최대값의 $1/e \\approx 37\\%$로 감쇠하는 거리이다.\n\n"
            "단위 분석: $\\lambda = \\sqrt{R_m / R_i}$ (슬라이드 p.8) — $R_m$은 막 저항, $R_i$는 내부 저항.\n\n"
            "$\\lambda$가 클수록: 멀리서 온 시냅스 입력(distal synaptic input)이 소마(soma)에 더 적게 감쇠되어 도달하므로 "
            "**공간적 통합 범위가 넓어진다**. 반대로 $\\lambda$가 작으면 근위부(proximal) 입력만 효과적으로 통합된다 — "
            "이것이 수지상 돌기(dendrite)의 입력 위치 가중치 차이를 결정하는 핵심 변수이다."
        ),
        "rationale_md": (
            "**흔한 학생 오개념**: 일반해에서 $e^{+x/\\lambda}$ 항을 놓치거나 경계 조건 적용 전에 "
            "바로 $e^{-x/\\lambda}$라고 쓰는 것. 이 항은 경계 조건($V_m(\\infty) = 0$)으로 "
            "소거되어야 하며, 이 과정이 '반무한 케이블'의 핵심 가정이다. 양쪽이 유한한 케이블이라면 "
            "두 항 모두 살아남고 쌍곡함수(cosh, sinh) 형태의 해가 나온다.\n\n"
            "**또 다른 오해**: $\\lambda$를 '신호가 전파되는 최대 거리'로 이해하는 것. "
            "실제로는 $1/e$ 감쇠 거리이고, 무한히 먼 곳에서도 신호는 지수적으로 작아질 뿐 "
            "완전히 0이 되지는 않는다.\n\n"
            "**연결**: 시간 의존 해(L6 p.12)는 전류 펄스(pulse) 입력에 대해 가우시안(Gaussian) 형태를 가지며, "
            "이는 확산 방정식(diffusion equation)과 동일한 수학 구조에서 비롯된다."
        ),
        "source_citation": {"kind": "slide", "lecture": "L6", "page": 10,
                             "note": "steady-state exponential solution L6 p.10–11"},
    },

    # ─── ID 9: Nernst recall ──────────────────────────────────────────────────
    # Original: cited L3 p.18 (membrane R/C slides) but content is Nernst/GHK
    # Fix: Nernst equation IS in slides at L3 p.27-29. Re-cite correctly.
    {
        "id": 9,
        "prompt_md": (
            "**Setup.** 슬라이드 L3 p.27–29는 이온이 선택적 이온 채널을 통해 확산(diffusion)할 때 "
            "농도 기울기(concentration gradient)와 전기 기울기(electrical gradient) 사이의 "
            "평형을 분석한다.\n\n"
            "(a) K⁺ 이온에 대한 **Nernst 방정식(Nernst equation)**을 쓰고, 각 기호 "
            "($R, T, F, z$)의 물리적 의미와 SI 단위를 명시하시오.\n"
            "(b) 슬라이드 p.29의 수치 대입: $[K^+]_{out} = 5.5\\ \\mathrm{mM}$, "
            "$[K^+]_{in} = 150\\ \\mathrm{mM}$, 체온 $T = 310\\ \\mathrm{K}$일 때 "
            "$E_K$를 계산하고 슬라이드가 제시한 값(-83 mV)과 비교하시오.\n"
            "(c) **타당성 영역 힌트**: Nernst 방정식이 성립하려면 어떤 가정이 필요한가? "
            "(막이 다수의 이온 종(species)에 대해 투과적일 때 어떤 방정식으로 대체되는가?)"
        ),
        "answer_md": (
            "(a) **Nernst 방정식**:\n"
            "$$E_{ion} = \\frac{RT}{zF} \\ln \\frac{[\\text{ion}]_{out}}{[\\text{ion}]_{in}}$$\n\n"
            "기호 설명:\n"
            "- $R = 8.314\\ \\mathrm{J\\,mol^{-1}\\,K^{-1}}$: 기체 상수\n"
            "- $T$ [K]: 절대 온도\n"
            "- $z$: 이온 가수(valency) — K⁺는 $z=+1$, Ca²⁺는 $z=+2$, Cl⁻는 $z=-1$\n"
            "- $F = 96485\\ \\mathrm{C\\,mol^{-1}}$: Faraday 상수\n\n"
            "체온 근사: $RT/F \\approx 26.7\\ \\mathrm{mV}$, 따라서 $RT/(zF) \\approx 26.7\\ \\mathrm{mV}$ (z=1).\n\n"
            "(b) **수치 계산**:\n"
            "$$E_K = \\frac{RT}{F} \\ln \\frac{5.5}{150} = 26.7 \\times \\ln(0.0367) \\approx 26.7 \\times (-3.31) \\approx -88\\ \\mathrm{mV}$$\n\n"
            "슬라이드 p.29는 log₁₀ 스케일로 $E_K = 58 \\log_{10}(5.5/150) \\approx -83\\ \\mathrm{mV}$를 제시. "
            "차이는 $\\log_e$ vs $\\log_{10}$ 변환: $58 \\times \\log_{10} = 26.7 \\times \\ln$ (모두 동등).\n\n"
            "(c) **Nernst 방정식의 타당성 영역 (regime of validity)**:\n\n"
            "- 막이 **단 하나의 이온 종에 대해서만 선택적 투과**일 때 정확히 성립.\n"
            "- 여러 이온 종이 동시에 투과하면 농도 구배와 투과도를 모두 고려한 **Goldman-Hodgkin-Katz (GHK) 방정식** (슬라이드 p.30)으로 대체:\n"
            "$$E_m = \\frac{RT}{F} \\ln \\frac{p_K[K^+]_{out} + p_{Na}[Na^+]_{out} + p_{Cl}[Cl^-]_{in}}{p_K[K^+]_{in} + p_{Na}[Na^+]_{in} + p_{Cl}[Cl^-]_{out}}$$\n"
            "- 전류가 흐르는(비평형) 상황에서는 Nernst 방정식은 평형(equilibrium) 조건이므로 부정확."
        ),
        "rationale_md": (
            "**흔한 학생 오개념**: Nernst 방정식에 $\\log_{10}$과 $\\ln$ 중 어느 것을 써야 하는지 혼동. "
            "슬라이드가 $58 \\log_{10}$을 사용하는 이유는 $\\frac{RT}{F} \\times \\ln 10 \\approx 26.7 \\times 2.303 \\approx 61.5\\ \\mathrm{mV}$를 "
            "체온 310K에서 58 mV로 근사했기 때문이다. 두 형태는 수학적으로 동일하다.\n\n"
            "**또 다른 오해**: $E_K$가 음수인 이유를 단순히 K⁺가 음이온이기 때문이라고 생각하는 것. "
            "실제로는 K⁺는 양이온이지만, **세포 내 농도(150 mM)가 세포 외(5.5 mM)보다 훨씬 높아서** "
            "ln(out/in) = ln(1/27) < 0이 되기 때문이다.\n\n"
            "**연결**: $E_K$는 L5 HH 모델에서 K⁺ 전류의 반전 전위(reversal potential)로 직접 사용된다 "
            "($i_K = \\bar{g}_K n^4 (V - E_K)$). "
            "또한 L3 p.31–33의 구동력(driving force, $V - E_{ion}$) 개념의 출발점이다."
        ),
        "source_citation": {"kind": "slide", "lecture": "L3", "page": 27,
                             "note": "Nernst equation derivation L3 p.27–29"},
    },

    # ─── ID 10: Nernst concept ────────────────────────────────────────────────
    # Original: cited L3 p.20 (capacitance slides) but GHK concept
    # Fix: GHK equation IS in slides at L3 p.30. Re-cite correctly.
    {
        "id": 10,
        "prompt_md": (
            "**Setup.** 슬라이드 L3 p.30은 Goldman-Hodgkin-Katz (GHK) 방정식으로 안정 막전위(resting "
            "membrane potential) $E_m$을 계산한다. K⁺, Na⁺, Cl⁻의 투과도(permeability) 비가 "
            "$p_K : p_{Na} : p_{Cl} \\approx 1 : 0.04 : 0.45$임을 가정한다.\n\n"
            "(a) GHK 방정식이 Nernst 방정식(single-ion)과 **물리적으로 다른 두 가지 핵심 가정**을 대조하시오. "
            "(이온 종의 독립적 투과 가정, 전기장의 공간적 분포 가정 각각 언급할 것)\n"
            "(b) 슬라이드 p.30의 수치에서 $p_{Na} \\ll p_K$인 안정 상태에서 $E_m$이 $E_{Na}$가 아닌 "
            "$E_K$에 가까운 이유를 투과도 비로 설명하시오.\n"
            "(c) 활동 전위(action potential) 정점(peak)에서는 $p_{Na}$가 급격히 증가한다. "
            "GHK 방정식에서 이때 $E_m$의 변화 방향을 정성적으로 예측하고, 이것이 슬라이드 L5 p.7–9에서 "
            "묘사된 활동 전위의 상승 국면(upstroke)과 어떻게 연결되는가?"
        ),
        "answer_md": (
            "(a) **GHK vs Nernst: 핵심 가정 비교**\n\n"
            "| 가정 | Nernst | GHK |\n"
            "|---|---|---|\n"
            "| 이온 종 | 단일 이온만 투과 | 다수 이온 동시 투과; 각각 **독립적**으로 이동 (Goldman field 가정) |\n"
            "| 전기장 | 막 양쪽의 평균값 사용 | 막 내부에서 **전기장이 균일(constant field assumption)**하다고 가정 |\n"
            "| 투과도 | 무한대(완전 선택) | 각 이온 별 유한한 투과도 상수 $p_{ion}$ |\n\n"
            "GHK의 상수장 가정(constant field assumption)은 얇은 막(~3–4 nm)에서 근사적으로 성립하지만, "
            "막 구조의 불균일성이 있으면 오류가 생긴다.\n\n"
            "(b) **안정 상태에서 $E_m \\approx E_K$인 이유**\n\n"
            "GHK 방정식에서 투과도가 높은 이온이 $E_m$에 더 강한 영향을 미친다. "
            "$p_K : p_{Na} = 1 : 0.04$이면 Na⁺는 K⁺에 비해 25배 낮은 투과도를 가지므로 "
            "$E_m$은 $E_K (-83\\ \\mathrm{mV})$ 쪽으로 강하게 당겨진다 ($E_m \\approx -65\\ \\mathrm{mV}$). "
            "Na⁺가 기여하는 양은 작지만 $E_{Na} \\approx +58\\ \\mathrm{mV}$가 매우 양(+)이어서 "
            "완전히 무시는 안 된다 — 이 때문에 $E_m$이 $E_K$보다 약간 양(positive) 방향으로 이동한다.\n\n"
            "(c) **활동 전위 상승국면의 예측**\n\n"
            "활동 전위 정점에서 전압 개폐 Na⁺ 채널이 급격히 열리면 $p_{Na} \\gg p_K$로 역전. "
            "GHK 방정식에서 $p_{Na}$ 항이 분자/분모를 지배하면 $E_m \\to E_{Na} \\approx +58\\ \\mathrm{mV}$. "
            "슬라이드 L5 p.7–9의 빠른 양의 순환(fast positive cycle): Na⁺ 유입 → 탈분극 → 더 많은 Na⁺ 채널 열림 → "
            "막전위가 $E_{Na}$에 가까워지는 방향으로 급격히 상승하는 것이 이 원리이다."
        ),
        "rationale_md": (
            "**흔한 학생 오개념**: GHK 방정식에서 투과도가 낮은 이온은 완전히 무시해도 된다고 생각하는 것. "
            "실제로는 $E_{Na} = +58\\ \\mathrm{mV}$가 $E_K = -83\\ \\mathrm{mV}$보다 약 141 mV 더 양수이므로, "
            "작은 $p_{Na}$라도 $E_m$을 $E_K$보다 위쪽으로 끌어올리는 데 상당한 기여를 한다.\n\n"
            "**또 다른 오해**: 활동 전위 정점에서 $E_m$이 정확히 $E_{Na}$에 도달한다고 생각하는 것. "
            "실제로는 $p_K$가 0이 되는 것이 아니고 K⁺ 투과도도 유지되므로 정점은 $E_{Na}$보다 낮다 (~+40 mV).\n\n"
            "**연결**: 슬라이드 L3 p.31–33의 구동력 $V - E_{ion}$과 L5 p.29의 "
            "$i_m = \\bar{g}_{Na} m^3 h (V - E_{Na}) + \\bar{g}_K n^4 (V - E_K) + \\bar{g}_L (V - E_L)$ "
            "식이 모두 GHK/Nernst 평형 전위를 기준으로 정의된다."
        ),
        "source_citation": {"kind": "slide", "lecture": "L3", "page": 30,
                             "note": "GHK equation L3 p.30"},
    },

    # ─── ID 11: Nernst application ────────────────────────────────────────────
    # Original: cited L3 p.22 (resistance slides) but GHK application content
    # Fix: driving force is L3 p.31-32. Membrane current from driving force.
    {
        "id": 11,
        "prompt_md": (
            "**Setup.** 슬라이드 L3 p.31–32는 이온 전류(ionic current)가 구동력(driving force, $V_m - E_{ion}$)에 "
            "비례한다는 선형 근사를 소개한다. 또한 p.32–33은 전체 막 전류(membrane current)를 "
            "개별 이온 전류의 합으로 정의한다.\n\n"
            "**문제.** 안정 상태($V_m = -65\\ \\mathrm{mV}$)의 뉴런에 다음 조건이 주어진다:\n"
            "- $E_K = -83\\ \\mathrm{mV}$, $\\bar{g}_K = 36\\ \\mathrm{mS/cm}^2$\n"
            "- $E_{Na} = +58\\ \\mathrm{mV}$, $\\bar{g}_{Na} = 120\\ \\mathrm{mS/cm}^2$ (활성화 없음)\n"
            "- $E_L = -65\\ \\mathrm{mV}$, $\\bar{g}_L = 0.3\\ \\mathrm{mS/cm}^2$\n\n"
            "(a) 각 이온 종의 구동력(driving force)을 계산하고, 전류의 **부호와 방향**(내향/외향)을 판단하시오. "
            "슬라이드 L3 p.32의 부호 규약(positive = 양이온이 세포 밖으로 이동)을 사용할 것.\n"
            "(b) 뉴런이 안정 상태일 때 알짜 막 전류(net membrane current)는 0이 되어야 한다. "
            "이 조건에서 세 전류의 합이 0이 되려면 어떤 추가 메커니즘이 필요한가?\n"
            "(c) 전압이 활동 전위 정점(+40 mV)으로 변하면 K⁺ 구동력은 어떻게 변하는가? "
            "방향과 크기 모두 계산하시오."
        ),
        "answer_md": (
            "(a) **구동력 계산과 전류 방향**\n\n"
            "$V_m = -65\\ \\mathrm{mV}$:\n\n"
            "- K⁺: $V_m - E_K = -65 - (-83) = +18\\ \\mathrm{mV}$ → 양수, "
            "즉 K⁺가 외향(outward) 이동. $i_K = 36 \\times 18 = 648\\ \\mu\\mathrm{A/cm}^2$ (외향, 양)\n"
            "- Na⁺: $V_m - E_{Na} = -65 - (+58) = -123\\ \\mathrm{mV}$ → 음수, "
            "즉 Na⁺가 내향(inward) 이동. $i_{Na} = 120 \\times (-123) = -14760\\ \\mu\\mathrm{A/cm}^2$ (내향, 음) "
            "[안정 상태에서는 Na⁺ 채널 거의 닫혀 있어 $\\bar{g}_{Na}$ 적용 안 됨]\n"
            "- Leak: $V_m - E_L = -65 - (-65) = 0\\ \\mathrm{mV}$ → 구동력 0, 전류 없음.\n\n"
            "실제 안정 상태에서 Na⁺ 채널은 거의 닫혀 있으므로 ($m \\approx 0$) 위 Na⁺ 전류는 "
            "최대값($\\bar{g}_{Na}$ 사용 시)이며, 실제 $g_{Na}$는 훨씬 작다.\n\n"
            "(b) **알짜 전류 = 0을 만족시키는 메커니즘**\n\n"
            "순수 수동 채널만으로는 $E_L = V_m$(안정)으로 설정하는 것 외에, "
            "Na⁺-K⁺ ATPase 펌프(능동 수송)가 Na⁺를 밖으로, K⁺를 안으로 지속적으로 이동시켜 "
            "농도 기울기를 유지한다 (슬라이드 L3 p.26 이온 펌프 참조). "
            "안정 상태는 수동 누설과 능동 펌프 사이의 **동적 평형(dynamic equilibrium)**이다 (슬라이드 p.16).\n\n"
            "(c) **활동 전위 정점(+40 mV)에서 K⁺ 구동력**\n\n"
            "$$V_m - E_K = +40 - (-83) = +123\\ \\mathrm{mV}$$\n"
            "안정 상태의 18 mV에서 123 mV로 **약 7배** 증가. "
            "방향은 여전히 외향(양수)이지만 크기가 훨씬 커진다 — 이것이 K⁺ 채널 열릴 때 "
            "강력한 재분극(repolarization) 전류가 생기는 이유이다 (슬라이드 L5 p.7–9)."
        ),
        "rationale_md": (
            "**흔한 학생 오개념**: 구동력이 음수이면 음이온이 이동한다고 생각하는 것. "
            "슬라이드의 부호 규약: 구동력의 부호는 **양이온의 방향**을 기준으로 한다. "
            "음의 구동력($V_m < E_{ion}$)은 양이온이 내향 이동함을 의미한다.\n\n"
            "**또 다른 오해**: 안정 막전위가 Nernst 평형에서 자연스럽게 형성된다고 생각하는 것. "
            "실제로는 이온 펌프가 없으면 농도 기울기가 서서히 소멸하여 $E_m = 0$ V로 수렴한다 "
            "(이것이 '안정'이 '동적 평형'인 이유).\n\n"
            "**연결**: L5 p.29의 HH 막 전류 방정식 $i_m$은 이 구동력 개념의 직접 확장이며, "
            "$n, m, h$ 게이팅 변수가 최대 conductance에 곱해져 실효 conductance를 정의한다."
        ),
        "source_citation": {"kind": "slide", "lecture": "L3", "page": 31,
                             "note": "driving force and membrane current L3 p.31–33"},
    },

    # ─── ID 12: Nernst proof ─────────────────────────────────────────────────
    # Original: cited L3 p.25 but GHK derivation is L3 p.27-30
    # Fix: Thermodynamic proof of Nernst from diffusion + electrical force balance
    {
        "id": 12,
        "prompt_md": (
            "**Setup.** 슬라이드 L3 p.27–28은 이온의 net 이동이 없는 평형 상태에서 "
            "확산 기울기력(diffusion force)과 전기력(electrical force)이 균형을 이룬다고 설명한다. "
            "p.28의 에너지 식: 확산력 $W_{diff} = nRT \\ln([ion]_{out}/[ion]_{in})$, "
            "전기력 $W_{elec} = nzFE$.\n\n"
            "(a) 평형 조건 $W_{diff} + W_{elec} = 0$에서 Nernst 방정식 "
            "$E_{ion} = \\frac{RT}{zF} \\ln \\frac{[ion]_{out}}{[ion]_{in}}$을 "
            "단계적으로 유도하시오. 각 기호의 물리적 의미를 명시하라.\n"
            "(b) 이 유도가 이온 채널의 구조(structure)에 대해 어떤 가정도 하지 않음을 서술하고, "
            "Nernst 방정식이 모든 이온 종에 대해 '동일한 수학 형태'를 갖는 이유를 설명하시오.\n"
            "(c) K⁺ ($z=+1$)와 Ca²⁺ ($z=+2$)에 대해 Nernst 방정식을 비교하고, "
            "가수(valency) $z$가 평형 전위 크기에 어떤 영향을 미치는가?"
        ),
        "answer_md": (
            "(a) **Nernst 방정식 유도 (슬라이드 L3 p.28 에너지 균형)**\n\n"
            "평형에서 양방향 플럭스가 같으므로 자유에너지 변화(free energy) = 0:\n"
            "$$W_{diff} + W_{elec} = 0$$\n"
            "$$nRT \\ln \\frac{[ion]_{out}}{[ion]_{in}} + nzFE = 0$$\n\n"
            "$n$으로 나누면:\n"
            "$$RT \\ln \\frac{[ion]_{out}}{[ion]_{in}} = -zFE$$\n\n"
            "$E$에 대해 풀면 ($E = V_{in} - V_{out} \\equiv E_{ion}$ 정의):\n"
            "$$\\boxed{E_{ion} = -\\frac{RT}{zF} \\ln \\frac{[ion]_{out}}{[ion]_{in}} = \\frac{RT}{zF} \\ln \\frac{[ion]_{in}}{[ion]_{out}}}$$\n\n"
            "또는 관례적으로 슬라이드 p.29 형태:\n"
            "$$E_{ion} = \\frac{RT}{zF} \\ln \\frac{[ion]_{out}}{[ion]_{in}}$$\n"
            "(부호는 $E_{ion} = V_{in} - V_{out}$ 정의에 따라 달라지므로 일관성 유지 필수)\n\n"
            "(b) **채널 구조에 무관한 이유**\n\n"
            "이 유도는 열역학적 평형 조건(자유에너지 최소화)만 사용한다. "
            "이온이 어떤 경로로 막을 통과하는지(채널 구조, 크기, 게이팅 메커니즘)는 무관하다. "
            "모든 이온이 동일한 자유에너지 원리를 따르기 때문에 $E_{ion} = (RT/zF) \\ln(C_{out}/C_{in})$ "
            "수식 형태는 이온 종과 무관하게 동일하다 — 차이는 오직 $z$, 농도 비, $T$뿐이다.\n\n"
            "(c) **K⁺ vs Ca²⁺ 비교**\n\n"
            "체온 ($T = 310\\ \\mathrm{K}$), $\\frac{RT}{F} \\approx 26.7\\ \\mathrm{mV}$:\n\n"
            "- K⁺ ($z=+1$): $E_K = \\frac{26.7}{1} \\ln \\frac{5.5}{150} \\approx -88\\ \\mathrm{mV}$\n"
            "- Ca²⁺ ($z=+2$): $\\frac{RT}{zF} = \\frac{26.7}{2} = 13.35\\ \\mathrm{mV}$; "
            "$[Ca^{2+}]_{out} \\approx 2\\ \\mathrm{mM}$, $[Ca^{2+}]_{in} \\approx 0.0001\\ \\mathrm{mM}$:\n"
            "$E_{Ca} = 13.35 \\times \\ln(20000) \\approx 13.35 \\times 9.9 \\approx +132\\ \\mathrm{mV}$\n\n"
            "가수 $z$가 클수록: ① 동일한 농도 비에서 평형 전위 크기가 $1/z$배로 **작아지고**, "
            "② 동일한 전압 변화에 대한 전기력이 더 크므로 전위 의존성이 더 민감해진다."
        ),
        "rationale_md": (
            "**흔한 학생 오개념**: Nernst 방정식 부호를 외울 때 $\\ln([out]/[in])$ vs $\\ln([in]/[out])$ 혼동. "
            "슬라이드 p.29 수치를 직접 대입해서 결과의 부호가 맞는지 확인하는 것이 가장 안전하다: "
            "K⁺는 inside가 outside보다 높으므로 $E_K < 0$이어야 한다.\n\n"
            "**또 다른 오해**: Nernst 방정식이 실제 막전위를 직접 결정한다고 생각하는 것. "
            "Nernst 방정식은 단일 이온의 **평형 전위** (그 이온만 투과할 때 전류가 0이 되는 전압)를 "
            "계산하며, 실제 막전위는 여러 이온의 투과도에 가중된 평균이다 (GHK 방정식).\n\n"
            "**연결**: L3 p.31 driving force $(V_m - E_K)$가 음수이면 K⁺는 내향 이동한다는 "
            "사실이 직접 이 유도로부터 나온다 — 그 방향이 에너지적으로 내리막이기 때문이다."
        ),
        "source_citation": {"kind": "slide", "lecture": "L3", "page": 27,
                             "note": "thermodynamic derivation of Nernst L3 p.27-29"},
    },

    # ─── ID 13: model_types concept ──────────────────────────────────────────
    # Original: bias-variance + AIC — NOT in slides
    # Fix: Slides cover HH vs IF vs Izhikevich triad (L7 p.5-9)
    # Rewrite as concept card contrasting the three model types
    {
        "id": 13,
        "prompt_md": (
            "**Setup.** 슬라이드 L7 p.5는 단일 뉴런 계산 모델의 세 가지 유형: "
            "**(1) Hodgkin-Huxley (HH) 모델**, **(2) Integrate-and-Fire (IF) 모델**, "
            "**(3) Izhikevich 모델**을 나란히 제시한다. p.6–9는 각 모델의 단순화 근거를 설명한다.\n\n"
            "(a) 세 모델을 다음 세 기준으로 **비교 표**를 작성하시오: "
            "(i) 계산 복잡도(computational cost), "
            "(ii) 생물학적 충실도(biological fidelity), "
            "(iii) 가장 적합한 응용 사례.\n"
            "(b) IF 모델이 HH 모델에서 어떤 가정을 추가함으로써 단순화되는지 설명하시오 "
            "(슬라이드 L7 p.9–10 참조). '스파이크 형태'에 대한 가정과 '역치 이하 동역학'에 대한 가정 각각 명시.\n"
            "(c) 슬라이드 p.6 '단순화의 두 가지 이유(Two main reasons for simplification)' 관점에서, "
            "HH 모델을 항상 IF 모델로 대체할 수 있는가? 어떤 경우에는 HH가 필수적인가?"
        ),
        "answer_md": (
            "(a) **세 모델 비교표**\n\n"
            "| 기준 | HH 모델 | IF 모델 | Izhikevich 모델 |\n"
            "|---|---|---|---|\n"
            "| 계산 복잡도 | 높음 (4 ODE) | 낮음 (1 ODE + reset) | 중간 (2 ODE) |\n"
            "| 생물학적 충실도 | 높음 (이온 채널 수준) | 낮음 (스파이크 형태 무시) | 중간 (다양한 발화 패턴 재현) |\n"
            "| 주요 응용 | 이온 채널 메커니즘, AP 형태, 전파 | 대규모 네트워크 시뮬레이션, 스파이크 타이밍 | 중간 규모 네트워크, 다양한 발화 패턴 필요 시 |\n\n"
            "(b) **HH → IF 단순화 가정 (슬라이드 L7 p.9–10)**\n\n"
            "① **스파이크 형태 가정**: 슬라이드 p.8 — '스파이크 형태(form of spikes)는 매우 정형화되어 있어 "
            "정보 전달에 세부 사항이 중요하지 않다.' → IF 모델은 스파이크를 발화 사건(event)으로만 기록하고 "
            "파형(waveform)은 모델링하지 않는다. V가 역치에 도달하면 즉시 재설정(reset).\n\n"
            "② **역치 이하 동역학 가정**: 슬라이드 p.10 — 역치 이하에서 Na⁺, K⁺ 능동 채널이 거의 닫혀 있어 "
            "($m \\approx 0, h \\approx 1, n \\approx 0$) HH 방정식에서 해당 항을 무시하면 "
            "막 방정식이 단순한 RC 회로 방정식 $\\tau_m dV/dt = -(V - E_L) + R_m I_{inj}$으로 축소된다.\n\n"
            "(c) **HH가 IF를 대체할 수 없는 경우**\n\n"
            "슬라이드 p.6 단순화 이유: ① 계산 효율, ② 최소 필수 특성 파악. "
            "HH가 필수적인 경우:\n"
            "- 이온 채널 메커니즘(channel kinetics) 자체를 연구할 때\n"
            "- 활동 전위 전파 속도나 형태가 연구 대상일 때 (L6 p.15–22)\n"
            "- 약물(drug)이나 돌연변이(mutation)의 채널-수준 효과를 시뮬레이션할 때\n"
            "- 다巴민성 뉴런(DA 뉴런) 같이 발화 패턴 선택에 특정 이온 채널이 중요한 경우 (L7 p.37–40)"
        ),
        "rationale_md": (
            "**흔한 학생 오개념**: IF 모델이 '단순하기 때문에 부정확하다'고 생각하는 것. "
            "단순화는 **의도적인 추상화**이며, 스파이크 타이밍 기반 정보 처리를 연구하는 데에는 "
            "오히려 IF가 더 명확한 해석을 제공할 수 있다 (L7 p.7 명시).\n\n"
            "**또 다른 오해**: Izhikevich 모델이 HH 모델의 수학적 단순화라고 생각하는 것. "
            "실제로는 HH에서 유도된 것이 아니라 **phenomenological한 2변수 시스템**으로 "
            "다양한 발화 패턴을 재현하도록 파라미터가 설계된 독립적인 모델이다 (슬라이드 p.25).\n\n"
            "**연결**: L7 p.45의 '어떤 모델을 선택할 것인가' 결론: 연구 질문에 따라 선택이 달라진다. "
            "이것이 모델 선택의 타당성 영역(regime of validity) 개념의 핵심이다."
        ),
        "source_citation": {"kind": "slide", "lecture": "L7", "page": 5,
                             "note": "model triad and simplification rationale L7 p.5-9"},
    },

    # ─── ID 14: model_types application ──────────────────────────────────────
    # Original: GIF + Mensi 2012 — NOT in slides
    # Fix: Adaptive IF model with g_sra IS in slides (L7 p.18-24)
    # Rewrite as application card on spike-rate adaptation with g_sra
    {
        "id": 14,
        "prompt_md": (
            "**Setup.** 슬라이드 L7 p.18–24는 적응적 integrate-and-fire (adaptive IF) 모델을 소개한다. "
            "기본 IF 모델에 적응 전도(spike-rate adaptation conductance) $g_{sra}$를 추가하면 "
            "스파이크 발화율 적응(spike-rate adaptation, SRA) 현상을 재현할 수 있다.\n\n"
            "**절차적 문제.** 다음 단계로 adaptive IF 모델을 분석하시오:\n\n"
            "(a) 슬라이드 p.23에 제시된 adaptive IF 방정식을 쓰시오: "
            "막 방정식($dV/dt$)과 $g_{sra}$ 방정식($dg_{sra}/dt$) 두 ODE를 명시하라. "
            "스파이크 발화 시 $g_{sra}$에 무슨 일이 일어나는지도 서술하라.\n"
            "(b) $g_{sra}$가 K⁺ 전도도로 모델링되는 이유를 슬라이드의 생물물리학적 근거로 설명하고, "
            "이것이 ISI(inter-spike interval)에 어떤 영향을 미치는지 정성적으로 분석하시오.\n"
            "(c) 슬라이드 L7 p.24의 그래프에서 단순 IF와 adaptive IF의 ISI를 비교하고, "
            "대규모 네트워크에서 SRA가 동기화 진동수(synchronized oscillation frequency)를 "
            "결정하는 데 어떤 역할을 하는지 서술하시오 (L7 p.28–36 참조)."
        ),
        "answer_md": (
            "(a) **Adaptive IF 방정식 (슬라이드 L7 p.23)**\n\n"
            "막 방정식:\n"
            "$$\\tau_m \\frac{dV}{dt} = -(V - E_L) - R_m g_{sra}(V - E_K) + R_m I_e$$\n\n"
            "$g_{sra}$ 방정식:\n"
            "$$\\tau_{sra} \\frac{dg_{sra}}{dt} = -g_{sra}$$\n"
            "(스파이크 사이에는 $g_{sra}$가 0으로 지수적 감쇠)\n\n"
            "스파이크 발화 시: $g_{sra} \\leftarrow g_{sra} + \\Delta g_{sra}$ (점프 증가). "
            "즉, 각 스파이크마다 $g_{sra}$가 $\\Delta g_{sra}$ 만큼 증분된다.\n\n"
            "(b) **K⁺ 전도도로 모델링하는 이유**\n\n"
            "슬라이드 p.23: $g_{sra}$는 **K⁺ 전도도**로 모델링한다. 이유:\n"
            "- K⁺의 평형 전위 $E_K \\approx -83\\ \\mathrm{mV}$는 역치($V_{th} \\approx -50\\ \\mathrm{mV}$)보다 낮다.\n"
            "- 스파이크 후 $g_{sra}$ 증가 → K⁺ 외향 전류 증가 → 막전위를 $E_K$ 방향으로 과분극(hyperpolarize) → "
            "다음 스파이크까지의 시간(ISI) 증가.\n"
            "- 반복 발화 시 $g_{sra}$가 누적(accumulate) → ISI가 점점 길어짐 = 스파이크 발화율 감소 = SRA.\n\n"
            "ISI 영향: 초기에는 짧은 ISI로 높은 발화율, 이후 $g_{sra}$ 누적으로 ISI 점진적 증가 → "
            "발화율이 일정 수준에서 수렴 (적응).\n\n"
            "(c) **ISI 비교와 네트워크 역할**\n\n"
            "슬라이드 L7 p.24: 단순 IF는 일정 전류에 대해 **일정한 ISI** (등간격 발화). "
            "Adaptive IF는 초기에는 짧은 ISI, 이후 점차 증가하다 수렴 — 실제 피질 뉴런의 SRA와 일치.\n\n"
            "슬라이드 L7 p.28–36: 적응 뉴런은 oscillatory 입력에 대해 특정 선호 주파수(preferred frequency)를 "
            "가진다. $g_{sra}$가 클수록 더 낮은 주파수에 동조. 대규모 적응 뉴런 네트워크에서 "
            "SRA가 집단 진동수(population oscillation)를 결정 — p.35 200-뉴런 네트워크 시뮬레이션에서 "
            "$g_{sra}$ 크기에 따라 6-7 Hz 리듬이 나타난다."
        ),
        "rationale_md": (
            "**흔한 학생 오개념**: 스파이크율 적응(SRA)이 단순히 '피로(fatigue)' 현상이라고 생각하는 것. "
            "SRA는 목적적 메커니즘으로, 지속적 입력에 대한 포화 방지 (슬라이드 p.19), "
            "선택적 주의(selective attention) 향상, 순방향 마스킹(forward masking) 등의 "
            "계산적 기능을 수행한다 (슬라이드 p.19–22).\n\n"
            "**또 다른 오해**: $g_{sra}$가 스파이크 중에만 작동한다고 생각하는 것. "
            "실제로는 스파이크 시 증가한 후 $\\tau_{sra}$ 시간 상수로 서서히 감쇠한다. "
            "이 '기억' 효과가 이전 스파이크의 영향을 현재에 전달한다.\n\n"
            "**연결**: L7 p.25–27 Izhikevich 모델의 매개변수 $a, b$가 회복 변수(recovery variable) $u$의 "
            "시간 규모와 역치 아래 결합을 제어하는데, 이것이 SRA를 포함한 다양한 적응 패턴을 낳는다 "
            "— adaptive IF의 $g_{sra}$와 개념적으로 유사한 역할."
        ),
        "source_citation": {"kind": "slide", "lecture": "L7", "page": 18,
                             "note": "spike-rate adaptation with g_sra L7 p.18-24"},
    },

    # ─── ID 15: model_types proof ─────────────────────────────────────────────
    # Original: Wilson-Cowan derivation — NOT in slides
    # Fix: LIF derivation from HH is in slides (L7 p.9-13)
    # Rewrite as proof of LIF ISI formula
    {
        "id": 15,
        "prompt_md": (
            "**Setup.** 슬라이드 L7 p.10–16은 Hodgkin-Huxley(HH) 방정식에서 "
            "Leaky Integrate-and-Fire (LIF) 모델을 도출하고, 일정 전류 $I_e$ 주입 시 "
            "발화 간격(ISI, inter-spike interval) $t_{ISI}$를 해석적으로 구한다.\n\n"
            "(a) HH 방정식 전체에서 역치 이하(subthreshold) 가정을 적용할 때 "
            "($m \\approx 0, n \\approx 0$) 단순화된 LIF 막 방정식이 어떻게 유도되는지 "
            "단계적으로 보이시오 (슬라이드 p.10 참조).\n"
            "(b) LIF 방정식 $\\tau_m \\frac{dV}{dt} = -(V - E_L) + R_m I_e$를 초기 조건 "
            "$V(0) = V_{reset}$로 풀어 $V(t)$ 해를 구하시오. (변수 분리법 사용, 중간 단계 명시)\n"
            "(c) (b)의 해에서 $V(t_{ISI}) = V_{th}$가 되는 시간 $t_{ISI}$를 구하는 "
            "공식을 도출하고, 슬라이드 p.16의 결과와 일치시키시오. "
            "이 공식이 유효한 조건(regime of validity)은 무엇인가?"
        ),
        "answer_md": (
            "(a) **HH → LIF 단순화 (슬라이드 L7 p.10)**\n\n"
            "HH 방정식:\n"
            "$$C_m \\frac{dV}{dt} = -\\bar{g}_L(V-E_L) - \\bar{g}_K n^4(V-E_K) - \\bar{g}_{Na} m^3 h (V-E_{Na}) + I_{inj}$$\n\n"
            "역치 이하 가정: 능동 채널 $m \\approx 0$ (Na⁺ 채널 닫힘), $n \\approx 0$ (K⁺ 채널 닫힘). "
            "따라서 $g_K n^4 \\approx 0$, $g_{Na} m^3 h \\approx 0$ 항 소거:\n"
            "$$C_m \\frac{dV}{dt} \\approx -\\bar{g}_L(V-E_L) + I_e$$\n\n"
            "$R_m = 1/\\bar{g}_L$로 양변에 $R_m$ 곱하고 $\\tau_m = R_m C_m$ 정의:\n"
            "$$\\boxed{\\tau_m \\frac{dV}{dt} = -(V - E_L) + R_m I_e}$$\n\n"
            "(b) **LIF ODE 풀기 (변수 분리법)**\n\n"
            "새 변수: $u = V - (E_L + R_m I_e)$ (점근값에서 편차). 그러면:\n"
            "$$\\tau_m \\frac{du}{dt} = -u$$\n"
            "변수 분리:\n"
            "$$\\frac{du}{u} = -\\frac{dt}{\\tau_m}$$\n"
            "양변 적분:\n"
            "$$\\ln|u| = -\\frac{t}{\\tau_m} + C \\implies u(t) = u(0)e^{-t/\\tau_m}$$\n\n"
            "초기 조건 $V(0) = V_{reset}$: $u(0) = V_{reset} - (E_L + R_m I_e)$.\n\n"
            "원래 변수로 복원:\n"
            "$$\\boxed{V(t) = (E_L + R_m I_e) + (V_{reset} - E_L - R_m I_e)e^{-t/\\tau_m}}$$\n\n"
            "(c) **ISI 공식 도출 (슬라이드 L7 p.16)**\n\n"
            "$V(t_{ISI}) = V_{th}$ 조건:\n"
            "$$V_{th} = (E_L + R_m I_e) + (V_{reset} - E_L - R_m I_e)e^{-t_{ISI}/\\tau_m}$$\n\n"
            "정리:\n"
            "$$e^{-t_{ISI}/\\tau_m} = \\frac{V_{th} - E_L - R_m I_e}{V_{reset} - E_L - R_m I_e}$$\n\n"
            "로그 취하고 부호 반전:\n"
            "$$\\boxed{t_{ISI} = \\tau_m \\ln \\frac{R_m I_e + E_L - V_{reset}}{R_m I_e + E_L - V_{th}}}$$\n\n"
            "이것이 슬라이드 L7 p.16의 결과이다.\n\n"
            "**타당성 영역 (regime of validity)**:\n"
            "- $R_m I_e > V_{th} - E_L$: 점근값 $E_L + R_m I_e$가 역치보다 높아야 발화 가능 "
            "(이 조건 불만족 시 $t_{ISI} \\to \\infty$, 발화 없음).\n"
            "- 역치 이하(subthreshold) 동역학의 선형 가정이 성립하는 범위.\n"
            "- 적응 전도(adaptation conductance)가 없는 경우에만 이 ISI가 일정하게 유지됨."
        ),
        "rationale_md": (
            "**흔한 학생 오개념**: 풀이에서 $u = V - V_{eq}$ 변수 치환 없이 바로 분리하려다 "
            "비균질(inhomogeneous) ODE를 틀리게 처리하는 것. "
            "올바른 방법은 정상 상태(steady-state) $V_{eq} = E_L + R_m I_e$를 먼저 구하고 "
            "편차 변수 $u$로 치환하면 균질(homogeneous) ODE가 된다.\n\n"
            "**또 다른 오해**: ISI 공식의 분자/분모 순서 혼동. "
            "$V_{reset} < V_{th}$이므로 분자 $(R_m I_e + E_L - V_{reset}) > (R_m I_e + E_L - V_{th})$ — "
            "즉, 분자 > 분모 > 0 이어야 $\\ln > 0$, 즉 $t_{ISI} > 0$이 성립.\n\n"
            "**연결**: 이 ISI 공식은 슬라이드 L7 p.17의 I-f 커브(전류-발화율 관계)를 "
            "$r = 1/t_{ISI}$로 직접 계산하는 데 사용되며, 실제 피질 뉴런의 in vivo 데이터와 비교된다."
        ),
        "source_citation": {"kind": "slide", "lecture": "L7", "page": 10,
                             "note": "LIF derivation and ISI formula L7 p.10-16"},
    },

    # ─── ID 17: neural_codes application ─────────────────────────────────────
    # Original: Fisher info + CRLB — NOT in slides
    # Fix: PSTH and rate code decoding IS in slides (L8 p.16-25)
    # Rewrite as application card on PSTH analysis procedure
    {
        "id": 17,
        "prompt_md": (
            "**Setup.** 슬라이드 L8 p.23–25는 시간 의존적 자극(time-dependent stimulus)에 대한 "
            "뉴런 반응을 분석하기 위해 발화율 밀도(spike density, PSTH)를 사용한다. "
            "PSTH (Peristimulus Time Histogram)는 동일 자극을 반복 시행(trial)하여 "
            "시간 빈(time bin) $\\Delta t$에서의 평균 발화 수를 기록한다.\n\n"
            "**절차적 문제.** 다음 분석 절차를 단계별로 수행하시오:\n\n"
            "(a) 자극 제시 후 100 ms 동안 10회 반복 시행에서 "
            "20 ms 빈(bin)별 스파이크 수가 $[2, 3, 5, 8, 6]$이라면, "
            "각 빈의 발화율(firing rate, $\\nu$, Hz 단위)을 계산하시오. "
            "공식 $\\nu = n_{sp}/(n_K \\cdot \\Delta t)$를 사용하고, $n_K$(반복 수)와 $\\Delta t$(빈 크기, s)를 명시하라.\n"
            "(b) PSTH가 '발화율 코드(rate code)'로 정보를 복호화(decode)하는 관점에서, "
            "이 분석의 **두 가지 핵심 가정**을 설명하시오.\n"
            "(c) 슬라이드 L8 p.24에서 지적한 PSTH의 **근본적 한계**: "
            "'개구리가 파리를 잡을 때 왜 PSTH를 사용할 수 없는가?'를 서술하고, "
            "이 한계가 속도 코딩(rate coding)의 어떤 일반적 문제를 드러내는가 (슬라이드 p.26–28)?"
        ),
        "answer_md": (
            "(a) **PSTH 발화율 계산**\n\n"
            "파라미터: $n_K = 10$ 반복, $\\Delta t = 20\\ \\mathrm{ms} = 0.02\\ \\mathrm{s}$.\n"
            "공식: $\\nu = n_{sp} / (n_K \\cdot \\Delta t)$\n\n"
            "| 빈 (ms) | 스파이크 수 | 발화율 (Hz) |\n"
            "|---|---|---|\n"
            "| 0–20 | 2 | $2 / (10 \\times 0.02) = 10$ Hz |\n"
            "| 20–40 | 3 | $3 / (10 \\times 0.02) = 15$ Hz |\n"
            "| 40–60 | 5 | $5 / (10 \\times 0.02) = 25$ Hz |\n"
            "| 60–80 | 8 | $8 / (10 \\times 0.02) = 40$ Hz |\n"
            "| 80–100 | 6 | $6 / (10 \\times 0.02) = 30$ Hz |\n\n"
            "(b) **PSTH의 두 가지 핵심 가정**\n\n"
            "① **정상성(stationarity) 가정**: 동일 자극에 대한 반응 통계가 시행 간 변하지 않는다 — "
            "뉴런의 내부 상태나 피로(fatigue)가 없다고 가정.\n\n"
            "② **집단 평균 = 개별 시행의 정보** 가정: PSTH는 많은 반복에서 평균하므로, "
            "단일 시행(single trial)의 스파이크 타이밍 정보는 버려진다. "
            "뇌가 실제로 발화율만 사용한다는 암묵적 가정이 포함된다.\n\n"
            "(c) **PSTH의 근본적 한계와 속도 코딩의 문제**\n\n"
            "슬라이드 L8 p.24 명시: PSTH는 **반복 시행 평균**이 필요하다. "
            "개구리가 파리를 잡는 상황: 파리의 궤적은 매번 다르고, 개구리는 단 하나의 시행(single run)으로 "
            "반응해야 한다 — 100번 반복해서 평균 낼 수 없다.\n\n"
            "슬라이드 p.26–28의 일반적 문제: **행동 실험의 반응 시간이 너무 짧다** "
            "(인간은 400 ms 이내 시각 장면 인식 — p.27). "
            "시간 평균 발화율은 적어도 수백 ms가 필요하지만, 뇌는 훨씬 빠르다. "
            "이 불일치가 순수 rate code 가설의 주된 반론이며, "
            "temporal code나 first-spike timing (L8 p.32–34)의 필요성을 시사한다."
        ),
        "rationale_md": (
            "**흔한 학생 오개념**: PSTH를 단순히 '히스토그램'으로만 이해하고, "
            "$n_K$ (반복 수) 나누기를 빠뜨려 Hz 단위 발화율로 변환하지 않는 것. "
            "분모에 $\\Delta t$ 와 $n_K$ 모두 필요하다.\n\n"
            "**또 다른 오해**: PSTH가 발화율 코드의 '증거'라고 생각하는 것. "
            "PSTH는 분석 도구이지, 뇌가 실제로 발화율을 사용한다는 증거가 아니다. "
            "단일 뉴런은 PSTH를 '계산'할 능력이 없다.\n\n"
            "**연결**: 슬라이드 L8 p.32–34의 'time-to-first-spike' 코딩은 PSTH 분석의 대안 — "
            "단일 스파이크의 타이밍에 자극 정보가 담겨 있어 반복 평균 없이도 정보 복호화가 가능하다. "
            "Thorpe et al. (1996)의 V1 결과가 그 근거로 슬라이드에 인용된다."
        ),
        "source_citation": {"kind": "slide", "lecture": "L8", "page": 23,
                             "note": "PSTH rate code analysis L8 p.23-25"},
    },

    # ─── ID 18: neural_codes proof ────────────────────────────────────────────
    # Original: mutual-info bit calculations — NOT in slides
    # Fix: Phase coding and theta-phase precession IS in slides (L8 p.35-46)
    # Rewrite as proof-level analysis of phase precession mechanism
    {
        "id": 18,
        "prompt_md": (
            "**Setup.** 슬라이드 L8 p.35–46은 해마(hippocampus)의 위상 코딩(phase code)과 "
            "위상 선행(phase precession)을 설명한다. O'Keefe & Recce (1993)의 핵심 발견: "
            "장소 세포(place cell)가 theta 진동(~8 Hz)의 점점 더 이른 위상(earlier phase)에 "
            "발화함으로써 동물의 공간 위치를 이중 부호화(dual code)한다.\n\n"
            "(a) 위상 선행(phase precession) 현상을 정량적으로 서술하시오: "
            "동물이 장소 수용장(place field)에 진입할 때부터 이탈할 때까지 "
            "theta 위상이 어떻게 변하는가? (슬라이드 p.39의 데이터 기반으로)\n"
            "(b) 발화율 코드(rate code)와 위상 코드(phase code)가 **동일한 스파이크 기차에 동시에 존재**한다는 "
            "주장을 뒷받침하는 논리를 서술하시오. 두 코드가 어떤 정보를 각각 담는가?\n"
            "(c) 슬라이드 p.41–43의 해마 재활성화(replay)는 위상 코드와 어떻게 연결되는가? "
            "수면 중 replay가 기억 공고화(memory consolidation)에 기여하는 메커니즘을 "
            "위상 코드 관점에서 설명하시오."
        ),
        "answer_md": (
            "(a) **위상 선행 정량 서술 (슬라이드 L8 p.39)**\n\n"
            "O'Keefe & Recce (1993) 데이터:\n"
            "- 장소 세포는 동물이 해당 장소 수용장(place field)에 있을 때만 발화.\n"
            "- 장소 수용장 **진입 시**: 발화가 theta 진동의 후기 위상(late phase, ~180°)에서 시작.\n"
            "- 장소 수용장 **중앙 통과 시**: 발화 위상이 약 90°로 이동.\n"
            "- 장소 수용장 **이탈 시**: 발화가 초기 위상(early phase, ~0°)에서 발생.\n\n"
            "요약: 동물이 장소 수용장을 통과하는 동안 theta 위상이 **약 360° (한 주기) 선행(precede)** — "
            "즉, 스파이크 위상이 theta 진동 대비 점점 앞당겨진다.\n\n"
            "(b) **동일 스파이크에서 이중 코드 공존**\n\n"
            "같은 스파이크 기차에서:\n"
            "- **발화율 코드**: 장소 수용장 중앙 근처에서 발화율이 최대 (가우시안 형태의 tuning curve).\n"
            "  → 발화율 = '지금 여기 있다'는 강도 정보.\n"
            "- **위상 코드**: 수용장 내에서 theta 위상이 선형적으로 선행 → 위상 = 수용장 내 **상대적 위치** 정보.\n"
            "  → 위상이 더 빠를수록 수용장 출구에 더 가까움.\n\n"
            "두 코드는 상호 보완적: 발화율이 높아도 위상 정보로 더 세밀한 위치 구분 가능 "
            "(Huxter et al. Nature 2003: 위상과 발화율이 독립적 정보를 제공함을 실험으로 확인).\n\n"
            "(c) **Replay와 위상 코드의 연결 (슬라이드 p.41–43)**\n\n"
            "슬라이드 p.41–42: 해마 장소 세포들은 깨어있는 상태에서 공간 순서대로 순차 활성화. "
            "수면 중 slow-wave sleep 동안 이 순서가 압축된 시간 척도(compressed timescale)로 **재활성화(replay)**.\n\n"
            "위상 코드 관점: \n"
            "- 각성 시 theta 위상 순서가 '공간 순서 = 시간 순서' 관계를 부호화.\n"
            "- 수면 replay는 이 시간 순서를 재생하여 해마-피질(hippocampal-cortical) 연결을 강화.\n"
            "- 장기 기억 공고화(memory consolidation) 메커니즘: 반복된 시퀀스 재활성이 "
            "신경 연결을 헤비안(Hebbian) 가소성으로 강화 → 피질로 지식 이전."
        ),
        "rationale_md": (
            "**흔한 학생 오개념**: 위상 선행이 단순히 '스파이크가 빨라진다'는 것으로만 이해하는 것. "
            "핵심은 스파이크 발화의 **절대적 시간**이 아니라 theta 배경 진동에 대한 **상대적 위상**이다. "
            "동물이 빠르게 움직여도 위상 선행 패턴은 유지된다 (위상이 거리에 따라 선행하는 것이지 시간이 아님).\n\n"
            "**또 다른 오해**: replay가 단순히 발화율 패턴의 재생이라고 생각하는 것. "
            "실제로는 세포들의 **순서(sequence)**가 중요하며, 이 순서가 공간 정보를 담고 있다 — "
            "이것이 위상 코드의 내러티브와 일치한다.\n\n"
            "**연결**: L8 p.47–55의 동기화(synchrony) 코드도 위상 참조 신호(reference signal)를 사용한다는 점에서 "
            "위상 코드와 연결된다. 또한 L7 p.34–36의 적응 뉴런 네트워크에서 나타나는 집단 진동이 "
            "이런 위상 참조 신호의 네트워크 수준 기원을 설명할 수 있다."
        ),
        "source_citation": {"kind": "slide", "lecture": "L8", "page": 35,
                             "note": "phase code and phase precession L8 p.35-46"},
    },
]


def run() -> None:
    conn = acquire()
    try:
        with conn.cursor() as cur:
            updated = 0
            for u in UPDATES:
                card_id = u["id"]
                prompt = u["prompt_md"]
                answer = u["answer_md"]
                rationale = u["rationale_md"]
                citation = json.dumps(u["source_citation"], ensure_ascii=False)

                cur.execute("SELECT id FROM question_bank WHERE id = %s", (card_id,))
                row = cur.fetchone()
                if row is None:
                    print(f"  SKIP id={card_id}: not found in DB")
                    continue

                cur.execute(
                    """
                    UPDATE question_bank
                    SET prompt_md       = %s,
                        answer_md       = %s,
                        rationale_md    = %s,
                        source_citation = %s::jsonb
                    WHERE id = %s
                    """,
                    (prompt, answer, rationale, citation, card_id),
                )
                updated += 1
                print(f"  UPDATED id={card_id}")

            print(f"\nDone. {updated}/{len(UPDATES)} cards updated.")
        conn.commit()
    finally:
        release(conn)


if __name__ == "__main__":
    run()
