#!/usr/bin/env python3
"""L7 quiz bank — Different Types of Computational Models of Single Neurons."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from generate_quiz_bank import insert_quiz_items, insert_take_home, DB_DSN
import psycopg2

L7_QUIZ = [
    {
        'position': 1, 'kind': 'mcq', 'difficulty': 1, 'bloom': 'Remember',
        'topic_tag': 'lif',
        'prompt_md': 'LIF (Leaky Integrate-and-Fire) 모델의 핵심 단순화는?',
        'choices_json': [
            {'key': 'A', 'text': 'Spike 자체를 *모델하지 않고* — 막전위가 임계 도달 시 reset, 이후 다시 충전.', 'correct': True},
            {'key': 'B', 'text': '$Na, K$ 채널의 동역학을 정확히 추적.', 'correct': False},
            {'key': 'C', 'text': '시냅스 동역학을 무시.', 'correct': False},
            {'key': 'D', 'text': '$V$ 가 항상 0.', 'correct': False},
        ],
        'correct_key': 'A',
        'rationale_md': 'LIF: $V < V_{th}$ 영역에서 $C dV/dt = -g_L(V-E_L) + I_e$ — RC 충전. $V \\geq V_{th}$ 면 spike 기록 + 즉시 $V \\leftarrow V_\\text{reset}$. *Spike 모양 자체는 모델 안 하고* 사건 시각만 기록 → HH 의 4 변수 ODE → *1 변수* 로 환원. 망 시뮬레이션에서 4 배 빠름 [Slide L7 §1].',
        'slide_ref': '[Slide L7 §1]',
    },
    {
        'position': 2, 'kind': 'mcq', 'difficulty': 2, 'bloom': 'Understand',
        'topic_tag': 'rheobase',
        'prompt_md': 'LIF 의 *rheobase* $I_\\text{thr}$ 정의로 가장 정확한 것은?',
        'choices_json': [
            {'key': 'A', 'text': '뉴런이 발화하는 최대 전류.', 'correct': False},
            {'key': 'B', 'text': '*$V_\\infty = E_L + R_m I_e$ 가 임계 $V_{th}$ 를 넘는* 최소 DC 전류 — i.e., $I_\\text{thr} = (V_{th} - E_L)/R_m$.', 'correct': True},
            {'key': 'C', 'text': '$\\bar g_\\text{Na}$ 의 값.', 'correct': False},
            {'key': 'D', 'text': 'Refractory period 중 인가 가능한 전류.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': '*Rheobase* = "발화를 *겨우* 시작시키는 DC 자극". LIF 에서 sub-threshold 충전이 $V_\\infty$ 에 점근 → 임계 $V_{th}$ 를 넘어야 spike. $V_\\infty < V_{th}$ 면 spike 못 함, $V_\\infty > V_{th}$ 면 발화 시작. 경계: $V_\\infty = V_{th} \\to I_e = (V_{th} - E_L)/R_m$. 임계 *전류값* (전압 아님) [Slide L7 §3].',
        'slide_ref': '[Slide L7 §3]',
    },
    {
        'position': 3, 'kind': 'mcq', 'difficulty': 3, 'bloom': 'Apply',
        'topic_tag': 'fi-curve',
        'prompt_md': 'LIF 의 firing rate $r(I)$ 가 큰 $I_e$ 에서 *포화* 되는 값은?',
        'choices_json': [
            {'key': 'A', 'text': '$1/\\tau_m$', 'correct': False},
            {'key': 'B', 'text': '$1/\\tau_\\text{ref}$ (refractory period 의 역수)', 'correct': True},
            {'key': 'C', 'text': '$\\bar g_\\text{Na}$', 'correct': False},
            {'key': 'D', 'text': '발화율은 무한히 증가.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': 'Refractory period $\\tau_\\text{ref}$ 는 spike 후 다음 spike 사이의 *최소* 시간. $I_e$ 가 매우 크면 sub-threshold 충전이 즉시 임계 도달 → 발화 사이 시간이 $\\tau_\\text{ref}$ 로 *제한*. 그러므로 $r_\\text{max} = 1/\\tau_\\text{ref}$. 일반적으로 $\\tau_\\text{ref} \\sim 4$ ms → $r_\\text{max} \\approx 250$ Hz [Slide L7 §3].',
        'slide_ref': '[Slide L7 §3]',
    },
    {
        'position': 4, 'kind': 'mcq', 'difficulty': 3, 'bloom': 'Analyze',
        'topic_tag': 'identifiability-models',
        'prompt_md': 'Izhikevich 모델 (a, b, c, d) 의 *식별성* 문제 — 표준 실험 (sub-threshold step, f-I 곡선) 만으로 4 매개변수를 분리할 수 있는가?',
        'choices_json': [
            {'key': 'A', 'text': '예. 4 개 모두 분리 가능.', 'correct': False},
            {'key': 'B', 'text': '*아니오*. f-I 곡선만으론 (a, b, c, d) 의 *조합* 이 같은 곡선을 만들 수 있다 — *식별 불가능*.', 'correct': True},
            {'key': 'C', 'text': '예. 정상상태 측정만으로 충분.', 'correct': False},
            {'key': 'D', 'text': '관련 없는 매개변수.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': 'Izhikevich 의 4 매개변수가 *동시* 효과를 줘 (e.g. a 와 d 모두 burst 패턴 결정) f-I 곡선 한 측정으론 분리 불가. *Spike pattern + ISI distribution* 같은 *시간 의존* 측정 추가가 필요. 이것이 LIF (4 매개변수, 표준 실험으로 *식별 가능*) 와 Izhikevich (식별 불가) 의 핵심 차이. 모델 선택 = 질문 + *측정 식별성* [Slide L7 §10.1].',
        'slide_ref': '[Slide L7 §10.1]',
    },
    {
        'position': 5, 'kind': 'mcq', 'difficulty': 2, 'bloom': 'Understand',
        'topic_tag': 'computation-cost',
        'prompt_md': '망 시뮬레이션에서 *N* 뉴런 LIF vs HH 망의 ODE 개수 비율은?',
        'choices_json': [
            {'key': 'A', 'text': '1 : 1', 'correct': False},
            {'key': 'B', 'text': '1 : 4 (HH 가 4 변수)', 'correct': True},
            {'key': 'C', 'text': '1 : 100', 'correct': False},
            {'key': 'D', 'text': 'LIF 가 더 많다.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': 'LIF: 1 변수 ($V$) per 뉴런 → $N$ ODE. HH: 4 변수 ($V, m, h, n$) per 뉴런 → $4N$ ODE. *4 배* 차이. 시뮬레이션 비용 (시간) 이 ODE 개수에 비례하므로 같은 시간에 *4 배 큰 망* 가능. $10^6$ 뉴런 LIF 망 (단일 GPU 실시간 가능) vs $10^4 \\sim 10^5$ HH (한 차수 작음) — 망 동역학 연구는 LIF 가 표준 [Slide L7 §10].',
        'slide_ref': '[Slide L7 §10]',
    },
    {
        'position': 6, 'kind': 'mcq', 'difficulty': 3, 'bloom': 'Apply',
        'topic_tag': 'model-selection',
        'prompt_md': '"이 뉴런의 *spike timing 패턴* 이 어떻게 다양한가" 라는 질문에 가장 적합한 모델은?',
        'choices_json': [
            {'key': 'A', 'text': 'LIF — 단순하고 빠름.', 'correct': False},
            {'key': 'B', 'text': 'Izhikevich (또는 AdEx) — 4 매개변수로 burst, RS, IB, FS 등 *다양한 spike 패턴* 표현 가능.', 'correct': True},
            {'key': 'C', 'text': 'HH — biophysically 정확.', 'correct': False},
            {'key': 'D', 'text': '모델 선택 무관.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': 'Izhikevich (2003) 의 *(a, b, c, d) 4 매개변수* 가 21 가지 spike 패턴 (regular spiking, intrinsic bursting, fast spiking, low-threshold spiking, ...) 을 표현 가능. 식별성은 떨어지지만 *spike pattern variety* 가 핵심 질문이라면 최적. LIF 는 단조 발화만 가능, HH 는 변화하기엔 너무 무거움. *모델 선택 = 질문 선택* [Slide L7 §6, 9].',
        'slide_ref': '[Slide L7 §9]',
    },
    {
        'position': 7, 'kind': 'mcq', 'difficulty': 3, 'bloom': 'Analyze',
        'topic_tag': 'lif-fitting',
        'prompt_md': 'LIF 의 polynomial f-I 곡선 $r(I) = 1/[\\tau_m \\ln((R_m I + E_L - V_\\text{reset})/(R_m I + E_L - V_{th}))]$ 가 *biological* AP 와 다른 점?',
        'choices_json': [
            {'key': 'A', 'text': 'Spike 모양 (upstroke/AHP) 이 없음 — *event-only* 표현.', 'correct': True},
            {'key': 'B', 'text': '발화율이 무한히 증가.', 'correct': False},
            {'key': 'C', 'text': 'Refractory period 가 없음.', 'correct': False},
            {'key': 'D', 'text': '시냅스 입력에 반응 안 함.', 'correct': False},
        ],
        'correct_key': 'A',
        'rationale_md': 'LIF 의 *event-only*: spike 발생 시각만 기록, 막전위 자체는 reset 으로 점프. 따라서 (1) AP 의 *모양* (peak, AHP 깊이, refractory 종류) 정보 없음, (2) Na/K 채널 동역학 미포함. 망 시뮬레이션에서 *언제 spike* 가 핵심이고 *spike 모양* 이 부차적일 때 적합 [Slide L7 §6].',
        'slide_ref': '[Slide L7 §6]',
    },
    {
        'position': 8, 'kind': 'mcq', 'difficulty': 4, 'bloom': 'Evaluate',
        'topic_tag': 'common-misconception',
        'prompt_md': '*"Biological 으로 가장 정확한 모델 (HH) 이 항상 최선이다"* — 평가하라.',
        'choices_json': [
            {'key': 'A', 'text': '맞다. HH 가 정확하므로.', 'correct': False},
            {'key': 'B', 'text': '*틀리다*. *질문에 따라 적합한 모델이 다르다*. 예: $10^6$-뉴런 망의 *통합 발화율 동역학* 은 LIF 로, *spike pattern variety* 는 Izhikevich 로, *spike 생성 메커니즘* 은 HH 로.', 'correct': True},
            {'key': 'C', 'text': 'HH 는 절대 사용하지 말아야.', 'correct': False},
            {'key': 'D', 'text': '관련 없는 두 개념.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': '*Realism ≠ 좋은 모델*. HH 의 4 변수 + biological detail 은 *spike 생성 메커니즘* 을 묻는 질문에 최적. 그러나 (i) 망 동역학은 LIF, (ii) spike 패턴은 Izhikevich, (iii) dendrite 비선형성은 multi-compartment, (iv) 학습은 rate-model + Hebbian. 모델 = *질문에 가장 단순* 한 추상화 [Slide L7 §11].',
        'slide_ref': '[Slide L7 §11]',
    },
    # Short-answer
    {
        'position': 9, 'kind': 'short_answer', 'difficulty': 2, 'bloom': 'Apply',
        'topic_tag': 'rheobase-formula',
        'prompt_md': 'LIF 의 rheobase $I_\\text{thr}$ 를 $V_{th}, E_L, R_m$ 으로 답하라.',
        'correct_text': '(V_th − E_L) / R_m',
        'accept_patterns': [
            r'(?i)\(?\s*V_?\{?th\}?\s*[-−]\s*E_?L\s*\)?\s*/\s*R_?m',
            r'(?i)\(?\s*V_?th\s*[-−]\s*E_L\s*\)?\s*/\s*R_m',
        ],
        'rationale_md': '$I_\\text{thr} = (V_{th} - E_L)/R_m$. 직관: $V_\\infty = E_L + R_m I_e$ 가 임계를 넘으려면 $R_m I_e > V_{th} - E_L$. 단위 점검: V/Ω = A. *DC* 자극 기준 — pulse 자극이면 더 큰 전류 필요 (충전 시간 부족).',
        'slide_ref': '[Slide L7 §3]',
    },
    {
        'position': 10, 'kind': 'short_answer', 'difficulty': 2, 'bloom': 'Remember',
        'topic_tag': 'firing-saturation',
        'prompt_md': 'LIF 의 *최대 발화율* 을 결정하는 매개변수는? (한 단어 또는 기호)',
        'correct_text': 'τ_ref',
        'accept_patterns': [
            r'(?i)\\?tau_?\{?ref\}?',
            r'(?i)refractory\s+period',
            r'(?i)\\?tau_?r\b',
        ],
        'rationale_md': '$r_\\text{max} = 1/\\tau_\\text{ref}$. 이 값을 *bypass* 하려면 모델에 refractory 자체를 제거 — 그러면 $V$ 가 계속 임계 도달 → 무한 발화 (비현실적). 일반적으로 $\\tau_\\text{ref} \\approx 2-5$ ms → $r_\\text{max} \\approx 200-500$ Hz, 실제 fast-spiking 인터뉴런과 일치.',
        'slide_ref': '[Slide L7 §3]',
    },
    {
        'position': 11, 'kind': 'short_answer', 'difficulty': 3, 'bloom': 'Apply',
        'topic_tag': 'computation-cost',
        'prompt_md': '$10^6$ 뉴런 LIF 망과 $10^6$ 뉴런 HH 망 — 같은 GPU 에서 시뮬레이션 시 LIF 는 실시간 가능, HH 는 *불가능*. 이 *원인* 매개변수 (LIF 의 어떤 양의 *몇 배* 인가)?',
        'correct_text': '4 (HH 의 ODE 개수가 LIF 의 4배)',
        'accept_patterns': [
            r'\b4\s*[xX×]\b',
            r'(?i)4\s*배',
            r'(?i)4\s*times',
            r'\b4\s*ODE',
        ],
        'rationale_md': 'HH 는 (V, m, h, n) 4 변수 → LIF (V) 1 변수의 4 배. ODE 시간복잡도 ∝ 변수 개수. 또한 HH 의 시간 step 이 더 작아야 함 ($\\tau_m \\approx 0.1$ ms 의 동역학 추적) — 추가로 ~5 배. 종합 ~20 배 차이. $10^6$ LIF 가 GPU 1 장에 가능하면 HH 는 $5 \\times 10^4$ 정도가 한계.',
        'slide_ref': '[Slide L7 §10]',
    },
    {
        'position': 12, 'kind': 'mcq', 'difficulty': 4, 'bloom': 'Analyze',
        'topic_tag': 'common-misconception',
        'prompt_md': '*"Izhikevich 모델은 HH 보다 더 정확하다"* — 평가하라.',
        'choices_json': [
            {'key': 'A', 'text': '맞다. 더 적은 변수로 같은 결과.', 'correct': False},
            {'key': 'B', 'text': '*틀리다*. Izhikevich 는 *abstraction level 이 다른* 모델. spike pattern variety 가 강점이지만 *biophysical 정확성* (이온 채널 conductance) 은 부재. 두 모델은 다른 질문에 답.', 'correct': True},
            {'key': 'C', 'text': '맞다. HH 는 obsolete.', 'correct': False},
            {'key': 'D', 'text': '두 모델 동일.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': 'Izhikevich 는 *phenomenological* — spike 패턴을 4 매개변수 fit 으로 재현하지만, $g_\\text{Na}, g_K$ 같은 *biophysical 양* 과의 직접 매핑이 없음. HH 는 *mechanistic* — ion-specific dynamics 와 spike 생성을 연결. *추상화 수준이 다름*. 두 모델의 비교는 "어느 모델이 맞느냐" 가 아니라 "어느 질문에 적합한가" 의 문제 [Slide L7 §11].',
        'slide_ref': '[Slide L7 §11]',
    },
]


L7_TAKE_HOME = [
    {
        'position': 1, 'kind': 'derivation', 'difficulty': 4, 'max_points': 15, 'expected_time_min': 25,
        'topic_tag': 'lif-isi',
        'prompt_md': '''LIF 의 inter-spike interval (ISI) 식을 closed form 으로 유도:
(a) (3점) Sub-threshold LIF: $\\tau_m dV/dt = -(V - V_\\infty)$, $V_\\infty = E_L + R_m I_e$. 일반해 $V(t) = V_\\infty + (V_0 - V_\\infty)e^{-t/\\tau_m}$ 작성.
(b) (4점) Spike 직후 reset $V(0) = V_\\text{reset}$. 다음 spike 시점 $t = t_\\text{ISI}$ 는 $V(t_\\text{ISI}) = V_{th}$ 조건. 이로부터 $t_\\text{ISI}$ 에 대해 풀라.
(c) (4점) 결과를 $r(I) = 1/(t_\\text{ISI} + \\tau_\\text{ref})$ 로 변환하여 closed-form $r(I)$ 도출.
(d) (4점) $V_\\infty < V_{th}$ 일 때 $r(I) = 0$ (발화 안 함) 임을 보이고, $V_\\infty > V_{th}$ 의 한계 $I \\to \\infty$ 에서 $r \\to 1/\\tau_\\text{ref}$ 가 됨을 보이라.''',
        'model_answer_md': '''(a) $\\tau_m dV/dt = -(V - V_\\infty)$, 분리변수: $du/u = -dt/\\tau_m$ ($u = V - V_\\infty$). 적분 + 초기조건 $V(0) = V_0$: $$V(t) = V_\\infty + (V_0 - V_\\infty) e^{-t/\\tau_m}.$$

(b) 초기 $V_0 = V_\\text{reset}$. 임계 도달 조건 $V(t_\\text{ISI}) = V_{th}$:
$$V_{th} = V_\\infty + (V_\\text{reset} - V_\\infty) e^{-t_\\text{ISI}/\\tau_m}$$
$$e^{-t_\\text{ISI}/\\tau_m} = \\frac{V_{th} - V_\\infty}{V_\\text{reset} - V_\\infty}$$
$$\\boxed{t_\\text{ISI} = \\tau_m \\ln \\frac{V_\\text{reset} - V_\\infty}{V_{th} - V_\\infty}.}$$

(c) **Firing rate** = (1 spike) / (period $t_\\text{ISI} + \\tau_\\text{ref}$):
$$r(I) = \\frac{1}{t_\\text{ISI} + \\tau_\\text{ref}} = \\frac{1}{\\tau_\\text{ref} + \\tau_m \\ln \\frac{V_\\text{reset} - V_\\infty}{V_{th} - V_\\infty}}.$$
$V_\\infty = E_L + R_m I$ 대입 → $r(I)$ 는 $I$ 의 함수. 단조 증가 sigmoid (rheobase 이상).

(d) **한계 분석**:
- $V_\\infty < V_{th}$: $V(t)$ 가 $V_\\infty$ 에 점근 — 절대 임계 도달 못 함. $t_\\text{ISI} \\to \\infty$ → $r = 0$. (이론적 발산).
- $V_\\infty \\to \\infty$ (즉 $I \\to \\infty$): $\\ln((V_\\text{reset} - V_\\infty)/(V_{th} - V_\\infty)) \\to \\ln(1) = 0$ ($V_\\infty$ 가 압도적으로 큼). 즉 $t_\\text{ISI} \\to 0$, $r \\to 1/\\tau_\\text{ref}$.
- 직관: 강한 자극이면 충전이 즉시 → spike 사이 시간이 *refractory 만으로* 제한 → 최대 발화율.''',
        'rubric_md': '''총 15점.
- (a) 3점: 분리변수 (1점) + 적분 + 초기조건 (1점) + 일반해 (1점).
- (b) 4점: 임계 도달 조건 (1점) + 지수 정리 (1점) + log 변환 (1점) + 최종 t_ISI 표현 (1점).
- (c) 4점: r(I) 정의 (1점) + 분모 표현 (1점) + V_∞ 대입 (1점) + 단조 증가 sigmoid 명시 (1점).
- (d) 4점: V_∞ < V_th 한계 (2점) + I → ∞ 한계 (2점). 둘 다 정확한 결론.''',
        'slide_ref': '[Slide L7 §3]',
    },
    {
        'position': 2, 'kind': 'derivation', 'difficulty': 4, 'max_points': 12, 'expected_time_min': 20,
        'topic_tag': 'spike-frequency-adaptation',
        'prompt_md': '''*Spike-frequency adaptation* (SFA) 을 LIF 에 추가하는 메커니즘:
(a) (3점) $C dV/dt = -g_L(V-E_L) - g_\\text{sra}(V - E_K) + I_e$ 에 SFA 변수 $g_\\text{sra}$ 가 추가. $g_\\text{sra}$ 의 동역학 ODE 작성 ($\\tau_\\text{sra}$, $\\Delta g$ 매개변수 사용).
(b) (4점) Spike 발생 시 $g_\\text{sra} \\to g_\\text{sra} + \\Delta g$ (jump). Spike 사이 시간 동안 $g_\\text{sra}$ 가 어떻게 회복되는가? Closed form 시간 의존성.
(c) (3점) 정상상태 spike train ($r$ 일정) 에서 $g_\\text{sra}$ 의 *평균값* 을 $r, \\tau_\\text{sra}, \\Delta g$ 로 표현.
(d) (2점) 이 mechanism 이 *adaptation* 을 만드는 이유 — 첫 spike 이후 발화율이 점진적으로 *낮아지는* 효과를 정성적으로 설명.''',
        'model_answer_md': '''(a) **SFA ODE**: $g_\\text{sra}$ 는 spike-triggered K-like conductance. Spike 사이 시간 동안 지수 감쇠:
$$\\tau_\\text{sra} \\frac{dg_\\text{sra}}{dt} = -g_\\text{sra}.$$
즉 $g_\\text{sra}$ 가 0 으로 회복되는 1차 ODE. 매개변수: $\\tau_\\text{sra} \\sim 100$ ms (slow), $\\Delta g \\sim 0.05 \\bar g_L$ (per spike increment).

(b) **Spike 사이 회복**: 직전 spike 에서 $g_\\text{sra}(t = 0^+) = g_0 + \\Delta g$ (이전 값 + jump). 이후 closed form: $$g_\\text{sra}(t) = (g_0 + \\Delta g) e^{-t/\\tau_\\text{sra}}.$$ 다음 spike 까지 $t = t_\\text{ISI}$ 동안 감쇠.

(c) **정상상태 평균**: 발화율 $r$ 의 정상 spike train 에서, 한 ISI 동안의 시간 평균:
$$\\langle g_\\text{sra} \\rangle = \\Delta g \\cdot \\frac{r \\tau_\\text{sra}}{1 - e^{-1/(r \\tau_\\text{sra})}}.$$
또는 $r \\tau_\\text{sra} \\gg 1$ 한계 (강한 발화) 에서 $\\langle g_\\text{sra} \\rangle \\to r \\tau_\\text{sra} \\Delta g$ — *발화율 ∝ 평균 SFA conductance*.

(d) **Adaptation 메커니즘**: 첫 spike 직후 $g_\\text{sra}$ 가 jump → 막의 effective leak 증가 → 다음 충전이 *느려지고* + driving force 가 $E_K$ 쪽으로 끌려 *감소* → 다음 spike 도달 시간 지연. 매번의 spike 가 $g_\\text{sra}$ 를 더 누적 (지수적으로 정상값에 접근) → 발화율이 *시간에 따라 감소* → 정상 발화율로 점근. 결과: 시작 발화율 (high) → 정상 발화율 (lower). 이것이 cortical pyramidal 뉴런의 *regular spiking with adaptation* (RSA) 패턴.''',
        'rubric_md': '''총 12점.
- (a) 3점: ODE 정확 (2점) + 매개변수 의미 (1점).
- (b) 4점: 초기조건 정확 (1점) + 지수 감쇠 식 (1점) + Δg 의 jump 메커니즘 (1점) + closed form (1점).
- (c) 3점: 정상상태 적분 (1점) + 한계 r τ ≫ 1 시도 (1점) + 평균식 (1점). 정확한 closed form 어려우면 한계 식만으로 부분 점수.
- (d) 2점: g_sra 가 충전 속도/driving force 변화시킴 (1점) + 시간에 따른 발화율 감소 결론 (1점).''',
        'slide_ref': '[Slide L7 §7]',
    },
    {
        'position': 3, 'kind': 'essay', 'difficulty': 4, 'max_points': 12, 'expected_time_min': 20,
        'topic_tag': 'identifiability-comparison',
        'prompt_md': '''LIF, Izhikevich, HH 의 *식별성 (identifiability)* 을 비교하라:
(a) (3점) LIF (4 매개변수): 각 매개변수가 *어떤 표준 실험* 으로 결정되는가? 식별 가능한가?
(b) (4점) Izhikevich (4 매개변수): f-I 곡선만으로 식별 가능한가? 추가로 어떤 측정이 필요?
(c) (5점) HH (수십 매개변수): voltage clamp + pharmacology 의 *결합* 이 어떻게 식별을 가능케 하는지 (또는 어렵게 만드는지) 분석. *완전* 식별 가능?''',
        'model_answer_md': '''(a) **LIF (V_th, V_reset, R_m, τ_m)**: *완전 식별 가능*.
- $\\tau_m$: sub-threshold step 의 지수 회귀 곡선 fit.
- $R_m$: 같은 step 의 정상상태 진폭.
- $V_{th}$: 발화 직전의 막전위 (또는 rheobase 로부터 역산).
- $V_\\text{reset}$: spike 직후 막전위 측정.
4 측정으로 4 매개변수 분리 — *완전 식별*.

(b) **Izhikevich (a, b, c, d)**: f-I 곡선만으론 식별 *불가능*. 4 매개변수가 동시에 spike 패턴 + ISI distribution + AHP 모양 등에 영향. 같은 f-I 곡선을 만드는 (a, b, c, d) 조합이 *무한히 많음* (parameter compensation). 추가 측정:
- ISI distribution
- Spike pattern category (RS/IB/FS/LTS/...) classification
- Phase plot ($v$ vs $u$)
- Bifurcation 분석 (rheobase 근처 동역학)
이 모든 측정을 결합해야 4 매개변수의 *조합 공간* 을 줄여나갈 수 있고, 그래도 일부 *parameter ridge* 가 남아 완전 분리는 어려움.

(c) **HH (수십 매개변수)**: $\\bar g_\\text{Na}, \\bar g_K, g_L, E_\\text{Na}, E_K, E_L, C_m$ + α, β 함수의 매개변수 (각 ~6 개, 3 gating × 2 함수). 총 30+ 매개변수.

**Voltage clamp + pharmacology 의 식별 트릭**:
1. **TTX/TEA 분리**: 한 번에 한 종류의 ion 만 측정 — 4 변수 ODE 를 *부분 선형화*.
2. **Step protocol**: 각 V_cmd 에서 *단일 지수* fit → α, β 를 V 의 함수로 추출 (다회 step 으로 V-의존성 곡선 획득).
3. **Pharmacology 결합**: TTX 하에 K 만, TEA 하에 Na 만 — 두 ion 의 매개변수를 *병렬* 결정.

이렇게 *부분 선형화* + *다회 측정* + *각 ion 분리* 결합으로 *완전 식별 가능*. 그러나 *조건*: passive 막 + 충분한 voltage clamp 정확도. 실제 *active* dendrite 의 비선형 채널 (NMDA, persistent Na) 까지 고려하면 추가 측정 + 모델 확장이 필요.

**결론**: 식별성은 *모델 복잡도* 와 *측정 다양성* 의 trade-off — LIF 는 단순해서 표준 실험으로 식별, Izhikevich 는 phenomenological 이라 식별 어려움, HH 는 복잡하지만 *분자적 분리 도구* (pharmacology) 가 식별을 가능케 함.''',
        'rubric_md': '''총 12점.
- (a) 3점: 4 매개변수 각각의 측정 (각 0.5점 = 2점) + 식별 가능 결론 (1점).
- (b) 4점: f-I 곡선만으로 불가능 (1점) + 추가 측정 ≥ 2 가지 (2점) + parameter ridge 언급 (1점).
- (c) 5점: TTX/TEA 분리 (1점) + step protocol α,β 추출 (1점) + 병렬 ion 결정 (1점) + 완전 식별 가능 결론 (1점) + active dendrite 한계 (1점).''',
        'slide_ref': '[Slide L7 §10]',
    },
    {
        'position': 4, 'kind': 'essay', 'difficulty': 3, 'max_points': 10, 'expected_time_min': 15,
        'topic_tag': 'model-selection-criteria',
        'prompt_md': '''*"모델 선택 = 질문 선택"* 이라는 원칙을 다음 4 가지 연구 시나리오에 적용:
(a) (2점) "$10^7$ 뉴런 cortical column 의 gamma 진동을 simulate" — 어느 모델?
(b) (2점) "Drug X 가 Na 채널 inactivation kinetics 를 어떻게 변화시키는가" — 어느 모델?
(c) (3점) "병변 환자의 fast-spiking interneuron 이 normal 과 어떻게 다른 spike 패턴을 보이는가" — 어느 모델?
(d) (3점) "Apical dendrite 의 NMDA spike 가 soma AP 시점에 어떻게 영향을 주는가" — 어느 모델? 단순 LIF/HH 만으로 부족한 이유.''',
        'model_answer_md': '''(a) **$10^7$ 뉴런 망 + gamma 진동**: **LIF** (또는 *exponential* LIF). 망 동역학 / 평균 발화율 / 진동의 *집단 패턴* 이 핵심 — 뉴런 1 개의 spike 모양은 부차적. 계산 비용 (10^7 × 1 변수) 만이 GPU 실시간 시뮬레이션을 허용. HH 라면 4 × 10^7 ODE 로 한 차수 느려짐.

(b) **Drug X + Na inactivation kinetics**: **HH (또는 더 정확한 ion-channel 모델)**. *Inactivation gate $h$ 의 동역학 매개변수 ($\\tau_h(V), h_\\infty(V)$) 가 직접 변화하는 것이 가설* — biophysical 정확성이 핵심. Voltage clamp + drug 인가 → α_h, β_h 의 변화 측정. LIF 는 채널 수준 추상화가 없어 부적합. Izhikevich 도 phenomenological — drug effect 와 매개변수 매핑 불명확.

(c) **병변 + fast-spiking interneuron 패턴**: **Izhikevich (또는 AdEx)**. *Spike pattern* 이 핵심 표현 — RS, FS, IB, LTS 의 4-매개변수 (a, b, c, d) 표현이 *카테고리화* 에 적합. 환자 vs normal 의 (a, b, c, d) shift 를 측정 → 어떤 매개변수가 임상적 차이를 만드는지 분석. HH 는 분자 수준이라 임상 phenotype 매핑 어려움. LIF 는 표현 다양성 부족.

(d) **Apical dendrite NMDA spike**: **Multi-compartment HH (또는 Hay et al. 2011 의 detailed pyramidal 모델)**. NMDA spike 는 *공간적* (apical dendrite 의 특정 branch) + *비선형* (NMDA voltage 의존성). 단일-compartment LIF/HH 는 *공간 정보* 부재 — distal dendrite 의 spike 가 *어디서 어떻게* soma 에 영향을 주는지 분석 불가. Cable + active dendrite + multiple ion channels 결합 필요. 계산 비용 ~10^4 / 뉴런 ODE — 단일 뉴런 정밀 분석에 적합.

**일반화**: *질문이 모델의 abstraction level 을 결정*. 망 진동 → LIF, channel kinetics → HH, spike pattern → Izhikevich, dendrite 비선형성 → multi-compartment. 한 모델이 모든 질문을 답하지 않는다.''',
        'rubric_md': '''총 10점.
- (a) 2점: LIF 선택 (1점) + 계산 비용 또는 망 동역학 정당화 (1점).
- (b) 2점: HH 선택 (1점) + voltage clamp + α_h, β_h 변화 측정 (1점).
- (c) 3점: Izhikevich (또는 AdEx) 선택 (1점) + spike pattern 카테고리 강점 (1점) + (a,b,c,d) shift 분석 (1점).
- (d) 3점: Multi-compartment HH 선택 (1점) + dendrite 공간 정보 필요 (1점) + NMDA voltage 의존성 (1점).''',
        'slide_ref': '[Slide L7 §11]',
    },
]


def main():
    conn = psycopg2.connect(DB_DSN)
    try:
        insert_quiz_items(conn, 'L7', L7_QUIZ)
        insert_take_home(conn, 'L7', L7_TAKE_HOME)
        print(f'L7: {len(L7_QUIZ)} quiz items + {len(L7_TAKE_HOME)} take-home items')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
