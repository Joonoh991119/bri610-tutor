"""
Lecture (강의) mode agent — Opus-designed.

The lecture mode walks a student through a single BRI610 lecture in 6–8 narrated
steps, alternating between (i) concept exposition (slide-grounded), (ii) quick
intuition checks (Socratic mini-questions), (iii) one full derivation, and
(iv) connection to adjacent lectures.

Distinct from the existing Walkthrough mode, which targets ONE specific
derivation (HH gating ODE, cable λ, Nernst, membrane equation). Lecture mode
takes a WHOLE lecture (L3, L4, L5, ...) and gives a high-level guided tour
designed for first-encounter or refresher reading.

State persistence in-memory (same shape as walkthrough orchestrator). The
narration generation routes through the harness `tutor` role (DeepSeek v4 pro
primary), so all telemetry + cascade fallback applies automatically.
"""
from __future__ import annotations
import logging
import uuid
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────
# Lecture plans — opinionated 6–8 step tours per lecture
# ──────────────────────────────────────────────────────────────────

@dataclass
class LectureStep:
    step_id: int
    kind: str                   # 'expose' | 'intuition_check' | 'derive' | 'connect'
    title_ko: str
    slide_refs: list[str]       # ['L3 p.12', 'L3 p.13', ...]
    instruction_md: str         # what the student should do at this step (Tutor expands)
    micro_question: Optional[str] = None    # for intuition_check kind only — STEM ONLY (no answer leak)
    choices: Optional[list] = None          # MCQ: [{"key":"A","text":"..."}, ...]
    correct_key: Optional[str] = None       # MCQ: "A" | "B" | ...
    rationale: Optional[str] = None         # shown after answer reveal


@dataclass
class LecturePlan:
    lecture_id: str
    title_ko: str
    objective: str              # one-sentence learning objective
    steps: list[LectureStep]


_L3_PLAN = LecturePlan(
    lecture_id="L3",
    title_ko="L3 — 막 생체물리학 I (Membrane Biophysics I)",
    objective="막전위의 기원, 막 RC 회로, Nernst/GHK 평형 — 24시간 안에 백지에서 막 방정식과 Nernst를 유도할 수 있게 한다.",
    steps=[
        LectureStep(1, "expose", "왜 뉴런은 전기적으로 흥미로운가",
                    ["L3 p.12", "L3 p.13"],
                    "**핵심 주장**: lipid bilayer 가 *절연체이자 capacitor* 이기 때문에 신경 신호가 전기적으로 가능하다 [Slide L3 p.12]. (i) 지질이 ion 통과를 막아 전위차를 *유지*하고 (ii) 얇은 두께가 charge 분리를 *저장*한다. *화학적* 막이 어떻게 *전기적* 신호기가 되는가 — 이 강의의 출발 질문 [Slide L3 p.13]."),
        LectureStep(2, "expose", "막전위 정의와 측정",
                    ["L3 p.14", "L3 p.15", "L3 p.16"],
                    "**핵심**: $V_m = V_{int} - V_{ext}$ — *내부 기준* 부호 규약 [Slide L3 p.14]. *V = 단위 전하당 퍼텐셜 에너지* 직관 환기. 휴지 막전위가 −60~−70 mV 로 음수인 이유: K⁺ 가 가장 투과성 높고 $E_K \\approx -83$ mV 이기 때문 — 막이 K⁺ 평형에 가까이 끌려간다 [Slide L3 p.16]."),
        LectureStep(3, "intuition_check", "Capacitor 직관 점검",
                    ["L3 p.17", "L3 p.18"],
                    "**핵심 직관**: 막 = *축전기* (charge 저장 ∝ voltage). $Q = CV$ 가 막 양쪽 ion 분리에 그대로 적용 — 양쪽 ion 농도차가 $Q$, 막전위가 $V$ [Slide L3 p.17]. *왜* 얇을수록 $C$ 가 큰가? 두 도체판이 가까울수록 *같은 voltage* 에 더 많은 charge 가 모이기 때문 ($C \\propto 1/d$).",
                    micro_question="막 두께가 *절반* 이 되면 $C_m$ 은 어떻게 변하는가?",
                    choices=[
                        {"key": "A", "text": "1/2 배"},
                        {"key": "B", "text": "변화 없음"},
                        {"key": "C", "text": "2 배"},
                        {"key": "D", "text": "4 배"},
                    ],
                    correct_key="C",
                    rationale="평행판 축전기 공식 $C = \\varepsilon\\varepsilon_0/d$ — 두께 $d$ 가 분모이므로 *반비례*. 두께 절반 → $C$ *2 배*."),
        LectureStep(4, "derive", "$I_C = C \\, dV/dt$ 1줄 유도",
                    ["L3 p.19", "L3 p.20"],
                    "**목표**: $Q=CV$ → $I_C = C\\,dV/dt$. \n1) $Q = CV$ 양변을 $t$ 로 미분.\n2) $C$ 는 막 기하 (시간 무관) → $dQ/dt = C\\,dV/dt$.\n3) 정의상 $I = dQ/dt$ → $I_C = C\\,dV/dt$.\n*직관*: $V$ 가 변하지 않으면 charge 가 새로 채워지지 않으므로 $I_C = 0$. p.20 정량값 (1 nA → 1 mV/ms) 인용."),
        LectureStep(5, "derive", "막 방정식 KCL 유도",
                    ["L3 p.20", "L3 p.22", "L3 p.23"],
                    "**목표**: KCL → $\\tau_m \\,dV/dt = -(V-V_{rest}) + R_m I_{inj}$.\n*KCL*: 노드의 들어오는 전류 = 나가는 전류 (Kirchhoff). \n1) 막 노드: $I_{inj} = I_C + I_R$.\n2) $I_C = C_m\\,dV/dt$, $I_R = (V-V_{rest})/R_m$ (*g=1/R*, leak conductance).\n3) $R_m$ 곱하면 $\\tau_m = R_m C_m$ 등장.\n*면적 무관*: specific $R\\propto 1/A$, specific $C\\propto A$ → 곱이 상쇄."),
        LectureStep(6, "expose", "Nernst 평형 — Boltzmann 관점",
                    ["L3 p.24", "L3 p.27", "L3 p.28", "L3 p.29"],
                    "**핵심**: 농도 기울기와 전기장이 *반대 방향*으로 균형 → 평형전위 $E_X$. 화학 퍼텐셜 $\\mu = \\mu^0 + RT\\ln C + zF\\phi$ 가 막 양쪽 동일 → $E_X = (RT/zF)\\ln([X]_o/[X]_i)$ [Slide L3 p.28]. 표준값: $E_K = -83$, $E_{Na} = +58$ mV. 이 부호가 휴지전위·AP 의 방향을 결정."),
        LectureStep(7, "expose", "GHK — 다이온 일반화의 *log-domain* 가중평균",
                    ["L3 p.30", "L3 p.31"],
                    "**핵심**: GHK 는 permeability 로 가중된 *log-domain* 평균이지 산술평균이 아니다 — 비선형 ion 흐름을 반영. 휴지 상태 $p_K \\gg p_{Na},p_{Cl}$ → $V_m \\approx E_K$. *왜 log*: $\\ln$ 안에서 $p_X[X]$ 합이 들어가므로 큰 $p$ 가 압도적으로 결과를 끌어간다 [Slide L3 p.31]."),
        LectureStep(8, "connect", "L5 HH 로의 연결",
                    ["L3 p.32", "L3 p.33"],
                    "**핵심**: 이 강의의 모든 식은 *passive* — $R, C$ 가 시간 독립. **유지되는 것**: 막 방정식의 KCL 구조 + $\\tau_m\\,dV/dt$ 형태. **추가되는 것**: L5 HH 에서 $R_m$ 이 voltage-time 함수가 되고 (active conductance), gating ODE 가 붙음. 즉 *구조 동일, 계수가 동역학적으로 진화* — L5 step 5 의 폐형 해도 같은 패턴."),
    ],
)

_L5_PLAN = LecturePlan(
    lecture_id="L5",
    title_ko="L5 — 활동전위 + Hodgkin-Huxley",
    objective="HH 4-ODE 시스템을 KCL+ohmic+gating Markov 로부터 구성하고 voltage-clamp 데이터의 의미를 이해한다.",
    steps=[
        LectureStep(1, "expose", "왜 HH 가 컴퓨터신경과학의 출발점인가",
                    ["L5 p.2", "L5 p.3"],
                    "**핵심**: HH (1952, *J Physiol* 117:500) 는 *수치 시뮬레이션*으로 spike 를 예측한 최초의 정량 모델 — 노벨상 1963. 전략: p.4 의 4-ODE 풀세트를 *먼저* 한 화면에 펼쳐 \"전모\" 를 보여주고, 이후 7 단계로 *어떻게 조립되는가* 를 역추적. L3 막 방정식 + voltage-dependent conductance 의 결합."),
        LectureStep(2, "expose", "AP 의 양·음 피드백 사이클",
                    ["L5 p.7", "L5 p.8", "L5 p.9"],
                    "**핵심**: AP 는 두 피드백 루프의 시간차로 만들어진다. (i) **Na 양의 피드백** — V↑ → Na 채널 열림 → Na⁺ 유입 → V↑↑ (폭주, *driving force* $V-E_{Na}$ 음수일 때 안쪽). (ii) **K 지연 음의 피드백** — V↑ → K 채널 (느리게) 열림 → K⁺ 유출 → V↓. 시간차가 all-or-none 의 *동역학적* 기원."),
        LectureStep(3, "expose", "Persistent vs Transient 채널",
                    ["L5 p.13", "L5 p.14", "L5 p.15", "L5 p.16"],
                    "**핵심**: 채널 종류에 따라 게이트 수가 다르다. K 채널 = *persistent* (한 게이트 n; 열리면 그대로). Na 채널 = *transient* (m = activation 게이트, h = inactivation 게이트; 둘 다 voltage-sensitive). *Gating*: 단백질 구조 변화로 ion pore 가 열리고 닫힘 — 분자적 스위치. 두 게이트 모두 충족 시 통과."),
        LectureStep(4, "derive", "$P_K = n^4$ 로부터 4-subunit 가정",
                    ["L5 p.17", "L5 p.18", "L5 p.19"],
                    "**목표**: 단일 게이트 확률 $n$ → 채널 열림 $P_K = n^4$.\n1) K 채널 = 4 동일 서브유닛, 각각 독립.\n2) *Binomial 독립 가정*: 모든 게이트 동시 열림 = $n \\cdot n \\cdot n \\cdot n$.\n3) 실험적 voltage-clamp 적합 결과 \"k=4 is consistent with the four-subunit structure\" [Slide L5 p.19] — 분자 구조 사후 확인."),
        LectureStep(5, "derive", "Channel kinetics ODE $dn/dt = \\alpha_n(1-n) - \\beta_n n$",
                    ["L5 p.20", "L5 p.21", "L5 p.22"],
                    "**목표**: 2-state Markov → 폐형 해.\n*2-state Markov*: closed ↔ open, rate α (열림), β (닫힘).\n1) Master eq: $dn/dt = \\alpha(1-n) - \\beta n$.\n2) 정상상태 ($dn/dt=0$): $n_\\infty = \\alpha/(\\alpha+\\beta)$, $\\tau_n = 1/(\\alpha+\\beta)$.\n3) *분리변수* (dy/y=adx → ln y=ax+C): $n(t) = n_\\infty + (n_0-n_\\infty)e^{-t/\\tau_n}$.\nL3 막방정식 해와 *동일 지수 패턴*."),
        LectureStep(6, "intuition_check", "$m^3 h$ vs $n^4$ — 왜 다른 형태?",
                    ["L5 p.25", "L5 p.26", "L5 p.27"],
                    "**핵심**: Na 채널은 게이트 종류가 *둘* (activation m, inactivation h) 이라 *곱셈* 형태. m=activation 3개 + h=inactivation 1개 모두 열려야 통과 → $P_{Na} = m^3 h$. K 의 단일 게이트 $n^4$ 와 구조적으로 다름.",
                    micro_question="$m = 1, h = 0$ 인 voltage 영역에서 Na current 의 크기는?",
                    choices=[
                        {"key": "A", "text": "최대 ($m = 1$ 이므로)"},
                        {"key": "B", "text": "0 ($h = 0$ 이 차단)"},
                        {"key": "C", "text": "절반 ($m \\times h$ 평균)"},
                        {"key": "D", "text": "$m^3$ 만큼"},
                    ],
                    correct_key="B",
                    rationale="$P_\\text{Na} = m^3 h = 1 \\cdot 0 = 0$. *Inactivation* gate ($h$) 가 닫히면 *activation* ($m$) 이 100% 라도 채널은 차단된다 — 두 게이트 모두 열려야 함 (AND 조건)."),
        LectureStep(7, "expose", "전체 HH 식 + 시뮬레이션",
                    ["L5 p.29", "L5 p.30"],
                    "**핵심**: $i_m = g_L(V-E_L) + \\bar g_K n^4 (V-E_K) + \\bar g_{Na} m^3 h (V-E_{Na})$ — 각 항 = (현재 conductance) × *driving force* $V - E_X$ (이온의 *움직이고 싶은* 방향). $n,m,h$ 는 각자 ODE 따라 진화. Simulated AP 의 모양: 빠른 상승 (Na) → 정점 → K 가 끌어내림 → AHP."),
        LectureStep(8, "connect", "L6 cable 로의 연결",
                    ["L5 p.31", "L5 p.34"],
                    "**핵심**: 지금 HH 는 *single compartment* (점 뉴런; 공간 무시). **유지되는 것**: KCL + ohmic + gating ODE 의 모든 구조. **추가되는 것**: L6 에서 공간 좌표 $x$ 가 들어가 막전위가 axon 을 따라 변화 → cable equation PDE. 동일 막을 *연결된 RC 회로 사슬*로 본다."),
    ],
)

_L6_PLAN = LecturePlan(
    lecture_id="L6",
    title_ko="L6 — 케이블 이론과 활동전위 전파",
    objective="Cable equation PDE 를 KCL/Ohm 로부터 유도하고 길이상수 λ 의 의미와 myelinated axon 의 전파 메커니즘을 이해한다.",
    steps=[
        LectureStep(1, "expose", "왜 single-compartment 만으론 부족한가",
                    ["L6 p.2", "L6 p.3"],
                    "**핵심**: 실제 dendrite/axon 에서 막전위는 *공간적으로* 변한다 — L5 의 점 뉴런 가정으로는 부족. p.3 \"thousands of synaptic inputs spread across surface\" 인용 — 멀리 떨어진 시냅스 입력은 세포체에 도달하기까지 *감쇠*된다. 공간 좌표 $x$ 가 새 변수."),
        LectureStep(2, "expose", "Passive 막 거동의 공간적 측정",
                    ["L6 p.4", "L6 p.5", "L6 p.6"],
                    "**핵심**: 거리가 멀수록 신호 amplitude 감소 + timing 지연. axon 한 지점에 전류 주입 후 다른 지점에서 측정 → 거리에 따른 *지수적* 공간 감쇠가 관찰됨. 이 감쇠를 정량화한 것이 다음 단계의 cable equation."),
        LectureStep(3, "derive", "Cable equation PDE 유도",
                    ["L6 p.7", "L6 p.8"],
                    "**목표**: 막 방정식을 공간으로 확장 → PDE.\n1) 한 segment $dx$ 에 *KCL*: 좌·우 axial current + capacitive ($C\\partial V/\\partial t$) + leak ($(V-V_{rest})/R_m$) = 외부 $I_{inj}$.\n2) 좌·우 axial = $-\\partial^2 V / \\partial x^2$ (Ohm + 연속).\n3) 결과: $\\lambda^2 \\partial^2 V/\\partial x^2 = \\tau \\partial V/\\partial t + (V_m - V_{rest}) - R_m I_{inj}$. **유지**: L3 RC 구조. **추가**: 공간 2차 미분 항."),
        LectureStep(4, "derive", "정상상태 spatial 해 $V(x) = V_0 e^{-x/\\lambda}$",
                    ["L6 p.10", "L6 p.11", "L6 p.12"],
                    "**목표**: 정상상태 → 공간 지수 감쇠.\n1) $\\partial V/\\partial t = 0$ → 시간 항 사라짐 → 1차 ODE in $x$: $\\lambda^2 V'' = V$.\n2) *분리변수* (또는 특성방정식 $\\lambda^2 r^2 = 1$): $V(x) = V_0 e^{-x/\\lambda}$.\n3) $\\lambda = \\sqrt{d R_m / 4 R_i}$ — 굵은 axon (d↑) → λ↑ → 신호 멀리. 직관: 굵은 케이블이 axial 저항 낮음 → 멀리 흘러감."),
        LectureStep(5, "intuition_check", "$\\lambda$ 의 의미 직관 점검",
                    ["L6 p.11"],
                    "**핵심**: $\\lambda$ = 막전위가 1/e (≈37%) 로 떨어지는 거리. $x=\\lambda$ → 37%, $x=2\\lambda$ → 14%, $x=3\\lambda$ → 5%. 즉 *3λ 너머* 는 신호 거의 사라짐. axon 굵기에 의해 결정.",
                    micro_question="직경 $d$ 가 *4 배* 가 되면 공간상수 $\\lambda$ 는 몇 배가 되는가?",
                    choices=[
                        {"key": "A", "text": "2 배"},
                        {"key": "B", "text": "4 배"},
                        {"key": "C", "text": "16 배"},
                        {"key": "D", "text": "$\\sqrt{2}$ 배"},
                    ],
                    correct_key="A",
                    rationale="$\\lambda = \\sqrt{d R_m / 4 R_i}$ — 직경 *제곱근* 의존. $d$ 가 4배 → $\\sqrt{4} = 2$ 배. 직관: 굵은 호스가 더 멀리 보내지만 *제곱근* 으로만."),
        LectureStep(6, "expose", "Multi-compartment 수치 모델",
                    ["L6 p.13", "L6 p.14"],
                    "**핵심**: 폐형 해가 안 되는 경우 (active conductance, 분기 dendrite, 비균질 $R_m$) → axon 을 작은 RC 회로 *체인* 으로 잘라 ODE 시스템을 수치 해법. NEURON·MOOSE 등 표준 시뮬레이터의 출발점. PDE → 연결된 ODE 들로 환원."),
        LectureStep(7, "expose", "AP 전파 — passive vs active",
                    ["L6 p.15", "L6 p.16", "L6 p.18", "L6 p.19", "L6 p.20"],
                    "**핵심 대비**: passive cable 은 *확산형* (신호 ∝ $1/\\sqrt{t}$ 로 퍼짐) → 긴 axon 끝까지 도달 불가. *Active*: 각 지점에서 voltage-gated Na 채널이 *재점화* → AP 가 *재생성* 되며 같은 amplitude 로 전파. 측정값 0.4 m/s (무수초). L5 HH 가 각 segment 에서 작동 중."),
        LectureStep(8, "connect", "Myelin + L7 로의 연결",
                    ["L6 p.21", "L6 p.22"],
                    "**핵심**: myelin 은 internode 를 절연 → $C_m \\downarrow$, $R_m \\uparrow$ → $\\tau_m \\downarrow$ + $\\lambda \\uparrow$ → passive 전파 빠르고 멀리. Node of Ranvier 에서만 active regeneration → *saltatory conduction* 50–100 m/s. **다음**: L7 에서 이 모든 메커니즘을 *얼마나 단순화*해 네트워크 시뮬레이션에 쓸 것인가 (HH→LIF→Izhikevich 의 trade-off)."),
    ],
)


_L4_PLAN = LecturePlan(
    lecture_id="L4",
    title_ko="L4 — 막 생체물리학 II (Ion Channels, Synaptic Transmission, Circuit Models)",
    objective="L3 의 RC 막을 이온 채널 분류 + 시냅스 입력 까지 확장. 컨덕턴스-기반 시냅스 모델과 alpha-function 직관 + 단일-컴파트먼트 회로 시뮬레이션 절차를 24시간 안에 백지에서 재현 가능하게 한다.",
    steps=[
        LectureStep(1, "expose", "이온 채널의 4가지 기본 분류",
                    ["L4 p.2", "L4 p.3", "L4 p.4"],
                    "**핵심**: 채널 = 4 종류, 각각 막 방정식의 다른 항에 들어감. (i) **Leak** — 항상 열림, $g_L$ 에 기여 (L3 의 $R_m$). (ii) **Pump** — ATP 로 ion 농도차 유지 (Nernst $E_X$ 의 기원). (iii) **Voltage-gated** — V↑ 시 개폐 (HH 의 $g_K, g_{Na}$). (iv) **Ligand-gated** — neurotransmitter 결합 시 개폐 (시냅스). 4 종류가 직렬·병렬로 한 막에 공존."),
        LectureStep(2, "expose", "Voltage-gated 채널 — Na, K, Ca",
                    ["L4 p.6", "L4 p.7", "L4 p.8"],
                    "**핵심**: voltage-gated 의 결정적 특성 — *conductance* (g=1/R, 채널 열림 정도) 가 voltage-time 함수. L3 의 시간 무관 $R$ 가정과 결별. Na: 양의 피드백 (AP 상승), K: 음의 피드백 (재분극), Ca: 시냅스 전 신경전달물질 방출 trigger. 각각 다른 voltage 영역에서 활성."),
        LectureStep(3, "expose", "Ionotropic vs Metabotropic 시냅스",
                    ["L4 p.11", "L4 p.12", "L4 p.13", "L4 p.14"],
                    "**핵심 대비**: ionotropic = 빠른 스위치 (ms), metabotropic = 느린 modulator (100ms–s). Ionotropic — neurotransmitter 가 *직접* 채널 열음 (AMPA→Na/K, NMDA→Na/K/Ca, GABA-A→Cl). Metabotropic — G-protein → 2nd messenger 캐스케이드 → 채널/효소 (GABA-B, mGluR). 시간 척도 차이가 회로 기능을 분리."),
        LectureStep(4, "intuition_check", "NMDA 의 \"AND-gate\" 직관",
                    ["L4 p.16", "L4 p.21"],
                    "**핵심**: NMDA = *동시 만족* 검출기 — (i) glutamate 결합 *그리고* (ii) 막 탈분극 둘 다 필요. Mg²⁺ 가 휴지 막전위에서 채널 입구를 막고 있다가 V↑ 시 빠짐 (voltage-dependent block). 분자 수준의 \"AND gate\" — Hebbian 학습의 물리적 기반.",
                    micro_question="휴지 막전위 $-65$ mV 에서 glutamate *만* NMDA 에 결합하면 무슨 일이 일어나는가?",
                    choices=[
                        {"key": "A", "text": "정상 활성화 — Na, Ca 유입"},
                        {"key": "B", "text": "거의 안 열림 — $\\text{Mg}^{2+}$ block 이 막음"},
                        {"key": "C", "text": "K 채널이 열림"},
                        {"key": "D", "text": "AMPA 가 자동 열림"},
                    ],
                    correct_key="B",
                    rationale="휴지 막전위에서 음전하인 $\\text{Mg}^{2+}$ 이 voltage 에 끌려 NMDA 채널 입구를 막고 있다 (*voltage-dependent block*). 막이 *먼저* AMPA 등으로 탈분극 되어야 $\\text{Mg}^{2+}$ 가 풀려 NMDA 가 활성화 — 이것이 *coincidence detection* (동시 활성 검출) 의 분자 기반."),
        LectureStep(5, "derive", "Conductance-based synaptic current",
                    ["L4 p.21", "L4 p.27"],
                    "**목표**: 시냅스 전류식 = conductance × driving force.\n$I_{syn} = g_{syn}(t)(V - E_{syn})$.\n1) $g_{syn}(t)$: 시냅스 활성 후 일시적으로 켜짐 (시간 의존).\n2) $V - E_{syn}$: *driving force* — 이온이 *움직이고 싶은 방향과 세기*.\n3) 두 인자의 곱이 PSP 의 모양 (시간) 과 부호 (EPSP/IPSP) 둘 다 결정. L5 HH 와 같은 ohmic 형식."),
        LectureStep(6, "derive", "Alpha function 시냅스 모델",
                    ["L4 p.27", "L4 p.28"],
                    "**목표**: $g_{syn}(t)$ 의 표준 함수.\n$g_{syn}(t) = g_{max} (t/\\tau_s)\\, e^{1 - t/\\tau_s} \\cdot \\Theta(t)$.\n1) $\\Theta(t)$: t<0 에서 0 (인과성).\n2) $dg/dt = 0$ 풀면 peak 시각 $t_{peak} = \\tau_s$.\n3) 정규화 인자 $e^1$ 이 peak 값을 정확히 $g_{max}$ 로 만듦.\n시상수: AMPA 2–5 ms, NMDA 100–200 ms — 시간 척도 차이가 NMDA 의 *적분기* 역할을 만듦."),
        LectureStep(7, "expose", "EPSP/IPSP 회로적 의미",
                    ["L4 p.29", "L4 p.30"],
                    "**핵심**: EPSP/IPSP 부호는 *driving force* $V - E_{syn}$ 부호로 결정. EPSP: $E_{syn} > V_{rest}$ (AMPA $E_{rev}\\approx 0$ mV) → 안쪽 양전하 흐름 → 탈분극. IPSP: $E_{syn} < V_{rest}$ (GABA-A $E_{Cl}\\approx -75$ mV) → 바깥쪽 양전하 (또는 안쪽 음전하) → 과분극. 같은 채널이라도 V 에 따라 반전 가능."),
        LectureStep(8, "connect", "L5 HH 로의 연결",
                    ["L4 p.31"],
                    "**핵심**: L4 의 $I_{syn}$ 이 L5 HH 식의 $I_{inj}$ 자리에 들어가 통합 모델 완성. **유지**: $C_m\\,dV/dt$ = (모든 이온 전류 합). **추가**: $C_m dV/dt = -I_{ion,HH} - I_{syn} + I_{ext}$ — voltage-gated + ligand-gated 동시. 시뮬레이션 dt 는 $\\tau_s$ (AMPA 2 ms) 보다 작아야 정확. 단일 뉴런 모델 완성."),
    ],
)

_L7_PLAN = LecturePlan(
    lecture_id="L7",
    title_ko="L7 — 다양한 단일 뉴런 계산 모델 (Different Types of Models)",
    objective="HH / LIF / Izhikevich 세 모델의 *trade-off* 를 이해. 어떤 질문에 어떤 모델을 쓸지 결정 가능하도록.",
    steps=[
        LectureStep(1, "expose", "왜 단순화하는가",
                    ["L7 p.6", "L7 p.7", "L7 p.8"],
                    "**핵심**: HH 는 뉴런당 4 ODE × 수십~수천 컴파트먼트 → 10⁶ 뉴런 네트워크는 비현실적 비용. spike *timing* 만 중요하다면 sub-threshold 동역학을 단순화 가능. 모델 = 답하려는 *질문* 에 맞춰 선택. 분자 메커니즘 → HH; 네트워크 통계 → LIF/Izhikevich."),
        LectureStep(2, "derive", "LIF 모델 — sub-threshold HH 의 단순화",
                    ["L7 p.10", "L7 p.11", "L7 p.12"],
                    "**목표**: HH → LIF 환원.\n1) Sub-threshold 영역에서 voltage-gated 채널 거의 닫힘 → $g_K n^4, g_{Na} m^3 h \\approx 0$.\n2) 남는 항: $C_m dV/dt = -g_L(V-E_L) + I_{ext}$ (=L3 막 방정식 그대로).\n3) Threshold $V_{th}$ 도달 시 *수동* spike 기록 + $V \\to V_{reset}$.\n*Integrate*: 입력을 적분; *Fire*: 임계값 도달 시 발화 + 리셋."),
        LectureStep(3, "derive", "ISI 폐형 해 (constant input)",
                    ["L7 p.13", "L7 p.14", "L7 p.15", "L7 p.16"],
                    "**목표**: 일정 입력 $I_{ext}$ 에서 ISI 공식.\n1) $\\tau_m dV/dt = -(V-E_L) + R_m I_{ext}$.\n2) *분리변수* (dy/y=adx 패턴) → $V(t) = (E_L + R_m I) + (V_{reset} - E_L - R_m I)e^{-t/\\tau_m}$.\n3) $V(t_{isi}) = V_{th}$ 풀면: $t_{isi} = \\tau_m \\ln \\frac{R_m I - (V_{reset}-E_L)}{R_m I - (V_{th}-E_L)}$.\n*Rheobase* $I_{rh}$: 분모 0 → 발화 임계 입력. $I < I_{rh}$ 면 결코 발화 안 함."),
        LectureStep(4, "intuition_check", "Spike-rate adaptation 의 메커니즘",
                    ["L7 p.18", "L7 p.19"],
                    "**핵심**: 지속 입력 시 firing rate 가 *점차 감소* — cortical 뉴런의 보편 행동. 메커니즘: spike 발화 때마다 K-conductance $g_{sra}$ (slow K) 가 *누적* → 막을 끌어내려 다음 발화 어려워짐. *변화 검출기* 역할.",
                    micro_question="*adaptation 이 없는* 순수 LIF 만 있다면 감각 시스템 (시각·청각) 에 어떤 한계가 생기는가?",
                    choices=[
                        {"key": "A", "text": "발화율이 너무 빠르다"},
                        {"key": "B", "text": "AP peak 가 낮아진다"},
                        {"key": "C", "text": "*변화* 를 검출 못 함 — 일정 입력에 일정 발화만"},
                        {"key": "D", "text": "AHP 가 사라진다"},
                    ],
                    correct_key="C",
                    rationale="Adaptation 이 없으면 *지속 자극에도 일정 rate* 로 계속 발화 → 자극의 *시작/끝* 같은 *변화* 신호를 강조 못 함. 시각의 *contrast* 검출, 청각의 *onset* 검출 같은 *transient* 응답은 adaptation 의 K-current 누적이 만든다."),
        LectureStep(5, "derive", "Adaptive LIF (aLIF) 식",
                    ["L7 p.23", "L7 p.24"],
                    "**목표**: LIF + spike-triggered K-current.\n1) Voltage ODE: $\\tau_m dV/dt = -(V-E_L) - R_m g_{sra}(V-E_K) + R_m I_{ext}$ — *driving force* $V-E_K$ 음수 항이 막을 K 평형으로 끌어내림.\n2) Adaptation ODE: $\\tau_{sra} dg_{sra}/dt = -g_{sra}$ — 자연 감쇠.\n3) 발화 시 jump: $g_{sra}\\mathrel{+}=\\Delta g$. 누적된 $g_{sra}$ 가 firing rate 를 점차 끌어내림."),
        LectureStep(6, "expose", "Izhikevich 2-ODE 절충",
                    ["L7 p.25", "L7 p.26", "L7 p.27"],
                    "**핵심**: Izhikevich (2003) 는 LIF 의 단순함 + HH 의 풍부한 패턴을 *2 ODE* 로 절충. $dV/dt = 0.04V^2 + 5V + 140 - u + I$ (비선형 양의 피드백, AP 흉내) + $du/dt = a(bV-u)$ (느린 회복). 4 파라미터 $(a,b,c,d)$ 만 조정해 cortical 20여 종 firing 패턴 (RS, IB, CH, FS, LTS) 재현."),
        LectureStep(7, "expose", "DA 뉴런 사례 — 다중 컴파트먼트 HH",
                    ["L7 p.37", "L7 p.38", "L7 p.39", "L7 p.40"],
                    "**핵심**: Komendantov 2004 — 흑질 DA 뉴런의 burst↔tonic 전환을 다중 컴파트먼트 HH 로 재현. GABA-A 입력 강도가 single-spike 모드 결정, SK 채널 (Ca-activated K) 이 burst 모드 결정. *NEURON* 시뮬레이터 사용. \"메커니즘 질문\" 에는 LIF 로는 부족, HH 가 필요한 사례."),
        LectureStep(8, "connect", "L8 로의 연결 — 어떤 모델을 언제 쓰는가",
                    ["L7 p.45"],
                    "**핵심 매핑**: ion-channel 메커니즘 연구 → HH; 네트워크 spike 통계 → LIF / Izhikevich; 행동 수준 회로 → mean-field rate model. *질문 ↔ 모델* 의 매핑이 모델링의 본질. **다음**: L8 에서 spike 가 *어떤 정보를 운반* 하는가 (rate vs timing vs phase) — 모델 선택은 어떤 부호 가설을 검증할지에 따라 결정됨."),
    ],
)

_L8_PLAN = LecturePlan(
    lecture_id="L8",
    title_ko="L8 — 신경 부호 (Neural Codes)",
    objective="Rate / Temporal / Phase / Synchrony 4 가지 부호의 정의 + 한계 + multiplexed 동시 사용 의 의미를 이해.",
    steps=[
        LectureStep(1, "expose", "왜 부호가 문제인가",
                    ["L8 p.5", "L8 p.6", "L8 p.7", "L8 p.8"],
                    "**핵심 질문**: spike train 의 *어떤 측면* 이 정보를 운반하는가 — rate? timing? phase? synchrony? 동시에 여러 부호가 *multiplex* 될 수도. 이 질문이 결정되어야 (i) 어떤 모델을 쓸지 (L7), (ii) 어떻게 decode 할지 정해진다. 80년의 논쟁."),
        LectureStep(2, "expose", "Rate code — Adrian 1926",
                    ["L8 p.16", "L8 p.17", "L8 p.18", "L8 p.19"],
                    "**핵심**: firing rate ∝ 자극 강도 — 가장 단순한 부호. Adrian 1926: 근방추 (stretch receptor) 의 rate 가 근육 늘어남에 비례 [Slide L8 p.17]. V1 simple cell 의 *tuning curve* — 선호 orientation 에서 rate 최대. 80년 표준 부호 — 단순하고 robust."),
        LectureStep(3, "intuition_check", "3 가지 \"rate\" 의 차이",
                    ["L8 p.20", "L8 p.21", "L8 p.22", "L8 p.23"],
                    "**핵심**: \"firing rate\" 는 셋 중 어느 평균인지에 따라 의미가 다르다. (i) **time-average** — 한 뉴런 한 trial 100 ms 창. (ii) **trial-average** (PSTH) — 같은 자극 N회 반복 평균. (iii) **population-average** — 동시 N 뉴런 평균. 각각 다른 가정·다른 사용 가능 영역.",
                    micro_question="개구리가 *날아오는 파리* 를 잡으려는 *single trial* 의 빠른 행동에서, *trial-average rate* (PSTH) 를 사용 가능한가?",
                    choices=[
                        {"key": "A", "text": "가능 — PSTH 가 표준 도구"},
                        {"key": "B", "text": "불가능 — trial 은 1 회뿐, 행동은 ~100 ms 안에 결정"},
                        {"key": "C", "text": "가능 — 1 회로도 평균 가능"},
                        {"key": "D", "text": "관계 없음"},
                    ],
                    correct_key="B",
                    rationale="*Trial-average* (PSTH) 는 정의상 같은 자극의 *반복 시행* 평균. 단발 행동에선 trial = 1 → 평균 불가능. 빠른 행동은 *single-trial population-average* (동시 활성 뉴런들의 순간 평균) 또는 *temporal code* 에 의존."),
        LectureStep(4, "expose", "Time-to-first-spike — Thorpe 1996",
                    ["L8 p.32", "L8 p.33", "L8 p.34"],
                    "**핵심**: 첫 spike *시각* 자체가 정보를 운반 — rate 평균을 낼 시간 없음. Thorpe 1996: 사람이 자연 장면을 ~150 ms 안에 분류 → 시각 cascade 각 단계 (망막→V1→IT) 에서 뉴런당 평균 1 spike 만 사용 가능. 첫 spike timing 으로 분류 완료."),
        LectureStep(5, "expose", "Phase code — O'Keefe & Recce 1993",
                    ["L8 p.35", "L8 p.36", "L8 p.37", "L8 p.38", "L8 p.39"],
                    "**핵심**: 해마 place cell 의 *phase precession* — 동물이 place field 진입→통과→빠져나옴 동안 spike 가 theta (~8 Hz) 주기 안에서 *점점 이른 위상*으로 이동. **공간 위치 → 위상**으로 부호화. Rate 만 보면 같은 firing 이지만 *언제* 발화하는가가 위치를 알려줌."),
        LectureStep(6, "expose", "Synchrony code + binding problem",
                    ["L8 p.47", "L8 p.50", "L8 p.51"],
                    "**핵심**: 여러 뉴런의 *동시* spike 가 \"하나의 객체\" 를 표시 — *binding problem* 의 한 가설. Singer 의 40 Hz gamma 가설: V1 에서 \"붉은 사각형\" 의 색·모양 뉴런들이 gamma 동기화로 묶임. Rate 가 같아도 synchrony 패턴이 다르면 다른 객체."),
        LectureStep(7, "expose", "Multiplexed code — Panzeri 2015",
                    ["L8 p.61", "L8 p.62"],
                    "**핵심**: 같은 spike train 이 *동시에* 여러 부호 채널을 운반 가능 — rate + temporal + synchrony 가 직교 정보 차원. Panzeri 2015 barrel cortex: L4 vs L5/6 가 layer-specific 한 multiplex 패턴 — rate 는 자극 *세기*, timing 은 자극 *정체성*."),
        LectureStep(8, "connect", "Mainen & Sejnowski 1995 — 부호 신뢰성",
                    ["L8 p.74"],
                    "**핵심**: 부호 가능성은 *입력의 통계*에 따라 결정. Mainen & Sejnowski 1995 — 같은 *fluctuating* (잡음 같은) 자극 반복 시 spike timing 이 ms-precision 으로 재현 → temporal code 가 *가능*. 그러나 DC (일정) 자극에선 spike timing 이 random → rate code 만 가능. 결론: 어떤 부호가 작동하는지는 자극 동역학에 의존 — L7 의 모델 선택과 직결."),
    ],
)


PLANS: dict[str, LecturePlan] = {
    "L3": _L3_PLAN,
    "L4": _L4_PLAN,
    "L5": _L5_PLAN,
    "L6": _L6_PLAN,
    "L7": _L7_PLAN,
    "L8": _L8_PLAN,
}


def get_plan(lecture_id: str) -> Optional[LecturePlan]:
    return PLANS.get(lecture_id)


def list_plans() -> list[dict]:
    return [
        {
            "id": p.lecture_id, "title_ko": p.title_ko,
            "objective": p.objective, "num_steps": len(p.steps),
        }
        for p in PLANS.values()
    ]


# ──────────────────────────────────────────────────────────────────
# Session state (in-memory, parallel to walkthrough state)
# ──────────────────────────────────────────────────────────────────

@dataclass
class LectureSession:
    session_id: str
    lecture_id: str
    user_id: int
    current_step: int = 1
    answers: list[dict] = field(default_factory=list)


_SESSIONS: dict[str, LectureSession] = {}


def start_lecture(lecture_id: str, user_id: int = 1) -> dict:
    plan = get_plan(lecture_id)
    if not plan:
        raise ValueError(f"no lecture plan for {lecture_id}")
    sid = str(uuid.uuid4())
    sess = LectureSession(session_id=sid, lecture_id=lecture_id, user_id=user_id)
    _SESSIONS[sid] = sess
    first = plan.steps[0]
    return {
        "session_id": sid,
        "lecture_id": lecture_id,
        "title_ko": plan.title_ko,
        "objective": plan.objective,
        "total_steps": len(plan.steps),
        "first_step": _step_to_dict(first, plan, 1),
    }


def _step_to_dict(step: LectureStep, plan: LecturePlan, step_num: int) -> dict:
    # Convert slide_refs (e.g., ["L3 p.12", "L3 p.13"]) into clickable image
    # URLs that the frontend can render inline. /api/slide-image/<lecture>/<page>.
    slide_images = []
    for ref in step.slide_refs:
        # parse "L3 p.12" → ("L3", 12)
        parts = ref.replace('p.', '').split()
        if len(parts) == 2:
            try:
                lec, pg = parts[0], int(parts[1])
                slide_images.append({
                    "ref": ref,
                    "lecture": lec,
                    "page": pg,
                    "url": f"/api/slide-image/{lec}/{pg}",
                })
            except ValueError:
                pass

    return {
        "step_id": step.step_id,
        "step_num": step_num,
        "total_steps": len(plan.steps),
        "kind": step.kind,
        "title_ko": step.title_ko,
        "slide_refs": step.slide_refs,
        "slide_images": slide_images,    # NEW: image URLs for inline rendering
        "instruction_md": step.instruction_md,
        "micro_question": step.micro_question,
        "choices": step.choices,         # MCQ format (intuition_check)
        "correct_key": step.correct_key,
        "rationale": step.rationale,
    }


async def narrate_step(session_id: str, *, expand: bool = True) -> dict:
    """
    Produce the actual student-facing narration for the current step. Calls the
    Tutor agent via harness with the step's instruction + slide refs.
    """
    sess = _SESSIONS.get(session_id)
    if not sess:
        raise KeyError(f"no session {session_id}")
    plan = get_plan(sess.lecture_id)
    if not plan:
        raise KeyError(f"no plan for {sess.lecture_id}")
    if sess.current_step > len(plan.steps):
        return {"is_complete": True, "session_id": session_id}

    step = plan.steps[sess.current_step - 1]
    base = _step_to_dict(step, plan, sess.current_step)

    if not expand:
        return base

    # Cache-first: serve pre-generated narration from `lecture_narrations` table
    # (no LLM round-trip → instant response). Table populated by
    # scripts/finalize_db.py on demand.
    try:
        from db_pool import acquire as _acq, release as _rel
        conn = _acq()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT narration_md, model FROM lecture_narrations
                    WHERE lecture=%s AND step_id=%s
                """, (plan.lecture_id, step.step_id))
                row = cur.fetchone()
            if row and row[0]:
                base["narration_md"] = row[0]
                base["route_used"] = (row[1] or "cached") + " (cached)"
                return base
        finally:
            _rel(conn)
    except Exception as e:
        log.warning("narration cache lookup failed: %s", e)

    # Live LLM expansion if no cache hit
    try:
        from harness import call_llm
        slide_list = ", ".join(f"[Slide {r}]" for r in step.slide_refs)
        sys_prompt = (
            "당신은 BRI610 박사과정 강의 가이드입니다. 학생이 이 강의를 24시간 안에 마스터하도록 "
            "각 단계를 박사 세미나 톤으로 풀어 설명합니다. 인용은 슬라이드만 사용하고, 영어 전문용어는 "
            "한국어 본문 안에 괄호로 병기. 학부 친절체 금지."
        )
        user = (
            f"강의 [{plan.title_ko}] 의 step {sess.current_step}/{len(plan.steps)}.\n"
            f"제목: {step.title_ko}\n"
            f"슬라이드 출처 (이 안에서만 인용): {slide_list}\n"
            f"학생에게 줘야 할 내용: {step.instruction_md}\n\n"
            "위 instruction 을 *확장* 하여 학생용 narration 을 작성하시오. 분량 350-600자. "
            "수식은 KaTeX 형식 ($...$ 또는 $$...$$). 첫 줄에 한 줄 핵심 메시지를 굵게 표시. "
            "마지막에 \"다음 단계로 넘어가기 전 잠시 생각해 보자\" 톤의 1문장 transition."
        )
        res = await call_llm(role="tutor", system=sys_prompt, user=user,
                              temperature=0.55, max_tokens=900,
                              cache=True)
        base["narration_md"] = (res.get("text") or "").strip()
        base["route_used"] = res.get("route_used")
    except Exception as e:
        log.warning("lecture narrate fallback: %s", e)
        base["narration_md"] = step.instruction_md  # graceful degrade
        base["route_used"] = "fallback"
    return base


def advance_lecture(session_id: str) -> dict:
    """Move the session pointer forward by 1. Returns updated state stub."""
    sess = _SESSIONS.get(session_id)
    if not sess:
        raise KeyError(f"no session {session_id}")
    plan = get_plan(sess.lecture_id)
    sess.current_step = min(sess.current_step + 1, len(plan.steps) + 1)
    is_complete = sess.current_step > len(plan.steps)
    return {
        "session_id": session_id,
        "current_step": sess.current_step,
        "total_steps": len(plan.steps),
        "is_complete": is_complete,
    }


def submit_intuition(session_id: str, answer_text: str) -> dict:
    """Record student's answer to a micro_question step. Returns echo + index."""
    sess = _SESSIONS.get(session_id)
    if not sess:
        raise KeyError(f"no session {session_id}")
    sess.answers.append({"step": sess.current_step, "answer": answer_text})
    return {"recorded": True, "answers_so_far": len(sess.answers)}
