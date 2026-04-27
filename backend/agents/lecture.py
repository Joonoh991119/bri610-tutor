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
    micro_question: Optional[str] = None  # for intuition_check kind only


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
                    "Lipid bilayer 가 절연체이자 capacitor 라는 사실에서 출발하라. *전기*적 신호가 *화학*적 막에서 어떻게 가능한가를 핵심 질문으로 제시."),
        LectureStep(2, "expose", "막전위 정의와 측정",
                    ["L3 p.14", "L3 p.15", "L3 p.16"],
                    "$V_m = V_{int} - V_{ext}$ 정의의 부호 규약을 설명. 휴지 막전위가 음수인 이유 (= $E_K$ 가 음수)."),
        LectureStep(3, "intuition_check", "Capacitor 직관 점검",
                    ["L3 p.17", "L3 p.18"],
                    "$Q = CV$ 가 막 양쪽 전하 분리에 어떻게 적용되는지 설명하게 한다. *왜* bilayer 두께가 작으면 specific capacitance 가 큰가?",
                    micro_question="만약 막 두께가 절반이 되면 $C_m$ 은 어떻게 변하는가? (정답: 2배 — $C \\propto 1/d$)."),
        LectureStep(4, "derive", "$I_C = C \\, dV/dt$ 1줄 유도",
                    ["L3 p.19", "L3 p.20"],
                    "$Q = CV$ 의 양변 시간 미분. *왜* $dV/dt = 0$ 이면 capacitive current 도 0 인지를 직관적으로 설명. 슬라이드 p.20의 1 nA → 1 mV/ms 정량 결과를 인용."),
        LectureStep(5, "derive", "막 방정식 KCL 유도",
                    ["L3 p.20", "L3 p.22", "L3 p.23"],
                    "$I_{inj} = I_C + I_R$ 의 KCL 평형으로부터 $\\tau_m \\, dV/dt = -(V - V_{rest}) + R_m I_{inj}$ 도출. 시상수 $\\tau_m = R_m C_m$ 이 *면적 무관* 한 수학적 이유 (specific R/C 둘 다 $A$ 의존성이 상쇄)."),
        LectureStep(6, "expose", "Nernst 평형 — Boltzmann 관점",
                    ["L3 p.24", "L3 p.27", "L3 p.28", "L3 p.29"],
                    "농도 기울기와 전기장의 *반대 방향* 균형. 화학 퍼텐셜 $\\mu = \\mu^0 + RT \\ln C + zF \\phi$ 양쪽 동일 조건에서 $E_X = (RT/zF) \\ln([X]_o/[X]_i)$ 도출. $E_K = -83$, $E_{Na} = +58$ mV 표준값."),
        LectureStep(7, "expose", "GHK — 다이온 일반화의 *log-domain* 가중평균",
                    ["L3 p.30", "L3 p.31"],
                    "왜 GHK 는 \"산술 평균\" 이 아닌 *log-도메인 가중평균* 인가? 휴지 상태에서 $p_K \\gg p_{Na}, p_{Cl}$ 이므로 $V_m \\approx E_K$ 인 이유."),
        LectureStep(8, "connect", "L4–L5 로의 연결",
                    ["L3 p.32", "L3 p.33"],
                    "이 강의의 모든 식이 *passive* (R, C 둘 다 시간 독립). L5 HH 모델은 동일 식에 단지 $R_m$ 을 voltage-time 함수로 만든다. 막 방정식의 *구조* 는 그대로 유지됨을 강조."),
    ],
)

_L5_PLAN = LecturePlan(
    lecture_id="L5",
    title_ko="L5 — 활동전위 + Hodgkin-Huxley",
    objective="HH 4-ODE 시스템을 KCL+ohmic+gating Markov 로부터 구성하고 voltage-clamp 데이터의 의미를 이해한다.",
    steps=[
        LectureStep(1, "expose", "왜 HH 가 컴퓨터신경과학의 출발점인가",
                    ["L5 p.2", "L5 p.3"],
                    "1952년 H&H 논문 (J Physiol 117:500) 의 4-Nobel-Prize 식 — *수치 시뮬레이션* 으로 신경 행동을 예측한 최초의 모델. p.4의 4-ODE 풀세트를 *먼저* 보여주고 이후 단계에서 *어떻게 조립되는가* 를 보여줌."),
        LectureStep(2, "expose", "AP 의 양·음 피드백 사이클",
                    ["L5 p.7", "L5 p.8", "L5 p.9"],
                    "Na 채널 양의 피드백 (V↑→Na 열림→Na 유입→V↑↑) 과 K 채널 지연된 음의 피드백 (V↑→K 열림→K 유출→V↓). all-or-none 의 동역학적 기원."),
        LectureStep(3, "expose", "Persistent vs Transient 채널",
                    ["L5 p.13", "L5 p.14", "L5 p.15", "L5 p.16"],
                    "K 채널 = persistent (한 종류 게이트만), Na 채널 = transient (활성 m + 비활성 h 두 게이트). gating 의 분자적 기원."),
        LectureStep(4, "derive", "$P_K = n^4$ 로부터 4-subunit 가정",
                    ["L5 p.17", "L5 p.18", "L5 p.19"],
                    "K 채널이 4 동일 서브유닛 ⇒ 4 독립 게이트의 동시 열림 확률 = $n^4$. *binomial 가정* 이 들어가는 단계를 명시. 슬라이드 \"k = 4 is consistent with the four-subunit structure\" 인용."),
        LectureStep(5, "derive", "Channel kinetics ODE $dn/dt = \\alpha_n(1-n) - \\beta_n n$",
                    ["L5 p.20", "L5 p.21", "L5 p.22"],
                    "2-state Markov chain (closed↔open) 의 master equation. 정상상태 $n_\\infty = \\alpha/(\\alpha+\\beta)$ 와 시상수 $\\tau_n = 1/(\\alpha+\\beta)$ 도출. 폐형 해 $n(t) = n_\\infty + (n_0-n_\\infty)e^{-t/\\tau_n}$ — L3 막방정식 해와 *동일 패턴*."),
        LectureStep(6, "intuition_check", "$m^3 h$ vs $n^4$ — 왜 다른 형태?",
                    ["L5 p.25", "L5 p.26", "L5 p.27"],
                    "Na 의 두 게이트 (활성 m, 비활성 h) 가 *모두* 열려야 통과. Activation × inactivation 의 multiplicative 형태.",
                    micro_question="m=1, h=0 인 voltage 영역에서 Na current 는? (정답: 0 — h 가 닫힘)."),
        LectureStep(7, "expose", "전체 HH 식 + 시뮬레이션",
                    ["L5 p.29", "L5 p.30"],
                    "$i_m = g_L(V-E_L) + \\bar g_K n^4 (V-E_K) + \\bar g_{Na} m^3 h (V-E_{Na})$ 의 의미 — 각 항이 한 종류 ion 의 conductance × driving force. Simulated AP 시각적 인식."),
        LectureStep(8, "connect", "L6 cable 로의 연결",
                    ["L5 p.31", "L5 p.34"],
                    "현재 모델은 *single compartment* (점 뉴런). 실제 axon/dendrite 는 길이가 있어 막전위가 공간적으로 변함 — L6 cable equation 의 출발점."),
    ],
)

_L6_PLAN = LecturePlan(
    lecture_id="L6",
    title_ko="L6 — 케이블 이론과 활동전위 전파",
    objective="Cable equation PDE 를 KCL/Ohm 로부터 유도하고 길이상수 λ 의 의미와 myelinated axon 의 전파 메커니즘을 이해한다.",
    steps=[
        LectureStep(1, "expose", "왜 single-compartment 만으론 부족한가",
                    ["L6 p.2", "L6 p.3"],
                    "실제 dendrite/axon 에서 막전위는 *공간적으로* 변한다. p.3 의 \"thousands of synaptic inputs spread across surface\" 인용."),
        LectureStep(2, "expose", "Passive 막 거동의 공간적 측정",
                    ["L6 p.4", "L6 p.5", "L6 p.6"],
                    "AP 가 axon 을 따라 점진적으로 \"감쇠\" 하는 실험 기록. 거리에 따른 amplitude/timing 변화."),
        LectureStep(3, "derive", "Cable equation PDE 유도",
                    ["L6 p.7", "L6 p.8"],
                    "한 segment $dx$ 에 대한 KCL: 좌·우 segment 에서 들어오는 axial current + capacitive current + leak current = 외부 입력. $\\lambda^2 \\partial^2 V/\\partial x^2 = \\tau \\partial V/\\partial t + (V_m - V_{rest}) - R_m I_{inj}$. *공간 좌표* 가 추가된 것 외엔 막 방정식 구조 그대로."),
        LectureStep(4, "derive", "정상상태 spatial 해 $V(x) = V_0 e^{-x/\\lambda}$",
                    ["L6 p.10", "L6 p.11", "L6 p.12"],
                    "$\\partial V/\\partial t = 0$ 가정 ⇒ 1차 ODE in $x$. 분리변수법으로 $V(x) = V_0 e^{-x/\\lambda}$. $\\lambda = \\sqrt{d R_m / 4 R_i}$ — 굵은 axon 일수록 신호가 멀리 도달."),
        LectureStep(5, "intuition_check", "$\\lambda$ 의 의미 직관 점검",
                    ["L6 p.11"],
                    "$x = \\lambda$ 에서 막전위는 어떤 값으로 감쇠? (37%, 1/e). $x = 2\\lambda$ 에서? (14%).",
                    micro_question="만약 직경 $d$ 가 4배가 되면 $\\lambda$ 는 몇 배? (정답: 2배 — $\\lambda \\propto \\sqrt{d}$)."),
        LectureStep(6, "expose", "Multi-compartment 수치 모델",
                    ["L6 p.13", "L6 p.14"],
                    "Cable PDE 를 closed-form 으로 못 풀 때 (active conductance, 분기, 비균질 $R_m$) 컴파트먼트 단위 ODE 시스템으로 수치 해법. NEURON 등의 시뮬레이터 출발점."),
        LectureStep(7, "expose", "AP 전파 — passive vs active",
                    ["L6 p.15", "L6 p.16", "L6 p.18", "L6 p.19", "L6 p.20"],
                    "Passive cable 은 *diffusive* (확산형 — 신호 거리 / $\\sqrt{t}$ 비례), 따라서 axon 길이를 따라 무한 전파 불가. *Active* regenerative (각 지점에서 voltage-gated Na 가 다시 발동) 만이 신호를 유지. 0.4 m/s 의 측정값."),
        LectureStep(8, "connect", "Myelin + L7/L8 로의 연결",
                    ["L6 p.21", "L6 p.22"],
                    "Myelinated axon: 절연체로 internode 의 capacitance 감소 → $\\tau_m$ 단축 → passive 빠른 전파, Node of Ranvier 에서만 active regeneration → saltatory conduction 50–100 m/s. *Cable theory + AP* 결합 의 정점."),
    ],
)


_L4_PLAN = LecturePlan(
    lecture_id="L4",
    title_ko="L4 — 막 생체물리학 II (Ion Channels, Synaptic Transmission, Circuit Models)",
    objective="L3 의 RC 막을 이온 채널 분류 + 시냅스 입력 까지 확장. 컨덕턴스-기반 시냅스 모델과 alpha-function 직관 + 단일-컴파트먼트 회로 시뮬레이션 절차를 24시간 안에 백지에서 재현 가능하게 한다.",
    steps=[
        LectureStep(1, "expose", "이온 채널의 4가지 기본 분류",
                    ["L4 p.2", "L4 p.3", "L4 p.4"],
                    "Leak / Pump / Voltage-gated / Ligand-gated. 각각의 *기능적 역할* 과 막 방정식의 어느 항에 들어가는지 매핑."),
        LectureStep(2, "expose", "Voltage-gated 채널 — Na, K, Ca",
                    ["L4 p.6", "L4 p.7", "L4 p.8"],
                    "각 이온의 conductance 가 voltage-time 함수임을 강조 — L3 의 *passive* (시간 무관 R) 모델과의 결정적 차이. AP 생성에 필요한 양의 피드백."),
        LectureStep(3, "expose", "Ionotropic vs Metabotropic 시냅스",
                    ["L4 p.11", "L4 p.12", "L4 p.13", "L4 p.14"],
                    "Ionotropic (직접 ion channel) — AMPA/NMDA/GABA-A; ms 시간 척도. Metabotropic (G-protein 매개) — 100ms~s 시간 척도. 각 receptor 가 어떤 ion 의 conductance 를 변화시키는지."),
        LectureStep(4, "intuition_check", "NMDA 의 \"AND-gate\" 직관",
                    ["L4 p.16", "L4 p.21"],
                    "NMDA 가 *동시* 에 (i) glutamate 결합 *그리고* (ii) 막 탈분극 — 두 조건이 *모두* 충족되어야 열림. Mg²⁺ block 이 voltage-dependent.",
                    micro_question="휴지 막전위 -65mV 에서 glutamate 가 NMDA 에 결합하면? (정답: Mg²⁺ block 때문에 거의 안 열림 — 막이 먼저 깨어나야 함. Hebbian \"동시 활성\" 의 분자 기반.)"),
        LectureStep(5, "derive", "Conductance-based synaptic current",
                    ["L4 p.21", "L4 p.27"],
                    "$I_{syn} = g_{syn}(t)(V - E_{syn})$. *Conductance* 가 시간 의존 (시냅스 활성 후 짧게 켜짐), *driving force* 는 막전위 의존. 이중 의존성이 PSP 모양을 만든다."),
        LectureStep(6, "derive", "Alpha function 시냅스 모델",
                    ["L4 p.27", "L4 p.28"],
                    "$g_{syn}(t) = g_{max} (t/\\tau_s) e^{1 - t/\\tau_s} \\cdot \\Theta(t)$. 정규화 상수 $e \\cdot t/\\tau_s$ 의 의미. $t_{peak} = \\tau_s$ 에서 최대값 도달. AMPA 시상수 $\\tau_s \\approx 2-5$ ms, NMDA $\\tau_s \\approx 100-200$ ms."),
        LectureStep(7, "expose", "EPSP/IPSP 회로적 의미",
                    ["L4 p.29", "L4 p.30"],
                    "EPSP: $E_{syn} > V_{rest}$ (예: AMPA $E_{rev} \\approx 0$ mV) → 막전위를 끌어올림. IPSP: $E_{syn} < V_{rest}$ (예: GABA $E_{Cl} \\approx -75$ mV) → 막전위를 끌어내림. *Driving force 의 부호* 가 EPSP/IPSP 결정."),
        LectureStep(8, "connect", "L5 HH로의 연결",
                    ["L4 p.31"],
                    "L4 의 시냅스 입력 $I_{syn}$ 이 L5 HH 식의 $I_{inj}$ 자리에 들어감. 통합된 단일 뉴런 모델: $C_m dV/dt = -I_{ion,HH} - I_{syn} + I_{ext}$. 시뮬레이션 시 시간 단계는 $\\tau_s$ 보다 작아야 정확."),
    ],
)

_L7_PLAN = LecturePlan(
    lecture_id="L7",
    title_ko="L7 — 다양한 단일 뉴런 계산 모델 (Different Types of Models)",
    objective="HH / LIF / Izhikevich 세 모델의 *trade-off* 를 이해. 어떤 질문에 어떤 모델을 쓸지 결정 가능하도록.",
    steps=[
        LectureStep(1, "expose", "왜 단순화하는가",
                    ["L7 p.6", "L7 p.7", "L7 p.8"],
                    "HH 모델은 뉴런당 수십 개 ODE — *대규모 네트워크* 시뮬레이션 비용 폭증. Spike *timing* 만 중요하다면 더 단순한 모델로 충분."),
        LectureStep(2, "derive", "LIF 모델 — sub-threshold HH 의 단순화",
                    ["L7 p.10", "L7 p.11", "L7 p.12"],
                    "Sub-threshold 에서 active conductance 항 무시 → $C_m dV/dt = -g_L(V-E_L) + I_{ext}$ (= L3 의 막 방정식). Threshold 도달 시 *수동으로* spike 발화 + reset. \"Integrate and Fire\" 의 의미."),
        LectureStep(3, "derive", "ISI 폐형 해 (constant input)",
                    ["L7 p.13", "L7 p.14", "L7 p.15", "L7 p.16"],
                    "$\\tau_m \\, dV/dt = -(V-E_L) + R_m I_{ext}$ 의 폐형 해를 V_th 까지 적분 → ISI 공식 $t_{isi} = \\tau_m \\ln \\frac{R_m I - (V_{reset} - E_L)}{R_m I - (V_{th} - E_L)}$. *rheobase* $R_m I_{rh} = V_{th} - E_L$."),
        LectureStep(4, "intuition_check", "Spike-rate adaptation 의 메커니즘",
                    ["L7 p.18", "L7 p.19"],
                    "지속적 입력에 대해 firing rate 가 *시간이 지나면서 감소* — 흔한 cortical 행동. 메커니즘은 spike-triggered K-current $g_{sra}$ 의 누적.",
                    micro_question="만약 모든 뉴런이 adaptation 없으면 (LIF 만)? — 신호의 *contrast* 변화에 둔감, 반복 자극에 동일하게 반응. Adaptation 이 있어야 *변화* 검출 가능."),
        LectureStep(5, "derive", "Adaptive LIF (aLIF) 식",
                    ["L7 p.23", "L7 p.24"],
                    "$\\tau_m dV/dt = -(V-E_L) - R_m g_{sra}(V-E_K) + R_m I_{ext}$. 추가 ODE $\\tau_{sra} dg_{sra}/dt = -g_{sra}$, spike 발화 시 $g_{sra} \\mathrel{+}= \\Delta g$. K-conductance 의 누적이 firing rate 를 끌어내림."),
        LectureStep(6, "expose", "Izhikevich 2-ODE 절충",
                    ["L7 p.25", "L7 p.26", "L7 p.27"],
                    "$dV/dt = 0.04 V^2 + 5V + 140 - u + I$, $du/dt = a(bV - u)$. *비선형* 첫 식 (HH 의 양의 피드백 흉내) + *선형* 회복 식. 4 매개변수 (a/b/c/d) 만 조정해 cortical 뉴런 20여 종 firing pattern 재현."),
        LectureStep(7, "expose", "DA 뉴런 사례 — 다중 컴파트먼트 HH",
                    ["L7 p.37", "L7 p.38", "L7 p.39", "L7 p.40"],
                    "Komendantov 2004: 흑질 DA 뉴런의 burst-vs-tonic 전환. GABA-A 가 단일-spike 모드를, SK channel 이 burst 모드를 결정. *NEURON* 시뮬레이터로 다중 컴파트먼트 HH."),
        LectureStep(8, "connect", "어떤 모델을 언제 쓰는가",
                    ["L7 p.45"],
                    "단일 뉴런의 ion-channel 메커니즘 연구 → HH; 네트워크 spike 통계 → LIF 또는 Izhikevich; 행동-수준 신경회로 모델 → mean-field rate model. 질문 ↔ 모델의 매핑."),
    ],
)

_L8_PLAN = LecturePlan(
    lecture_id="L8",
    title_ko="L8 — 신경 부호 (Neural Codes)",
    objective="Rate / Temporal / Phase / Synchrony 4 가지 부호의 정의 + 한계 + multiplexed 동시 사용 의 의미를 이해.",
    steps=[
        LectureStep(1, "expose", "왜 부호가 문제인가",
                    ["L8 p.5", "L8 p.6", "L8 p.7", "L8 p.8"],
                    "뉴런 spike 의 *어떤 측면* 이 정보를 운반하는가? Rate? Timing? Phase? Synchrony? 동시에 여러 부호가 사용된다면?"),
        LectureStep(2, "expose", "Rate code — Adrian 1926",
                    ["L8 p.16", "L8 p.17", "L8 p.18", "L8 p.19"],
                    "근방추(stretch receptor) 의 firing rate 가 *근육 늘어남* 정도에 비례. V1 simple cell 의 *tuning curve* — orientation 에 따라 firing rate 변화. 80년 사용된 표준 부호."),
        LectureStep(3, "intuition_check", "3 가지 \"rate\" 의 차이",
                    ["L8 p.20", "L8 p.21", "L8 p.22", "L8 p.23"],
                    "(i) time-average over 100ms window, (ii) trial-average across repetitions (PSTH), (iii) population-average across neurons. 각각 다른 가정.",
                    micro_question="개구리가 파리를 잡을 때 \"trial-average\" rate를 사용하는가? (정답: 안 됨 — 행동 응답 시간 (~100ms) 이 너무 짧고 시행이 1번뿐)."),
        LectureStep(4, "expose", "Time-to-first-spike — Thorpe 1996",
                    ["L8 p.32", "L8 p.33", "L8 p.34"],
                    "사람이 시각 장면을 ~150ms 안에 분류 — 신경 단위 처리 시간을 고려하면 *각 뉴런이 최대 1 spike* 만 기여. 첫 spike 의 *시간* 자체가 정보."),
        LectureStep(5, "expose", "Phase code — O'Keefe & Recce 1993",
                    ["L8 p.35", "L8 p.36", "L8 p.37", "L8 p.38", "L8 p.39"],
                    "해마 place cell 의 phase precession: 동물이 place field 에 진입 → 통과 → 빠져나옴 동안 spike 의 theta 위상이 *점진적으로 빠른 위상* 으로 이동. *공간 위치* 가 *위상* 으로 부호화."),
        LectureStep(6, "expose", "Synchrony code + binding problem",
                    ["L8 p.47", "L8 p.50", "L8 p.51"],
                    "여러 뉴런이 *동시* 에 spike → 하나의 *통합된* 객체 표현. \"붉은 사각형\" 의 색-모양 binding 의 후보. Singer 의 40Hz gamma 가설."),
        LectureStep(7, "expose", "Multiplexed code — Panzeri 2015",
                    ["L8 p.61", "L8 p.62"],
                    "Rate + Temporal + Synchrony 를 *동시에* 사용 — 같은 spike train 이 여러 부호 채널 운반. Barrel cortex 자극 실험에서 L4 vs L5/6 layer-specific multiplexed code."),
        LectureStep(8, "connect", "Mainen & Sejnowski 1995 — 부호 신뢰성",
                    ["L8 p.74"],
                    "동일 *fluctuating* 자극 입력 시 spike timing 이 ms-precision 으로 재현 가능 — temporal code 가 가능함을 *증명*. DC 자극 시는 spike timing 이 random — 부호 가능성은 *입력의 통계* 에 따라."),
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
    return {
        "step_id": step.step_id,
        "step_num": step_num,
        "total_steps": len(plan.steps),
        "kind": step.kind,
        "title_ko": step.title_ko,
        "slide_refs": step.slide_refs,
        "instruction_md": step.instruction_md,
        "micro_question": step.micro_question,
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

    # Build a Tutor prompt that explicitly references the slide refs and
    # instruction. The harness routes this through DeepSeek v4 pro by default.
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
