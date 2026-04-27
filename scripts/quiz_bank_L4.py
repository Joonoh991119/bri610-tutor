#!/usr/bin/env python3
"""L4 quiz bank — Neural Membrane Biophysics II: Ion Channels & Synapses."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from generate_quiz_bank import insert_quiz_items, insert_take_home, DB_DSN
import psycopg2

L4_QUIZ = [
    {
        'position': 1, 'kind': 'mcq', 'difficulty': 1, 'bloom': 'Remember',
        'topic_tag': 'channel-types',
        'prompt_md': '*Membrane equation* 의 모든 conductance 항이 *parallel* (병렬) 로 결합되는 이유로 가장 적절한 것은?',
        'choices_json': [
            {'key': 'A', 'text': '계산이 쉽기 때문.', 'correct': False},
            {'key': 'B', 'text': '모든 채널이 *동일한 막전위 $V$* 에 직접 노출되어 있기 때문 — 각 경로가 막을 가로지르는 *독립* 통로.', 'correct': True},
            {'key': 'C', 'text': '직렬 결합은 KCL 위배이기 때문.', 'correct': False},
            {'key': 'D', 'text': '실험적으로만 확인된 사실.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': '회로 의미: *같은 두 노드 (intra/extra)* 사이에 연결된 도선 = 병렬. 막 위의 모든 ion 채널이 막 양쪽에 동시에 닿아 있으므로 자동 병렬. 따라서 $1/R_m = \\sum 1/R_X = \\sum g_X$ 식이 성립 [Slide L4 p.4].',
        'slide_ref': '[Slide L4 p.4]',
    },
    {
        'position': 2, 'kind': 'mcq', 'difficulty': 2, 'bloom': 'Understand',
        'topic_tag': 'reversal-potential',
        'prompt_md': 'AMPA 시냅스의 reversal potential $E_\\text{AMPA} \\approx 0$ mV 인 이유는?',
        'choices_json': [
            {'key': 'A', 'text': '$Cl^-$ 만 통과시키므로.', 'correct': False},
            {'key': 'B', 'text': '$Na^+$ 와 $K^+$ 를 *모두* 통과시키는 비선택 cation 채널 — 두 이온의 reversal 사이 가중 평균.', 'correct': True},
            {'key': 'C', 'text': '$Ca^{2+}$ 만 통과시키므로.', 'correct': False},
            {'key': 'D', 'text': 'AMPA 가 voltage-gated 이기 때문.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': 'AMPA 는 ligand-gated *비선택* cation channel — $Na, K$ 둘 다 통과 ($Ca^{2+}$ 도 일부 subunit composition 에 따라). $E_\\text{Na} \\approx +60$, $E_K \\approx -90$ → 가중평균 $\\approx 0$ mV. 이 값이 *normal V 보다 위* 이므로 AMPA 활성화는 *depolarization* (EPSP) 발생 [Slide L4 p.7].',
        'slide_ref': '[Slide L4 p.7]',
    },
    {
        'position': 3, 'kind': 'mcq', 'difficulty': 2, 'bloom': 'Understand',
        'topic_tag': 'reversal-potential',
        'prompt_md': '$\\text{GABA}_A$ 시냅스가 *억제성* (inhibitory) 인 가장 정확한 이유는?',
        'choices_json': [
            {'key': 'A', 'text': '$E_\\text{GABA_A} \\approx -70$ mV 가 *대부분 뉴런의 휴지 막전위 $V_\\text{rest}$ 와 비슷* 해서, 활성화 시 막을 휴지 근처로 *고정* (clamp) 한다 — *shunting inhibition*.', 'correct': True},
            {'key': 'B', 'text': 'GABA 채널이 항상 닫혀 있기 때문.', 'correct': False},
            {'key': 'C', 'text': 'GABA 가 막을 항상 *과분극* 만 시킨다.', 'correct': False},
            {'key': 'D', 'text': 'GABA 가 voltage-gated 이기 때문.', 'correct': False},
        ],
        'correct_key': 'A',
        'rationale_md': '$\\text{GABA}_A$ 는 $Cl^-$ 통과 → $E_\\text{Cl} \\approx -70$ mV. *Driving force* $V - E_\\text{Cl} \\approx 0$ near $V_\\text{rest}$, so 전류는 작지만 *컨덕턴스 자체* 가 다른 입력의 효과를 *희석* (shunt). 막을 -70 mV 에 *고정* 하여 다른 EPSP 가 임계 도달을 방해. 이것이 단순 hyperpolarization 보다 *효과적* 인 억제 메커니즘 [Slide L4 p.18–19].',
        'slide_ref': '[Slide L4 p.18–19]',
    },
    {
        'position': 4, 'kind': 'mcq', 'difficulty': 3, 'bloom': 'Apply',
        'topic_tag': 'channel-distinction',
        'prompt_md': 'NMDA 수용체가 AMPA 수용체와 *결정적으로 다른* 특징은?',
        'choices_json': [
            {'key': 'A', 'text': 'NMDA 는 voltage-gated 이고 AMPA 는 ligand-gated 이다.', 'correct': False},
            {'key': 'B', 'text': 'NMDA 는 *ligand AND voltage* 둘 다 필요 — $Mg^{2+}$ block 이 탈분극으로 풀려야 활성. AMPA 는 ligand 만으로 충분.', 'correct': True},
            {'key': 'C', 'text': 'NMDA 는 $Cl^-$ 를 통과시킨다.', 'correct': False},
            {'key': 'D', 'text': '둘은 동일하다.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': 'NMDA 의 분자적 특징: glutamate binding 후에도 *$Mg^{2+}$ 가 채널 입구를 막고* 있다 — 막이 -70 mV 일 때 음전하인 $Mg^{2+}$ 가 voltage 에 의해 끌려와 block. *탈분극* (e.g. 충분한 AMPA EPSP 누적) 으로 $Mg^{2+}$ 가 풀려야 NMDA 가 cation flow 시작. 이것이 *coincidence detection* 의 분자적 기반 — pre-synaptic 활성 + post-synaptic 탈분극 = NMDA-매개 $Ca^{2+}$ influx → LTP 의 trigger [Slide L4 p.19].',
        'slide_ref': '[Slide L4 p.19]',
    },
    {
        'position': 5, 'kind': 'mcq', 'difficulty': 2, 'bloom': 'Understand',
        'topic_tag': 'gating-structure',
        'prompt_md': '$K_v$ 채널의 $P_\\text{open} = n^4$ 식에서 *지수 4* 의 의미는?',
        'choices_json': [
            {'key': 'A', 'text': '실험 fitting 에서 우연히 가장 잘 맞는 값.', 'correct': False},
            {'key': 'B', 'text': '4 개의 *동등하고 독립적* 인 subunit 이 모두 활성 상태여야 채널이 열린다 (구조적 의미).', 'correct': True},
            {'key': 'C', 'text': 'K 의 원자번호와 관련.', 'correct': False},
            {'key': 'D', 'text': '4 개의 ion 이 동시에 통과해야 함.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': 'Slide L5 p.21 명시: *"k = 4 is consistent with the four-subunit structure"*. $K_v$ 는 4 개의 *독립* α-subunit, 각각 활성 확률 $n$. 모두 동시에 활성일 확률 = $n^4$ (독립성 가정). 단, $Na_v$ 는 *하나의 polypeptide 의 4 도메인* — $m^3$ (3 활성) × $h$ (1 inactivation) 형태로 비대칭 [Slide L4 p.10–11; L5 p.21].',
        'slide_ref': '[Slide L4 p.10–11; L5 p.21]',
    },
    {
        'position': 6, 'kind': 'mcq', 'difficulty': 4, 'bloom': 'Analyze',
        'topic_tag': 'alpha-function',
        'prompt_md': 'Alpha function $g(t) = A\\,t\\,e^{-t/t_\\text{peak}}$ 의 극대 (peak) 시간은?',
        'choices_json': [
            {'key': 'A', 'text': '$t = 0$', 'correct': False},
            {'key': 'B', 'text': '$t = t_\\text{peak}$', 'correct': True},
            {'key': 'C', 'text': '$t = 2 t_\\text{peak}$', 'correct': False},
            {'key': 'D', 'text': '$t = e \\cdot t_\\text{peak}$', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': '$dg/dt = A(1 - t/t_\\text{peak})e^{-t/t_\\text{peak}}$. $dg/dt = 0$ → $t = t_\\text{peak}$. *직관*: $t e^{-t/\\tau}$ 의 모양은 *상승 ($t$ 인자)* 과 *감쇠 ($e^{-t/\\tau}$ 인자)* 의 균형 — 정확히 $\\tau$ 에서 균형. 이 단일 매개변수가 PSP 의 *상승+감쇠* 모양을 *동시* 에 결정 [Slide L4 §10].',
        'slide_ref': '[Slide L4 §10]',
    },
    {
        'position': 7, 'kind': 'mcq', 'difficulty': 3, 'bloom': 'Apply',
        'topic_tag': 'driving-force',
        'prompt_md': 'AMPA 채널이 열려 있을 때, 휴지 ($V \\approx -70$ mV) 와 -50 mV 중 어디서 *EPSP 진폭* 이 더 큰가? ($E_\\text{AMPA} \\approx 0$)',
        'choices_json': [
            {'key': 'A', 'text': '-70 mV (휴지에서)', 'correct': True},
            {'key': 'B', 'text': '-50 mV (탈분극에서)', 'correct': False},
            {'key': 'C', 'text': '두 경우 모두 동일.', 'correct': False},
            {'key': 'D', 'text': 'AMPA 는 voltage 무관.', 'correct': False},
        ],
        'correct_key': 'A',
        'rationale_md': 'EPSP 진폭 ∝ driving force $|V - E_\\text{AMPA}|$. -70 → driving = 70, -50 → driving = 50. *Synaptic gain* 이 막전위에 의존 — *발화 임계 근처에선 EPSP 가 작아지는* 자기억제 효과. 이는 *integrator* 가 임계 근처에서 *덜 민감* 해지는 비선형성의 원천 [Slide L4 §10].',
        'slide_ref': '[Slide L4 §10]',
    },
    {
        'position': 8, 'kind': 'mcq', 'difficulty': 4, 'bloom': 'Evaluate',
        'topic_tag': 'common-misconception',
        'prompt_md': '*"NMDA 의 $Mg^{2+}$ block 을 풀려면 AP 가 반드시 필요하다"* — 평가하라.',
        'choices_json': [
            {'key': 'A', 'text': '맞다. AP 없이는 절대 풀리지 않는다.', 'correct': False},
            {'key': 'B', 'text': '*꼭 그렇진 않다*. 충분한 sub-threshold 탈분극 (여러 AMPA EPSP 합) 만으로도 부분적으로 풀린다.', 'correct': True},
            {'key': 'C', 'text': '$Mg^{2+}$ 는 AP 와 무관.', 'correct': False},
            {'key': 'D', 'text': 'NMDA 와 AP 는 직접 연결되지 않는다.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': '$Mg^{2+}$ 의 voltage-block 은 *연속적* (sigmoid) — 막이 -50 mV 정도로 부분 탈분극되면 일부 unblock. AP 까지 가지 않아도 *coincidence detection* 가능. 이것이 sub-threshold 학습 (silent synapse, slow plasticity) 의 분자적 기반. 흔한 오해: AP 가 *binary on/off* 이듯 NMDA 도 그렇다고 가정 [Slide L4 §11].',
        'slide_ref': '[Slide L4 §11]',
    },
    # Short-answer
    {
        'position': 9, 'kind': 'short_answer', 'difficulty': 1, 'bloom': 'Remember',
        'topic_tag': 'reversal',
        'prompt_md': '$E_\\text{Na}, E_K, E_\\text{Cl}$ 의 표준 값을 mV 단위로 (콤마로 구분) 답하라.',
        'correct_text': '+60, -90, -70',
        'accept_patterns': [
            r'\+?\s*60\s*[,;\s]+\s*[-−]\s*90\s*[,;\s]+\s*[-−]\s*70',
            r'(?i).*\+?60.*[-−]90.*[-−]70',
            r'(?i).*Na.*60.*K.*[-−]90.*Cl.*[-−]70',
        ],
        'rationale_md': '$E_\\text{Na} \\approx +58 \\sim +60$, $E_K \\approx -90$, $E_\\text{Cl} \\approx -70$ mV (척추동물 표준). 이 값들이 *AP 의 상한·하한* 과 *시냅스 reversal* 의 기준. Driving force 가 이로부터 결정.',
        'slide_ref': '[Slide L4 p.6]',
    },
    {
        'position': 10, 'kind': 'short_answer', 'difficulty': 2, 'bloom': 'Apply',
        'topic_tag': 'gating-exponent',
        'prompt_md': 'Hodgkin-Huxley $K_v$ 채널의 $P_\\text{open}$ 식을 작성하라 ($n$ 사용).',
        'correct_text': 'n^4',
        'accept_patterns': [
            r'(?i)\bn\s*\^?\s*\{?\s*4\s*\}?\b',
            r'(?i)P_?\{?open\}?\s*=\s*n\s*\^?\s*4\b',
        ],
        'rationale_md': '$K_v$ 의 4 개 동등 subunit 이 모두 활성 상태일 확률. $n$ 은 단일 subunit 의 활성 확률 ($\\in [0, 1]$), 시간·전압 의존. 즉 $P_\\text{open}^{K_v} = n^4$.',
        'slide_ref': '[Slide L4 p.10; L5 p.21]',
    },
    {
        'position': 11, 'kind': 'short_answer', 'difficulty': 2, 'bloom': 'Apply',
        'topic_tag': 'gating-exponent',
        'prompt_md': 'Hodgkin-Huxley $Na_v$ 채널의 $P_\\text{open}$ 식을 작성하라.',
        'correct_text': 'm^3 h',
        'accept_patterns': [
            r'(?i)\bm\s*\^?\s*\{?\s*3\s*\}?\s*\*?\s*h\b',
            r'(?i)P_?\{?open\}?\s*=\s*m\s*\^?\s*3\s*h\b',
        ],
        'rationale_md': '$Na_v$ 는 단일 polypeptide 의 4 도메인 — *3 활성* gate ($m^3$) × *1 inactivation* gate ($h$). $m$ 은 빠르게 활성, $h$ 는 늦게 비활성 — 이 *시간 분리* 가 spike upstroke + Na inactivation 의 시퀀스를 만든다.',
        'slide_ref': '[Slide L4 p.10; L5 p.21]',
    },
    {
        'position': 12, 'kind': 'mcq', 'difficulty': 3, 'bloom': 'Analyze',
        'topic_tag': 'shunting',
        'prompt_md': '*"Shunting inhibition"* 이 단순 hyperpolarization 보다 효과적인 이유로 가장 정확한 것은?',
        'choices_json': [
            {'key': 'A', 'text': 'Shunting 이 더 큰 음의 막전위를 만든다.', 'correct': False},
            {'key': 'B', 'text': 'Shunting 은 *컨덕턴스를 증가* 시켜 다른 입력의 효과를 *나누어 희석* 하므로, $V$ 변화는 작아도 *상대적 영향* 은 크다.', 'correct': True},
            {'key': 'C', 'text': 'Shunting 은 AP 를 직접 차단한다.', 'correct': False},
            {'key': 'D', 'text': 'Shunting 은 휴지 막전위와 무관하다.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': '$\\text{GABA}_A$ 활성화 → $g_\\text{GABA}$ 증가 → 다른 EPSP 의 effective $\\Delta V$ 가 $g_\\text{EPSP}/(g_\\text{leak} + g_\\text{GABA} + ...)$ 로 *감소*. 막전위 자체는 변화 작아도 *입력 통합* 이 둔화됨. 이것이 단순 hyperpolarization 보다 *효율적인 억제* — 적은 전류로 큰 효과 [Slide L4 §11].',
        'slide_ref': '[Slide L4 §11]',
    },
]


L4_TAKE_HOME = [
    {
        'position': 1, 'kind': 'derivation', 'difficulty': 4, 'max_points': 12, 'expected_time_min': 20,
        'topic_tag': 'alpha-function',
        'prompt_md': '''Alpha function $g(t) = A\\,t\\,e^{-t/t_\\text{peak}}$ 의 미분과 극값을 계산:
(a) (3점) $dg/dt$ 를 계산하고, 극대 시점을 결정.
(b) (3점) 극대 진폭 $g_\\text{max}$ 를 $A$ 와 $t_\\text{peak}$ 로 표현.
(c) (3점) 만약 $A$ 의 단위가 $\\mu\\text{S}/\\text{ms}$, $t_\\text{peak} = 1$ ms 이면, $g_\\text{max} = ?$ ($A = 100$ 가정). 단위 포함.
(d) (3점) Alpha function 이 *두 개의 1차 지수의 합성곱* (convolution) 의 한계 — *상승 시간상수 $\\tau_r$, 감쇠 시간상수 $\\tau_d$* 가 같아질 때 ($\\tau_r \\to \\tau_d \\equiv \\tau$) — 임을 *직관적* 으로 설명 (수식 유도 불필요).''',
        'model_answer_md': '''(a) **미분**: $g(t) = A t e^{-t/t_\\text{peak}}$. 곱의 법칙: $dg/dt = A e^{-t/t_\\text{peak}} + A t \\cdot (-1/t_\\text{peak}) e^{-t/t_\\text{peak}} = A e^{-t/t_\\text{peak}} (1 - t/t_\\text{peak})$. **극대 조건**: $dg/dt = 0$ → $1 - t/t_\\text{peak} = 0$ → $t = t_\\text{peak}$. ($e^{-t/t_\\text{peak}} > 0$ 항상.)

(b) **극대 진폭**: $g_\\text{max} = g(t_\\text{peak}) = A \\cdot t_\\text{peak} \\cdot e^{-1} = A t_\\text{peak} / e$.

(c) $g_\\text{max} = (100\\,\\mu\\text{S}/\\text{ms}) \\cdot (1\\,\\text{ms}) / e \\approx 100 / 2.718 \\approx 36.8\\,\\mu\\text{S}$.

(d) **두 지수의 convolution 한계**: 일반 PSP 는 *bi-exponential* — 빠른 상승 시간상수 $\\tau_r$ (ligand binding + channel opening) 과 느린 감쇠 시간상수 $\\tau_d$ (channel closing + neurotransmitter clearance) 의 *순차* 적용. 이 둘의 합성곱: $g(t) = g_0 (\\tau_d/(\\tau_d - \\tau_r))(e^{-t/\\tau_d} - e^{-t/\\tau_r})$. *극한* $\\tau_r \\to \\tau_d \\equiv \\tau$: 분모 0 으로 발산을 피하려면 L'Hopital → $g(t) = g_0 (t/\\tau) e^{-t/\\tau}$ — 정확히 alpha function 형태. **직관**: 두 시간상수가 같으면 *상승과 감쇠가 한 시간 척도로 융합* 되어 *단일* 매개변수로 PSP 모양 전체를 기술 가능. 실제 시냅스에서 $\\tau_r \\approx \\tau_d$ 인 경우 (e.g. AMPA $\\sim$ ms) alpha 가 좋은 근사.''',
        'rubric_md': '''총 12점.
- (a) 3점: 미분 (1점) + $1 - t/t_\\text{peak} = 0$ 도출 (1점) + $t = t_\\text{peak}$ 결론 (1점).
- (b) 3점: $g(t_\\text{peak})$ 대입 (1점) + $e^{-1}$ 인수 (1점) + 최종 표현 $A t_\\text{peak}/e$ (1점).
- (c) 3점: 정확한 수치 ≈ 36.8 (1점) + 단위 정확 (1점) + $e$ 사용 (1점). 36~37 범위 정답.
- (d) 3점: bi-exponential PSP 일반 형태 언급 (1점) + L'Hopital 또는 한계 인수 (1점) + 두 시간상수 융합 직관 (1점).''',
        'slide_ref': '[Slide L4 §10]',
    },
    {
        'position': 2, 'kind': 'derivation', 'difficulty': 4, 'max_points': 12, 'expected_time_min': 20,
        'topic_tag': 'membrane-equation-extended',
        'prompt_md': '''L3 의 *single conductance* 막 방정식을 *4 채널 형태* 로 확장:
(a) (3점) Leak ($g_L$, $E_L$), voltage-gated ($g_v(V,t)$, $E_v$), pump (electrogenic 전류 $I_\\text{pump}$ 상수 근사), ligand-gated ($g_\\text{syn}(t)$, $E_\\text{syn}$) 4 종을 모두 포함하는 KCL 식을 작성.
(b) (4점) 각 항의 *시간 의존성* 과 *전압 의존성* 의 차이를 표 (다음 표 채우기) 형식으로 정리:
| 채널 종류 | $g$ 의 $V$ 의존? | $g$ 의 $t$ 의존? | $E$ 가 fixed? |
(c) (3점) Leak 만 활성, $I_\\text{inj} = 0$, pump 무시 시 *steady state* $V_\\infty$ 와 *Nernst $E_K$* 가 같지 않은 이유를 구체 항으로 설명.
(d) (2점) 만약 *모든 channel 이 동시에 열려 있다면* (i.e. 모든 $g$ 가 큰 양수), 막은 어떤 전압으로 끌려가는가 (정량 지침 + 직관).''',
        'model_answer_md': '''(a) **확장 KCL**:
$$C_m \\frac{dV}{dt} = -g_L (V - E_L) - \\sum_v g_v(V,t) (V - E_v) - \\sum_s g_\\text{syn,s}(t) (V - E_\\text{syn,s}) - I_\\text{pump} + I_\\text{inj}.$$
( pump 는 *전류 형식* 으로 직접 추가 — conductance 형식 아님; 별도 *electrogenic* 항. )

(b) | 채널 종류 | $g$ 의 $V$ 의존? | $g$ 의 $t$ 의존? | $E$ 가 fixed? |
|---|---|---|---|
| Leak | ✗ (상수) | ✗ | ✓ ($E_L$) |
| Voltage-gated | ✓ ($m, h, n$ 의 $V$ 의존성) | ✓ ($\\tau_m(V)$ 동역학) | ✓ ($E_\\text{Na}, E_K$) |
| Pump (electrogenic) | (대체로) ✗ | (대체로) ✗ | (전압 형식 아님) |
| Ligand-gated | ✗ (수용체 자체는 voltage-independent; NMDA 예외) | ✓ ($g_\\text{syn}(t)$ alpha-form) | ✓ ($E_\\text{syn}$) |

(c) Leak 만 활성, $I_\\text{inj}=0$, pump 무시 시: $0 = -g_L(V_\\infty - E_L)$ → $V_\\infty = E_L$. 그러나 $E_L \\neq E_K$ — leak 채널은 *비선택* (여러 이온 통과) 이므로 $E_L$ 은 GHK 식의 가중평균 $\\approx -70$ mV 이고 $E_K \\approx -90$ mV. 즉 *leak 의 reversal 자체* 가 단일 이온의 Nernst 가 아닌 *혼합 평형* — Na leakage 가 K-only 보다 막을 약간 *덜 음수* 로 끌어올림.

(d) **모든 g 동시에 큰 양수 시**: $V_\\infty = (\\sum g_X E_X) / (\\sum g_X)$ — *conductance-가중 평균*. 모든 $g$ 가 같은 크기면 $V_\\infty$ 는 모든 $E_X$ 의 산술평균에 가까워진다. $E_\\text{Na} +60, E_K -90, E_\\text{Cl} -70$ 의 평균 ≈ -33 mV. *직관*: AP 의 *peak* 직후 모든 채널이 열린 상태와 비슷 — 막은 정상상태가 아닌 *비정상 high-conductance* 상태로 빠르게 -30 ~ 0 mV 로 끌려가다 K_v 우세로 재분극.''',
        'rubric_md': '''총 12점.
- (a) 3점: 4 항 모두 포함 (3점). 각 항 누락 −1.
- (b) 4점: 표 4 행 × 3 열 = 12 칸 중 정확 8 이상 (4점). 7 정확 (3점). 4-6 정확 (2점). 3 이하 (1점).
- (c) 3점: $V_\\infty = E_L$ 도출 (1점) + leak 의 비선택성 (1점) + GHK 가중 평균이 K Nernst 와 다름 (1점).
- (d) 2점: 가중평균 정성 (1점) + AP peak 직관 + 정량 추정 (1점).''',
        'slide_ref': '[Slide L4 p.4–6]',
    },
    {
        'position': 3, 'kind': 'essay', 'difficulty': 3, 'max_points': 10, 'expected_time_min': 15,
        'topic_tag': 'channel-selectivity',
        'prompt_md': '''$K_v$ 채널이 *4 개 동등 subunit* 인 반면 $Na_v$ 가 *1 polypeptide × 4 도메인* 으로 비대칭 진화한 *기능적 이유* 를 다음 관점에서 분석 (≥ 250 단어):
(a) (3점) Inactivation gate ($h$) 의 필요성과 *비대칭 구조* 의 관계.
(b) (4점) $K_v$ 가 *대칭* 일 수 있는 이유 — 즉 inactivation 이 *덜 중요* 한 이유.
(c) (3점) 진화적 관점: 두 채널 family 의 *발현 패턴 (분자/조직)* 이 어떻게 이 구조 차이를 반영하는가? (구체 예시 1-2 개)''',
        'model_answer_md': '''**(a) Inactivation 과 비대칭**: AP 의 정의적 특징은 *all-or-none* + *Na 자기제동*. Na 의 양의 피드백 ($V \\uparrow \\to m \\uparrow \\to g_\\text{Na} \\uparrow \\to V \\uparrow$) 은 외부 brake 가 없으면 막을 $E_\\text{Na} = +60$ mV 까지 무한 끌어올린다. *Inactivation gate* $h$ — 활성화 후 *시간 지연* 으로 닫히는 별도 게이트 — 가 이 폭주를 끝낸다. $h$ 는 *m 과는 다른 시간 척도* 에서 작동해야 (느려야) 하므로, 4 도메인이 *동일 함수* 를 갖는 대칭 구조로는 $h$ 를 별도로 진화시킬 수 없다. 단일 polypeptide × 4 비대칭 도메인 → 각 도메인이 *서로 다른 역할* 을 진화시킬 수 있는 *유전자 자유도* 제공 — 한 도메인이 inactivation ball-and-chain 으로 분화 가능.

**(b) $K_v$ 의 대칭성 이유**: K 의 역할은 AP 의 *재분극* — 막을 $E_K$ 쪽으로 빠르게 끌어내림. 양의 피드백이 *없다* (K efflux → V 하강 → K 채널이 *닫힘* → 자기 종료). 즉 K_v 자체가 *자기 제어* 이므로 별도의 inactivation gate 가 불필요. 모든 4 subunit 이 동일하게 활성/비활성 → 단순한 $n^4$ 제어. 대칭은 *진화적 단순성* 의 결과 — 별도 도메인 분화 압력이 없었다.

**(c) 진화·분자 발현**: $K_v$ family 는 *광범위 발현* — 거의 모든 흥분 세포에서 다양한 subtype (Kv1.x, Kv2.x, ..., Kv11.x = HERG) 으로 fine-tuning. 각 subtype 은 동일한 4-subunit 구조이지만 동역학이 미세 조정 (e.g. delayed rectifier vs A-type fast inactivation; A-type 은 별도 N-terminal "ball" 이 inactivation 을 추가 — 이것이 K_v 에서 inactivation 이 *옵션* 으로 진화한 사례). $Na_v$ family 는 9 paralogs (Nav1.1-1.9) 모두 *단일 polypeptide × 4 도메인* — 이 *고정* 구조 위에 SCN 유전자 다양화로 발현 부위 (CNS, PNS, cardiac) 를 분화. 즉 $Na_v$ 의 *비대칭 단일체* 가 inactivation 을 *필수* 로 보존하는 진화적 선택, $K_v$ 의 *대칭 다중체* 가 inactivation 을 *유연히* 옵션으로 추가/제거하는 진화적 자유도를 제공.''',
        'rubric_md': '''총 10점.
- (a) 3점: Na 양의 피드백 (1점) + inactivation 의 필요성 (1점) + 비대칭이 별도 gate 진화를 가능케 함 (1점).
- (b) 4점: K 가 자기 제어 (양의 피드백 없음) (1점) + inactivation 불필요 (1점) + 대칭의 진화적 단순성 (1점) + n^4 제어로 충분 (1점).
- (c) 3점: K_v 의 다양한 subtype + A-type inactivation 옵션 (1점) + Na_v 의 9 paralogs + 단일 구조 보존 (1점) + 두 family 의 진화적 자유도 비교 (1점).''',
        'slide_ref': '[Slide L4 p.10–11; L5 p.21]',
    },
    {
        'position': 4, 'kind': 'essay', 'difficulty': 4, 'max_points': 10, 'expected_time_min': 15,
        'topic_tag': 'shunting-vs-hyperpolarization',
        'prompt_md': '''*Shunting inhibition* 과 *hyperpolarizing inhibition* 의 차이를 다음으로 분석:
(a) (3점) $E_\\text{syn} = V_\\text{rest}$ 와 $E_\\text{syn} \\ll V_\\text{rest}$ 두 경우의 시냅스 효과 차이를 막 방정식으로 설명.
(b) (4점) 같은 EPSP 가 도달하는 dendrite 위치를 변화시킬 때 (e.g. apical 끝 vs soma 근처), shunting 의 효과 차이는? Cable 관점.
(c) (3점) Cortical 회로에서 *fast-spiking parvalbumin+ 인터뉴런* 이 주로 사용하는 억제 형태와 그 계산적 함의.''',
        'model_answer_md': '''**(a) 막 방정식 차이**: 시냅스 활성 시 $C_m dV/dt = -g_\\text{leak}(V - E_L) - g_\\text{syn}(V - E_\\text{syn}) + I_\\text{ext}$.

- *$E_\\text{syn} = V_\\text{rest}$*: 시냅스 reversal 이 휴지와 같으므로 *전류 자체* 는 0 (driving force = 0). 그러나 $g_\\text{syn}$ 증가는 *총 conductance* ($g_L + g_\\text{syn}$) 를 늘려 다른 입력의 effective $\\Delta V$ 를 *축소* — *shunting*. 막전위는 거의 변화 없지만 *민감도* 가 떨어진다.

- *$E_\\text{syn} \\ll V_\\text{rest}$* (예: $E_\\text{Cl} = -90$ mV, 미성숙 뉴런): driving force $V_\\text{rest} - E_\\text{syn} > 0$ → 음의 전류 → *hyperpolarizing*. 막이 더 음수로 직접 끌려간다.

**(b) Cable 위치별 shunting 효과**: dendrite 의 cable 동역학에 의해 신호는 $\\lambda$ 거리에서 $1/e$ 로 감쇠. *근위 (proximal) shunting* (soma 근처 GABA 시냅스) 은 모든 distal EPSP 를 *공통 path* 에서 차단 — *gating* 효과 큼. *원위 (distal) shunting* (apical 끝) 은 *해당 가지의 EPSP 만* 영향 — 효과 국소화. 즉 동일 shunting 이라도 *어디 있는가* 가 *얼마나 차단되는가* 를 결정. Pyramidal 뉴런의 *axo-axonic* GABA 시냅스 (axon initial segment) 가 가장 강력한 출력 차단인 이유.

**(c) Fast-spiking PV+ 인터뉴런**: 주로 axo-somatic 또는 axo-axonic 위치에 *shunting* GABA_A 시냅스. 계산적 함의: (1) *gain control* — 모든 입력의 effective gain 을 timing-precise 하게 조절, (2) *gamma 진동* — PV+ 의 빠른 시간상수 + shunting 이 30-80 Hz 동기화의 동역학 기반, (3) *winner-take-all* — 강한 EPSP 만 통과시키는 비선형 thresholding. Shunting 은 *상대적 비교* (gain) 에 강하고, hyperpolarizing 은 *절대적 음수화* (off-switch) 에 강함. PV+ 는 cortical *fast 동역학* 의 핵심.''',
        'rubric_md': '''총 10점.
- (a) 3점: 두 경우의 막 방정식 (1점) + driving force 차이 (1점) + shunting vs hyperpolarizing 결과 (1점).
- (b) 4점: cable 감쇠 언급 (1점) + 근위 shunting (gating) (1점) + 원위 shunting (국소) (1점) + axo-axonic 의 의의 (1점).
- (c) 3점: PV+ 위치 특정 (1점) + 계산적 함의 ≥ 2개 (gain control + gamma 또는 WTA) (1점) + shunting vs hyperpolarizing 비교 결론 (1점).''',
        'slide_ref': '[Slide L4 p.18–19]',
    },
]


def main():
    conn = psycopg2.connect(DB_DSN)
    try:
        insert_quiz_items(conn, 'L4', L4_QUIZ)
        insert_take_home(conn, 'L4', L4_TAKE_HOME)
        print(f'L4: {len(L4_QUIZ)} quiz items + {len(L4_TAKE_HOME)} take-home items')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
