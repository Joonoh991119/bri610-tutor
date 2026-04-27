"""
backend.agents.walkthrough — Walkthrough domain model.

State-machine-driven guided derivation sessions.  Three pre-authored walkthroughs:
  1. HH gating ODE          (6 steps)
  2. Cable equation λ        (5 steps)
  3. Nernst equilibrium      (4 steps)

Each step is either:
  explain       — tutor narrates / sets context
  socratic      — student must answer a conceptual probe
  derive_attempt — student submits LaTeX derivation (accepts_latex=True)
  hint          — hint surfaced after first failure on a derive step
  reveal        — full solution shown after 3 failures (mode-lock exit)
  checkpoint    — brief Socratic check before advancing

Narration register: graduate-seminar Korean with English technical terms inline.
Citation style: [Slide L# p#] hardcoded per step (slides-only mandate).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional


# ────────────────────────────────────────────────────────────────
# Core types
# ────────────────────────────────────────────────────────────────

StepKind = Literal["explain", "socratic", "derive_attempt", "hint", "reveal", "checkpoint"]


@dataclass
class WalkthroughStep:
    step_id: int
    kind: StepKind
    prompt_md: str           # KaTeX-ready markdown, bilingual KO+EN
    expected_concept: str    # keyword for misconception detection
    accepts_latex: bool = False
    expected_lhs: str = ""   # LHS for SymPy verifier (if accepts_latex)
    expected_rhs: str = ""   # RHS for SymPy verifier
    slide_refs: list[str] = field(default_factory=list)  # e.g. ["L5 p12"]
    hint_md: str = ""        # surfaced after 1st failure on derive_attempt


@dataclass
class WalkthroughMeta:
    walkthrough_id: str
    title: str           # English
    title_ko: str        # Korean
    lecture_id: str      # e.g. "L5"
    topic: str           # e.g. "HH_gating_ODE"
    num_steps: int
    steps: list[WalkthroughStep]


@dataclass
class WalkthroughState:
    session_id: str
    walkthrough_id: str
    lecture_id: str
    topic: str
    current_step: int          # 0-indexed into WalkthroughMeta.steps
    attempts: int              # attempts on current step
    mode_lock_failures: int    # cumulative failures triggering mode-lock
    history: list[dict] = field(default_factory=list)  # [{role, content}]
    is_complete: bool = False


# ────────────────────────────────────────────────────────────────
# Walkthrough 1 — Hodgkin-Huxley Gating ODE (6 steps)
# Based on: [Slide L5 p8–p24], [Slide L6 p3–p11]
# Covers: ODE setup → variable identification → n_∞ derivation
#         → τ_n derivation → voltage-clamp connection
# ────────────────────────────────────────────────────────────────

_HH_STEPS: list[WalkthroughStep] = [
    WalkthroughStep(
        step_id=1,
        kind="explain",
        prompt_md="""## Hodgkin-Huxley Gating ODE — 개요 (Overview)

**[Slide L5 p8, L6 p3]**

우리는 오늘 Hodgkin & Huxley(1952)가 K⁺ 채널 게이팅을 기술하기 위해 도입한 **activation variable $n$** 의 역학 방정식을 처음부터 유도합니다.

> *We will derive from first principles the kinetic ODE governing the K⁺ channel gating variable $n$, as introduced by Hodgkin & Huxley (1952) — arguably the most influential set of equations in computational neuroscience.*

**핵심 질문**: 이온 채널 게이팅(ion channel gating)은 왜 단순한 대수 관계(algebraic relation)가 아니라 미분방정식(ODE)으로 기술되어야 하는가?

채널 개폐는 전압-의존 속도 상수(voltage-dependent rate constants) $\\alpha_n(V)$와 $\\beta_n(V)$를 갖는 **2-state Markov process**로 모형화됩니다:

$$\\text{closed} \\xrightarrow{\\alpha_n(V)} \\text{open} \\xrightarrow{\\beta_n(V)} \\text{closed}$$

이 도식으로부터 ODE를 직접 세우는 것이 다음 단계의 목표입니다.""",
        expected_concept="markov_gating",
        slide_refs=["L5 p8", "L6 p3"],
    ),

    WalkthroughStep(
        step_id=2,
        kind="socratic",
        prompt_md="""## Step 2 — ODE 세우기 (Writing the ODE)

**[Slide L5 p10]**

위 2-state Markov 도식에서 $n$ = (열린 상태의 게이트 분율, fraction of open gates)이라 할 때, **$dn/dt$를 $\\alpha_n$, $\\beta_n$, $n$ 으로 표현하시오.**

답하기 전에 아래 세 가지를 먼저 기록하세요:
- 내가 이해한 바 (what I understand)
- 내가 시도한 것 (what I tried)
- 막힌 부분 (where I'm stuck)

> *Tip: The rate of change of the open fraction equals the rate of transition into the open state minus the rate out of it. Think in terms of probability flux.*

**예상 오류 (common error):** 많은 학생이 $dn/dt = \\alpha_n - \\beta_n$ 으로 쓰지만, 이는 $n$의 농도 의존성을 무시한 것임에 주의하라.""",
        expected_concept="dn_dt_ODE",
        accepts_latex=True,
        expected_lhs="dn/dt",
        expected_rhs="alpha_n*(1-n) - beta_n*n",
        slide_refs=["L5 p10"],
        hint_md="""**힌트 (Hint):** 열린 상태로의 유입 플럭스(flux into open)는 닫힌 분율 $(1-n)$에 $\\alpha_n$을 곱한 것, 유출 플럭스(flux out of open)는 $n$에 $\\beta_n$을 곱한 것입니다:

$$\\frac{dn}{dt} = \\alpha_n(V)(1-n) - \\beta_n(V)n$$

이 형태가 **mass-action kinetics**의 직접적 적용임을 확인하세요.""",
    ),

    WalkthroughStep(
        step_id=3,
        kind="derive_attempt",
        prompt_md="""## Step 3 — 정상 상태 값 $n_\\infty$ 유도 (Deriving Steady-State $n_\\infty$)

**[Slide L5 p12]**

ODE:
$$\\frac{dn}{dt} = \\alpha_n(V)(1-n) - \\beta_n(V)n$$

**정상 상태(steady state)**: $dn/dt = 0$ 을 놓을 때 $n_\\infty(V)$를 $\\alpha_n$, $\\beta_n$ 으로 표현하시오.

> *This is the asymptotic value that $n$ would reach if voltage were held constant indefinitely — directly measurable in a voltage-clamp experiment.*

답을 $n_\\infty = \\ldots$ 형태의 LaTeX 식으로 제출하세요.

**검증 포인트**: 유도한 식이 다음 두 극한을 만족하는지 확인하세요:
- $\\alpha_n \\gg \\beta_n$ 이면 $n_\\infty \\to 1$ (채널 완전 개방)
- $\\beta_n \\gg \\alpha_n$ 이면 $n_\\infty \\to 0$ (채널 완전 폐쇄)""",
        expected_concept="n_infinity",
        accepts_latex=True,
        expected_lhs="n_inf",
        expected_rhs="alpha_n/(alpha_n + beta_n)",
        slide_refs=["L5 p12"],
        hint_md="""**힌트**: $\\alpha_n(1-n) = \\beta_n n$ 에서 $n$을 분리하면:

$$n_\\infty = \\frac{\\alpha_n}{\\alpha_n + \\beta_n}$$

단위 확인: $\\alpha_n$, $\\beta_n$ 모두 $[\\text{ms}^{-1}]$ 이므로 분수는 무차원(dimensionless), $0 < n_\\infty < 1$ — 올바른 분율.""",
    ),

    WalkthroughStep(
        step_id=4,
        kind="derive_attempt",
        prompt_md="""## Step 4 — 시상수 $\\tau_n$ 유도 (Deriving the Time Constant $\\tau_n$)

**[Slide L5 p13]**

HH 논문은 ODE를 다음 표준 형식으로 재작성합니다:

$$\\frac{dn}{dt} = \\frac{n_\\infty(V) - n}{\\tau_n(V)}$$

**과제**: $\\alpha_n$, $\\beta_n$ 을 이용해 $\\tau_n(V)$를 유도하시오.

단계별로 기술하고, $\\tau_n$의 단위(unit)가 $[\\text{ms}]$ 임을 차원 분석(dimensional analysis)으로 확인하세요.

> *Note: this rearrangement is not just cosmetic — it separates the voltage-dependence of the equilibrium ($n_\\infty$) from the speed of relaxation ($\\tau_n$), enabling independent experimental measurement of each.*

**오개념 경고**: $\\tau_n = 1/\\alpha_n$ 이라고 단순화하는 것은 $\\beta_n \\neq 0$ 인 경우 틀림.""",
        expected_concept="tau_n",
        accepts_latex=True,
        expected_lhs="tau_n",
        expected_rhs="1/(alpha_n + beta_n)",
        slide_refs=["L5 p13"],
        hint_md="""**힌트**: $\\alpha_n(1-n) - \\beta_n n = -(\\alpha_n + \\beta_n)n + \\alpha_n$

이를 $n_\\infty = \\alpha_n/(\\alpha_n+\\beta_n)$ 으로 표현하면:

$$\\frac{dn}{dt} = (\\alpha_n + \\beta_n)\\left(n_\\infty - n\\right) = \\frac{n_\\infty - n}{\\tau_n}$$

따라서 $\\tau_n = \\dfrac{1}{\\alpha_n + \\beta_n}$. 차원: $[\\text{ms}^{-1}]^{-1} = [\\text{ms}]$. ✓""",
    ),

    WalkthroughStep(
        step_id=5,
        kind="checkpoint",
        prompt_md="""## Step 5 — Voltage Clamp 연결 (Connecting to Voltage Clamp)

**[Slide L6 p8–p11]**

Voltage-clamp 실험에서 전압을 $V_\\text{hold}$로 고정하면:

1. 전류 $I_K(t) = \\bar{g}_K \\cdot n(t)^4 \\cdot (V_\\text{hold} - E_K)$ 를 측정합니다.
2. $n(t)$는 위에서 유도한 ODE를 따라 지수적으로 $n_\\infty(V_\\text{hold})$ 로 이완합니다.

**체크포인트 질문**: 다음 두 가지를 간결하게(2–3문장) 설명하시오:

(a) $n(t)$ 의 지수 이완 해(exponential relaxation solution)를 $n_0$, $n_\\infty$, $\\tau_n$ 으로 쓰시오.
(b) HH 논문이 $n^4$ 거듭제곱을 선택한 실험적 근거는 무엇인가? (단순히 "잘 맞아서"가 아닌 물리적 해석)

> *This checkpoint tests whether you can connect the ODE machinery to the observable: the sigmoid K⁺ current turn-on, whose sigmoidicity is explained by the $n^4$ factor.*""",
        expected_concept="voltage_clamp_n4",
        slide_refs=["L6 p8", "L6 p11"],
    ),

    WalkthroughStep(
        step_id=6,
        kind="explain",
        prompt_md="""## Step 6 — 종합 및 시사점 (Synthesis & Implications)

**[Slide L6 p11, L5 p24]**

**완주를 축하합니다.** 이 워크스루에서 우리는 다음을 직접 유도했습니다:

$$\\boxed{\\frac{dn}{dt} = \\alpha_n(V)(1-n) - \\beta_n(V)n = \\frac{n_\\infty(V) - n}{\\tau_n(V)}}$$

**핵심 시사점 (key insights)**:

1. **가역성(reversibility)**: $\\alpha_n$, $\\beta_n$ 이 모두 양수이므로 게이팅은 항상 가역적 — 비평형 열역학적 구동(non-equilibrium thermodynamic drive)은 이온 농도 기울기에서 옴.
2. **분리 가능성(separability)**: $n_\\infty$와 $\\tau_n$의 전압 의존성이 분리 가능 → voltage-step 실험으로 각각 독립적으로 피팅 가능.
3. **$n^4$ 의 의미**: 4개의 독립적인 게이팅 입자(gating particle)의 곱 → single-channel patch-clamp 데이터에서 직접 검증됨 (Conti & Neher 1980).
4. **한계(limitation)**: HH는 phenomenological — 채널 구조(channel structure)나 활성화 메커니즘을 설명하지 않음. Markov chain 확장(multi-state Markov, Zagotta-Hoshi-Aldrich 1994)이 이를 보완.

다음 단계: Cable Equation 워크스루로 HH를 공간적으로 확장하세요.""",
        expected_concept="HH_synthesis",
        slide_refs=["L6 p11", "L5 p24"],
    ),
]

WALKTHROUGH_HH = WalkthroughMeta(
    walkthrough_id="HH_gating_ODE",
    title="Hodgkin-Huxley Gating ODE",
    title_ko="Hodgkin-Huxley 게이팅 ODE 유도",
    lecture_id="L5",
    topic="HH_gating_ODE",
    num_steps=len(_HH_STEPS),
    steps=_HH_STEPS,
)


# ────────────────────────────────────────────────────────────────
# Walkthrough 2 — Cable Equation Length Constant (5 steps)
# Based on: [Slide L7 p4–p18]
# Covers: cable PDE → steady state → V(x) = V₀e^{-x/λ} → λ derivation
# ────────────────────────────────────────────────────────────────

_CABLE_STEPS: list[WalkthroughStep] = [
    WalkthroughStep(
        step_id=1,
        kind="explain",
        prompt_md="""## Cable Equation — 개요 (Overview)

**[Slide L7 p4]**

Wilfrid Rall(1959)은 수상돌기(dendrite)를 **leaky electrical cable**로 취급하여 전압 분포를 기술하는 편미분방정식(PDE)을 도출했습니다.

> *Rall's cable theory transformed our understanding of how dendrites integrate synaptic inputs — the length constant λ is the single most important parameter governing how far a local depolarization spreads.*

**물리적 직관**: 케이블을 따라 전류가 흐를 때, 일부는 축방향(axial)으로 전달되고 일부는 막을 통해 누출(leak)됩니다. 두 경쟁적 과정의 비율이 **length constant $\\lambda$**를 결정합니다.

핵심 파라미터:
- $r_a$ : 세포질 축방향 저항(axial resistance) $[\\Omega/\\text{cm}]$
- $r_m$ : 막 저항(membrane resistance) $[\\Omega \\cdot \\text{cm}]$
- $c_m$ : 막 정전용량(membrane capacitance) $[\\text{F}/\\text{cm}]$

이 워크스루에서는 정적 해(steady-state solution)에 집중합니다.""",
        expected_concept="cable_physical_intuition",
        slide_refs=["L7 p4"],
    ),

    WalkthroughStep(
        step_id=2,
        kind="derive_attempt",
        prompt_md="""## Step 2 — Cable PDE 세우기 (Deriving the Cable PDE)

**[Slide L7 p7]**

단위 길이당(per unit length) 전류 보존(current conservation)을 적용하면:

$$\\lambda^2 \\frac{\\partial^2 V}{\\partial x^2} - \\tau_m \\frac{\\partial V}{\\partial t} = V$$

여기서 $\\lambda^2 = r_m / r_a$ (단위 확인!), $\\tau_m = r_m c_m$ 입니다.

**과제**: $\\lambda$의 물리적 차원(dimension)을 $r_m$, $r_a$ 의 단위를 이용해 유도하고, $\\lambda$가 $[\\text{cm}]$ 임을 보이시오.

> *Dimensional analysis here is not cosmetic — it confirms that the ratio $r_m/r_a$ has units of length squared, which is physically meaningful as the electrotonic length scale.*

차원 유도 과정을 단계별로 LaTeX로 제출하세요.""",
        expected_concept="lambda_dimension",
        accepts_latex=True,
        expected_lhs="lambda",
        expected_rhs="sqrt(r_m/r_a)",
        slide_refs=["L7 p7"],
        hint_md="""**힌트**: $r_m [\\Omega \\cdot \\text{cm}]$, $r_a [\\Omega/\\text{cm}]$이므로:

$$\\frac{r_m}{r_a} = \\frac{[\\Omega \\cdot \\text{cm}]}{[\\Omega/\\text{cm}]} = [\\text{cm}^2]$$

따라서 $\\lambda = \\sqrt{r_m/r_a}$ 의 단위는 $[\\text{cm}]$. ✓
물리적으로: $\\lambda$가 클수록 막이 누출을 적게 하고 (high $r_m$), 또는 축방향 저항이 낮아 (low $r_a$) 전류가 더 멀리 전달됨.""",
    ),

    WalkthroughStep(
        step_id=3,
        kind="derive_attempt",
        prompt_md="""## Step 3 — 정적 해 $V(x)$ 유도 (Steady-State Solution)

**[Slide L7 p10]**

정적 상태($\\partial V/\\partial t = 0$)에서 cable PDE는:

$$\\lambda^2 \\frac{d^2 V}{dx^2} = V$$

이 ODE는 **변수 분리 없이** 직접 상수 계수 2차 ODE로 풀립니다.

**과제**: 반무한 케이블(semi-infinite cable, $x \\in [0, \\infty)$)에서 경계 조건 $V(0) = V_0$, $V(\\infty) = 0$을 적용하여 해를 구하시오.

특성 방정식(characteristic equation)을 명시하고, 두 근 중 어느 것을 버려야 하는지 그 이유와 함께 서술하세요.

> *The boundary condition at infinity is a physical requirement — voltage cannot blow up arbitrarily far from the injection site.*""",
        expected_concept="cable_exponential_solution",
        accepts_latex=True,
        expected_lhs="V(x)",
        expected_rhs="V_0*exp(-x/lambda)",
        slide_refs=["L7 p10"],
        hint_md="""**힌트**: 특성 방정식 $\\lambda^2 m^2 = 1$ 의 근: $m = \\pm 1/\\lambda$.

일반 해: $V(x) = A e^{x/\\lambda} + B e^{-x/\\lambda}$.

$x \\to \\infty$에서 $V \\to 0$ 이려면 $A = 0$ (발산 항 제거).
$V(0) = V_0$에서 $B = V_0$.

∴ $V(x) = V_0 e^{-x/\\lambda}$ — 전압이 공간적으로 지수 감소.""",
    ),

    WalkthroughStep(
        step_id=4,
        kind="checkpoint",
        prompt_md="""## Step 4 — $\\lambda$의 의미와 실험적 측정 (Significance & Measurement)

**[Slide L7 p14, p18]**

**체크포인트 (2–3문장씩 답하시오)**:

(a) $\\lambda$는 실험적으로 어떻게 측정하는가? (patch-clamp 실험 설계를 구체적으로 기술하라)

(b) 수상돌기(dendrite)의 전형적인 $\\lambda$ 값(order of magnitude)은? 이것이 **synaptic integration**에 어떤 의미를 갖는가?

(c) 단일 구획 모형(single-compartment model)과 달리 cable model이 반드시 필요한 상황은 언제인가? 조건을 하나 이상 제시하라.

> *These questions test whether you can translate the mathematical parameter into experimental observables and biological significance — the hallmark of a mature understanding.*""",
        expected_concept="lambda_experimental",
        slide_refs=["L7 p14", "L7 p18"],
    ),

    WalkthroughStep(
        step_id=5,
        kind="explain",
        prompt_md="""## Step 5 — 종합: Cable Theory의 한계와 확장 (Synthesis & Extensions)

**[Slide L7 p18]**

이 워크스루에서 유도한 핵심 결과:

$$\\boxed{V(x) = V_0 \\, e^{-x/\\lambda}, \\qquad \\lambda = \\sqrt{\\frac{r_m}{r_a}}}$$

**중요 한계 (critical limitations):**

1. **Linear passive cable**: 활성 채널(active channels)이 없다고 가정 — 실제 수상돌기는 HH-type 채널을 포함하여 비선형(nonlinear) 거동을 보임.
2. **Uniform geometry**: 가지(branching)와 테이퍼링(tapering)을 무시 — Rall의 **equivalent cylinder** 조건($d^{3/2}$ 분기 법칙)으로 부분적 해결.
3. **Steady-state only**: 시변(time-varying) 입력에 대해서는 전체 PDE(temporal component)를 풀어야 함.

**연결 (cross-topic links):**
- HH 게이팅: 활성 cable = passive cable + HH 전류 항
- Information theory: $\\lambda$가 작으면 원위 시냅스(distal synapse)의 영향력 감소 → 신호 처리의 공간적 독립성 증가
- Mainen & Sejnowski (1995): 수상돌기 형태가 발화 패턴에 미치는 영향 시뮬레이션

다음: Nernst 워크스루로 전기화학적 평형(electrochemical equilibrium) 유도.""",
        expected_concept="cable_synthesis",
        slide_refs=["L7 p18"],
    ),
]

WALKTHROUGH_CABLE = WalkthroughMeta(
    walkthrough_id="cable_length_constant",
    title="Cable Equation Length Constant",
    title_ko="Cable 방정식 길이 상수 λ 유도",
    lecture_id="L6",
    topic="cable_length_constant",
    num_steps=len(_CABLE_STEPS),
    steps=_CABLE_STEPS,
)


# ────────────────────────────────────────────────────────────────
# Walkthrough 3 — Nernst Equilibrium Potential (4 steps)
# Based on: [Slide L3 p5–p14]
# Covers: Boltzmann → equilibrium condition → solve for E_X
# ────────────────────────────────────────────────────────────────

_NERNST_STEPS: list[WalkthroughStep] = [
    WalkthroughStep(
        step_id=1,
        kind="explain",
        prompt_md="""## Nernst 평형 전위 — 개요 (Overview)

**[Slide L3 p5]**

이온의 평형 전위(equilibrium potential, Nernst potential) $E_X$는 이온 채널의 구동력(driving force)을 결정하는 기본 파라미터입니다.

> *The Nernst equation is not merely a formula to memorize — it is a thermodynamic result that arises from balancing two competing forces: the entropic drive to equalize concentration gradients, and the electrostatic force from the membrane potential.*

**목표**: Boltzmann 통계(Boltzmann statistics)와 전기화학적 퍼텐셜(electrochemical potential) 균형 조건으로부터 Nernst 방정식을 유도합니다.

**물리적 직관**: 농도 기울기(concentration gradient)는 이온을 고농도에서 저농도로 밀어냄(엔트로피 증가). 막전위(membrane potential)는 전하를 반대 방향으로 밀어냄(전기력). 두 힘이 균형을 이룰 때 알짜 플럭스(net flux) = 0 → 이것이 $E_X$.

사용 기호:
- $[X]_o$: 세포 외 이온 농도 (extracellular)
- $[X]_i$: 세포 내 이온 농도 (intracellular)
- $z$: 이온 가수(valence)
- $F$: Faraday 상수, $R$: 기체 상수, $T$: 절대 온도""",
        expected_concept="nernst_physical_setup",
        slide_refs=["L3 p5"],
    ),

    WalkthroughStep(
        step_id=2,
        kind="derive_attempt",
        prompt_md="""## Step 2 — 전기화학적 퍼텐셜 균형 (Electrochemical Potential Balance)

**[Slide L3 p9]**

이온 종 $X$가 막을 통해 자유롭게 투과(freely permeable)될 수 있다고 가정합니다. 평형 조건은 세포 내외 **전기화학 퍼텐셜(electrochemical potential) $\\mu$가 같음**입니다:

$$\\mu_i = \\mu_o$$

전기화학 퍼텐셜은:
$$\\mu = \\mu^0 + RT \\ln[X] + zFV$$

**과제**: 위 평형 조건 $\\mu_i = \\mu_o$ 를 이용하여 $E_X = V_i - V_o$ 를 $[X]_o / [X]_i$, $z$, $R$, $T$, $F$ 로 표현하시오.

각 단계에서 사용한 가정(assumptions)을 명시하고, 상수항 $\\mu^0$가 상쇄되는 이유를 서술하세요.

> *The cancellation of $\\mu^0$ is physically meaningful: the reference chemical potential is the same species on both sides of the membrane.*

LaTeX로 최종 식을 제출하세요.""",
        expected_concept="nernst_derivation",
        accepts_latex=True,
        expected_lhs="E_X",
        expected_rhs="(R*T/(z*F))*log([X]_o/[X]_i)",
        slide_refs=["L3 p9"],
        hint_md="""**힌트**: $\\mu_i = \\mu_o$ 에서:

$$RT \\ln[X]_i + zF V_i = RT \\ln[X]_o + zF V_o$$

재정리:

$$zF(V_i - V_o) = RT(\\ln[X]_o - \\ln[X]_i) = RT \\ln\\frac{[X]_o}{[X]_i}$$

$$E_X = V_i - V_o = \\frac{RT}{zF} \\ln \\frac{[X]_o}{[X]_i}$$

**차원 확인**: $RT$ $[\\text{J/mol}]$, $zF$ $[\\text{C/mol}]$, 따라서 $E_X$ $[\\text{J/C}] = [\\text{V}]$. ✓""",
    ),

    WalkthroughStep(
        step_id=3,
        kind="socratic",
        prompt_md="""## Step 3 — 생리학적 적용 및 GHK와의 비교 (Application & GHK Comparison)

**[Slide L3 p12–p14]**

K⁺에 대한 전형적 값: $[K^+]_i = 140 \\text{ mM}$, $[K^+]_o = 5 \\text{ mM}$, $T = 310 \\text{ K}$.

**질문 (답 전에 세 칸을 채우세요)**:

(a) Nernst 방정식으로 $E_K$ 를 계산하시오. (상온 $RT/F \\approx 25.7 \\text{ mV}$ 사용)
(b) Goldman-Hodgkin-Katz (GHK) 방정식은 Nernst와 어떻게 다른가? GHK가 필요한 상황은 언제인가?
(c) $z = -1$ (Cl⁻)일 때 Nernst 식의 부호가 바뀌는 것의 물리적 의미를 설명하시오.

> *Understanding when Nernst fails (multi-ion non-equilibrium membranes) and where GHK applies is what separates a graduate-level understanding from an undergraduate one.*""",
        expected_concept="nernst_vs_GHK",
        slide_refs=["L3 p12", "L3 p14"],
    ),

    WalkthroughStep(
        step_id=4,
        kind="explain",
        prompt_md="""## Step 4 — 종합: Nernst의 한계와 연결 (Synthesis)

**[Slide L3 p14]**

유도된 핵심 결과:

$$\\boxed{E_X = \\frac{RT}{zF} \\ln \\frac{[X]_o}{[X]_i} \\approx \\frac{58 \\text{ mV}}{z} \\log_{10} \\frac{[X]_o}{[X]_i} \\quad (T = 310 \\text{ K})}$$

**한계 (limitations)**:

1. **단일 이온 평형**: 여러 이온이 동시에 투과할 때 실제 막전위는 GHK 방정식으로 기술 (농도 × 투과도 가중 평균 — 진정한 평형은 아님).
2. **Constant field assumption**: GHK조차 전기장이 막 전체에 걸쳐 균일하다고 가정 — 채널 밀도가 불균일할 때 위반.
3. **활동계수(activity coefficient)**: 고농도에서 이온 간 상호작용 → 몰 농도 대신 활동도(activity) 사용해야 함.

**Cross-topic 연결**:
- HH 모형: 구동력 $(V - E_X)$이 각 이온 전류의 비례 상수 → Nernst가 HH ODE의 입력
- 막전위 안정성: $E_K < E_{Na}$ 의 차이가 활동전위(action potential)를 가능하게 함
- 정보이론: 막전위 범위 ≈ $[-90, +60]$ mV 가 채널의 신호 공간을 정의

**워크스루 완료.**""",
        expected_concept="nernst_synthesis",
        slide_refs=["L3 p14"],
    ),
]

WALKTHROUGH_NERNST = WalkthroughMeta(
    walkthrough_id="Nernst_equilibrium",
    title="Nernst Equilibrium Potential",
    title_ko="Nernst 평형 전위 유도",
    lecture_id="L3",
    topic="Nernst_equilibrium",
    num_steps=len(_NERNST_STEPS),
    steps=_NERNST_STEPS,
)


# ────────────────────────────────────────────────────────────────
# Registry
# ────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────
# Walkthrough 4: Membrane Equation (t=0 / t=∞ derivation)  [user-emphasized]
# ────────────────────────────────────────────────────────────────

_MEMBRANE_STEPS: list[WalkthroughStep] = [
    WalkthroughStep(
        step_id=1, kind="explain",
        prompt_md="""## Step 1 — 막 방정식 유도의 출발점 (Setup)

**[Slide L3 p.19, p.22]**

단일 컴파트먼트 뉴런에 일정 전류 $I_{inj}$ 가 주입될 때 막전위 $V(t)$ 의 시간 거동을 구하는 것이 목표다.

**키르히호프 전류 법칙(KCL)**: 막을 가로지르는 전체 전류는 (i) capacitive current $I_C = C_m\\,dV/dt$, (ii) 누설 전류 $I_L = (V - V_{rest})/R_m$, (iii) 외부 주입 전류 $I_{inj}$. 평형:

$$\\boxed{C_m \\frac{dV}{dt} \\;=\\; -\\frac{V - V_{rest}}{R_m} \\;+\\; I_{inj}.}$$

양변에 $R_m$ 을 곱하고 $\\tau_m = R_m C_m$ 도입:

$$\\tau_m \\frac{dV}{dt} \\;=\\; -(V - V_{rest}) \\;+\\; R_m I_{inj}.$$

> *오늘 우리는 이 ODE를 풀어 $V(t) = V_\\infty + (V_0 - V_\\infty) e^{-t/\\tau_m}$ 형태의 폐형 해를 얻을 것이다.*

**핵심 질문**: 두 극한 $t = 0$ 과 $t \\to \\infty$ 에서 어떤 일이 벌어지는가?""",
        expected_concept="membrane_eq_setup",
        slide_refs=["L3 p19", "L3 p22"],
    ),

    WalkthroughStep(
        step_id=2, kind="derive_attempt",
        prompt_md="""## Step 2 — 정상상태 $V_\\infty$ 유도 (t → ∞)

$t \\to \\infty$ 에서 $dV/dt \\to 0$ (정의에 의해 정상상태). 이 조건을 ODE에 대입하여 $V_\\infty$ 를 $V_{rest}, R_m, I_{inj}$ 만의 함수로 쓰시오.

**제출 형식**: LaTeX 수식, $V_\\infty = ?$ 형태.""",
        expected_concept="steady_state",
        accepts_latex=True,
        expected_lhs=r"V_\infty",
        expected_rhs=r"V_{rest} + R_m I_{inj}",
        hint_md="""**Hint**: $\\tau_m \\cdot 0 = -(V_\\infty - V_{rest}) + R_m I_{inj}$. 좌변이 0이므로 우변도 0. $V_\\infty$ 에 대해 정리하라.""",
        slide_refs=["L3 p20"],
    ),

    WalkthroughStep(
        step_id=3, kind="derive_attempt",
        prompt_md="""## Step 3 — 변수 변환 $u = V - V_\\infty$ 로 동질 ODE 만들기

$V_\\infty$ 가 시간에 무관함을 사용하면 $du/dt = dV/dt$. ODE에 $V = u + V_\\infty$ 를 대입하고 Step 2 결과 ($V_\\infty - V_{rest} = R_m I_{inj}$) 를 사용해 모든 비동질 항을 소거하라.

**기대 결과**: $\\tau_m \\, du/dt = ?$ (오직 $u$ 와 상수만 등장)""",
        expected_concept="homogeneous_ode",
        accepts_latex=True,
        expected_lhs=r"\tau_m \frac{du}{dt}",
        expected_rhs=r"-u",
        hint_md="""**Hint**: $\\tau_m du/dt = -(u + V_\\infty - V_{rest}) + R_m I_{inj}$. 괄호를 풀고 Step 2의 $V_\\infty - V_{rest} = R_m I_{inj}$ 를 대입하면 비동질 항이 정확히 상쇄.""",
        slide_refs=["L3 p20"],
    ),

    WalkthroughStep(
        step_id=4, kind="derive_attempt",
        prompt_md="""## Step 4 — 분리변수법으로 $u(t)$ 풀기

ODE $\\tau_m \\, du/dt = -u$ 를 분리변수법(separation of variables)으로 풀어 $u(t)$ 를 얻으시오. 적분상수는 $A$ 로 두라.

**기대 결과**: $u(t) = ?$ (지수 함수)""",
        expected_concept="exp_decay",
        accepts_latex=True,
        expected_lhs=r"u(t)",
        expected_rhs=r"A e^{-t/\tau_m}",
        hint_md="""**Hint**: $du/u = -dt/\\tau_m$. 양변 적분 후 지수화. 결과는 $u(t) = A e^{-t/\\tau_m}$.""",
        slide_refs=["L3 p20"],
    ),

    WalkthroughStep(
        step_id=5, kind="derive_attempt",
        prompt_md="""## Step 5 — $t = 0$ 경계조건으로 적분상수 결정

$V(0) = V_0$ (initial condition) → $u(0) = V_0 - V_\\infty$. Step 4의 $u(t) = A e^{-t/\\tau_m}$ 와 결합하여 $A$ 를 결정하고, 최종 $V(t)$ 를 적으시오.

**기대 결과**: $V(t) = V_\\infty + (V_0 - V_\\infty) e^{-t/\\tau_m}$.""",
        expected_concept="closed_form",
        accepts_latex=True,
        expected_lhs=r"V(t)",
        expected_rhs=r"V_\infty + (V_0 - V_\infty) e^{-t/\tau_m}",
        hint_md="""**Hint**: $u(0) = A \\cdot 1 = A$. 따라서 $A = V_0 - V_\\infty$. $V = u + V_\\infty$ 로 되돌리면 끝.""",
        slide_refs=["L3 p20"],
    ),

    WalkthroughStep(
        step_id=6, kind="explain",
        prompt_md="""## Step 6 — 두 극한 sanity check + HH로의 연결

**최종 결과**:
$$\\boxed{V(t) \\;=\\; V_\\infty + (V_0 - V_\\infty) e^{-t/\\tau_m}, \\quad V_\\infty = V_{rest} + R_m I_{inj}.}$$

**Sanity check**:
- $t = 0$: $V(0) = V_\\infty + (V_0 - V_\\infty) \\cdot 1 = V_0$ ✓ (초기조건)
- $t \\to \\infty$: $e^{-t/\\tau_m} \\to 0$, $V(\\infty) = V_\\infty$ ✓ (정상상태)
- $V_0 = V_{rest}$ (휴지 상태에서 출발) → $V(t) = V_{rest} + R_m I_{inj}(1 - e^{-t/\\tau_m})$ — \"capacitor charging\" 표준형.

**차원 검증**:
- $t/\\tau_m$: $[\\mathrm{s}]/[\\mathrm{s}] = $ dimensionless ✓
- $R_m I_{inj}$: $[\\Omega][A] = [V]$ ✓

**HH 모델로의 연결**:
이 유도 패턴은 **HH 게이팅 변수** $n(t), m(t), h(t)$ (슬라이드 L5 p.22) 에서 정확히 동일하게 재등장:
$$n(t) = n_\\infty(V) + (n_0 - n_\\infty(V)) e^{-t/\\tau_n(V)}.$$
차이점: HH 의 $n_\\infty$ 와 $\\tau_n$ 은 **voltage-dependent** ($V$ 의 함수). 따라서 ODE 가 nonlinear coupled system 이 되고, 닫힌 해는 일반적으로 없다 — 수치 해법 필요.

**또 다른 연결**: Cable 방정식 (L6 p.10)의 정상상태 $V(x) = V_0 e^{-x/\\lambda}$ 도 같은 분리변수 패턴, 다만 시간 → 공간 좌표.

**원전 인용**: Lapicque 1907 (현 leaky-integrate-and-fire 의 기원), 슬라이드 L7 p.9.

**워크스루 완료.** 이제 이 유도를 1분 안에 백지에서 재생산할 수 있는지 자기 점검하라.""",
        expected_concept="membrane_synthesis",
        slide_refs=["L3 p20", "L5 p22"],
    ),
]

WALKTHROUGH_MEMBRANE = WalkthroughMeta(
    walkthrough_id="membrane_equation",
    title="Membrane Equation (t=0 / t=∞ derivation)",
    title_ko="막 방정식 유도 (t=0, t=∞ 경계 + 폐형 해)",
    lecture_id="L3",
    topic="membrane_equation",
    num_steps=len(_MEMBRANE_STEPS),
    steps=_MEMBRANE_STEPS,
)


WALKTHROUGHS: dict[str, WalkthroughMeta] = {
    wt.walkthrough_id: wt
    for wt in [WALKTHROUGH_MEMBRANE, WALKTHROUGH_HH, WALKTHROUGH_CABLE, WALKTHROUGH_NERNST]
}


def get_walkthrough(walkthrough_id: str) -> Optional[WalkthroughMeta]:
    return WALKTHROUGHS.get(walkthrough_id)


def list_walkthroughs() -> list[dict]:
    return [
        {
            "id": wt.walkthrough_id,
            "title": wt.title,
            "title_ko": wt.title_ko,
            "lecture": wt.lecture_id,
            "topic": wt.topic,
            "num_steps": wt.num_steps,
        }
        for wt in WALKTHROUGHS.values()
    ]
