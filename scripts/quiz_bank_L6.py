#!/usr/bin/env python3
"""L6 quiz bank — Cable Theory & Action Potential Propagation."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from generate_quiz_bank import insert_quiz_items, insert_take_home, DB_DSN
import psycopg2

L6_QUIZ = [
    {
        'position': 1, 'kind': 'mcq', 'difficulty': 2, 'bloom': 'Understand',
        'topic_tag': 'cable-equation',
        'prompt_md': 'Cable equation $\\tau_m \\partial_t V = \\lambda^2 \\partial_x^2 V - V$ 가 L3 의 단일-compartment ODE 와 *결정적으로 다른* 점은?',
        'choices_json': [
            {'key': 'A', 'text': '시간 도함수가 더 들어 있다.', 'correct': False},
            {'key': 'B', 'text': '*공간 도함수* $\\partial_x^2 V$ 항이 추가되어 *위치별* 막전위 차이가 명시적.', 'correct': True},
            {'key': 'C', 'text': '비선형 항이 들어 있다.', 'correct': False},
            {'key': 'D', 'text': '확률적 잡음 항이 있다.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': 'Cable equation 은 *PDE* (partial differential eq) — 시간 + 공간. 단일 컴파트먼트는 *모든 위치 동일 V* 가정. dendrite/axon 처럼 길쭉한 구조에서 위치별 V 가 다르므로 PDE 가 필수. 핵심 매개변수: 시간상수 $\\tau_m$ (충전 속도) + 공간상수 $\\lambda$ (감쇠 거리) [Slide L6 §1].',
        'slide_ref': '[Slide L6 §1]',
    },
    {
        'position': 2, 'kind': 'mcq', 'difficulty': 2, 'bloom': 'Remember',
        'topic_tag': 'lambda',
        'prompt_md': '공간상수 $\\lambda = \\sqrt{d R_m / 4 R_i}$ 에서 $d$ 는 *직경*, $R_m$ 은 specific membrane resistance, $R_i$ 는 cytoplasm 저항도. *직경 2 배* 시 $\\lambda$ 의 변화는?',
        'choices_json': [
            {'key': 'A', 'text': '2 배 증가', 'correct': False},
            {'key': 'B', 'text': '$\\sqrt{2}$ 배 증가 (≈ 1.41 배)', 'correct': True},
            {'key': 'C', 'text': '4 배 증가', 'correct': False},
            {'key': 'D', 'text': '변화 없음', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': '$\\lambda \\propto \\sqrt{d}$ — 직경 제곱근 의존. 굵은 호스가 더 멀리 가는 것과 같은 직관: 단면적 ∝ $d^2$ 가 axial 흐름 용량을 늘리므로, $\\lambda^2 \\propto d$ → $\\lambda \\propto \\sqrt{d}$. 무수초 진화 한계 — 큰 속도 향상을 위해 직경을 *제곱* 으로 키워야 함 [Slide L6 §6].',
        'slide_ref': '[Slide L6 §6]',
    },
    {
        'position': 3, 'kind': 'mcq', 'difficulty': 3, 'bloom': 'Apply',
        'topic_tag': 'spatial-decay',
        'prompt_md': '$\\lambda = 1$ mm 인 dendrite 에서 시냅스 입력이 거리 *2 mm* 떨어진 soma 에 도달할 때, *passive* (subthreshold) 진폭 비율은?',
        'choices_json': [
            {'key': 'A', 'text': '$\\approx 0.50$', 'correct': False},
            {'key': 'B', 'text': '$\\approx 0.37$ (= $1/e$)', 'correct': False},
            {'key': 'C', 'text': '$\\approx 0.14$ (= $1/e^2$)', 'correct': True},
            {'key': 'D', 'text': '$\\approx 0.05$', 'correct': False},
        ],
        'correct_key': 'C',
        'rationale_md': 'Steady state 공간 감쇠: $V(x) = V_0 e^{-x/\\lambda}$. $x = 2\\lambda \\to V/V_0 = e^{-2} \\approx 0.135$. 즉 *14%* 만 도달. 이것이 distal dendrite 시냅스가 *active* dendrite 동역학 (NMDA spike, $Ca^{2+}$ plateau) 없이는 soma 에 거의 영향 못 주는 이유 [Slide L6 §4].',
        'slide_ref': '[Slide L6 §4]',
    },
    {
        'position': 4, 'kind': 'mcq', 'difficulty': 3, 'bloom': 'Analyze',
        'topic_tag': 'myelination',
        'prompt_md': 'Myelin 이 internode 에서 cable 매개변수에 미치는 *동시* 효과로 가장 정확한 것은?',
        'choices_json': [
            {'key': 'A', 'text': '$C_m$ 만 감소.', 'correct': False},
            {'key': 'B', 'text': '$R_m$ 만 증가.', 'correct': False},
            {'key': 'C', 'text': '$C_m$ ↓ ($\\tau_m$ ↓ → 빠른 응답) AND $R_m$ ↑ ($\\lambda$ ↑ → 멀리) 의 *동시 최적화*.', 'correct': True},
            {'key': 'D', 'text': '직경 $d$ 가 변화한다.', 'correct': False},
        ],
        'correct_key': 'C',
        'rationale_md': 'Myelin 은 다층 lipid bilayer → (1) 직렬 capacitor 합쳐서 internode 의 effective $C_m$ 감소, (2) leak 채널 거의 없어 effective $R_m$ 증가. 결과: $\\tau_m = R_m C_m$ 의 변화는 trade-off ($R_m \\uparrow$ 가 우세해 약간 증가) 지만 *λ ∝ √R_m* 가 크게 증가 → 신호가 다음 node 까지 거의 감쇠 없이 도달. 두 변수 *동시* 최적화 → spike 속도 $v \\propto d$ (선형 in d) [Slide L6 §7.1].',
        'slide_ref': '[Slide L6 §7.1]',
    },
    {
        'position': 5, 'kind': 'mcq', 'difficulty': 2, 'bloom': 'Understand',
        'topic_tag': 'saltatory',
        'prompt_md': 'Saltatory conduction 의 *어원과 의미* 로 정확한 것은?',
        'choices_json': [
            {'key': 'A', 'text': '\"saltare\" (라틴어 \"춤추다\") — AP 가 axon 위에서 진동.', 'correct': False},
            {'key': 'B', 'text': '\"saltare\" (라틴어 \"점프\") — AP 가 myelinated internode 를 *건너뛰며* node of Ranvier 에서만 재생.', 'correct': True},
            {'key': 'C', 'text': '\"salt\" (소금) — sodium 을 강조한 명명.', 'correct': False},
            {'key': 'D', 'text': '직진하는 AP.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': 'Latin "saltare" = "점프하다, 도약하다". 무수초 axon 은 *연속* 전파 (모든 위치에서 active 재생), 수초 axon 은 internode 에선 *passive* cable 전파 (감쇠 거의 없음, λ 큼) + node of Ranvier 에서 *active* 재생만 — 즉 AP 가 node 사이를 *점프* 하는 것처럼 보인다. 이것이 *수초 + node 의 진화적 단위* [Slide L6 §7].',
        'slide_ref': '[Slide L6 §7]',
    },
    {
        'position': 6, 'kind': 'mcq', 'difficulty': 4, 'bloom': 'Analyze',
        'topic_tag': 'identifiability',
        'prompt_md': 'Steady-state cable 측정 (e.g. 거리별 입력 저항) 만으로 $R_m, R_i, C_m$ 을 *분리* 할 수 있는가?',
        'choices_json': [
            {'key': 'A', 'text': '셋 다 분리 가능.', 'correct': False},
            {'key': 'B', 'text': '$\\lambda$ 만 결정 — *비율* $R_m/R_i$ 만; $R_m, R_i$ 독립 분리 불가능. $C_m$ 은 *transient* 만으로 가능.', 'correct': True},
            {'key': 'C', 'text': '$R_m, R_i$ 는 분리, $C_m$ 만 분리 불가.', 'correct': False},
            {'key': 'D', 'text': '셋 다 분리 불가능.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': '$\\lambda^2 = d R_m / 4 R_i$ — *비율* 만 결정. $(R_m, R_i)$ 와 $(2 R_m, 2 R_i)$ 는 정확히 동일한 λ. *Steady state* 측정만으론 두 변수의 *조합* 만 식별. $\\tau_m = R_m C_m$ 가 다른 정보 ($C_m$ 식별) 를 제공하지만 여전히 $R_m$ 과의 곱. 결국 *입력 저항* (steady state) + *시간상수* (transient) 두 측정으로 *부분* 분리 가능; *형태 매개변수* ($d$) 가 추가로 알려져야 완전 식별 [Slide L6 §10].',
        'slide_ref': '[Slide L6 §10]',
    },
    {
        'position': 7, 'kind': 'mcq', 'difficulty': 3, 'bloom': 'Apply',
        'topic_tag': 'cable-derivation',
        'prompt_md': 'Cable equation 의 *공간 항* $\\lambda^2 \\partial_x^2 V$ 의 *물리적 의미* 는?',
        'choices_json': [
            {'key': 'A', 'text': 'Capacitor 충전 속도.', 'correct': False},
            {'key': 'B', 'text': 'Axial current 의 *발산* (divergence) — 인접한 두 위치의 V 차이가 어떻게 *지역적으로 V 변화* 를 만드는가.', 'correct': True},
            {'key': 'C', 'text': 'Membrane resistance 의 시간 의존성.', 'correct': False},
            {'key': 'D', 'text': '시냅스 입력의 합산.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': '$I_a(x)$ = axial current. 인접 위치의 차이 = $\\partial I_a/\\partial x$ 가 막을 통해 *방출/흡수* 되는 전류. KCL on infinitesimal slice 와 Ohm ($I_a = -(\\partial V/\\partial x)/r_i$) 결합 → $\\partial V / \\partial t \\propto \\partial^2 V / \\partial x^2$ — *2 차* 공간 미분이 *위치별 충전/방전 속도* 결정 [Slide L6 §3].',
        'slide_ref': '[Slide L6 §3]',
    },
    {
        'position': 8, 'kind': 'mcq', 'difficulty': 4, 'bloom': 'Evaluate',
        'topic_tag': 'common-misconception',
        'prompt_md': '*"$\\lambda$ 가 크면 AP 도 더 빠르게 전파된다"* — 평가하라.',
        'choices_json': [
            {'key': 'A', 'text': '맞다. λ 와 v 는 같은 양.', 'correct': False},
            {'key': 'B', 'text': '*틀리다*. $\\lambda$ 는 *passive* (subthreshold) 감쇠 거리; AP 속도는 *active* 재생 역학에 의존. *둘은 다른 양*. 단, myelin 은 둘 *동시에* 영향을 줘 두 효과가 결합.', 'correct': True},
            {'key': 'C', 'text': '맞다. 신호 전달 거리 = 속도.', 'correct': False},
            {'key': 'D', 'text': '관련 없다.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': '$\\lambda$ 는 *수동* 시상수 — 거리 저항 / 막 누설의 비율. AP 속도 $v$ 는 *active* 재생 (Na/K 채널 동역학 + cable 시상수) 의 함수. 무수초: $v \\propto \\sqrt{d/(\\tau_m r_i)}$. λ 가 직접 등장하지 않음. 그러나 myelin 처럼 $R_m, C_m$ 둘 다 바꾸는 경우 λ 와 v 가 *상관* — 우연이 아니라 같은 변수에 영향을 받기 때문 [Slide L6 §12].',
        'slide_ref': '[Slide L6 §12]',
    },
    # Short-answer
    {
        'position': 9, 'kind': 'short_answer', 'difficulty': 2, 'bloom': 'Remember',
        'topic_tag': 'lambda',
        'prompt_md': '공간상수 $\\lambda$ 의 정의식을 $d, R_m, R_i$ 로 답하라.',
        'correct_text': 'sqrt(d R_m / 4 R_i)',
        'accept_patterns': [
            r'(?i)\\?sqrt\s*\(?\s*d\s*\*?\s*R_?m\s*/\s*\(?\s*4\s*R_?i\s*\)?\s*\)?',
            r'(?i)\\sqrt\{\s*d\s*R_?m\s*/\s*4\s*R_?i\s*\}',
            r'(?i)\(?\s*d\s*R_?m\s*/\s*4\s*R_?i\s*\)?\s*\^\s*\(?\s*1\s*/\s*2\s*\)?',
        ],
        'rationale_md': '$\\lambda = \\sqrt{d R_m / 4 R_i}$. 진동 (cable PDE 의 standard form) 에서 derived. 직경 ↑, $R_m$ ↑ → λ ↑; $R_i$ ↑ → λ ↓. 핵심: 직경에 *제곱근* (linear 아님) 의존.',
        'slide_ref': '[Slide L6 §3]',
    },
    {
        'position': 10, 'kind': 'short_answer', 'difficulty': 2, 'bloom': 'Apply',
        'topic_tag': 'speed-scaling',
        'prompt_md': '*무수초* axon 에서 AP 속도 $v$ 의 직경 $d$ 의존성을 답하라 (스케일링).',
        'correct_text': 'v ∝ √d',
        'accept_patterns': [
            r'(?i)v\s*∝\s*\\?sqrt\s*\(?\s*d\s*\)?',
            r'(?i)v\s*[~∝]\s*d\s*\^?\s*\(?\s*1\s*/\s*2\s*\)?',
            r'(?i)v\s*=?\s*proportional\s+to\s+sqrt',
        ],
        'rationale_md': '$v \\propto \\sqrt{d}$ 무수초; $v \\propto d$ 수초. 차이가 같은 직경에서 myelinated axon 이 한 차수 빠른 이유. 오징어 거대 축삭 ($d \\approx 500\\mu m$) ≈ 25 m/s; 포유류 운동신경 ($d \\approx 20\\mu m$, myelinated) ≈ 120 m/s.',
        'slide_ref': '[Slide L6 §6]',
    },
    {
        'position': 11, 'kind': 'short_answer', 'difficulty': 3, 'bloom': 'Apply',
        'topic_tag': 'spatial-decay-quant',
        'prompt_md': '$V(x) = V_0 e^{-x/\\lambda}$ 일 때, $V/V_0 = 0.5$ 가 되는 거리를 $\\lambda$ 의 배수로 답하라 (정확값).',
        'correct_text': 'ln(2) λ ≈ 0.693 λ',
        'accept_patterns': [
            r'(?i)\\?ln\s*\(?\s*2\s*\)?\s*\\?[*·×]?\s*\\?lambda',
            r'(?i)0[\.,]69\d?\s*\\?lambda',
            r'(?i)\\?lambda\s*\\?[*·×]?\s*\\?ln\s*\(?\s*2\s*\)?',
        ],
        'rationale_md': '$0.5 = e^{-x/\\lambda} \\to x = \\lambda \\ln 2 \\approx 0.693 \\lambda$. *반감 거리* (half-distance). 이는 *e-folding 거리* λ 의 친숙 비교 — 라디오 신호 강도 측정의 dB 와 비슷한 직관.',
        'slide_ref': '[Slide L6 §4]',
    },
    {
        'position': 12, 'kind': 'mcq', 'difficulty': 3, 'bloom': 'Analyze',
        'topic_tag': 'common-misconception',
        'prompt_md': '*"$\\tau_m$ 은 신호가 axon 을 따라 전파되는 시간이다"* — 평가하라.',
        'choices_json': [
            {'key': 'A', 'text': '맞다. τ_m 의 정의가 그것이다.', 'correct': False},
            {'key': 'B', 'text': '*틀리다*. $\\tau_m = R_m C_m$ 은 *한 위치에서* 막이 정상상태 도달까지의 충전 시간 — *공간 전파 시간이 아님*. 전파 속도는 active 동역학에 의존.', 'correct': True},
            {'key': 'C', 'text': '맞다. λ × τ = 전파시간.', 'correct': False},
            {'key': 'D', 'text': '관련 없다.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': 'τ_m 은 *지역적* 시간 척도 — *어떤 한 점* 의 막이 충전되는 데 걸리는 시간. 신호 전파 속도 $v$ 는 별도 매개변수로 *cable diffusion* + *active regeneration* 의 결합. 둘은 *단위* 부터 다르다 (τ: ms / 시간; v: m/s / 거리/시간). 흔한 오해 [Slide L6 §12].',
        'slide_ref': '[Slide L6 §12]',
    },
]


L6_TAKE_HOME = [
    {
        'position': 1, 'kind': 'derivation', 'difficulty': 5, 'max_points': 18, 'expected_time_min': 30,
        'topic_tag': 'cable-derivation',
        'prompt_md': '''Cable equation 을 KCL + Ohm 으로부터 *직접* 유도하라:
(a) (4점) Cylindrical axon 의 *infinitesimal slice* (위치 $x \\to x+dx$, 길이 $dx$) 의 KCL 식. Axial current $I_a(x)$, $I_a(x+dx)$, capacitive 전류 $I_C$, 막 leak 전류 $I_R$, 시냅스 등 외부 전류 $I_\\text{inj}$.
(b) (4점) Ohm: $I_a(x) = -(\\partial V/\\partial x)/r_i$ ($r_i$ = 단위 길이당 cytoplasm 저항). $I_a(x+dx) - I_a(x) \\approx (\\partial I_a / \\partial x) dx$ 로 정리.
(c) (5점) Capacitor 정의 $I_C = c_m \\partial V/\\partial t \\cdot dx$, leak $I_R = (V - V_\\text{rest})/r_m \\cdot dx$. 모두 KCL 에 대입하여 PDE: $$c_m \\partial V/\\partial t = \\frac{1}{r_i} \\partial^2 V / \\partial x^2 - (V - V_\\text{rest})/r_m + i_\\text{inj}.$$
(d) (5점) $\\tau_m \\equiv r_m c_m$, $\\lambda^2 \\equiv r_m / r_i$, $u \\equiv V - V_\\text{rest}$ 로 치환하여 *standard form* $\\tau_m \\partial_t u = \\lambda^2 \\partial_x^2 u - u + r_m i_\\text{inj}$ 를 얻으라.''',
        'model_answer_md': '''(a) **Slice KCL**: 위치 $x \\to x+dx$ 의 cylindrical slice 에 대한 *전류 보존* (전하 보존):
$$I_a(x) - I_a(x+dx) + I_\\text{inj}\\,dx = I_C + I_R$$
(들어오는 axial - 나가는 axial + 외부 주입 = 막을 통해 흘러나가는 capacitive + leak).

(b) **Ohm + Taylor**: $I_a = -\\partial V/(\\partial x \\cdot r_i)$ (음의 부호: 전압이 *감소* 하는 방향으로 흐름). Taylor expansion:
$$I_a(x) - I_a(x+dx) = -\\frac{\\partial I_a}{\\partial x} dx = -\\frac{\\partial}{\\partial x}\\left(-\\frac{1}{r_i}\\frac{\\partial V}{\\partial x}\\right) dx = \\frac{1}{r_i}\\frac{\\partial^2 V}{\\partial x^2} dx.$$

(c) **대입**: $I_C = c_m (\\partial V/\\partial t) dx$, $I_R = (V - V_\\text{rest})/r_m \\cdot dx$. KCL → 양변 $dx$ 약분:
$$c_m \\frac{\\partial V}{\\partial t} = \\frac{1}{r_i} \\frac{\\partial^2 V}{\\partial x^2} - \\frac{V - V_\\text{rest}}{r_m} + i_\\text{inj}.$$

(d) **표준 형식**: 정의 $\\tau_m = r_m c_m$, $\\lambda^2 = r_m / r_i$, $u = V - V_\\text{rest}$. (c) 양변에 $r_m$ 곱하기:
$$r_m c_m \\frac{\\partial V}{\\partial t} = \\frac{r_m}{r_i} \\frac{\\partial^2 V}{\\partial x^2} - (V - V_\\text{rest}) + r_m i_\\text{inj}$$
$$\\boxed{\\tau_m \\frac{\\partial u}{\\partial t} = \\lambda^2 \\frac{\\partial^2 u}{\\partial x^2} - u + r_m i_\\text{inj}}.$$
$u$ 의 시간 변화 = (공간 확산) - (지역 감쇠) + (외부 주입). PDE 의 *parabolic 형태* — diffusion equation 의 변형.''',
        'rubric_md': '''총 18점.
- (a) 4점: KCL 식 정확 (2점) + 모든 항 (axial 들어옴/나감, I_inj, I_C, I_R) 포함 (2점).
- (b) 4점: Ohm $I_a = -(1/r_i)\\partial V/\\partial x$ (1점) + Taylor (1점) + 부호 처리 (1점) + $\\partial^2 V/\\partial x^2$ 도출 (1점).
- (c) 5점: 각 항 정확 (3점) + KCL 대입 (1점) + dx 약분 (1점).
- (d) 5점: τ_m, λ², u 정의 (각 1점, 총 3점) + r_m 곱하기 (1점) + standard form (1점).''',
        'slide_ref': '[Slide L6 §3]',
    },
    {
        'position': 2, 'kind': 'derivation', 'difficulty': 4, 'max_points': 12, 'expected_time_min': 20,
        'topic_tag': 'steady-state-cable',
        'prompt_md': '''Cable equation 의 *steady state* ($\\partial_t V = 0$) 해를 구하라:
(a) (3점) Steady state 에서 PDE 가 *2 차 ODE* $\\lambda^2 d^2 u/dx^2 = u$ 로 환원됨을 보이라.
(b) (4점) 특성방정식과 일반해 $u(x) = A e^{x/\\lambda} + B e^{-x/\\lambda}$ 도출.
(c) (3점) 경계조건 *semi-infinite cable* ($x \\to +\\infty \\Rightarrow u \\to 0$) 적용 → $A = 0$. 즉 $u(x) = u(0) e^{-x/\\lambda}$.
(d) (2점) $u(0) = V_0$ (즉 $x = 0$ 에서 인가된 전압) 일 때, *37%* 도달 거리와 *14%* 거리를 $\\lambda$ 단위로 답하라.''',
        'model_answer_md': '''(a) **Steady state**: $\\partial_t V = 0$. Cable PDE → $0 = \\lambda^2 \\partial^2 u/\\partial x^2 - u$ (외부 주입 없는 영역). 정리: $$\\lambda^2 \\frac{d^2 u}{dx^2} = u.$$

(b) **특성방정식**: 시도해 $u = e^{kx}$ → $\\lambda^2 k^2 = 1$ → $k = \\pm 1/\\lambda$. 일반해 (선형 결합):
$$u(x) = A e^{x/\\lambda} + B e^{-x/\\lambda}.$$

(c) **경계조건**: Semi-infinite cable 에서 $x \\to +\\infty$ 면 $V$ 가 무한히 발산하지 않아야 함 → $u \\to 0$. $A e^{x/\\lambda} \\to \\infty$ 항을 제거: $A = 0$. 남은 해: $u(x) = B e^{-x/\\lambda}$. 두 번째 경계조건 $u(0) = V_0 \\to B = V_0$. **최종**: $$u(x) = V_0 e^{-x/\\lambda}.$$

(d) **거리 계산**: $V/V_0 = 1/e \\approx 0.37$ → $x = \\lambda$. $V/V_0 = 1/e^2 \\approx 0.14$ → $x = 2\\lambda$. 즉 *37% 거리 = λ, 14% 거리 = 2λ*. e-folding 거리 (1/e) 가 λ 의 정의 그 자체.''',
        'rubric_md': '''총 12점.
- (a) 3점: $\\partial_t V = 0$ 적용 (1점) + 외부 항 처리 (1점) + ODE 형태 (1점).
- (b) 4점: 특성방정식 시도해 (1점) + $k = \\pm 1/\\lambda$ (1점) + 일반해 (1점) + 두 항 부호 명확 (1점).
- (c) 3점: 경계조건 명시 (1점) + A = 0 (1점) + B = V_0 도출 (1점).
- (d) 2점: 37% → λ (1점) + 14% → 2λ (1점).''',
        'slide_ref': '[Slide L6 §3]',
    },
    {
        'position': 3, 'kind': 'essay', 'difficulty': 4, 'max_points': 12, 'expected_time_min': 20,
        'topic_tag': 'myelination-evolution',
        'prompt_md': '''Myelin 의 진화적 출현이 *동시* 에 다루는 *3 가지 trade-off* 를 다음 관점에서 분석:
(a) (4점) **속도 vs 직경**: 무수초에서 큰 속도를 위한 *제곱* 비례 비용 (직경) — 척추동물의 brain volume 한계.
(b) (4점) **속도 vs 에너지**: AP 의 metabolic cost 가 직경 + 재생 빈도에 의존 — myelin 이 어떻게 둘을 분리.
(c) (4점) **가소성 vs 안정성**: Myelination 자체가 *학습* 으로 조절될 수 있다는 최근 발견. Oligodendrocyte 의 axon-specific myelination 패턴이 회로 timing 을 fine-tune.''',
        'model_answer_md': '''(a) **속도 vs 직경의 trade-off**: 무수초 axon 에서 $v \\propto \\sqrt{d}$ — 두 배 빠르려면 *4 배* 직경. 오징어 거대 축삭 ($d \\approx 500\\,\\mu m$, $v \\approx 25$ m/s) 은 한 hemisphere 에 수십 개만 패킹 가능. 척추동물 brain 은 ~$10^{11}$ 뉴런 + $10^{14}$ 축삭 — 직경을 늘리는 strategy 는 *원리적으로 불가능*. Myelin 이 도입한 $v \\propto d$ (선형) 으로 *같은 두께* 에서 한 차수 빠른 속도 + 더 많은 축삭 패킹 가능. 척추동물 진화의 *질적 도약* — 후뇌의 복잡성과 연결.

(b) **속도 vs 에너지의 trade-off**: AP 한 번당 metabolic cost = $\\bar g_\\text{Na} \\cdot \\Delta V \\cdot$ axon area $\\cdot$ 채널 밀도. 무수초에서 *모든 위치* 에서 active 재생 → 단위 길이당 ATP 소비량 큼. Myelin 의 internode 는 *passive* 전파 (energy 0) + node 만 active → 단위 길이당 ATP 소비량 *수십~수백 분의 1*. 동시에 감쇠가 적어 (큰 λ) 속도도 빠름 — 즉 *빠르고 + 효율적*. Trade-off 자체를 *우회* 하는 진화 — Pareto frontier 의 새로운 점.

(c) **가소성 vs 안정성**: 최근 연구 (Fields 2008, McKenzie et al. 2014) 가 *myelination 이 학습 조절* 가능함을 증명 — 운동 학습 시 oligodendrocyte 가 axon 을 새로 myelinate 하거나 internode 길이를 조절. 회로 *timing* 이 행동에 결정적인 시스템 (motor coordination, language) 에서 myelin 의 차이가 회로 속도를 fine-tune. **Trade-off**: 안정적 구조여야 일관된 속도 보장 + 가소적이어야 학습 가능. Myelin sheath 는 *분 ~ 시간* 단위로 새로 형성/제거 — 시냅스 가소성 (*ms ~ s*) 보다 *느린 시간 척도* 의 학습 메커니즘. *Multiple sclerosis* (MS) 에서 myelin 면역 파괴 → saltatory 무너짐 → 학습된 timing 회로 손상이 핵심 병리.''',
        'rubric_md': '''총 12점.
- (a) 4점: $v \\propto \\sqrt{d}$ 무수초 한계 (1점) + 큰 직경의 패킹 한계 (1점) + myelin 의 $v \\propto d$ (1점) + 척추동물 진화적 도약 (1점).
- (b) 4점: 무수초의 단위 길이당 high cost (1점) + myelin 의 internode passive (1점) + node 만 active 의 효율 (1점) + Pareto 우회 표현 (1점).
- (c) 4점: 학습 조절 myelination (1점) + oligodendrocyte 의 timing 조절 (1점) + 가소성-안정성 trade-off (1점) + MS 임상 의의 (1점).''',
        'slide_ref': '[Slide L6 §7, §11]',
    },
    {
        'position': 4, 'kind': 'essay', 'difficulty': 3, 'max_points': 10, 'expected_time_min': 15,
        'topic_tag': 'identifiability-cable',
        'prompt_md': '''Cable 매개변수 $R_m, R_i, C_m, d$ 의 *식별성* (identifiability) 을 분석:
(a) (3점) Steady state cable 측정 (입력 저항 $R_\\text{in}$) 만으로 *어떤* 매개변수 조합이 결정되는가?
(b) (4점) Transient (시간상수 $\\tau_m$) 측정을 추가하면 *어떤* 매개변수가 분리되는가?
(c) (3점) $\\lambda$ 측정 (예: 두 점에서 V 진폭 비) 을 추가하면 어떤 정보가 더 추출되는가? 모든 4 매개변수가 분리되는 *최소 측정 set* 은?''',
        'model_answer_md': '''(a) **Steady state $R_\\text{in}$**: Semi-infinite cable 의 입력 저항 $R_\\text{in} = R_m / (A \\cdot \\sqrt{2})$ 형태로 *$R_m / A$ 비율* 만 결정 (A = surface area). 즉 *specific* $R_m$ 과 *형태* (size) 의 곱. Cable 형태 ($d$, 길이) 가 알려지지 않으면 $R_m$ 자체 분리 불가.

(b) **+ τ_m**: $\\tau_m = R_m C_m$ — *비율의 곱*. 이로부터 (i) $R_m$ 이 (a) 에서 분리되었다면 $C_m$ 직접 결정. (ii) 그러나 (a) 만으로 $R_m$ 이 분리 안 되었다면 $\\tau_m$ 도 도움 안 됨 — 결합된 $R_m C_m / A$ 만 추출. 일반적으로 *$R_m$ 과 $C_m$ 의 비율* 은 결정되지만 절댓값은 형태 정보 필요.

(c) **+ λ 측정**: $\\lambda^2 = d R_m / 4 R_i$ — *세 매개변수의 결합*. Steady state 에서 두 점 $V$ 비율로 $\\lambda$ 직접 측정 가능. 이로부터 $d R_m / R_i$ 결정. (a)+(b)+(c) + *직경 $d$* (light/electron microscopy 측정) 가 알려지면 4 매개변수 모두 분리:
- $d$ (microscopy)
- $\\lambda$ (steady state, 두 점)
- $R_\\text{in}$ (steady state, 한 점)
- $\\tau_m$ (transient, 한 점)
→ $R_m, R_i, C_m$ 모두 *unique* 결정. 4 *독립* 측정이 4 *독립* 매개변수를 결정 — *완전 식별성*. 단 이는 *passive* 가정 하의 결과; active dendrite (NMDA, $Ca^{2+}$ spike) 에선 비선형성이 추가되어 더 복잡한 측정 필요.''',
        'rubric_md': '''총 10점.
- (a) 3점: $R_\\text{in} \\propto R_m/A$ (1점) + 형태 정보 필요 (1점) + 절댓값 분리 불가 (1점).
- (b) 4점: $\\tau_m = R_m C_m$ (1점) + (a) 와 결합 시 분리 조건 (1점) + 단독으론 결합량만 (1점) + 비율은 분리 가능 (1점).
- (c) 3점: λ 정의식 (1점) + 4 독립 측정 set 명시 (microscopy + λ + R_in + τ_m) (1점) + active dendrite 한계 언급 (1점).''',
        'slide_ref': '[Slide L6 §10]',
    },
]


def main():
    conn = psycopg2.connect(DB_DSN)
    try:
        insert_quiz_items(conn, 'L6', L6_QUIZ)
        insert_take_home(conn, 'L6', L6_TAKE_HOME)
        print(f'L6: {len(L6_QUIZ)} quiz items + {len(L6_TAKE_HOME)} take-home items')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
