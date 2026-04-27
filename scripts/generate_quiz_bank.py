#!/usr/bin/env python3
"""
Quiz bank generator — Opus 4.7 hand-authored MCQ + short-answer + take-home items
for L2-L8. Items written by Claude Code Opus session per user mandate
(no OpenRouter Opus calls; this Opus session is the source).

Convention:
  - quiz_items: MCQ + short-answer; auto-gradeable; ≤90s expected
  - take_home_exam: derivation + essay; manual-graded; 10-30min expected

All items grounded in DB lecture_summaries + slide refs. Run incrementally
per lecture; idempotent via (lecture, position) unique constraint.
"""
import json
import psycopg2

DB_DSN = 'dbname=bri610 user=tutor password=tutor610 host=localhost'


# ──────────────────────────────────────────────────────────────────
# L2 — Computational Neuroscience: What & Why (intro, no heavy math)
# ──────────────────────────────────────────────────────────────────
L2_QUIZ = [
    # MCQ — concept recall
    {
        'position': 1, 'kind': 'mcq', 'difficulty': 1, 'bloom': 'Remember',
        'topic_tag': 'definition',
        'prompt_md': 'Computational neuroscience 가 *neural networks* (artificial) 와 가장 결정적으로 다른 지점은?',
        'choices_json': [
            {'key': 'A', 'text': '사용하는 수학이 다르다 (전자는 ODE, 후자는 행렬 곱).', 'correct': False},
            {'key': 'B', 'text': '*가정 변경 시 생물학적 근거*를 요구하는가의 차이.', 'correct': True},
            {'key': 'C', 'text': '학습 알고리즘의 유무.', 'correct': False},
            {'key': 'D', 'text': '계산 비용의 차이.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': 'Neural networks 는 *공학적 효율성* 으로 가정을 바꿀 수 있지만, computational neuroscience 는 막전위·이온 채널 같은 *생물학적 실체* 로부터 가정이 정당화되어야 한다 [Slide L2 p.12]. 이것이 두 분야가 같은 수학을 써도 *목적이 분기* 하는 핵심.',
        'slide_ref': '[Slide L2 p.12]',
    },
    {
        'position': 2, 'kind': 'mcq', 'difficulty': 2, 'bloom': 'Understand',
        'topic_tag': 'marr-levels',
        'prompt_md': 'Marr 의 3 단계 중 *"왜 그것이 적절한 목표인가"* 를 묻는 단계는?',
        'choices_json': [
            {'key': 'A', 'text': 'Computational level', 'correct': True},
            {'key': 'B', 'text': 'Algorithmic level', 'correct': False},
            {'key': 'C', 'text': 'Implementational level', 'correct': False},
            {'key': 'D', 'text': 'Behavioral level', 'correct': False},
        ],
        'correct_key': 'A',
        'rationale_md': 'Computational level = "*이 시스템이 해결해야 할 논리적 문제·목표가 무엇인가*" 를 묻는다 [Slide L2 p.34]. 이는 Dayan & Abbott 의 *Why* (Interpretive) 와 동의어 — *별개 체계로 오해 금물*. Algorithmic = 어떤 표상·알고리즘으로? Implementational = 어떤 회로·신경으로?',
        'slide_ref': '[Slide L2 p.34]',
    },
    {
        'position': 3, 'kind': 'mcq', 'difficulty': 2, 'bloom': 'Understand',
        'topic_tag': 'model-types',
        'prompt_md': 'Hodgkin–Huxley (1952) 모델은 D&A 의 어느 모델 종류에 가장 적합한가?',
        'choices_json': [
            {'key': 'A', 'text': 'Descriptive (What) — 현상의 정량적 기술.', 'correct': False},
            {'key': 'B', 'text': 'Mechanistic (How) — 회로·메커니즘 수준의 설명.', 'correct': True},
            {'key': 'C', 'text': 'Interpretive (Why) — 기능적 정당화.', 'correct': False},
            {'key': 'D', 'text': '셋 모두 동시에 — 단일 모델로 모든 질문에 답.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': 'HH 는 *how* 의 모범답안 — Na/K 채널 conductance 의 동역학으로 spike 생성 *메커니즘* 을 설명한다 [Slide L2 p.17]. *Why* (자연선택이 왜 이 회로를 골랐는가) 에는 답하지 않는다. *역할 분담 원칙*: 한 모델이 세 질문을 모두 답하지 않는다.',
        'slide_ref': '[Slide L2 p.17]',
    },
    {
        'position': 4, 'kind': 'mcq', 'difficulty': 3, 'bloom': 'Apply',
        'topic_tag': 'model-selection',
        'prompt_md': '"이 V1 뉴런의 tuning curve 는 45° 에서 최대 발화율 40 Hz, FWHM 30° 의 Gaussian 형태" — 이 진술은 어느 모델 관점인가?',
        'choices_json': [
            {'key': 'A', 'text': 'Descriptive (What)', 'correct': True},
            {'key': 'B', 'text': 'Mechanistic (How)', 'correct': False},
            {'key': 'C', 'text': 'Interpretive (Why)', 'correct': False},
            {'key': 'D', 'text': '모델이 아닌 단순 측정.', 'correct': False},
        ],
        'correct_key': 'A',
        'rationale_md': 'Tuning curve 의 *형태·매개변수* (peak, FWHM, Gaussian) 를 측정·정량 기술 → descriptive. Mechanistic 이라면 "LGN center cell 들이 특정 배열로 수렴해 orientation 을 만든다" (Hubel-Wiesel 가설). Interpretive 라면 "natural image 통계가 sparse code 를 선호하므로". *같은 V1 뉴런* 이라도 도구가 답하는 질문이 다르다 [Slide L2 §3].',
        'slide_ref': '[Slide L2 p.17–18]',
    },
    {
        'position': 5, 'kind': 'mcq', 'difficulty': 2, 'bloom': 'Understand',
        'topic_tag': 'history',
        'prompt_md': 'Hodgkin–Huxley (1952) 가 *학문 분야로서* computational neuroscience 의 출발점이 된 이유로 가장 적절한 것은?',
        'choices_json': [
            {'key': 'A', 'text': '뉴런을 처음 측정한 실험이라서.', 'correct': False},
            {'key': 'B', 'text': 'AP 를 voltage clamp 로 분리·정량하고 ODE 모델로 *예측 가능한* 형태로 환원했기 때문에.', 'correct': True},
            {'key': 'C', 'text': '인공신경망의 학습 규칙을 처음 제안했기 때문에.', 'correct': False},
            {'key': 'D', 'text': 'Marr 의 3 단계 framework 를 발표했기 때문에.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': 'HH 의 결정적 기여: voltage clamp 로 $g_{Na}, g_K$ 를 *분리 측정* → ODE 4 변수 ($V, m, h, n$) 시스템으로 환원 → *예측 가능한 spike shape*. 이 환원성이 "측정 + 수학 + 모델 = 새 학문" 을 정당화 [Slide L2 p.20–22]. 이전에는 *측정* 은 있었으나 *예측 가능 모델* 은 없었음.',
        'slide_ref': '[Slide L2 p.20–22]',
    },
    {
        'position': 6, 'kind': 'mcq', 'difficulty': 3, 'bloom': 'Analyze',
        'topic_tag': 'abstraction-ladder',
        'prompt_md': '"Abstraction ladder" 의 핵심 원칙으로 가장 정확한 것은?',
        'choices_json': [
            {'key': 'A', 'text': '항상 가장 *상세한* 모델이 가장 좋은 모델이다.', 'correct': False},
            {'key': 'B', 'text': '같은 현상이라도 *질문 수준* 에 따라 다른 추상화가 최적이다.', 'correct': True},
            {'key': 'C', 'text': '추상화가 높을수록 신뢰도가 떨어진다.', 'correct': False},
            {'key': 'D', 'text': '실험 측정 기술이 모델 추상화 수준을 결정하지 않는다.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': '*최소 충분 복잡도 (parsimony)*: 더 단순한 모델이 같은 현상을 설명하면 우선. *질문 먼저, 모델 나중* — 망 진동을 보려면 LIF 가, spike 생성 메커니즘을 보려면 HH 가, 행동 수준이면 rate model 이 최적. *측정 기술의 한계가 모델 추상화 수준을 강제* 한다는 일반화도 같은 원칙의 다른 면 [Slide L2 §1].',
        'slide_ref': '[Slide L2 §1]',
    },
    {
        'position': 7, 'kind': 'mcq', 'difficulty': 2, 'bloom': 'Remember',
        'topic_tag': 'history',
        'prompt_md': 'Marr 의 *Vision* (1982) 이 computational neuroscience 에 미친 가장 중요한 영향은?',
        'choices_json': [
            {'key': 'A', 'text': '뉴런 시뮬레이션 소프트웨어를 처음 만들었다.', 'correct': False},
            {'key': 'B', 'text': '3 levels 분석 framework 로 분야 간 *공통 언어* 를 제공했다.', 'correct': True},
            {'key': 'C', 'text': 'Hodgkin–Huxley 모델을 일반화했다.', 'correct': False},
            {'key': 'D', 'text': '기능적 MRI 를 발명했다.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': 'Marr (1982) 는 *모든 정보 처리 시스템* — 뇌·컴퓨터 둘 다 — 을 Computational/Algorithmic/Implementational 의 세 *분리 가능* 한 수준에서 분석해야 한다고 주장. 이 framework 가 신경과학·심리학·AI 의 *공통 언어* 가 됨 [Slide L2 p.34]. 시뮬레이션 소프트웨어는 1980s-90s GENESIS/NEURON.',
        'slide_ref': '[Slide L2 p.34]',
    },
    # Short-answer
    {
        'position': 8, 'kind': 'short_answer', 'difficulty': 2, 'bloom': 'Remember',
        'topic_tag': 'marr-levels',
        'prompt_md': 'Marr 의 3 단계를 이름만 영어로 나열하라 (위에서 아래 순서).',
        'correct_text': 'Computational, Algorithmic, Implementational',
        'accept_patterns': [
            r'^\s*Computational\W+Algorithmic\W+Implement(ation)?al\s*\.?\s*$',
            r'^\s*Computation(al)?,?\s+Algorithm(ic)?,?\s+Implementation(al)?\W*$',
        ],
        'rationale_md': '*Computational* (왜 — 목표·문제), *Algorithmic* (어떻게 — 표상·알고리즘), *Implementational* (어디서 — 회로·하드웨어). 위에서 아래로 *추상도* 감소.',
        'slide_ref': '[Slide L2 p.34]',
    },
    {
        'position': 9, 'kind': 'short_answer', 'difficulty': 2, 'bloom': 'Remember',
        'topic_tag': 'model-types',
        'prompt_md': 'Dayan & Abbott 의 3 model types 를 영어로 나열하라.',
        'correct_text': 'Descriptive, Mechanistic, Interpretive',
        'accept_patterns': [
            r'^\s*Descriptive\W+Mechanistic\W+Interpretive\W*$',
            r'(?i).*descriptive.*mechanistic.*interpretive.*',
        ],
        'rationale_md': '*Descriptive* (What — 현상 정량 기술), *Mechanistic* (How — 회로 메커니즘), *Interpretive* (Why — 기능적 정당화). Marr Computational ≈ D&A Interpretive (둘 다 "왜").',
        'slide_ref': '[Slide L2 §1]',
    },
    {
        'position': 10, 'kind': 'short_answer', 'difficulty': 1, 'bloom': 'Remember',
        'topic_tag': 'definition',
        'prompt_md': '*Specific membrane capacitance* 의 표준 값을 단위와 함께 답하라.',
        'correct_text': '1 μF/cm²',
        'accept_patterns': [
            r'(?i)\b1(\.0+)?\s*(μ|u|mu|micro)\s*F\s*/\s*cm[²2]?\b',
            r'(?i)\b1(\.0+)?\s*microF\s*/\s*cm[²2]?\b',
        ],
        'rationale_md': 'Lipid bilayer 두께 (3–4 nm) 가 진화적으로 보존되어 모든 척추동물 뉴런에서 단위 면적당 capacitance ≈ $1\\,\\mu\\text{F}/\\text{cm}^2$ 로 거의 일정 [Slide L3 p.18; L2 p.21 도입]. *세포 종류와 무관* 한 진화적 상수.',
        'slide_ref': '[Slide L3 p.18]',
    },
    {
        'position': 11, 'kind': 'short_answer', 'difficulty': 3, 'bloom': 'Apply',
        'topic_tag': 'model-selection',
        'prompt_md': '*"왜 V1 뉴런이 edge detector 처럼 행동하는가"* 를 묻는 모델은 D&A 의 어느 종류인가? (한 단어, 영어)',
        'correct_text': 'Interpretive',
        'accept_patterns': [
            r'(?i)^\s*interpretive\W*$',
        ],
        'rationale_md': '"Why" 질문 → Interpretive. 답: 자연영상의 edge 통계가 sparse code 를 선호하므로 ICA-유사 최적화가 edge detector 를 *해로 갖는다*. Mechanistic 이라면 "Hubel-Wiesel LGN 회로", Descriptive 라면 "tuning curve 의 모양 자체".',
        'slide_ref': '[Slide L2 §3]',
    },
    {
        'position': 12, 'kind': 'mcq', 'difficulty': 4, 'bloom': 'Evaluate',
        'topic_tag': 'common-misconception',
        'prompt_md': '*"가장 생물학적으로 상세한 모델이 항상 가장 좋은 모델이다"* — 이 진술의 평가는?',
        'choices_json': [
            {'key': 'A', 'text': '맞다. 상세할수록 정확하다.', 'correct': False},
            {'key': 'B', 'text': '틀리다. *질문에 따라* 단순 모델이 더 적합할 수 있다 (parsimony).', 'correct': True},
            {'key': 'C', 'text': '맞지만 계산 비용이 너무 크다.', 'correct': False},
            {'key': 'D', 'text': '실험적으로 검증 불가능하다.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': '*Realism ≠ 좋은 모델*. 망 동역학을 묻는다면 LIF 가 HH 보다 적합 (식별 가능성, 계산 비용, 해석 용이성). HH 는 *spike 생성 메커니즘* 을 묻는 질문에 최적. 모델 선택 = *질문 선택* [Slide L2 §7].',
        'slide_ref': '[Slide L2 §7]',
    },
]

L2_TAKE_HOME = [
    {
        'position': 1, 'kind': 'essay', 'difficulty': 3, 'max_points': 15, 'expected_time_min': 25,
        'topic_tag': 'marr-vs-da',
        'prompt_md': '''Marr 의 3 단계와 Dayan & Abbott 의 3 model types 를 *대응* 시키되, 단순 동의어 매핑이 아닌 *어디서 일치하고 어디서 어긋나는가* 를 자신의 언어로 논하라. 시각 V1 뉴런의 orientation selectivity 를 구체 예시로 사용 (≥ 250 단어).''',
        'model_answer_md': '''Marr 의 *Computational* 과 D&A 의 *Interpretive* 는 둘 다 "왜" 를 묻는다는 점에서 동의어로 취급되곤 한다. 그러나 *동기* 가 다르다.

Marr 의 Computational 은 "이 시스템이 *해결해야 할 문제* 가 무엇인가" 를 묻는 *공학적 정의* — 입력에서 출력으로 가는 함수의 *명세* (specification). 시각의 경우 "2D retinal image → 3D world surfaces 추정". 이는 *이상적 관찰자 (ideal observer)* 의 관점.

D&A 의 Interpretive 는 "왜 *자연선택이* 이 회로·표상을 골랐는가" 를 묻는 *생물학적 정당화* — 진화적 적합도. V1 의 edge detection 이 *natural image 통계의 sparse code* 와 일치한다는 ICA 분석 (Olshausen-Field 1996) 이 전형 [Slide L2 §3].

겹치는 부분: 둘 다 *목적* 을 묻는다. 어긋나는 부분: Marr 는 *논리적 명세* (이상적), D&A 는 *진화적 제약* (실현된 trade-off). V1 의 경우 — Computational 답: "edge 정보를 추출하는 함수". Interpretive 답: "자연영상 통계 + 망막 한계 + 에너지 효율 → ICA-유사 sparse code 가 선택됨". 두 답은 *서로를 보완* 하지만 *동일하지 않다*.

Marr 의 Algorithmic ↔ D&A 의 Mechanistic 도 비슷하게 *근사 동의어*: 둘 다 "어떻게" 를 묻는다. 그러나 Algorithmic 은 *표상 + 알고리즘* (정보 처리 단계), Mechanistic 은 *회로 + 동역학* (물리 메커니즘). V1 의 경우 — Algorithmic: "Gabor filter convolution". Mechanistic: "LGN center cells 의 elongated 배열 → simple cell". Algorithmic 은 Mechanistic 의 *수준 위* 에 있다.

Marr 의 Implementational ↔ 실험 신경과학의 *세포·분자 수준* — D&A 에는 직접 대응이 없다 (D&A 는 *모델링* framework, Marr 는 *분석* framework).

핵심 통찰: *질문이 모델을 결정한다*. Computational/Interpretive 답을 mechanistic 모델로 풀려는 것은 범주 오류 — Hodgkin–Huxley 로 "왜 edge detection 인가" 에 답할 수 없다 (HH 는 spike 생성의 *how* 만 답).''',
        'rubric_md': '''총 15점.
- (3점) Marr 3 단계 정확 정의
- (3점) D&A 3 types 정확 정의
- (4점) Computational ↔ Interpretive 의 *겹침과 어긋남* 명시 (단순 동의어 매핑이면 −2)
- (3점) V1 orientation selectivity 의 *구체* 예시로 두 framework 적용
- (2점) 추가: Algorithmic vs Mechanistic 의 미묘한 차이, *질문이 모델을 결정* 한다는 결론 등 통합적 통찰''',
        'slide_ref': '[Slide L2 §1, §3, p.34]',
    },
    {
        'position': 2, 'kind': 'derivation', 'difficulty': 4, 'max_points': 12, 'expected_time_min': 20,
        'topic_tag': 'capacitor-derivation',
        'prompt_md': '''Lipid bilayer 가 *parallel-plate capacitor* 처럼 행동한다는 가정 하에:
(a) (4점) Bilayer 두께 $d$, 면적 $A$, 유전율 $\\varepsilon$, 진공유전율 $\\varepsilon_0$ 만으로 전체 capacitance $C$ 를 유도하라.
(b) (3점) *Specific* capacitance $C_m = C/A$ 가 세포 종류에 거의 무관한 이유를 진화적 관점에서 설명하라.
(c) (3점) 만약 myelin 이 internode 에 *수십 겹* 의 lipid bilayer 를 추가한다면, 그 구간의 *effective* $C_m$ 은 어떻게 달라지는가? (수식 + 직관 둘 다)
(d) (2점) 위 (c) 가 saltatory conduction 의 속도 향상에 어떻게 기여하는지 cable 시간상수 $\\tau_m = R_m C_m$ 으로 설명하라.''',
        'model_answer_md': '''(a) Parallel-plate capacitor: 전기장 $E = \\sigma/\\varepsilon\\varepsilon_0$, 전압 $V = Ed = \\sigma d/(\\varepsilon\\varepsilon_0)$. 전하 $Q = \\sigma A$. 정의 $C = Q/V$ 대입 → $$C = \\frac{\\varepsilon \\varepsilon_0 A}{d}.$$ 단위 면적당: $C_m = C/A = \\varepsilon\\varepsilon_0/d$.

(b) Bilayer 두께 $d \\approx 3$–$4$ nm 는 *모든 척추동물 세포* 에서 거의 동일 — phospholipid 분자 길이 + acyl chain 두께가 진화적으로 보존됨. 유전율 $\\varepsilon$ 도 lipid acyl-chain 의 분자 종류에 거의 무관 ($\\varepsilon \\approx 2$). 따라서 $C_m = \\varepsilon\\varepsilon_0/d \\approx 1\\,\\mu\\text{F}/\\text{cm}^2$ 가 *세포 종류·종 무관 상수*. 진화는 channel density (= conductance) 만 바꿀 수 있고 $C_m$ 은 거의 못 바꾼다 [Slide L3 p.18].

(c) Myelin 은 internode 에 $n$ 겹 ($n \\sim 10$–$50$) 의 bilayer 를 직렬 추가. 직렬 capacitor 는 $1/C_\\text{tot} = \\sum 1/C_i$ → $C_m^\\text{eff} = C_m / n$. 즉 *수십 분의 일* 로 감소. *직관*: 더 두꺼운 절연층 → 같은 전압당 저장 전하 감소 → "전류 먹는 양" 감소.

(d) 시간상수 $\\tau_m = R_m C_m$. Myelin 은 동시에 $R_m$ 도 *증가* (leak 채널 부재) — 보통 $R_m$ 은 100배 이상 ↑, 그러나 $C_m$ 은 $n$ 배 ↓. 종합: $\\tau_m$ 은 $R_m$ 증가가 우세해 *증가* 하지만, *공간상수* $\\lambda = \\sqrt{d R_m / 4 R_i} \\propto \\sqrt{R_m}$ 가 더 크게 늘어나 신호가 *훨씬 멀리* 감쇠 없이 전파. Node 사이 internode 길이를 $\\lambda$ 의 1–2 배로 두면, 한 node 의 AP 가 다음 node 의 임계까지 *수동적으로* 도달 → saltatory (jumping) conduction. 결과: 무수초 $v \\propto \\sqrt{d}$ 가 수초 $v \\propto d$ 로 — 같은 직경에서 *한 차수* 빠름.''',
        'rubric_md': '''총 12점.
- (a) 4점: 정의 → $V = Ed$, $Q = \\sigma A$ → $C$ 수식 (3점) + 단위 면적당 표현 (1점). 부호 오류는 −1.
- (b) 3점: bilayer 두께 보존 (1점) + 유전율 보존 (1점) + 진화는 conductance 만 바꾼다 (1점).
- (c) 3점: 직렬 capacitor 공식 1/C_tot = Σ 1/C_i (1점) + $C_m^\\text{eff} = C_m/n$ 결론 (1점) + 직관 설명 (1점).
- (d) 2점: τ_m·λ 의 동시 변화 분석 (1점) + saltatory 메커니즘 연결 (1점).''',
        'slide_ref': '[Slide L2 p.21; L3 p.18; L6 p.17–22]',
    },
    {
        'position': 3, 'kind': 'essay', 'difficulty': 3, 'max_points': 10, 'expected_time_min': 15,
        'topic_tag': 'measurement-abstraction',
        'prompt_md': '''*"각 시대의 모델 추상화 수준은 그 시대의 측정 기술 가용성에 의해 강제된다"* — 이 일반화 원칙을 (1) 1907 Lapicque LIF, (2) 1952 Hodgkin–Huxley, (3) 2010s+ Allen Brain Atlas 의 세 사례로 정당화하라 (각 사례마다 *어떤 측정* 이 어떤 *추상화* 를 가능케 했는지 ≥ 50 단어).''',
        'model_answer_md': '''**1907 Lapicque LIF**: 당시 측정 가능한 것은 *근육 수축으로 본 발화 유무 + 자극 강도* — 막 내부 전압은 측정 불가 (intracellular electrode 없음). 따라서 모델은 "$V$ 가 임계에 도달하면 발화" 라는 *블랙박스 추상화* 가 최선. Spike 모양 (millisecond 동역학, ion 채널) 은 *접근 불가* 하므로 추상화 대상에서 제외. 결과적으로 LIF 는 1-변수 ODE — 측정 한계가 모델 단순성을 *강제*.

**1952 Hodgkin–Huxley**: Voltage clamp (Marmont–Cole 1947, Hodgkin–Huxley 정교화) + giant squid axon (큰 직경, 다회 측정 가능) + radio-tracer (이온별 분리) 가 등장 → *각 이온의 conductance 를 시간·전압 의존적으로* 측정 가능. 따라서 모델 추상화 수준이 격상 — 4 변수 ODE ($V, m, h, n$), ion-specific kinetics. 측정이 *예측 가능 모델* 을 가능케 했다.

**2010s+ Allen Brain Atlas / BRAIN initiative**: 단일세포 RNA-seq (수만 종 transcriptional 분류), 두뇌 전체 connectomics (전자현미경 reconstruction), patch-seq (전기 + 분자 동시) — 측정이 *세포 다양성·연결성* 까지 확장. 따라서 모델 추상화도 다세포 회로, deep learning re-convergence, 다세포 phenotype-genotype 연결로 격상. *Big data 시대* 의 모델은 *통계적 학습 (interpretive)* 과 *생물학적 다양성* 을 동시에 다룬다.

**일반화**: 측정 기술이 *접근 가능한 변수* 를 결정하고, *접근 가능한 변수의 집합* 이 모델의 추상화 수준을 강제한다. 이 원칙은 미래 — 가령 광유전학 + voltage imaging 결합이 새 추상화 (gene-circuit-behavior 통합) 를 가능케 할 것 — 도 예측한다.''',
        'rubric_md': '''총 10점.
- (3점) 1907 Lapicque: 측정 한계 (intracellular 없음) → 블랙박스 추상화 정당화.
- (3점) 1952 HH: voltage clamp + squid axon + tracer → ion-specific kinetics 모델 가능.
- (3점) 2010s+: 단일세포 분석 + connectomics → 세포 다양성/회로 모델로 격상.
- (1점) 일반화 원칙을 *명확히 진술* (단순 사례 나열 만이면 0).''',
        'slide_ref': '[Slide L2 p.20–32]',
    },
    {
        'position': 4, 'kind': 'essay', 'difficulty': 4, 'max_points': 12, 'expected_time_min': 20,
        'topic_tag': 'model-vs-measurement',
        'prompt_md': '''*"Computational neuroscience 와 (artificial) neural networks 의 차이는 단순히 사용하는 수학이나 응용 분야가 아니라, *가정 변경 시 생물학적 근거를 요구하는가* 에 있다"* — 이 주장을 다음 항목으로 검토하라:
(a) (3점) Backpropagation 학습은 두 분야에서 어떻게 다르게 다뤄지는가?
(b) (3점) ReLU 활성화 함수는 신경과학적으로 정당화될 수 있는가? 어느 측면에서?
(c) (3점) Spike-timing-dependent plasticity (STDP) 가 NN 학습 규칙으로 적합한가? 그 한계는?
(d) (3점) 두 분야가 *수렴* 하는 사례 (deep learning re-convergence) 와 *발산* 하는 사례를 각 1 개씩.''',
        'model_answer_md': '''(a) **Backprop**: NN 에서는 *효율적 gradient 계산* 을 위해 자유롭게 사용 — 가중치를 양방향으로 전파한다는 가정에 의문 없음. Computational neuroscience 에서는 *생물학적 backprop 은 어렵다* 가 표준 입장 — 시냅스는 단방향, postsynaptic 정보가 presynaptic 에 도달할 메커니즘 부재. 대안: Hebbian, equilibrium propagation, predictive coding, target propagation 등 *생물학적 근거* 를 요구.

(b) **ReLU**: $f(x) = \\max(0, x)$. NN 측면: gradient saturation 회피 + 계산 효율. 신경과학 측면: 부분적 정당화 가능 — 실제 뉴런의 *firing rate* 는 음수가 될 수 없음 (rate ≥ 0 하한), threshold 이상에서 거의 *선형*. 그러나 sigmoidal saturation, refractory period, adaptation 같은 실제 nonlinearity 는 ReLU 에 없음. *근사 정당화* 는 가능하지만 정확하지 않음.

(c) **STDP**: spike timing 차이 ($\\Delta t$) 에 따라 시냅스 강도를 변화시키는 *생물학적으로 관찰된* 규칙. NN 학습 규칙으로는 (i) gradient 와의 관계가 명확하지 않고, (ii) supervised loss 와 직접 연결 어렵고, (iii) 대규모 망에서 수렴 보장이 약하다. 일부 *unsupervised* / spiking neural net (SNN) 에 활용되나, 표준 deep learning 의 SGD 만큼 강력하지 않음. 한계: *생물학적 사실* 과 *학습 효율성* 의 trade-off.

(d) **수렴 사례**: 2010s deep learning re-convergence — convolutional NN 의 receptive field 가 V1 simple cell 과 통계적으로 유사 (Yamins-DiCarlo 2014); ImageNet-학습 CNN 의 layer 별 활성이 ventral stream IT 와 상관. → "*망구조와 자연 통계가 비슷한 표상으로 수렴* 한다" 는 강력한 증거. **발산 사례**: GPT-style transformer 의 self-attention 메커니즘 — *메모리 + 시퀀스 처리* 에서 매우 강력하지만, 뇌의 어떤 회로와도 직접 대응 어려움 (특히 K-V cache 의 *모든 과거 input 동시 접근* 은 생물학적으로 부적절). 두 분야가 *수학을 공유* 하더라도 *질문의 분기* 에 따라 발산.

**결론**: 가정 변경 시 *왜 그것이 생물학적으로 가능한가* 를 요구하는 것이 computational neuroscience 의 정체성. NN 은 *왜 그것이 효율적인가* 를 요구. 동일한 backprop, 동일한 ReLU 라도 두 분야의 *수용 기준* 이 다르다.''',
        'rubric_md': '''총 12점.
- (a) 3점: backprop 의 *생물학적 어려움* 명시 (1점) + NN 에서의 자유로운 사용 (1점) + 생물학적 대안 1개 이상 (1점).
- (b) 3점: ReLU 의 NN 정당화 (1점) + 신경과학적 부분 정당화 (rate ≥ 0, threshold 선형) (1점) + 한계 (sigmoid, refractory, adaptation 등) (1점).
- (c) 3점: STDP 의 *생물학적 사실* (1점) + NN 학습 규칙으로의 한계 3가지 중 2가지 이상 (2점).
- (d) 3점: 수렴 사례 (deep learning re-convergence with V1/IT) (1.5점) + 발산 사례 (transformer attention 등) (1.5점).
*가산점 없음 — 12점 만점.*''',
        'slide_ref': '[Slide L2 p.12, p.30–32]',
    },
]


# ──────────────────────────────────────────────────────────────────
# Insertion helper
# ──────────────────────────────────────────────────────────────────

def insert_quiz_items(conn, lecture, items):
    with conn.cursor() as cur:
        for q in items:
            cur.execute("""
                INSERT INTO quiz_items
                  (lecture, position, kind, prompt_md, choices_json, correct_key,
                   correct_text, accept_patterns, rationale_md, slide_ref,
                   difficulty, bloom, topic_tag)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (lecture, position) DO UPDATE SET
                  kind=EXCLUDED.kind, prompt_md=EXCLUDED.prompt_md,
                  choices_json=EXCLUDED.choices_json, correct_key=EXCLUDED.correct_key,
                  correct_text=EXCLUDED.correct_text, accept_patterns=EXCLUDED.accept_patterns,
                  rationale_md=EXCLUDED.rationale_md, slide_ref=EXCLUDED.slide_ref,
                  difficulty=EXCLUDED.difficulty, bloom=EXCLUDED.bloom, topic_tag=EXCLUDED.topic_tag
            """, (
                lecture, q['position'], q['kind'], q['prompt_md'],
                json.dumps(q.get('choices_json'), ensure_ascii=False) if q.get('choices_json') else None,
                q.get('correct_key'),
                q.get('correct_text'),
                json.dumps(q.get('accept_patterns'), ensure_ascii=False) if q.get('accept_patterns') else None,
                q['rationale_md'], q.get('slide_ref'),
                q['difficulty'], q.get('bloom'), q.get('topic_tag'),
            ))
    conn.commit()


def insert_take_home(conn, lecture, items):
    with conn.cursor() as cur:
        for t in items:
            cur.execute("""
                INSERT INTO take_home_exam
                  (lecture, position, kind, prompt_md, model_answer_md, rubric_md,
                   max_points, expected_time_min, slide_ref, topic_tag)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (lecture, position) DO UPDATE SET
                  kind=EXCLUDED.kind, prompt_md=EXCLUDED.prompt_md,
                  model_answer_md=EXCLUDED.model_answer_md, rubric_md=EXCLUDED.rubric_md,
                  max_points=EXCLUDED.max_points, expected_time_min=EXCLUDED.expected_time_min,
                  slide_ref=EXCLUDED.slide_ref, topic_tag=EXCLUDED.topic_tag
            """, (
                lecture, t['position'], t['kind'], t['prompt_md'],
                t['model_answer_md'], t['rubric_md'],
                t.get('max_points', 10), t.get('expected_time_min', 15),
                t.get('slide_ref'), t.get('topic_tag'),
            ))
    conn.commit()


def main():
    conn = psycopg2.connect(DB_DSN)
    try:
        # L2
        insert_quiz_items(conn, 'L2', L2_QUIZ)
        insert_take_home(conn, 'L2', L2_TAKE_HOME)
        print(f'L2: {len(L2_QUIZ)} quiz items + {len(L2_TAKE_HOME)} take-home items')

        # L3-L8 — generated in subsequent script invocations
        # Per-lecture banks added in sibling files generate_quiz_bank_L{n}.py
    finally:
        conn.close()


if __name__ == '__main__':
    main()
