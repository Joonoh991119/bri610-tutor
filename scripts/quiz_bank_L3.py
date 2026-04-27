#!/usr/bin/env python3
"""L3 quiz bank — Neural Membrane Biophysics I (Nernst, GHK, RC dynamics).

Hand-authored by Opus 4.7 in this Claude Code session per user mandate
(no OpenRouter Opus). Items grounded in lecture_summaries + L3 slides.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from generate_quiz_bank import insert_quiz_items, insert_take_home, DB_DSN
import psycopg2

L3_QUIZ = [
    # MCQ — Capacitance / RC
    {
        'position': 1, 'kind': 'mcq', 'difficulty': 1, 'bloom': 'Remember',
        'topic_tag': 'capacitance',
        'prompt_md': 'Lipid bilayer 의 *specific membrane capacitance* $c_m$ 가 모든 척추동물 뉴런에서 거의 동일한 ($\\approx 1\\,\\mu\\text{F}/\\text{cm}^2$) 가장 본질적인 이유는?',
        'choices_json': [
            {'key': 'A', 'text': '모든 세포가 동일한 lipid 분자를 사용하기 때문.', 'correct': False},
            {'key': 'B', 'text': 'Bilayer 두께 $d$ 가 진화적으로 보존되었기 때문 ($c_m = \\varepsilon\\varepsilon_0 / d$).', 'correct': True},
            {'key': 'C', 'text': '단백질 채널 밀도가 일정해서.', 'correct': False},
            {'key': 'D', 'text': '실험 측정의 정밀도 한계.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': 'Parallel-plate capacitor: $c_m = \\varepsilon\\varepsilon_0/d$. Lipid bilayer 두께 ≈ 3–4 nm 가 척추동물 진화 전반에 보존됨 → $c_m$ 도 보존. 진화는 channel density (=$g$) 만 변경 가능, $c_m$ 은 거의 고정 [Slide L3 p.18].',
        'slide_ref': '[Slide L3 p.18]',
    },
    {
        'position': 2, 'kind': 'mcq', 'difficulty': 2, 'bloom': 'Apply',
        'topic_tag': 'rc-dynamics',
        'prompt_md': 'Step current 인가 후 $V(t) = V_\\infty(1 - e^{-t/\\tau_m})$ 일 때, $t = \\tau_m$ 에서 $V/V_\\infty$ 의 값은?',
        'choices_json': [
            {'key': 'A', 'text': '$\\approx 0.37$ (즉 1/e)', 'correct': False},
            {'key': 'B', 'text': '$\\approx 0.50$', 'correct': False},
            {'key': 'C', 'text': '$\\approx 0.63$ (즉 1 − 1/e)', 'correct': True},
            {'key': 'D', 'text': '$\\approx 0.95$', 'correct': False},
        ],
        'correct_key': 'C',
        'rationale_md': '$1 - e^{-1} \\approx 1 - 0.368 \\approx 0.632$. *시간상수* $\\tau_m$ 의 정의: "정상상태까지의 거리의 63% 를 채우는 시간". Decay (e.g. 방전) 라면 1/e ≈ 37% 이지만, *charging* 은 (1−1/e) [Slide L3 p.24].',
        'slide_ref': '[Slide L3 p.24]',
    },
    {
        'position': 3, 'kind': 'mcq', 'difficulty': 2, 'bloom': 'Understand',
        'topic_tag': 'membrane-equation',
        'prompt_md': '단일-compartment 막 방정식 $C_m\\,dV/dt = I_\\text{inj} - (V - E_L)/R_m$ 에서, $dV/dt = 0$ 일 때 ($V = V_\\infty$) 막의 *steady state* 전압을 결정하는 항은?',
        'choices_json': [
            {'key': 'A', 'text': '$C_m$ 만으로 결정.', 'correct': False},
            {'key': 'B', 'text': '$E_L$ 과 $R_m \\cdot I_\\text{inj}$ 의 합 — $V_\\infty = E_L + R_m I_\\text{inj}$.', 'correct': True},
            {'key': 'C', 'text': '$\\tau_m$ 의 크기.', 'correct': False},
            {'key': 'D', 'text': '$dV/dt$ 의 평균값.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': '$dV/dt = 0$ 대입 → $0 = I_\\text{inj} - (V_\\infty - E_L)/R_m$ → $V_\\infty = E_L + R_m I_\\text{inj}$. *Steady state* 에서 $C_m$ 은 *보이지 않는다* (변화량에서만 등장). 이 사실은 §9 식별성 논리의 핵심 [Slide L3 p.22–24].',
        'slide_ref': '[Slide L3 p.22–24]',
    },
    {
        'position': 4, 'kind': 'mcq', 'difficulty': 3, 'bloom': 'Analyze',
        'topic_tag': 'identifiability',
        'prompt_md': '*Steady-state* 측정만으로 $C_m$ 을 결정할 수 *없는* 이유는?',
        'choices_json': [
            {'key': 'A', 'text': '측정 장비의 정밀도가 부족하기 때문.', 'correct': False},
            {'key': 'B', 'text': '$C_m$ 이 시간 의존성 ($dV/dt$) 에서만 막 방정식에 등장하기 때문.', 'correct': True},
            {'key': 'C', 'text': '$C_m$ 은 사실 측정 불가능한 상수이기 때문.', 'correct': False},
            {'key': 'D', 'text': '온도 의존성 때문.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': '막 방정식 $C_m\\,dV/dt = I_\\text{inj} - (V-E_L)/R_m$ 에서 *steady state* ($dV/dt=0$) 는 $C_m$ 항을 *제거* 한다. 따라서 $C_m$ 은 *transient* 에서만 관측 가능 → step 직후의 기울기, 또는 $\\tau_m = R_m C_m$ 로부터 분리. $R_m$ 은 정상상태에서 분리 가능, $C_m$ 은 transient 에서만 [Slide L3 p.32 표].',
        'slide_ref': '[Slide L3 §9.5]',
    },
    # MCQ — Nernst / GHK
    {
        'position': 5, 'kind': 'mcq', 'difficulty': 2, 'bloom': 'Understand',
        'topic_tag': 'nernst',
        'prompt_md': '$E_K \\approx -90$ mV 라는 값이 모든 척추동물 뉴런에서 거의 동일한 이유로 가장 적절한 것은?',
        'choices_json': [
            {'key': 'A', 'text': '모든 뉴런이 같은 K leak 채널을 사용해서.', 'correct': False},
            {'key': 'B', 'text': '$[K^+]$ 의 세포 내외 농도 비율이 진화적으로 보존되어 ($[K]_i \\approx 140$ mM 안 / $[K]_o \\approx 4$ mM 밖).', 'correct': True},
            {'key': 'C', 'text': '온도 $T$ 가 항상 동일하므로.', 'correct': False},
            {'key': 'D', 'text': '$z$ 의 부호가 +1 이므로.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': 'Nernst 식 $E_X = (RT/zF) \\ln([X]_o/[X]_i)$. 척추동물에서 K 의 농도비 ($[K]_i \\approx 140$, $[K]_o \\approx 4$ → 비율 35) 가 진화적으로 보존됨. $RT/F \\approx 26$ mV at 37°C → $E_K \\approx 26 \\ln(4/140) \\approx -92$ mV. 이 보존성이 휴지 막전위가 종에 무관하게 음수가 되는 이유 [Slide L3 p.27].',
        'slide_ref': '[Slide L3 p.27]',
    },
    {
        'position': 6, 'kind': 'mcq', 'difficulty': 3, 'bloom': 'Apply',
        'topic_tag': 'ghk',
        'prompt_md': '휴지 상태 ($V_\\text{rest} \\approx -70$ mV) 가 $E_K \\approx -90$ mV 와 정확히 같지 *않은* 이유는?',
        'choices_json': [
            {'key': 'A', 'text': 'K 채널이 부분적으로 닫혀 있기 때문.', 'correct': False},
            {'key': 'B', 'text': '*작지만 0 이 아닌* Na 투과도 ($p_\\text{Na} > 0$) 가 막전위를 $E_\\text{Na}$ 쪽으로 끌어당기기 때문.', 'correct': True},
            {'key': 'C', 'text': '온도가 정확히 37°C 가 아니기 때문.', 'correct': False},
            {'key': 'D', 'text': 'Na/K pump 가 멈춰 있기 때문.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': 'GHK 식 $V_m = (RT/F) \\ln \\frac{p_K[K]_o + p_\\text{Na}[Na]_o + p_\\text{Cl}[Cl]_i}{p_K[K]_i + p_\\text{Na}[Na]_i + p_\\text{Cl}[Cl]_o}$. 휴지에서 $p_K \\gg p_\\text{Na}$ 이지만 $p_\\text{Na}/p_K \\approx 0.04$ 가 0 이 아니므로 $V_m$ 이 $E_K$ 에서 약 +20 mV 끌어올려진다 [Slide L3 p.30]. Pump 의 electrogenic 기여도 작지만 (-1~-2 mV).',
        'slide_ref': '[Slide L3 p.30]',
    },
    {
        'position': 7, 'kind': 'mcq', 'difficulty': 3, 'bloom': 'Analyze',
        'topic_tag': 'reversal-potential',
        'prompt_md': '*Equilibrium potential* (Nernst) 와 *reversal potential* 의 관계로 가장 정확한 것은?',
        'choices_json': [
            {'key': 'A', 'text': '항상 동일하다.', 'correct': False},
            {'key': 'B', 'text': '단일-이온 선택 채널에선 같지만, AMPA 같은 *비선택 cation* 채널에선 reversal 이 더 정확한 용어다.', 'correct': True},
            {'key': 'C', 'text': '둘은 완전히 다른 개념이다.', 'correct': False},
            {'key': 'D', 'text': 'Reversal 이 항상 더 음수이다.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': '*Equilibrium* 은 *단일 이온* 의 net flux = 0 (Nernst 식). *Reversal* 은 채널을 통한 *순전류* (net current) = 0. 단일-이온 채널은 두 정의가 일치. AMPA (Na + K 동시 통과) 는 두 이온의 GHK-가중 평균이 0 인 점이 reversal — 별도의 단일 이온 평형은 존재 안 함 [Slide L3 p.36; L4 §1].',
        'slide_ref': '[Slide L4 §1]',
    },
    {
        'position': 8, 'kind': 'mcq', 'difficulty': 4, 'bloom': 'Evaluate',
        'topic_tag': 'identifiability',
        'prompt_md': '"$\\tau_m$ 측정만으로 $C_m$ 을 추정할 수 있다" — 이 주장의 평가는?',
        'choices_json': [
            {'key': 'A', 'text': '맞다. $C_m$ 은 직접 관측 가능하므로.', 'correct': False},
            {'key': 'B', 'text': '맞다 — 단, *$R_m$ 이 독립적으로 알려진 경우* 에 한해 $C_m = \\tau_m / R_m$ 으로 분리 가능.', 'correct': True},
            {'key': 'C', 'text': '틀렸다. $\\tau_m$ 과 $C_m$ 은 무관하다.', 'correct': False},
            {'key': 'D', 'text': '틀렸다. 항상 추가 측정이 필요하다.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': '$\\tau_m = R_m C_m$ 이므로 *두 미지수 → 한 식*. 식별을 위해선 $R_m$ 을 *steady state* 입력저항 측정으로 *독립적* 으로 결정한 뒤 $C_m = \\tau_m/R_m$. 작은 뉴런은 면적이 작아 $R_m$ 이 커도 $\\tau_m$ 이 작을 수 있다 [Slide L3 §9.4].',
        'slide_ref': '[Slide L3 §9.5]',
    },
    # Short-answer
    {
        'position': 9, 'kind': 'short_answer', 'difficulty': 2, 'bloom': 'Remember',
        'topic_tag': 'nernst',
        'prompt_md': '체온 (37°C) 에서 $RT/F$ 의 값을 mV 단위로 답하라 (소수 첫째 자리까지).',
        'correct_text': '26.7 mV',
        'accept_patterns': [
            r'(?i)\b26[\.,]?[5-9]?\s*mV\b',
            r'(?i)\b27\s*mV\b',
            r'(?i)\b25[5-9]?\s*mV\b',
        ],
        'rationale_md': '$R = 8.314$ J/(mol·K), $T = 310$ K, $F = 96485$ C/mol → $RT/F \\approx 26.7$ mV. 종종 25 mV 또는 26 mV 로 근사 (실온 25°C 라면 25.7 mV). 이 값은 Nernst 식의 *prefactor* 이며 $|z|$ 로 나누면 다가 이온의 전위 척도가 된다.',
        'slide_ref': '[Slide L3 p.27]',
    },
    {
        'position': 10, 'kind': 'short_answer', 'difficulty': 1, 'bloom': 'Remember',
        'topic_tag': 'driving-force',
        'prompt_md': 'Driving force 의 정의를 *수식으로* 답하라 (변수 이름은 표준 표기).',
        'correct_text': '(V − E_X)',
        'accept_patterns': [
            r'\(?\s*V\s*[-−]\s*E_?X\s*\)?',
            r'\(?\s*V_m?\s*[-−]\s*E_?X\s*\)?',
            r'V\s*[-−]\s*E\b',
        ],
        'rationale_md': 'Driving force $= V - E_X$. 부호가 *현재 막전위* 와 *해당 이온의 reversal* 사이의 거리. $> 0$ 면 양이온이 밖으로, $< 0$ 면 양이온이 안으로. Ohm 의 채널 버전 $I_X = g_X (V - E_X)$ 의 핵심 항.',
        'slide_ref': '[Slide L4 p.6]',
    },
    {
        'position': 11, 'kind': 'short_answer', 'difficulty': 3, 'bloom': 'Apply',
        'topic_tag': 'rc-dynamics',
        'prompt_md': '$\\tau_m = 5$ ms 인 뉴런에 step current 인가 후, $V(t)$ 가 정상상태까지 *95%* 채워지는 시간을 ms 단위로 답하라 (자연로그 사용; 정수 ms).',
        'correct_text': '15 ms',
        'accept_patterns': [
            r'\b15\s*ms\b',
            r'\b14[\.,]?\d*\s*ms\b',  # 14.something is also acceptable since 3τ ≈ 14.98
            r'\b3\s*[xX×]\s*\\?tau_?m\b',
            r'\b3\s*\\?tau\b',
        ],
        'rationale_md': '$1 - e^{-t/\\tau} = 0.95$ → $t = -\\tau \\ln(0.05) \\approx 3\\tau$. $3 \\times 5 = 15$ ms. 흔한 *경험칙*: $3\\tau$ 면 95%, $5\\tau$ 면 99% 도달.',
        'slide_ref': '[Slide L3 p.24]',
    },
    {
        'position': 12, 'kind': 'mcq', 'difficulty': 4, 'bloom': 'Analyze',
        'topic_tag': 'common-misconception',
        'prompt_md': '*"휴지 막전위는 Na/K pump 가 만든다"* — 이 진술의 평가는?',
        'choices_json': [
            {'key': 'A', 'text': '완전히 맞다. Pump 가 없으면 휴지 막전위도 없다.', 'correct': False},
            {'key': 'B', 'text': '*부분적으로 틀렸다*. 휴지 막전위의 *주요 결정자* 는 K leak 채널의 GHK 평형 — pump 는 농도비 *유지* 와 작은 (-1~-2 mV) electrogenic 기여만.', 'correct': True},
            {'key': 'C', 'text': '완전히 틀렸다. Pump 는 휴지 막전위와 무관하다.', 'correct': False},
            {'key': 'D', 'text': 'Pump 만으로 -90 mV 를 만든다.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': 'Pump 의 즉각적인 전압 기여는 *작다* (electrogenic ≈ -1~-2 mV; 3 Na 밖, 2 K 안 → 1+ 정전하 외향). 그러나 pump 가 *수일~수주 단위* 로 멈추면 농도 구배가 무너져 GHK 평형 자체가 사라짐. 즉 *직접 만든다* 는 표현은 단기 (ms) 에선 *틀린* 단순화이며, 장기 (days) 로 보면 *간접적으로 필요* — 미묘한 시간 척도 분리 [Slide L3 §3.6].',
        'slide_ref': '[Slide L3 §3.6]',
    },
]

L3_TAKE_HOME = [
    {
        'position': 1, 'kind': 'derivation', 'difficulty': 4, 'max_points': 15, 'expected_time_min': 25,
        'topic_tag': 'membrane-equation',
        'prompt_md': '''Single-compartment 뉴런의 *passive membrane equation* 을 KCL + Ohm + capacitor 정의로부터 유도하라:
(a) (4점) 등가 회로 (capacitor $C_m$, 저항 $R_m$ + EMF $E_L$, 주입 전류 $I_\\text{inj}$) 의 KCL 식을 *임의의* 노드 전압 $V$ 에 대해 작성하라.
(b) (4점) (a) 의 식을 변수분리형 ODE 로 정리하고, $\\tau_m \\equiv R_m C_m$, $V_\\infty \\equiv E_L + R_m I_\\text{inj}$ 로 치환하여 *standard form* $\\tau_m\\,du/dt = -u$ ($u = V - V_\\infty$) 를 얻으라.
(c) (4점) 분리변수 풀이로 $V(t) = V_\\infty + (V_0 - V_\\infty)\\,e^{-t/\\tau_m}$ 를 얻으라 (적분상수 $C$ 는 초기조건 $V(0) = V_0$ 으로 결정).
(d) (3점) 그래프 (가로 $t$, 세로 $V$): 점근선 $V_\\infty$, 초기 기울기 (= $V_\\infty/\\tau_m$), 63% 도달점 ($t = \\tau_m$) 을 라벨링.''',
        'model_answer_md': '''(a) 노드 $V$ 에서 KCL: 들어오는 전류 = 나가는 전류. 들어오는 = $I_\\text{inj}$. 나가는 = $I_C + I_R$.
- Capacitor: $I_C = C_m\\,dV/dt$ (정의 $Q = C_m V$ 미분).
- 저항 + EMF: $I_R = (V - E_L)/R_m$ (Ohm + battery 직렬).

KCL: $$I_\\text{inj} = C_m\\,\\frac{dV}{dt} + \\frac{V - E_L}{R_m}.$$ 양변에 $R_m$ 곱하기: $$R_m C_m\\,\\frac{dV}{dt} = R_m I_\\text{inj} - (V - E_L).$$

(b) 정의 $\\tau_m \\equiv R_m C_m$, $V_\\infty \\equiv E_L + R_m I_\\text{inj}$. 우변 정리: $$R_m I_\\text{inj} - (V - E_L) = (E_L + R_m I_\\text{inj}) - V = V_\\infty - V.$$ 치환 $u = V - V_\\infty$ → $V = u + V_\\infty$, $dV/dt = du/dt$. 우변 $= V_\\infty - V = -u$. $$\\tau_m\\,\\frac{du}{dt} = -u.$$

(c) Standard form 분리: $du/u = -dt/\\tau_m$. 적분: $\\ln|u| = -t/\\tau_m + C$. $u(t) = A\\,e^{-t/\\tau_m}$ ($A = e^C$, 부호 흡수). 초기조건 $u(0) = V_0 - V_\\infty$ → $A = V_0 - V_\\infty$. 복귀: $$V(t) = V_\\infty + (V_0 - V_\\infty)\\,e^{-t/\\tau_m}.$$

(d) [그래프 텍스트 묘사]
- $t$-축: $0 \\to 5\\tau_m$
- $V$-축: $V_0$ 에서 $V_\\infty$ 로 지수적으로 접근.
- 점근선: $V = V_\\infty$ (수평 점선).
- 초기 기울기: $V'(0) = (V_\\infty - V_0)/\\tau_m$. 만약 $V_0 = E_L$ 이면 $V'(0) = R_m I_\\text{inj}/\\tau_m = I_\\text{inj}/C_m$.
- 63% 점: $(t = \\tau_m, V = V_0 + 0.63(V_\\infty - V_0))$ 를 dot 으로 표시 + 점선 가로 세로 라벨.''',
        'rubric_md': '''총 15점.
- (a) 4점: KCL 정의 (1점) + $I_C = C_m dV/dt$ (1점) + $I_R = (V−E_L)/R_m$ (1점) + 정리된 막 방정식 (1점). 부호 오류 −1.
- (b) 4점: $\\tau_m$, $V_\\infty$ 정의 (1점) + 우변 인수분해 (1점) + 치환 $u$ (1점) + standard form 도출 (1점).
- (c) 4점: 분리변수 (1점) + 적분 (1점) + 일반해 + 적분상수 (1점) + 초기조건 적용 → 최종 (1점).
- (d) 3점: 점근선 (1점) + 63% 점 위치 정확 (1점) + 초기 기울기 라벨 (1점).''',
        'slide_ref': '[Slide L3 p.22–24]',
    },
    {
        'position': 2, 'kind': 'derivation', 'difficulty': 4, 'max_points': 12, 'expected_time_min': 20,
        'topic_tag': 'nernst',
        'prompt_md': '''Nernst 식을 Boltzmann 평형으로부터 유도하라:
(a) (3점) 평형 조건: 막 양쪽의 *전기화학 포텐셜* $\\tilde\\mu = \\mu^0 + RT \\ln[X] + zF\\phi$ 가 *같다* — 즉 $\\tilde\\mu_i = \\tilde\\mu_o$.
(b) (4점) 위 조건에서 $\\mu^0$ (이온 종류만의 함수) 가 양변에서 상쇄됨을 보이고, $RT \\ln([X]_o/[X]_i) = zF(\\phi_i - \\phi_o)$ 를 얻으라.
(c) (3점) $E_X \\equiv \\phi_i - \\phi_o$ (안 − 바깥) 정의를 도입하여 $E_X = (RT/zF) \\ln([X]_o/[X]_i)$ 를 얻으라.
(d) (2점) $z = -1$ (예: $Cl^-$) 일 때 로그 항 부호가 어떻게 뒤집히는지, *결과* 가 *물리적 직관* 과 일치함을 한 문장으로 서술 (안쪽 농도 ↑ → $E_X$ 가 양수 vs 음수 어느 쪽?).''',
        'model_answer_md': '''(a) 평형: 막 안 ($i$) 과 밖 ($o$) 의 전기화학 포텐셜이 같다. $$\\tilde\\mu_i = \\tilde\\mu_o.$$ $$\\mu^0 + RT \\ln[X]_i + zF\\phi_i = \\mu^0 + RT \\ln[X]_o + zF\\phi_o.$$

(b) $\\mu^0$ 는 *이온 종류만의 함수* 이므로 양변에서 상쇄. 정리: $$RT (\\ln[X]_i - \\ln[X]_o) = zF(\\phi_o - \\phi_i),$$ $$RT \\ln \\frac{[X]_o}{[X]_i} = zF(\\phi_i - \\phi_o).$$

(c) 정의 $E_X = \\phi_i - \\phi_o$ (관례: 안 − 바깥). 양변을 $zF$ 로 나누기: $$\\boxed{E_X = \\frac{RT}{zF} \\ln \\frac{[X]_o}{[X]_i}}.$$

(d) $z = -1$ (예: $Cl^-$): $RT/(zF) = -RT/F$ → 로그 부호가 뒤집힌다. 즉 $E_\\text{Cl} = -(RT/F) \\ln([Cl]_o/[Cl]_i)$. **물리적 직관 일치**: $Cl^-$ 가 *밖에* 더 많으면 ($[Cl]_o > [Cl]_i$, 일반적인 신경세포 상황), 평형 시 $Cl^-$ 가 안으로 들어와 *내부에 음전하 축적* — 즉 $E_\\text{Cl}$ 이 *음수*. 부호 뒤집힘이 이를 정확히 재현 ($\\ln(o/i) > 0$ × $z = -1$ × 양수 → 음수). 양이온이라면 안쪽 농도가 작을 때 (e.g. K) 평형 음수, 큰 쪽으로의 이동이 음의 $E_X$ 를 만든다는 동일 직관.''',
        'rubric_md': '''총 12점.
- (a) 3점: 평형 정의 (1점) + 전기화학 포텐셜 정확 표기 (1점) + 양변 같다 표현 (1점).
- (b) 4점: $\\mu^0$ 상쇄 (1점) + 부호 정리 (1점) + 로그 차 → 비율 (1점) + 최종 형태 (1점).
- (c) 3점: $E_X$ 정의 (1점) + $zF$ 로 나누기 (1점) + 최종 박스 형식 (1점).
- (d) 2점: 부호 뒤집힘 (1점) + $Cl^-$ 직관 일치 설명 (1점).''',
        'slide_ref': '[Slide L3 p.27–29]',
    },
    {
        'position': 3, 'kind': 'essay', 'difficulty': 3, 'max_points': 10, 'expected_time_min': 15,
        'topic_tag': 'identifiability',
        'prompt_md': '''*"$\\tau_m, R_m, C_m$ 중 어느 것이 *직접 측정 가능* 하고 어느 것이 *분리 가능* 한가"* — 이 식별성 (identifiability) 문제를 분석하라:
(a) (3점) Step current 인가 후 *어떤 데이터 의 어떤 부분* 이 $R_m$ 결정에 사용되는가?
(b) (3점) $\\tau_m$ 결정에 사용되는 부분은?
(c) (4점) $C_m$ 이 *직접* 결정 불가능하고 *간접* ($\\tau_m / R_m$) 으로만 결정되는 이유를 막 방정식의 구조로 설명. 측정 가능성과 식별성의 차이를 명시.''',
        'model_answer_md': '''(a) **$R_m$ — *steady state* 진폭**: Step 인가 후 $V$ 가 충분한 시간 ($t \\gg \\tau_m$) 후 도달한 정상상태 값 $V_\\infty$ 와 *베이스라인* $E_L$ 의 차이로부터 $R_m = (V_\\infty - E_L)/I_\\text{inj}$. 측정자: *최종 도달 전압* 만 보면 됨. 시간 정보 불필요.

(b) **$\\tau_m$ — *transient 곡선의 모양***: $V(t) = V_\\infty + (V_0 - V_\\infty)e^{-t/\\tau_m}$ 의 지수 fit, 또는 63% 도달 시점의 측정. 곡선의 *시간 척도* 자체. 정상상태 값 ($V_\\infty$) 만 보면 $\\tau_m$ 정보가 없다 — *변화의 속도* 를 봐야 함.

(c) **$C_m$ — 직접 측정 불가능, 간접 식별만**: 막 방정식 $C_m\\,dV/dt = I_\\text{inj} - (V-E_L)/R_m$ 에서 $C_m$ 은 *시간 미분* $dV/dt$ 의 계수로만 등장. *어떤 단일 측정량* 도 $C_m$ 단독으로 결정하지 않는다.

- *Steady state* ($dV/dt = 0$): $C_m$ 항 사라짐 → $C_m$ 정보 없음.
- *Transient* 곡선: $\\tau_m = R_m C_m$ 의 *복합* 만 결정.

식별 절차: (i) steady-state 로 $R_m$ 분리 → (ii) transient 로 $\\tau_m$ 추출 → (iii) $C_m = \\tau_m/R_m$ 로 *역산*. **측정가능성** (observability) ≠ **식별가능성** (identifiability) — $C_m$ 은 모든 시점에서 *영향* 을 주지만, *그 효과만으로는 분리 불가*.

이 구조는 일반적: 두 매개변수가 *곱* 으로만 데이터에 등장하면 무한히 많은 조합이 같은 곡선을 만든다 (공선성). $C_m$ 의 분리는 $R_m$ 에 *독립* 정보가 있어야만 가능 — *두 시간 척도 (instantaneous + steady-state)* 가 그 독립 정보를 제공.''',
        'rubric_md': '''총 10점.
- (a) 3점: steady state 진폭 사용 (1점) + $R_m = \\Delta V / I$ 공식 (1점) + 시간 정보 불필요 (1점).
- (b) 3점: transient 곡선 fit (1점) + 63% 시점 또는 지수 fit (1점) + steady state 만으론 부족 (1점).
- (c) 4점: $C_m$ 이 시간 미분에서만 등장 (1점) + steady state 에서 $C_m$ 항 사라짐 (1점) + 분리 절차 (steady state → R_m → τ → C_m) (1점) + 측정가능성 vs 식별가능성 구분 (1점).''',
        'slide_ref': '[Slide L3 §9, p.32]',
    },
    {
        'position': 4, 'kind': 'essay', 'difficulty': 4, 'max_points': 12, 'expected_time_min': 20,
        'topic_tag': 'ghk-vs-nernst',
        'prompt_md': '''GHK 식과 Nernst 식의 관계를 *log-domain 가중평균* 관점에서 분석하라:
(a) (3점) 단일-이온 막에서 GHK 가 Nernst 로 환원됨을 보이라 (한 이온 종만 있을 때 GHK 식 → Nernst 식).
(b) (3점) 다이온 막 ($K + Na$) 에서, GHK 가 *Nernst 의 산술평균* 이 *아닌* *log-도메인 가중평균* 인 이유를 한 단락으로 설명.
(c) (3점) "$V_\\infty = (g_K E_K + g_\\text{Na} E_\\text{Na})/(g_K + g_\\text{Na})$" 라는 *conductance-가중 평균* 식이 GHK 와 *수학적으로 다른* 이유 — 어느 한쪽이 더 정확한 이유. 휴지에서 두 식이 *근사적으로* 일치하는 조건.
(d) (3점) 만약 $p_\\text{Na}/p_K$ 가 0 에서 0.04 로 증가하면 ($V_\\text{rest}$ 가 어떻게 변하는가) 정량적 추정 (음수 → 덜 음수 또는 양수). $E_K = -90$, $E_\\text{Na} = +60$ mV 가정.''',
        'model_answer_md': '''(a) **단일 이온 (예: K)**: GHK $V_m = (RT/F) \\ln[(p_K[K]_o)/(p_K[K]_i)] = (RT/F) \\ln([K]_o/[K]_i)$ — $p_K$ 가 분자/분모에서 상쇄, $z = +1$ 로 Nernst 식 그대로. 다른 이온이 모두 $p = 0$ 이면 GHK = Nernst.

(b) **Log-domain 가중평균**: GHK 의 분자 = $\\sum p_X [X]_o$ ($z = +1$ 의 경우), 분모 = $\\sum p_X [X]_i$. 즉 *농도의 합* 의 비율의 *로그*. 수학적으로 이는 $$V_m = \\frac{RT}{F} \\ln \\left( \\frac{\\sum p_X [X]_o}{\\sum p_X [X]_i} \\right) \\neq \\sum w_X \\ln([X]_o/[X]_i) = \\sum w_X E_X.$$ Nernst 들의 *산술* 가중평균이 아니라, *원농도* 의 가중평균을 *로그* 취한 것이므로 비선형.

(c) **Conductance-가중 평균 vs GHK**: $V_\\infty = \\sum g_X E_X / \\sum g_X$ 는 *Ohmic 한계* (선형 I-V) 에서 정확. 휴지 막처럼 작은 driving force 영역 ($V \\approx E_K$) 에선 $g$ 가 상수 → conductance-가중 평균이 GHK 와 *근사 일치*. AP 처럼 큰 driving force 변화에선 GHK 의 비선형 (Goldman flux) 이 더 정확. *조건*: 채널 전류가 Ohmic 이고 $V$ 변화 폭이 작을 때 두 식 일치 [Slide L3 p.30, p.36].

(d) **정량적 추정**: $p_\\text{Na}/p_K = 0$ → $V_\\text{rest} = E_K = -90$ mV. $p_\\text{Na}/p_K = 0.04$ 이면 (대략 $[Na]_o/[Na]_i \\approx 12$, $[K]_o/[K]_i \\approx 0.029$ 가정), GHK: $V_m = 26.7 \\ln \\frac{0.029 + 0.04 \\cdot 12}{1 + 0.04/12} \\approx 26.7 \\ln(0.509/1.003) \\approx -18 \\ln \\approx -71$ mV. 즉 *약 +20 mV 끌어올림* — 휴지 막전위가 -90 → -70 mV 로 약화. 작지만 0 이 아닌 Na 투과도가 휴지 막을 *덜 음수* 로 만드는 정확한 정량적 결과 [Slide L3 §3.5].''',
        'rubric_md': '''총 12점.
- (a) 3점: 단일 이온 시 분자/분모 상쇄 (1점) + Nernst 식 환원 (1점) + $p_X$ 의 의미 명시 (1점).
- (b) 3점: 산술평균 vs 로그-도메인 차이 (1점) + 비선형성 (1점) + 수식 표현 (1점).
- (c) 3점: conductance-가중 평균이 Ohmic 한계 (1점) + GHK 가 비선형 정확 (1점) + 휴지 근사 일치 조건 (1점).
- (d) 3점: $p_\\text{Na}/p_K = 0$ 에서 $E_K = -90$ (1점) + GHK 계산 시도 (1점) + 약 -70 mV 결론 (1점). 소수점 정확도는 ±5 mV.''',
        'slide_ref': '[Slide L3 p.30, §3.5]',
    },
]


def main():
    conn = psycopg2.connect(DB_DSN)
    try:
        insert_quiz_items(conn, 'L3', L3_QUIZ)
        insert_take_home(conn, 'L3', L3_TAKE_HOME)
        print(f'L3: {len(L3_QUIZ)} quiz items + {len(L3_TAKE_HOME)} take-home items')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
