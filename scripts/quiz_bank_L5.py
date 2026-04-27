#!/usr/bin/env python3
"""L5 quiz bank — Action Potential & Hodgkin–Huxley Theory."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from generate_quiz_bank import insert_quiz_items, insert_take_home, DB_DSN
import psycopg2

L5_QUIZ = [
    {
        'position': 1, 'kind': 'mcq', 'difficulty': 1, 'bloom': 'Remember',
        'topic_tag': 'ap-phases',
        'prompt_md': 'AP 의 4 국면을 *시간 순* 으로 정확히 나열한 것은?',
        'choices_json': [
            {'key': 'A', 'text': 'rest → upstroke → falling → AHP', 'correct': True},
            {'key': 'B', 'text': 'upstroke → rest → AHP → falling', 'correct': False},
            {'key': 'C', 'text': 'AHP → rest → upstroke → falling', 'correct': False},
            {'key': 'D', 'text': 'rest → falling → upstroke → AHP', 'correct': False},
        ],
        'correct_key': 'A',
        'rationale_md': '*Rest* (-70 mV, K leak 우세) → *upstroke* (Na 활성화 양의 피드백, peak 까지) → *falling* (Na inactivation + K_v 활성화로 재분극) → *AHP* (after-hyperpolarization, $V < V_\\text{rest}$ 잠시; K_v 가 천천히 닫히는 동안). 이 4 국면이 곧 HH 4 변수 ($V, m, h, n$) 의 동역학에 일대일 대응 [Slide L5 p.7–9].',
        'slide_ref': '[Slide L5 p.7–9]',
    },
    {
        'position': 2, 'kind': 'mcq', 'difficulty': 2, 'bloom': 'Understand',
        'topic_tag': 'voltage-clamp',
        'prompt_md': 'Voltage clamp 가 HH 측정을 가능케 한 *결정적* 트릭은?',
        'choices_json': [
            {'key': 'A', 'text': 'Ion 별 selective dye 를 사용해 분리 측정.', 'correct': False},
            {'key': 'B', 'text': '$V$ 를 강제 고정 → $dV/dt = 0$ → *capacitive 항 제거* → ionic 전류만 분리.', 'correct': True},
            {'key': 'C', 'text': '시간을 정지시켜 정상상태만 측정.', 'correct': False},
            {'key': 'D', 'text': '온도 조절로 inactivation 을 막음.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': '자유 막에선 $V, g_\\text{Na}(V,t), g_K(V,t), dV/dt$ 4 미지수 → 분리 불가능. Clamp $V$ → $dV/dt = 0$ → $C_m dV/dt = 0$ 사라짐 → 측정 전류 = $-I_\\text{ion}$. 이후 *각 step 에서 $V$ 를 다르게* 설정해 $g_X(V,t)$ 의 *시간 의존성* 만 분리. Pharmacology (TTX/TEA) 와 결합해 ion 별 분리 [Slide L5 p.10–11].',
        'slide_ref': '[Slide L5 p.10–11]',
    },
    {
        'position': 3, 'kind': 'mcq', 'difficulty': 2, 'bloom': 'Understand',
        'topic_tag': 'positive-feedback',
        'prompt_md': 'AP upstroke 의 *양의 피드백* (positive feedback) 메커니즘으로 가장 정확한 것은?',
        'choices_json': [
            {'key': 'A', 'text': '$V \\uparrow \\to m \\uparrow \\to g_\\text{Na} \\uparrow \\to I_\\text{Na}$ inward $\\uparrow \\to V \\uparrow \\uparrow$', 'correct': True},
            {'key': 'B', 'text': '$V \\uparrow \\to n \\uparrow \\to g_K \\uparrow \\to V \\uparrow$', 'correct': False},
            {'key': 'C', 'text': '$V \\uparrow \\to h \\uparrow \\to g_\\text{Na} \\uparrow$', 'correct': False},
            {'key': 'D', 'text': '$V \\downarrow \\to m \\uparrow$', 'correct': False},
        ],
        'correct_key': 'A',
        'rationale_md': '$m$ 은 *활성화* gate, $V$ 와 *동일 방향* 변화. 탈분극 → $m$ 빨리 커짐 → Na 채널 개방 → Na 내향 전류 (driving force $V - E_\\text{Na} < 0$) → 더 탈분극. 자기 가속. $h$ 는 *반대* 방향 ($V \\uparrow \\to h \\downarrow$) — *음의* 피드백 (지연된 inactivation). $n$ 은 *느린 활성화* — 음의 피드백 (재분극) [Slide L5 §2].',
        'slide_ref': '[Slide L5 §2]',
    },
    {
        'position': 4, 'kind': 'mcq', 'difficulty': 3, 'bloom': 'Apply',
        'topic_tag': 'refractory',
        'prompt_md': '*Absolute refractory period* 의 분자적 원인은?',
        'choices_json': [
            {'key': 'A', 'text': 'K_v 가 닫혀 있어 막이 너무 음수.', 'correct': False},
            {'key': 'B', 'text': '$h \\approx 0$ (Na inactivation 게이트 닫혀) — 어떤 자극으로도 새 AP 발생 *불가*.', 'correct': True},
            {'key': 'C', 'text': 'ATP 고갈로 pump 정지.', 'correct': False},
            {'key': 'D', 'text': 'AMPA 수용체 desensitization.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': 'AP peak 직후 $h \\approx 0$ 으로 *모든 Na 채널이 inactivated* — $V$ 가 다시 상승해도 $g_\\text{Na} = \\bar g_\\text{Na} m^3 h \\approx 0$ → upstroke 불가. $h$ 가 자동으로 회복 ($V$ 가 음수로 돌아온 후) 하기까지의 시간 (~1 ms) 이 absolute refractory. 이후 *relative refractory* — $h$ 부분 회복 + AHP 의 음의 막전위가 합쳐져 *큰 자극에서만* 재발화 가능 [Slide L5 §6].',
        'slide_ref': '[Slide L5 §6]',
    },
    {
        'position': 5, 'kind': 'mcq', 'difficulty': 3, 'bloom': 'Analyze',
        'topic_tag': 'gating-time',
        'prompt_md': '$\\tau_n > \\tau_m$ (즉 K 활성화가 Na 활성화보다 *느림*) 이 AP 모양에 미치는 영향은?',
        'choices_json': [
            {'key': 'A', 'text': 'AP 의 peak 가 더 음수가 된다.', 'correct': False},
            {'key': 'B', 'text': 'Upstroke 동안 K_v 가 *충분히 활성화되지 않아* Na 가 막을 $E_\\text{Na}$ 방향으로 끌어올림 — *시간 분리* 가 spike 의 가능성을 만든다.', 'correct': True},
            {'key': 'C', 'text': 'AP 가 발생하지 않는다.', 'correct': False},
            {'key': 'D', 'text': 'Refractory period 가 사라진다.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': 'AP 의 *존재 자체* 가 $\\tau_m \\ll \\tau_n$ 에 의존. 만약 $\\tau_n \\to \\tau_m$ 이면 K 가 Na 와 *동시* 에 활성화 → 두 전류가 즉시 상쇄 → spike 없음. 진화는 두 채널의 시간상수를 *분리* 시켜 spike 가능성을 확보. *오개념*: "큰 conductance 가 spike 를 만든다" — 사실은 *시간 비대칭* 이 핵심 [Slide L5 §3].',
        'slide_ref': '[Slide L5 §3]',
    },
    {
        'position': 6, 'kind': 'mcq', 'difficulty': 3, 'bloom': 'Apply',
        'topic_tag': 'ahp',
        'prompt_md': 'After-hyperpolarization (AHP) 가 발생하는 직접적 원인은?',
        'choices_json': [
            {'key': 'A', 'text': 'Na/K pump 가 일시적으로 활성화되기 때문.', 'correct': False},
            {'key': 'B', 'text': 'K_v 가 *느리게 닫히는* 동안 K efflux 가 지속 → 막이 $V_\\text{rest}$ 보다 더 음수 ($E_K \\approx -90$ 방향) 로 끌려감.', 'correct': True},
            {'key': 'C', 'text': 'Cl 채널의 갑작스러운 활성화.', 'correct': False},
            {'key': 'D', 'text': '시냅스 입력의 일시 중단.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': 'AP peak 후 $h$ 가 닫혀 Na 멈춤 + $n$ 이 *천천히* 0 으로 돌아오는 동안 $g_K$ 가 여전히 큼 → 막이 K 의 평형 ($E_K = -90$ mV) 쪽으로 끌려가 *V_rest 보다 더 음수*. *수십 ms* 후 $n \\to n_\\infty(V_\\text{rest})$ 로 회복하면 AHP 종료. 일부 뉴런은 추가로 $g_\\text{sra}$ (slow K, $Ca^{2+}$-activated) 가 더 깊은 medium-AHP 를 만든다 [Slide L5 §6; L7 §7].',
        'slide_ref': '[Slide L5 §6]',
    },
    {
        'position': 7, 'kind': 'mcq', 'difficulty': 4, 'bloom': 'Analyze',
        'topic_tag': 'identifiability',
        'prompt_md': 'Voltage clamp + pharmacology (TTX, TEA) 를 결합하면 *어떻게* HH 의 ion-별 conductance 를 분리할 수 있는가?',
        'choices_json': [
            {'key': 'A', 'text': 'TTX 로 Na 차단 → 남은 trace = $g_K$; TEA 로 K 차단 → 남은 trace = $g_\\text{Na}$.', 'correct': True},
            {'key': 'B', 'text': 'TTX 와 TEA 모두 동시에 사용해 baseline 을 측정.', 'correct': False},
            {'key': 'C', 'text': 'TTX 는 K 차단제, TEA 는 Na 차단제이므로 각각 분리.', 'correct': False},
            {'key': 'D', 'text': 'Pharmacology 는 HH 분리에 사용되지 않는다.', 'correct': False},
        ],
        'correct_key': 'A',
        'rationale_md': 'TTX (tetrodotoxin) 는 *Na 채널 selective blocker* — Na 차단 후 측정 = $g_K(t) (V - E_K)$. TEA (tetraethylammonium) 는 *K 채널 blocker* — K 차단 후 측정 = $g_\\text{Na}(t) (V - E_\\text{Na})$. 두 측정의 *차분* + *각 step 의 V 의존성* 을 fit 하여 $m, h, n$ 의 동역학 매개변수 ($\\alpha, \\beta$ 함수) 를 결정. 이 결합이 HH (1952) 의 4-변수 ODE 모델을 *식별 가능* 하게 한 핵심 [Slide L5 §3.1].',
        'slide_ref': '[Slide L5 §3.1]',
    },
    {
        'position': 8, 'kind': 'mcq', 'difficulty': 4, 'bloom': 'Evaluate',
        'topic_tag': 'common-misconception',
        'prompt_md': '*"AP 의 peak 가 정확히 $E_\\text{Na} = +60$ mV 까지 도달한다"* — 평가하라.',
        'choices_json': [
            {'key': 'A', 'text': '맞다. Na 가 평형 도달까지 흐른다.', 'correct': False},
            {'key': 'B', 'text': '*틀리다*. Peak ≈ +30 mV — *$E_\\text{Na}$ 에 접근하던 중 K_v 가 지연 활성화로 끼어들면서 종료* 된다.', 'correct': True},
            {'key': 'C', 'text': '맞다. 실제 측정값이 +60 mV 이다.', 'correct': False},
            {'key': 'D', 'text': '실험에 따라 다르므로 일반화 불가.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': '*상한* 은 $E_\\text{Na}$ 가 맞지만 *도달하지 않는다* — K_v 의 지연 활성화 ($\\tau_n > \\tau_m$) 가 막을 끌어내리기 시작하여 실제 peak 는 +30 mV 정도. *모든 척추동물 뉴런에서 거의 동일* — Na/K 의 conductance ratio + 시간상수가 진화적으로 보존된 결과 [Slide L5 §2].',
        'slide_ref': '[Slide L5 §2]',
    },
    # Short-answer
    {
        'position': 9, 'kind': 'short_answer', 'difficulty': 2, 'bloom': 'Remember',
        'topic_tag': 'gating-variables',
        'prompt_md': 'HH 의 4 변수를 나열하라 ($V$ 포함).',
        'correct_text': 'V, m, h, n',
        'accept_patterns': [
            r'(?i)V\s*[,;\s]\s*m\s*[,;\s]\s*h\s*[,;\s]\s*n\b',
            r'(?i)V\s*&\s*m\s*&\s*h\s*&\s*n\b',
            r'(?i).*\bV\b.*\bm\b.*\bh\b.*\bn\b',
        ],
        'rationale_md': '$V$: 막전위. $m$: Na_v 활성화 (빠름). $h$: Na_v 비활성화 (느림). $n$: K_v 활성화 (중간). 4 변수 ODE 시스템: $C_m dV/dt = -\\bar g_\\text{Na} m^3 h(V-E_\\text{Na}) - \\bar g_K n^4(V-E_K) - g_L(V-E_L) + I_\\text{ext}$ + 3 gating ODE.',
        'slide_ref': '[Slide L5 §1, p.21]',
    },
    {
        'position': 10, 'kind': 'short_answer', 'difficulty': 1, 'bloom': 'Remember',
        'topic_tag': 'pharmacology',
        'prompt_md': 'Na 채널을 selective 하게 차단하는 천연 독소 (HH 실험에 사용) 의 이름은?',
        'correct_text': 'TTX (tetrodotoxin)',
        'accept_patterns': [
            r'(?i)\bTTX\b',
            r'(?i)tetrodotoxin',
            r'(?i)복어\s*독|푸가\s*독',
        ],
        'rationale_md': 'TTX (tetrodotoxin) — 복어 (puffer fish) 등에서 추출. $Na_v$ 채널의 selectivity filter 입구를 차단. K_v 차단제는 *TEA* (tetraethylammonium). 두 toxin 의 selective 차단이 HH 의 ion-별 conductance 분리 측정을 가능케 했다.',
        'slide_ref': '[Slide L5 §3]',
    },
    {
        'position': 11, 'kind': 'short_answer', 'difficulty': 3, 'bloom': 'Apply',
        'topic_tag': 'open-probability',
        'prompt_md': '$m = 0.8, h = 0.3, n = 0.5$ 일 때, $P_\\text{open}^\\text{Na}$ 의 값을 답하라 (소수점 셋째 자리까지).',
        'correct_text': '0.154',
        'accept_patterns': [
            r'\b0[\.,]15[34]\b',
            r'\b0[\.,]1\d{1,2}\b',
            r'\b15[\.,]\d?\s*%',
        ],
        'rationale_md': '$P_\\text{open}^\\text{Na} = m^3 h = 0.8^3 \\times 0.3 = 0.512 \\times 0.3 = 0.1536 \\approx 0.154$. *직관*: 활성화 (m) 가 충분해도 inactivation (h) 가 부분이면 채널 활성도는 두 인수의 곱으로 큰 폭 감소.',
        'slide_ref': '[Slide L5 §1]',
    },
    {
        'position': 12, 'kind': 'mcq', 'difficulty': 4, 'bloom': 'Analyze',
        'topic_tag': 'common-misconception',
        'prompt_md': '*"All-or-none 은 channel 이 binary on/off 이기 때문이다"* — 평가하라.',
        'choices_json': [
            {'key': 'A', 'text': '맞다. 단일 채널은 0 또는 1.', 'correct': False},
            {'key': 'B', 'text': '*부분적으로 틀리다*. 단일 채널은 binary 지만, *수많은 채널의 평균* 으로 $P_\\text{open}$ 이 *연속* 값. All-or-none 은 *시스템 수준* 의 양의 피드백 (Na regenerative loop) 이 임계 (threshold) 를 만들어 *0 / 큰 값* 의 두 결과만 안정화하기 때문.', 'correct': True},
            {'key': 'C', 'text': '맞다. 막전위가 binary 이므로.', 'correct': False},
            {'key': 'D', 'text': '관련 없는 두 개념.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': '단일 채널은 stochastic on/off (Markov 상태). *Population $P_\\text{open}$* 은 [0,1] 의 연속 확률. All-or-none 의 *시스템적* 원천: 양의 피드백 (Na 폭주) 이 임계 미만에선 사그라들고, 임계 초과에선 폭주를 일으켜 *두 끝* 의 결과만 안정 — bistability 의 한 면. 이는 *bifurcation theory* 의 saddle-node bifurcation 과 연결 [Slide L5 §2; 흔한 오해].',
        'slide_ref': '[Slide L5 §2; §11]',
    },
]


L5_TAKE_HOME = [
    {
        'position': 1, 'kind': 'derivation', 'difficulty': 5, 'max_points': 20, 'expected_time_min': 30,
        'topic_tag': 'hh-derivation',
        'prompt_md': '''Hodgkin-Huxley 모델의 핵심 ODE 시스템을 *완전히* 작성하고 각 항의 의미를 설명하라:
(a) (5점) $V$ 에 대한 KCL (4 변수 등장).
(b) (5점) $m, h, n$ 각각의 동역학 ODE: $dx/dt = \\alpha_x(V)(1-x) - \\beta_x(V) x$ 형태로 작성. $\\alpha, \\beta$ 의 *물리적 의미* (transition rate) 를 한 문장씩.
(c) (5점) Steady state $x_\\infty(V)$ 와 시간상수 $\\tau_x(V)$ 를 $\\alpha, \\beta$ 로 표현. 한계 $V \\to \\pm \\infty$ 에서 $m_\\infty, h_\\infty, n_\\infty$ 의 한계값을 정성적으로 (sigmoid 의 모양).
(d) (5점) Voltage clamp 실험에서 *어떤 양을 측정* 하면 어떻게 $\\alpha, \\beta$ 를 *수치적으로* 결정하는가? (Step protocol + fitting 절차).''',
        'model_answer_md': '''(a) **막 KCL**:
$$C_m \\frac{dV}{dt} = -\\bar g_\\text{Na} m^3 h (V - E_\\text{Na}) - \\bar g_K n^4 (V - E_K) - g_L (V - E_L) + I_\\text{ext}$$
변수: $V$ (막전위), $m, h, n$ (gating 확률, $\\in [0,1]$). 매개변수: $\\bar g_\\text{Na}, \\bar g_K$ (최대 conductance), $E_\\text{Na} = +60, E_K = -90, E_L \\approx -60$ mV, $g_L$ (leak), $C_m \\approx 1\\,\\mu\\text{F}/\\text{cm}^2$, $I_\\text{ext}$ (외부 주입).

(b) **Gating ODE**:
$$\\frac{dm}{dt} = \\alpha_m(V)(1-m) - \\beta_m(V) m$$
$$\\frac{dh}{dt} = \\alpha_h(V)(1-h) - \\beta_h(V) h$$
$$\\frac{dn}{dt} = \\alpha_n(V)(1-n) - \\beta_n(V) n$$
- $\\alpha_x(V)$: closed → open 의 transition rate (단위: 1/ms). 즉 *닫힌* subunit 이 시간당 *열리는* 비율.
- $\\beta_x(V)$: open → closed 의 transition rate. *열린* subunit 이 *닫히는* 비율.
- 두 rate 는 모두 $V$ 의 함수 — *전압 의존성* 이 막전위에서 게이팅 변화를 만드는 이유.

(c) **정상상태 + 시간상수**: $dx/dt = 0$ 조건: $\\alpha(1-x) = \\beta x$ → $$x_\\infty(V) = \\frac{\\alpha(V)}{\\alpha(V) + \\beta(V)}.$$ 시간상수 (지수 회귀 속도): $$\\tau_x(V) = \\frac{1}{\\alpha(V) + \\beta(V)}.$$ 그러면 $dx/dt = (x_\\infty - x)/\\tau_x$ 라는 *standard form*.
**한계**: $V \\to +\\infty$ (강한 탈분극): $m_\\infty \\to 1$ (활성화), $h_\\infty \\to 0$ (비활성화), $n_\\infty \\to 1$ (활성화). $V \\to -\\infty$: $m_\\infty \\to 0$, $h_\\infty \\to 1$, $n_\\infty \\to 0$. 모두 sigmoidal monotone — m/n 은 증가, h 는 감소.

(d) **수치 결정 절차**:
1. **Step protocol**: 막을 holding voltage (-80 mV) 에서 갑자기 step voltage $V_\\text{cmd}$ 로 clamp.
2. **TTX/TEA 분리**: 한 번은 TTX 로 Na 차단 → 남은 trace = $g_K(t)(V_\\text{cmd}-E_K)$. 다른 한 번은 TEA 로 K 차단 → 남은 trace = $g_\\text{Na}(t)(V_\\text{cmd}-E_\\text{Na})$.
3. **단일 지수 fit**: $g_K(t) = \\bar g_K n^4(t)$. $V$ 가 *고정* 되어 있으므로 $\\alpha_n, \\beta_n$ 도 상수 → $n(t) = n_\\infty - (n_\\infty - n_0) e^{-t/\\tau_n}$. 즉 $n^4(t)$ 의 거듭제곱 sigmoid 형태로 fit → $n_\\infty(V_\\text{cmd}), \\tau_n(V_\\text{cmd})$ 결정.
4. **다양한 $V_\\text{cmd}$ 에서 반복** → $n_\\infty(V), \\tau_n(V)$ 곡선 (V 의 함수) 획득.
5. 역변환: $\\alpha_n(V) = n_\\infty(V)/\\tau_n(V)$, $\\beta_n(V) = (1 - n_\\infty(V))/\\tau_n(V)$.
6. Na 도 동일 — 단 *peak conductance* 와 *inactivation 시간상수* 가 빠른 transient 이므로 fit 이 더 까다롭다 ($g_\\text{Na}^\\text{peak} = \\bar g_\\text{Na} m_\\infty^3 h_\\infty$, 그리고 $h$ 의 회복은 또 다른 step).''',
        'rubric_md': '''총 20점.
- (a) 5점: 막 방정식 정확 (3점) + 모든 항 부호 정확 (1점) + 매개변수 정의 (1점).
- (b) 5점: 3 ODE 정확한 형태 (3점) + α, β 의 물리적 의미 (2점).
- (c) 5점: $x_\\infty = \\alpha/(\\alpha+\\beta)$ 정확 (1점) + $\\tau_x = 1/(\\alpha+\\beta)$ 정확 (1점) + standard form 변환 (1점) + sigmoidal 한계 m/h/n 모두 정확 (2점).
- (d) 5점: step protocol (1점) + TTX/TEA 분리 (1점) + 단일 지수 fit + n^4 (1점) + V_cmd 다회 반복 (1점) + α, β 역변환 (1점).''',
        'slide_ref': '[Slide L5 §1–3]',
    },
    {
        'position': 2, 'kind': 'derivation', 'difficulty': 5, 'max_points': 15, 'expected_time_min': 25,
        'topic_tag': 'gating-exponent-meaning',
        'prompt_md': '''$P_\\text{open}^{K_v} = n^4$ 와 $P_\\text{open}^{Na_v} = m^3 h$ 의 *지수* 가 channel 구조의 *직접 반영* 임을 보이라:
(a) (4점) $K_v$ 의 4 *동등* subunit 가정 하에 (i) 각 subunit 의 활성 확률이 $n$ 이고, (ii) 모두 *독립* 일 때, 모든 4 가 활성일 확률이 $n^4$ 임을 직접 유도.
(b) (4점) 만약 4 subunit 이 *완전히 의존적* (모두 함께 움직임) 이라면 $P_\\text{open}$ 이 어떻게 달라지는가? Real $K_v$ 의 동역학과 어느 모델이 더 잘 맞는가?
(c) (4점) $Na_v$ 의 *3 활성 + 1 inactivation* 구조에서 $m^3$ 의 3 은 어디서 오는가? Domain I, II, III 의 voltage sensor 가 모두 활성이어야 한다는 *분자 증거* 와 함께 설명.
(d) (3점) 만약 $h$ 게이트가 없다면 ($P_\\text{open} = m^3$) AP 가 어떻게 달라지겠는가?''',
        'model_answer_md': '''(a) **4 동등 subunit 독립 가정**: 각 subunit 의 활성 확률 = $P(\\text{active}) = n$, 비활성 확률 = $1 - n$. 4 개 subunit 모두 활성일 확률 (독립 → 곱셈): $$P(\\text{all 4 active}) = n \\times n \\times n \\times n = n^4.$$ 채널 개방 = 모든 4 subunit 동시 활성이라는 *구조적* 가정.

(b) **완전 의존 (cooperative) 모델**: 모든 4 subunit 이 단일 *macro-state* 로 묶인다면 $P_\\text{open} = n_\\text{macro}$ — *단일 1차 sigmoid*. 실제 측정은 *느린 sigmoid 상승 + 빠른 종료* — 단일 지수보다 *high-order* 모양 → $n^4$ (4 차 power) 가 더 잘 맞는다. Slide L5 p.21: *"k = 4 is consistent with the four-subunit structure"*. 의존 모델은 단순 sigmoid 라서 실험 곡선의 *상승부 가파름* 을 재현 못함.

(c) **$m^3$ 의 3 = 4 도메인 중 *3 의 voltage sensor***: $Na_v$ 는 단일 polypeptide 의 4 도메인 (I, II, III, IV). 분자 측정 (gating current, fluorescence) 결과: 도메인 I, II, III 의 S4 voltage sensor 가 *각각 활성* 되어 활성화 → $m \\times m \\times m = m^3$. 도메인 IV 의 S4 는 *inactivation* 에 관여 — 즉 별도 게이트 $h$. 따라서 $P_\\text{open}^{Na_v} = m^3 h$ — *비대칭* 4 도메인의 직접 반영.

(d) **$h$ 게이트 없는 가상 시나리오**: $P_\\text{open}^{Na_v} = m^3$ (지속). $V \\uparrow \\to m \\uparrow \\to g_\\text{Na} \\uparrow \\to V \\uparrow$ 양의 피드백이 *영구적*. 막은 $E_\\text{Na} = +60$ mV 까지 *상승하고 머무름*. K_v 가 활성화되어도 $V$ 가 떨어지면 $m$ 도 같이 작아지므로 *영원한 spike* — 즉 더 이상 spike 가 아님. *Inactivation* 이 곧 spike 의 *종료 조건* 이며, 이것이 없으면 *bistable* 막 (두 안정 V 사이를 오가는 다른 동역학) 이 된다.''',
        'rubric_md': '''총 15점.
- (a) 4점: 독립 가정 명시 (1점) + 곱셈 적용 (1점) + n^4 도출 (1점) + 구조적 의미 명시 (1점).
- (b) 4점: 의존 모델 = 단일 sigmoid (1점) + 실험 곡선의 상승부 (1점) + n^4 가 더 잘 맞는다는 결론 (1점) + Slide 인용 (1점).
- (c) 4점: 4 도메인 중 3 voltage sensor 활성 (1점) + 도메인 I/II/III 가 m, IV 가 h (1점) + 분자 증거 (gating current) 언급 (1점) + m^3 h 의 결합 식 (1점).
- (d) 3점: 양의 피드백 영구 (1점) + V → E_Na 머무름 (1점) + spike 종료 메커니즘 부재 결론 (1점).''',
        'slide_ref': '[Slide L5 p.21; §11]',
    },
    {
        'position': 3, 'kind': 'essay', 'difficulty': 4, 'max_points': 12, 'expected_time_min': 20,
        'topic_tag': 'identifiability-extended',
        'prompt_md': '''Voltage clamp 가 *없다면* HH 모델의 매개변수를 결정할 수 있는가? 다음으로 분석:
(a) (3점) Current clamp 만 있을 때, *측정 가능* 한 변수는 무엇이고 *불가능* 한 것은?
(b) (4점) 자유 막 (current clamp) 의 식 $C_m dV/dt = -g_\\text{Na}(V,t)(V-E_\\text{Na}) - g_K(V,t)(V-E_K) + ...$ 에서 *4 미지 시변량* ($V, g_\\text{Na}, g_K, dV/dt$) 을 *한 식* 으로 분리할 수 있는가? 식별성 분석.
(c) (3점) Voltage clamp 가 도입한 *결정적 단순화* 를 한 문장으로 요약. *왜* 이것이 식별 문제를 해결하는가?
(d) (2점) Voltage clamp 의 *가공적* 측면 (즉 자연스럽지 않다는 비판) 에 대해 *이론적 분리 도구* 로서의 가치를 옹호.''',
        'model_answer_md': '''(a) **Current clamp 측정 가능량**: $V(t)$, $I_\\text{ext}$ (인가 전류). **불가능**: 각 ion 별 $g_X(t)$ 의 분리 — $V$ 가 변화하는 동안 $g_X$ 가 *V 와 t 둘 다* 의존하므로 한 측정에서 시간 의존성 + 전압 의존성을 *분리* 할 수 없다.

(b) **4 미지 시변량**: $V(t)$ — 측정 가능. $dV/dt$ — $V(t)$ 에서 미분으로 얻음 (측정 가능). 그러나 $g_\\text{Na}(V,t)$ 와 $g_K(V,t)$ 는 *둘 다 미지* — 한 식에 두 미지수. 게다가 $V$ 가 변화하므로 $g_X$ 의 *V 의존성 형태* 도 동시에 미지. *식별 불가능*: 무한히 많은 $(g_\\text{Na}, g_K)$ 조합이 같은 $V(t)$ 곡선을 만든다 — 합 ($g_\\text{Na}(V-E_\\text{Na}) + g_K(V-E_K)$) 만 *관측* 되고, 분해 불가.

(c) **Voltage clamp 의 결정적 단순화**: $V$ 를 *상수* 로 강제 → $dV/dt = 0$ 의 capacitive 항 제거 + $g_X$ 의 V 의존성을 *각 step 에서 상수* 로 분리. 따라서 *시간 의존성만* 남음 → 단일 지수 fit 으로 $\\tau_x(V_\\text{cmd}), x_\\infty(V_\\text{cmd})$ 결정 가능. 식별 문제는 *각 step 마다 V 가 다르게 고정* 되는 *다중 실험 설계* 로 해결.

(d) **Voltage clamp 의 가공적 측면 옹호**: *실제 뉴런이 voltage clamp 를 받지 않는다* 는 비판은 옳지만, voltage clamp 는 *현상 자체를 측정* 하는 게 아니라 *분리된 conductance dynamics 를 추출* 하는 *이론적 도구*. 일단 $\\alpha, \\beta$ 함수가 결정되면, 이를 자유 막 ODE 에 다시 대입해 *예측* 한 V(t) 가 *실제 voltage clamp 가 없는 자유 막 측정* 과 일치 — 이것이 HH 모델의 *예측력 검증* 의 핵심. 즉 voltage clamp 는 *측정 도구* 이지 *현상 자체* 가 아니다. 측정 가능 vs 측정 불가능을 명확히 분리한 *역사적 통찰* 의 가치 [Slide L5 흔한 오해 §11].''',
        'rubric_md': '''총 12점.
- (a) 3점: 측정 가능 V(t), I_ext (1점) + dV/dt 도출 (1점) + g_X 분리 불가능 (1점).
- (b) 4점: 4 미지수 (1점) + 한 식으로 분리 불가능 결론 (1점) + 합만 관측 (1점) + 식별성 일반 논리 (1점).
- (c) 3점: V 상수 → capacitive 항 제거 (1점) + g 의 V 의존성을 step 별 분리 (1점) + 다중 step 으로 V 의존성 추출 (1점).
- (d) 2점: voltage clamp 가 도구임을 명시 (1점) + 자유 막 검증을 통한 모델 정당화 (1점).''',
        'slide_ref': '[Slide L5 §3, §11]',
    },
    {
        'position': 4, 'kind': 'essay', 'difficulty': 4, 'max_points': 10, 'expected_time_min': 15,
        'topic_tag': 'temporal-asymmetry',
        'prompt_md': '''*"AP 가 가능한 이유는 conductance 의 절대적 크기가 아니라 시간 비대칭이다"* 라는 명제를 다음으로 검토:
(a) (3점) $\\tau_m \\ll \\tau_n$ 가 spike 생성에 *왜* 필수적인지 phase plane 또는 *동역학* 관점으로 설명.
(b) (3점) 만약 $\\tau_n \\to \\tau_m$ (즉 K 와 Na 가 *동시* 활성화) 이면 막 동역학은 어떻게 달라지는가?
(c) (4점) 진화적으로 *왜* 이 시간 비대칭이 보존되었는가? 단순히 더 큰 $\\bar g_\\text{Na}$ 만으로는 spike 를 만들 수 없는 이유.''',
        'model_answer_md': '''(a) **시간 비대칭의 필요성**: 막 동역학은 다중 ODE 시스템. AP 의 핵심은 *fast positive feedback (Na) + slow negative feedback (K)* 의 *시간 분리*. $\\tau_m \\approx 0.1$ ms vs $\\tau_n \\approx 1$ ms — 한 자리 수 차이. Phase plane: $V$ 와 $n$ 의 평면에서 nullcline ($dV/dt = 0$, $dn/dt = 0$) 의 교차점이 *불안정 saddle* + *안정 limit cycle* 을 만든다. 빠른 V-axis 에서 양의 피드백이 폭주 → 느린 n 이 따라잡으며 limit cycle 닫음. 시간 분리가 곧 *2D 동역학의 saddle-node bifurcation* 구조를 보장.

(b) **$\\tau_n \\to \\tau_m$ 시나리오**: K 가 Na 와 즉시 활성화 → driving force 가 동시 두 방향으로 균형 → $V$ 변화 *작고 단조*. Phase plane 의 fast/slow 분리가 사라져 *limit cycle 이 사라지고 단일 안정 fixed point* 만 남음. 즉 막은 임계 자극에 *작은 sigmoidal 응답* 만 보일 뿐 *spike 없음*. 모든 자극에 대해 *graded* 응답.

(c) **진화적 보존 + 큰 $\\bar g_\\text{Na}$ 무용성**: 진화는 *속도가 다른 두 게이트* 를 별도 분자로 진화 — Na_v 의 빠른 m + K_v 의 느린 n + Na_v 의 더 느린 h. 시간상수는 channel 단백질의 *분자 동역학* 결정 (S4 voltage sensor 의 conformational change 속도, ball-and-chain 의 확산 등). 단순히 $\\bar g_\\text{Na}$ 를 키우면 *V 가 $E_\\text{Na}$ 로 더 빠르게* 끌려가지만, K 가 *동시에* 활성화되면 추가 driving force 가 정확히 상쇄. *시간 비대칭이 없으면 spike 가 *원리적으로* 불가능* — 어떤 conductance 비율로도 fast-slow 분리 없이는 limit cycle 이 형성되지 않는다. 진화는 *동역학 속도 분리* 를 spike 의 *정의* 로 보존했다 [Slide L5 §3].''',
        'rubric_md': '''총 10점.
- (a) 3점: τ_m << τ_n 의 시간 분리 (1점) + phase plane 또는 fast-slow 동역학 언급 (1점) + saddle-node + limit cycle 언급 (1점).
- (b) 3점: K-Na 즉시 균형 (1점) + V 변화 작아짐 (1점) + spike 없음 결론 (1점).
- (c) 4점: 시간상수의 분자적 결정 (1점) + 단순한 g_Na 증가의 무효성 (1점) + 시간 비대칭 없으면 spike 원리적 불가능 (1점) + 진화적 보존 (1점).''',
        'slide_ref': '[Slide L5 §3, §11]',
    },
]


def main():
    conn = psycopg2.connect(DB_DSN)
    try:
        insert_quiz_items(conn, 'L5', L5_QUIZ)
        insert_take_home(conn, 'L5', L5_TAKE_HOME)
        print(f'L5: {len(L5_QUIZ)} quiz items + {len(L5_TAKE_HOME)} take-home items')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
