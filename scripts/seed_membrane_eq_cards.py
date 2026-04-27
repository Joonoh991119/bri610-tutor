#!/usr/bin/env python3
"""
seed_membrane_eq_cards.py — explicit membrane equation derivation cards.

Per user mandate: weight on the membrane equation
    C_m dV/dt = -(V - V_rest)/R_m + I_inj
        ⇔  τ_m dV/dt = -(V - V_rest) + R_m I_inj
with t=0 initial condition and t=∞ steady-state derivation,
solved as V(t) = V(∞) + (V(0) - V(∞)) e^(-t/τ_m).

Slide grounding (verified against `slides` table content):
  L3 p.17–20: membrane capacitance, I_C = C dV/dt
  L3 p.21–23: membrane resistance, τ_m = R_m C_m, "10–100 ms"
  L7 p.10–14: leaky IF derivation, τ_m dV/dt = -(V - E_L) + R_m I_e

Adds 6 cards (recall / concept / application / 3× proof — full-derivation
weighted as user requested), all citing slide pages whose text actually
covers the cited concept.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "backend"))
from db_pool import acquire, release  # noqa: E402


SEEDS: list[dict] = [
    # ─── 1. RECALL ─────────────────────────────────────────────────────────
    {
        "topic": "membrane_eq",
        "card_type": "recall",
        "difficulty": 3,
        "bloom": "Understand",
        "prompt_md": (
            "**Setup.** 슬라이드 L3 p.19–20에서 도입된 capacitive current $I_C = C_m \\, dV/dt$와 "
            "p.22–23의 specific membrane resistance $R_m$ 정의를 사용한다.\n\n"
            "(a) 전류 $I_{inj}(t)$가 단일 컴파트먼트 뉴런에 주입될 때 막전위(membrane potential) $V(t)$를 지배하는 "
            "**막 방정식(membrane equation)** 을 1차 ODE 형태로 적으시오. 두 가지 등가 형태로 모두 작성하라:\n"
            "  ① 전하-보존(Kirchhoff current law) 형태: $C_m\\,dV/dt = ?$\n"
            "  ② 시간 상수 $\\tau_m = R_m C_m$ 으로 정규화한 형태: $\\tau_m\\,dV/dt = ?$\n\n"
            "(b) $\\tau_m$의 차원(dimension)을 확인하고, 슬라이드 p.23이 명시한 전형적 값 범위를 답하시오."
        ),
        "answer_md": (
            "(a) **두 등가 형태**:\n\n"
            "① Kirchhoff/charge-conservation 형태:\n"
            "$$C_m \\frac{dV}{dt} \\;=\\; -\\frac{V - V_{rest}}{R_m} \\;+\\; I_{inj}(t).$$\n\n"
            "② $R_m$ 으로 양변을 곱하고 $\\tau_m = R_m C_m$ 도입:\n"
            "$$\\tau_m \\frac{dV}{dt} \\;=\\; -(V - V_{rest}) \\;+\\; R_m I_{inj}(t).$$\n\n"
            "물리적 의미: 좌변은 막 전압의 변화율 × 정전용량 = 축적되는 전하의 시간 변화. "
            "우변 첫 항은 누설 전류(leak current; 막을 통해 빠져나가는 전류, $V > V_{rest}$ 일 때 $V$를 끌어내림), "
            "둘째 항은 외부 주입 전류.\n\n"
            "(b) 차원 분석:\n"
            "$$[\\tau_m] \\;=\\; [R_m] \\cdot [C_m] \\;=\\; (\\Omega \\cdot \\mathrm{cm}^2) \\cdot (\\mathrm{F}/\\mathrm{cm}^2) "
            "\\;=\\; \\Omega \\cdot \\mathrm{F} \\;=\\; \\mathrm{s}.$$\n"
            "Specific 단위로 표기되더라도 면적 의존성이 상쇄되어 **시간** 차원이 정확히 떨어진다 (슬라이드 p.23: \"Tm is independent of area\"). "
            "전형적 값: **10–100 ms**."
        ),
        "rationale_md": (
            "**흔한 학생 오해**: ① 항의 부호를 바꿔 $+\\frac{V}{R_m}$ 로 적는 실수 — 이렇게 쓰면 \n"
            "막 전위가 발산하는 비물리적 해가 나온다. 누설 전류는 항상 $V$를 $V_{rest}$ 쪽으로 끌어당겨야 함. "
            "**또 다른 흔한 오해**: $\\tau_m$ 이 표면적에 의존한다고 생각하는 것 — $R_m$ 은 면적에 반비례, $C_m$ 은 면적에 비례하므로 곱하면 면적이 상쇄된다 (슬라이드 L3 p.23 명시). "
            "**연결**: 이 식은 L7 p.10–13의 leaky integrate-and-fire (IF) 모델 도입의 출발점이며, L5 HH 모델의 leak 항 "
            "$g_L(V - E_L)$ 과 동일한 구조 — 다만 HH는 거기에 voltage-dependent active conductance 항이 더해진다."
        ),
        "source_citation": {"kind": "slide", "lecture": "L3", "page": 23,
                             "secondary_lecture": "L7", "secondary_page": 11,
                             "primary": "Dayan & Abbott Ch.5 §5.3 (참고용)"},
        "priority_score": 0.98,
        "info_density": 0.95,
        "mastery_target": "membrane_equation_form",
    },

    # ─── 2. CONCEPT ────────────────────────────────────────────────────────
    {
        "topic": "membrane_eq",
        "card_type": "concept",
        "difficulty": 4,
        "bloom": "Analyze",
        "prompt_md": (
            "**Setup.** 단일 컴파트먼트 막 방정식 $\\tau_m \\, dV/dt = -(V - V_{rest}) + R_m I_{inj}$ 를 고려한다 "
            "(슬라이드 L3 p.20, L7 p.11).\n\n"
            "(a) **$t = 0$ 직후의 거동**과 **$t \\to \\infty$ 정상상태(steady state) 거동**을 각각 *물리적으로* "
            "(수식 풀이가 아닌 1차 ODE의 두 항이 어떻게 균형을 이루는지를) 설명하라.\n"
            "(b) $t = 0$에서 $I_{inj}$가 갑자기 켜졌을 때(step input), $V(t)$ 곡선의 모양을 정성적으로 그려서 "
            "(증가/감소, 곡률, 점근선) 묘사하라. 이 모양이 1차 RC 회로의 'capacitor charging curve'와 일치하는 "
            "이유를 한 문장으로 답하라.\n"
            "(c) 만약 시간 상수 $\\tau_m$ 이 작아진다면 (예: 막 전도도가 커져 $R_m$ 감소), $V(t)$ 곡선은 어떻게 "
            "변하는가? 슬라이드 L3 p.23이 명시한 \"larger the capacitance, the slower the resultant voltage change\" "
            "(p.19) 와 어떻게 맞물리는가?"
        ),
        "answer_md": (
            "(a) **두 극한의 물리적 균형**:\n"
            "  - **$t = 0^+$**: 막전위가 변화하기 시작하는 순간, capacitive 항 $C_m dV/dt$ 가 dominant. "
            "    누설 전류는 아직 $V \\approx V_{rest}$ 라 거의 0. $\\Rightarrow$ 모든 주입 전류가 capacitor를 충전: "
            "    $C_m dV/dt \\approx I_{inj}$, 즉 dV/dt 는 최대값 $I_{inj}/C_m$.\n"
            "  - **$t \\to \\infty$**: $dV/dt \\to 0$ (정상상태). 좌변이 0이 되어 누설 전류와 주입 전류가 균형: "
            "    $-(V_\\infty - V_{rest})/R_m + I_{inj} = 0$ $\\Rightarrow$ "
            "    $V_\\infty = V_{rest} + R_m I_{inj}$.\n\n"
            "(b) Step input $I_{inj}$ 켜진 직후: $V$는 $V_{rest}$에서 시작하여 **단조 증가**, 초기 기울기 $I_{inj}/C_m$, "
            "위로 오목(concave-down) 곡선, 점근선 $V_\\infty = V_{rest} + R_m I_{inj}$ 에 지수적으로 수렴.\n"
            "  ⮕ RC 회로의 capacitor charging curve와 동일한 이유: 막 방정식이 정확히 RC 회로의 KCL 방정식이며, "
            "막 자체가 1차 lowpass filter 로 동작하기 때문이다.\n\n"
            "(c) $\\tau_m$ 감소 → 곡선이 더 빠르게 정상상태에 도달 (e-folding 시간 짧아짐). 슬라이드 p.19에서 "
            "\"larger C, slower V change\" — $\\tau_m = R_m C_m$ 이므로 $C_m$ 감소가 곧 $\\tau_m$ 감소, 결과적으로 "
            "더 빠른 응답. 그러나 정상상태 진폭 $V_\\infty - V_{rest} = R_m I_{inj}$는 $C_m$에 무관하므로 변하지 않음 — "
            "**시간 응답 속도와 진폭은 분리된다**."
        ),
        "rationale_md": (
            "**흔한 오개념 1**: $V_\\infty$ 가 $C_m$ 에 의존한다고 생각하는 것. 정상상태에서 $dV/dt = 0$ 이므로 capacitor는 "
            "시야에서 사라지고 (DC에서 capacitor는 open), 오직 저항-구동 균형만 남는다. $\\Rightarrow V_\\infty$ 는 $R_m, I_{inj}$ 만의 함수.\n"
            "**흔한 오개념 2**: $t=0$ 에서 \"$V$가 즉시 점프한다\" — 아니다. Capacitor는 전압의 즉각 변화를 막는다 (charge-conservation). "
            "$V$는 연속이고, $dV/dt$ 만 점프한다.\n"
            "**연결**: 이 두 극한 사이를 잇는 폐형 해 $V(t) = V_\\infty + (V_0 - V_\\infty) e^{-t/\\tau_m}$ 이 다음 카드의 proof. "
            "또 동일 구조가 **HH 게이팅 변수의 $n_\\infty(V)$, $\\tau_n(V)$** (L5 p.22) 와 **cable equation의 정상상태/시간 의존 분리** (L6 p.10) "
            "에 그대로 재등장한다."
        ),
        "source_citation": {"kind": "slide", "lecture": "L3", "page": 20,
                             "secondary_lecture": "L7", "secondary_page": 14},
        "priority_score": 0.97,
        "info_density": 0.94,
        "mastery_target": "membrane_eq_limits",
    },

    # ─── 3. APPLICATION ───────────────────────────────────────────────────
    {
        "topic": "membrane_eq",
        "card_type": "application",
        "difficulty": 4,
        "bloom": "Apply",
        "prompt_md": (
            "**Setup (수치 계산).** 슬라이드 L3 p.20: \"1 nA changes V_m of a neuron with C_m = 1 nF at "
            "1 mV/ms\". 한 단일 컴파트먼트 뉴런이 다음 매개변수를 갖는다고 가정한다:\n"
            "$C_m = 1\\,\\mathrm{nF}$, $R_m = 100\\,\\mathrm{M}\\Omega$, $V_{rest} = -65\\,\\mathrm{mV}$, "
            "$I_{inj} = 0.5\\,\\mathrm{nA}$ (step at $t=0$).\n\n"
            "(a) 시간 상수 $\\tau_m$ 을 계산하라.\n"
            "(b) 정상상태 막전위 $V_\\infty$ 를 계산하라.\n"
            "(c) $t = \\tau_m$ 에서 $V(t)$ 의 값을 계산하라 (단, $V(0) = V_{rest}$).\n"
            "(d) 동일한 뉴런이 활동전위 발화 역치(spike threshold) $V_{th} = -50\\,\\mathrm{mV}$ 를 갖는다면, "
            "이 step input 만으로 발화 가능한지 판단하라. (불가능하다면, 발화 가능한 최소 $I_{inj}$ 를 구하라.)"
        ),
        "answer_md": (
            "(a) $\\tau_m = R_m C_m = (10^8\\,\\Omega)(10^{-9}\\,\\mathrm{F}) = 0.1\\,\\mathrm{s} = \\mathbf{100\\,\\mathrm{ms}}$.\n\n"
            "(b) $V_\\infty = V_{rest} + R_m I_{inj} = -65 + (10^8)(0.5 \\times 10^{-9})\\,\\mathrm{V} "
            "= -65 + 0.05\\,\\mathrm{V} = -65 + 50\\,\\mathrm{mV} = \\mathbf{-15\\,\\mathrm{mV}}$.\n\n"
            "(c) 폐형 해: $V(t) = V_\\infty + (V_0 - V_\\infty) e^{-t/\\tau_m}$.\n"
            "    $V(\\tau_m) = V_\\infty + (V_0 - V_\\infty) e^{-1} = V_\\infty - (V_\\infty - V_0)/e$\n"
            "    $= -15 - (-15 - (-65))/e = -15 - 50/e = -15 - 18.4 = \\mathbf{-33.4\\,\\mathrm{mV}}$.\n"
            "  ⮕ 1 시간 상수 후, $V_\\infty$ 까지의 거리 중 $1 - 1/e \\approx 63.2\\%$ 를 채운다.\n\n"
            "(d) $V_\\infty = -15\\,\\mathrm{mV} > V_{th} = -50\\,\\mathrm{mV}$ 이므로 **발화 가능** (passive 모델 한계 내에서). "
            "발화 임계 도달의 *최소* $I_{inj}$ 는 $V_\\infty = V_{th}$ 일 때:\n"
            "$$I_{min} = \\frac{V_{th} - V_{rest}}{R_m} = \\frac{-50 - (-65)\\,\\mathrm{mV}}{10^8\\,\\Omega} "
            "= \\frac{15\\,\\mathrm{mV}}{100\\,\\mathrm{M}\\Omega} = \\mathbf{0.15\\,\\mathrm{nA}}.$$\n"
            "단, passive 모델은 spike를 직접 생성하지 않는다 — 슬라이드 L7 p.9에서 명시: \"IF 모델은 V가 V_th에 도달하면 "
            "스파이크 발화로 *해석*하고 V_reset 으로 리셋\" — 즉 reset rule 을 추가해야 spike train 이 나온다."
        ),
        "rationale_md": (
            "**흔한 계산 실수 1**: $\\tau_m = R_m C_m$ 에서 단위를 $M\\Omega$ × $nF$ 로 그대로 곱해 \"100 (단위 없음)\" 으로 답하는 것. "
            "$M\\Omega \\cdot nF = 10^6 \\Omega \\cdot 10^{-9} F = 10^{-3} s = 1 ms$ 이므로 100 × $10^{-3}$ s = 100 ms. "
            "단위 변환이 핵심.\n"
            "**흔한 실수 2**: $V_\\infty = R_m I_{inj}$ 만 적고 $V_{rest}$ 더하기를 빠뜨리는 것. 막 방정식의 누설 항이 "
            "$-(V - V_{rest})$ 이므로 정상상태는 $V_{rest}$ 기준으로 변위된다.\n"
            "**연결**: (d)의 발화 임계 계산은 **rheobase** 의 정의 — passive 한계로부터 spike 발화 가능 여부를 정하는 "
            "최소 일정 전류. L7 p.16의 IF 모델 ISI(inter-spike interval) 공식이 $R_m I_e > V_{th} - E_L$ 조건에서만 유효한 "
            "이유와 정확히 같다."
        ),
        "source_citation": {"kind": "slide", "lecture": "L3", "page": 20,
                             "secondary_lecture": "L7", "secondary_page": 16},
        "priority_score": 0.96,
        "info_density": 0.96,
        "mastery_target": "membrane_eq_numerical",
    },

    # ─── 4. PROOF (full derivation, t=0 / t=∞ explicit) ──────────────────
    {
        "topic": "membrane_eq",
        "card_type": "proof",
        "difficulty": 5,
        "bloom": "Evaluate",
        "prompt_md": (
            "**Setup (전면 유도 — 사용자 강조 카드).** 막 방정식\n"
            "$$\\tau_m \\frac{dV}{dt} \\;=\\; -(V - V_{rest}) \\;+\\; R_m I_{inj}, \\qquad V(0) = V_0$$\n"
            "을 폐형(closed-form)으로 풀어 $V(t)$ 를 구한다. 다음을 모두 수행하라:\n\n"
            "(a) 정상상태 (steady state) 값 $V_\\infty$ 를 $dV/dt = 0$ 조건에서 유도하라.\n"
            "(b) $u(t) \\equiv V(t) - V_\\infty$ 변수 변환을 도입하여 ODE를 *동질(homogeneous)* 1차 ODE로 환원하라.\n"
            "(c) (b)의 동질 ODE를 분리변수법(separation of variables)으로 풀어 $u(t)$ 를 얻고, $V(t)$ 로 되돌려 적으라.\n"
            "(d) **$t = 0$ 경계조건**을 적용하여 적분상수를 결정하라. 결과를 다음 형태로 정리하라:\n"
            "    $$V(t) = V_\\infty + (V_0 - V_\\infty)\\, e^{-t/\\tau_m}.$$\n"
            "(e) **차원 검증**: $e^{-t/\\tau_m}$ 의 지수가 무차원임을 확인하고, $V_\\infty - V_{rest}$ 가 mV 단위임을 확인하라.\n"
            "(f) **두 극한 sanity check**: $t = 0$ 와 $t \\to \\infty$ 에서 (d)의 식이 (a)의 정상상태 및 초기 조건과 "
            "    각각 일치함을 보이라."
        ),
        "answer_md": (
            "(a) **정상상태**:\n"
            "$dV/dt = 0$ 대입: $0 = -(V_\\infty - V_{rest}) + R_m I_{inj}$.\n"
            "$$\\boxed{V_\\infty = V_{rest} + R_m I_{inj}.}$$\n\n"
            "(b) **변수 변환 $u = V - V_\\infty$**:\n"
            "$du/dt = dV/dt$ (왜? $V_\\infty$ 가 시간 무관). 막 방정식에 대입:\n"
            "$\\tau_m du/dt = -(V - V_{rest}) + R_m I_{inj} = -[(V - V_\\infty) + (V_\\infty - V_{rest})] + R_m I_{inj}$.\n"
            "(a)에 의해 $V_\\infty - V_{rest} = R_m I_{inj}$ 이므로:\n"
            "$\\tau_m du/dt = -u - R_m I_{inj} + R_m I_{inj} = -u$.\n"
            "$$\\boxed{\\tau_m \\frac{du}{dt} = -u.}$$ (동질 1차 ODE)\n\n"
            "(c) **분리변수**:\n"
            "$\\dfrac{du}{u} = -\\dfrac{dt}{\\tau_m}$. 양변 적분: $\\ln|u| = -t/\\tau_m + C_1$.\n"
            "지수화: $u(t) = A\\, e^{-t/\\tau_m}$, 여기서 $A = \\pm e^{C_1}$ 임의 상수.\n"
            "원래 변수: $V(t) = V_\\infty + A\\, e^{-t/\\tau_m}$.\n\n"
            "(d) **경계조건 $V(0) = V_0$**:\n"
            "$V_0 = V_\\infty + A \\Rightarrow A = V_0 - V_\\infty$.\n"
            "$$\\boxed{V(t) \\;=\\; V_\\infty + (V_0 - V_\\infty)\\, e^{-t/\\tau_m}.}$$\n\n"
            "(e) **차원 검증**:\n"
            "  - $t/\\tau_m$ : $[s]/[s] = $ dimensionless ✓\n"
            "  - $V_\\infty - V_{rest} = R_m I_{inj}$: $[\\Omega][A] = [V]$ ✓\n"
            "  - $V_0 - V_\\infty$: 두 전위의 차, $[V]$ ✓\n\n"
            "(f) **두 극한 sanity check**:\n"
            "  - $t = 0$: $V(0) = V_\\infty + (V_0 - V_\\infty) \\cdot 1 = V_0$ ✓ (초기조건과 일치)\n"
            "  - $t \\to \\infty$: $e^{-t/\\tau_m} \\to 0$, $V(\\infty) = V_\\infty$ ✓ (정상상태와 일치)\n"
            "  - 추가: $V_0 = V_{rest}$ (휴지 상태에서 출발) 인 표준 케이스 →\n"
            "    $V(t) = V_{rest} + R_m I_{inj}(1 - e^{-t/\\tau_m})$ → \"capacitor charging curve\" 표준형."
        ),
        "rationale_md": (
            "**흔한 유도 실수 1**: 변수 변환을 건너뛰고 비동질 ODE를 직접 풀려는 시도 — 가능하지만 적분인자(integrating factor) "
            "법이 더 길다. (b)의 $u = V - V_\\infty$ 트릭은 비동질 항을 *흡수* 하는 핵심.\n"
            "**흔한 실수 2**: 적분상수 $A$ 를 $V_0$ 로 잘못 두는 것. (d) 에서 보았듯 $A = V_0 - V_\\infty$ 가 맞다.\n"
            "**흔한 실수 3**: 부호 오류 — 누설 항의 $-(V - V_{rest})$ 부호가 $V_{rest}$ 쪽으로 끌어당김의 핵심. 부호 뒤집으면 발산해.\n"
            "**핵심 통찰**: 이 유도는 컴퓨터신경과학 전체에서 **재사용** 된다 — \n"
            "(i) HH 게이팅 변수 $n(t)$ 의 닫힌 해 (L5 p.22): $n(t) = n_\\infty + (n_0 - n_\\infty)e^{-t/\\tau_n}$ 동일한 구조.\n"
            "(ii) Cable equation 정상상태 (L6 p.10): 시간이 사라지면 ODE가 ODE in $x$ 가 되어 같은 패턴.\n"
            "(iii) Leaky IF (L7 p.13–15): 이 유도가 ISI 공식의 출발점.\n"
            "**원전 인용**: Lapicque(1907)가 막 자체를 RC 회로로 처음 모형화 — 슬라이드 L7 p.9이 명시. "
            "그 100년 뒤 우리는 같은 식을 사용한다."
        ),
        "source_citation": {"kind": "slide", "lecture": "L3", "page": 23,
                             "secondary_lecture": "L7", "secondary_page": 13,
                             "primary": "Lapicque 1907 (membrane RC model)"},
        "priority_score": 1.0,
        "info_density": 1.0,
        "mastery_target": "membrane_eq_full_derivation",
    },

    # ─── 5. PROOF — t=0+ behavior in detail ───────────────────────────────
    {
        "topic": "membrane_eq",
        "card_type": "proof",
        "difficulty": 4,
        "bloom": "Analyze",
        "prompt_md": (
            "**Setup (t=0+ 미시 거동).** 막 방정식 해 $V(t) = V_\\infty + (V_0 - V_\\infty)e^{-t/\\tau_m}$ "
            "에 대해 step input $I_{inj}(t) = I_0 \\cdot \\Theta(t)$ ($\\Theta$ Heaviside) 를 가정하고 $V_0 = V_{rest}$ 라 하자.\n\n"
            "(a) $V(t)$ 의 1차 Taylor 전개를 $t = 0$ 주변에서 2차 항까지 구하라.\n"
            "(b) $dV/dt|_{t=0^+}$ 가 $I_0/C_m$ 임을 (a)로부터 직접 보이고, 이것이 슬라이드 L3 p.20 의 정량적 진술 "
            "\"1 nA → 1 mV/ms for $C_m = 1$ nF\" 와 일관됨을 확인하라.\n"
            "(c) (a)의 2차 항이 음수임을 확인하고, 그 물리적 의미 — '왜 $V$ 가 곡선이 위로 오목해지는가' — 를 "
            "누설 전류의 *피드백* 관점에서 설명하라.\n"
            "(d) **$V$ 자체는 $t = 0$ 에서 연속이지만 $dV/dt$ 는 점프한다** 는 사실을 보이라. (Hint: $t = 0^-$ 와 "
            "$t = 0^+$ 에서 각각 $dV/dt$ 를 계산.)"
        ),
        "answer_md": (
            "(a) **Taylor 전개**:\n"
            "$V(t) = V_\\infty + (V_0 - V_\\infty)(1 - t/\\tau_m + (t/\\tau_m)^2/2 - \\cdots)$.\n"
            "$V_0 = V_{rest}$ 이므로 $V_0 - V_\\infty = -R_m I_0$ (음수). 정리:\n"
            "$$V(t) \\approx V_{rest} + R_m I_0 \\cdot [t/\\tau_m - (t/\\tau_m)^2/2] + O(t^3).$$\n\n"
            "(b) **초기 기울기**:\n"
            "$dV/dt|_{t=0^+} = R_m I_0 / \\tau_m = R_m I_0 / (R_m C_m) = I_0 / C_m$.\n"
            "수치: $I_0 = 1\\,\\mathrm{nA}, C_m = 1\\,\\mathrm{nF}$ → $1\\,\\mathrm{nA}/1\\,\\mathrm{nF} = 1\\,\\mathrm{V/s} "
            "= 1\\,\\mathrm{mV/ms}$ ✓ (슬라이드 L3 p.20의 진술과 정확히 일치).\n"
            "이 결과는 *$R_m$ 에 무관*한 점이 핵심: $t=0+$ 순간엔 capacitor만 작동, 누설은 아직 안 켜짐.\n\n"
            "(c) **2차 항의 부호와 해석**:\n"
            "$R_m I_0 > 0$ 이므로 2차 항 $-(R_m I_0)(t/\\tau_m)^2/2$ 은 **음수**.\n"
            "물리적 의미: 시간이 지나면서 $V$ 가 $V_{rest}$ 위로 올라감 → 누설 전류 $(V - V_{rest})/R_m$ 가 활성화 → "
            "주입 전류 일부를 상쇄 → 변화율 둔화. 즉, **막의 자기-안정화(self-stabilizing) 피드백**이 활성화되어 "
            "곡선이 위로 오목 (concave-down) 해진다.\n\n"
            "(d) **$V$ 연속성 vs $dV/dt$ 점프**:\n"
            "  - $t = 0^-$: $I_{inj} = 0$ 이고 $V = V_{rest}$ 이므로 $dV/dt = -(V_{rest} - V_{rest})/\\tau_m + 0 = 0$.\n"
            "  - $t = 0^+$: 위에서 $dV/dt = I_0/C_m \\neq 0$.\n"
            "  ⮕ $dV/dt$ 점프 폭 $= I_0 / C_m$, **discontinuous**.\n"
            "  - $V$ 자체: 양쪽 모두 $V_{rest}$ → **continuous**.\n"
            "이는 KCL 의 capacitor 법칙 $I_C = C_m dV/dt$ 의 직접 결과 — capacitor가 *전압*의 즉각 변화는 막지만 "
            "*전류*의 즉각 변화는 흡수한다."
        ),
        "rationale_md": (
            "**흔한 오개념**: \"$V$가 점프한다\" 라고 잘못 그리는 것. 회로에서 capacitor 양단 전압은 항상 연속이다 (charge-conservation). "
            "오직 *기울기* 만 점프할 수 있다.\n"
            "**핵심 통찰**: 1차 RC 응답의 \"capacitor charging\" 곡선이 왜 위로 오목한지를 *피드백 관점*에서 보면, $V$ 증가가 누설을 깨우고 누설이 변화율을 줄이는 자기조절 루프가 보인다. "
            "이 패턴은 **HH 게이팅 변수**(L5 p.22)에서도 동일: $n$ 이 상승하면서 $\\beta_n n$ 항이 커져 자기-안정화.\n"
            "**연결**: (b)의 \"capacitor만 작동, 누설은 아직 안 켜짐\" 직관은 **dendritic compartment 의 capacitive transient** 분석 — "
            "L6 p.4 의 voltage-clamp 실험에서 첫 0.5 ms를 capacitive transient 로 처리해 분리하는 표준 절차의 출발점이다."
        ),
        "source_citation": {"kind": "slide", "lecture": "L3", "page": 19,
                             "secondary_lecture": "L3", "secondary_page": 20},
        "priority_score": 0.95,
        "info_density": 0.95,
        "mastery_target": "membrane_eq_initial_behavior",
    },

    # ─── 6. PROOF — t→∞ + comparison with HH ──────────────────────────────
    {
        "topic": "membrane_eq",
        "card_type": "proof",
        "difficulty": 5,
        "bloom": "Evaluate",
        "prompt_md": (
            "**Setup (정상상태 비교, passive vs active).** Passive 막 방정식의 정상상태는 $V_\\infty = V_{rest} + R_m I_{inj}$ "
            "(슬라이드 L3 p.20-22). 이를 HH 모델 (슬라이드 L5 p.29) 의 정상상태와 비교한다.\n\n"
            "(a) Passive 모델의 $V_\\infty - V_{rest}$ 가 *왜* $I_{inj}$ 에 정확히 선형인지를 1차 ODE 우변에서 직접 읽어내라.\n"
            "(b) HH 모델의 정상상태 막 전류 방정식을 적고, 이를 $V$ 에 대해 풀려면 *어떤 비선형성*이 발생하는지 명시하라.\n"
            "    슬라이드 L5 p.29 의 $i_m$ 표기를 그대로 사용하라.\n"
            "(c) HH 모델에서 $I_{inj}$ 가 매우 작을 때 ($V$ 가 휴지점 근처) passive 모델로 *선형화 (linearize)* 하면 "
            "효과적 $R_m^{eff}$ 는 어떻게 정의되는가? (Hint: 휴지점에서의 conductance 합 $g_{tot} = g_L + \\bar g_K n_\\infty^4 + \\bar g_{Na} m_\\infty^3 h_\\infty$.)\n"
            "(d) (c)의 선형화가 *언제* 깨지는가 — 어느 voltage 영역에서 1차 근사가 더 이상 유효하지 않은지 슬라이드 L5 p.31 의 "
            "행동 (V가 -50mV 부근에서 m이 급격히 1로 향함) 을 들어 설명하라."
        ),
        "answer_md": (
            "(a) **Passive 선형성 출처**: 막 방정식 $\\tau_m dV/dt = -(V - V_{rest}) + R_m I_{inj}$ 에서 우변이 $V$ 에 대해 *1차 다항식* 이고 $I_{inj}$ 에 대해서도 *1차 다항식*. "
            "정상상태 ($dV/dt = 0$): $V_\\infty = V_{rest} + R_m I_{inj}$ — $V_\\infty$ 는 $I_{inj}$ 의 *완전 선형* 함수. "
            "기울기 $R_m$ (input resistance), 절편 $V_{rest}$.\n\n"
            "(b) **HH 모델 정상상태**:\n"
            "$$0 \\;=\\; -[g_L(V - E_L) + \\bar g_K n^4 (V - E_K) + \\bar g_{Na} m^3 h (V - E_{Na})] + I_{inj}.$$\n"
            "비선형성:\n"
            "  - $n_\\infty(V), m_\\infty(V), h_\\infty(V)$ 가 V 에 대해 **sigmoidal** 함수 (Boltzmann form, 슬라이드 p.22).\n"
            "  - 또 $n_\\infty^4$ 등의 *멱함수* 곱.\n"
            "  - 결과: $g_{eff}(V) = g_L + \\bar g_K n_\\infty(V)^4 + \\bar g_{Na} m_\\infty(V)^3 h_\\infty(V)$ 가 $V$ 에 강한 비선형 의존.\n"
            "$V$ 에 대해 이 식은 일반적으로 닫힌 해석해를 갖지 않으며, 수치적 해법 (Newton's method) 또는 graphical (intersection of conductance curve and load line) 분석이 필요.\n\n"
            "(c) **휴지점 선형화**:\n"
            "$V \\approx V_{rest}$ 근방에서 $n_\\infty \\approx n_0, m_\\infty \\approx m_0, h_\\infty \\approx h_0$ 고정으로 보고:\n"
            "$g_{tot} = g_L + \\bar g_K n_0^4 + \\bar g_{Na} m_0^3 h_0$,\n"
            "$$R_m^{eff} = 1 / g_{tot}.$$\n"
            "이 \"input resistance\" 는 휴지 상태에서 측정 가능한 양이며, passive 모델의 $R_m$ 자리를 차지한다. 슬라이드 L3 p.22 의 \"membrane resistance vary considerably... depending on the number, type, and state of ion channels\" 가 정확히 이 점을 가리킴.\n\n"
            "(d) **선형화의 깨짐**:\n"
            "  - **임계 영역 ($V \\to V_{th} \\approx -50\\,\\mathrm{mV}$)**: 슬라이드 L5 p.31 - \"m rises sharply to almost 1\". "
            "    $m_\\infty(V)$ 의 sigmoidal 곡선이 가파른 천이 영역을 통과하면서 $g_{Na}$ 가 quasi-instantaneously 폭발 → "
            "    **양의 피드백** (V↑ → m↑ → I_Na 유입↑ → V↑↑) 발생. 1차 근사 invalid.\n"
            "  - **결과**: $V_\\infty$ 가 $I_{inj}$ 의 매끄러운 함수가 아닌 **bistable / bifurcation** 행동 — \n"
            "    임계 미만은 passive-like 안정화, 임계 초과는 actively spike 발화. \n"
            "  - 이 비선형성이 정확히 \"action potential 의 all-or-none\" 성질의 기원 (슬라이드 p.7-9, p.31).\n\n"
            "정량 비교 (sanity check):\n"
            "  - Passive: $V_\\infty(I) = V_{rest} + R_m I$ — 직선.\n"
            "  - HH (small $I$): 선형 근사로 같지만 $R_m^{eff} < R_m$ (active conductance 들이 leak에 더해짐).\n"
            "  - HH (large $I$, near threshold): nonlinear, eventually periodic spiking — passive 한계 완전 초과."
        ),
        "rationale_md": (
            "**흔한 오개념**: HH 모델에서도 \"input resistance\" 가 의미 있다고 생각하지 않는 것 — 실제로는 휴지 영역의 *선형 근사* 로서 정확히 잘 정의된 양이며, 실험에서도 일상적으로 측정 (slope of V-I curve at rest).\n"
            "**연결**: (d)의 양의 피드백 → 양의 기울기 영역 → bistability — 이것은 **dynamical systems** 관점에서 fold (saddle-node) 분기점. L7 p.25–27 의 Izhikevich 모델은 정확히 이 분기 구조를 2-ODE 로 *압축* 한 것.\n"
            "**연결 2**: passive 와 HH 의 차이는 \"membrane time constant 가 voltage-independent vs voltage-dependent\" 라는 한 줄로 표현 가능: passive 는 $\\tau_m$ 일정, HH 는 $\\tau_m^{eff}(V)$ 가 V 의 함수이며 천이 영역에서 매우 짧아짐 (sub-ms).\n"
            "**원전**: Hodgkin & Huxley 1952 J Physiol 117:500 — Section 1 \"Membrane current\" 이 정확히 이 비교를 수행."
        ),
        "source_citation": {"kind": "slide", "lecture": "L3", "page": 22,
                             "secondary_lecture": "L5", "secondary_page": 29,
                             "primary": "Hodgkin & Huxley 1952 J Physiol 117:500"},
        "priority_score": 0.97,
        "info_density": 1.0,
        "mastery_target": "membrane_eq_steady_state_HH_link",
    },
]


def insert_cards(items):
    conn = acquire()
    try:
        with conn.cursor() as cur:
            ids = []
            for it in items:
                cur.execute("""
                    INSERT INTO question_bank
                      (topic, card_type, difficulty, bloom, prompt_md, answer_md,
                       rationale_md, source_citation, priority_score, info_density,
                       mastery_target, status)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,'active')
                    ON CONFLICT DO NOTHING
                    RETURNING id
                """, (
                    it["topic"], it["card_type"], it["difficulty"], it["bloom"],
                    it["prompt_md"], it["answer_md"], it["rationale_md"],
                    json.dumps(it["source_citation"], ensure_ascii=False),
                    it["priority_score"], it["info_density"],
                    it.get("mastery_target"),
                ))
                row = cur.fetchone()
                if row:
                    ids.append(row[0])
            for bid in ids:
                cur.execute("""
                    INSERT INTO srs_cards (user_id, bank_item_id, state)
                    VALUES (1,%s,'New')
                    ON CONFLICT (user_id, bank_item_id) DO NOTHING
                """, (bid,))
        conn.commit()
        return ids
    finally:
        release(conn)


if __name__ == "__main__":
    ids = insert_cards(SEEDS)
    print(f"inserted {len(ids)} membrane-equation cards: ids {ids}")
    print("topics × types added:")
    for it in SEEDS:
        print(f"  {it['topic']:>14} {it['card_type']:>11} d={it['difficulty']} → "
              f"[Slide {it['source_citation']['lecture']} p.{it['source_citation']['page']}]")
