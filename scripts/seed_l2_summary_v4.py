#!/usr/bin/env python3
"""
Seed L2 summary v4 — concept + history + essay-prep oriented.

L2 is a computational-neuroscience overview lecture (intro/history). Per user
requirement, this summary should NOT focus on memorizing equations or running
derivations. Instead it provides:
  - Why we model neurons (purpose + 4 motivations)
  - Marr's 3 levels (computational / algorithmic / implementational)
  - Comp-neuro vs neural networks (science vs engineering)
  - Historical milestones in narrative form
  - <details> toggles for prerequisite background
  - Common-pitfalls section
  - Essay-style problem-prep section (논술 서술형 대비) with D&A page
    references + answer scaffolds (the 'practice essay' part is the
    distinctive new section vs L3-L8)
"""
import os
import psycopg2

DB_DSN = os.environ.get('DATABASE_URL', 'dbname=bri610 user=tutor password=tutor610 host=localhost')

L2_SUMMARY = r"""> **한 문장 핵심.** 뇌라는 *세상에서 가장 복잡한 정보 처리 장치* 를 우리는 어떻게 *이해* 할 수 있는가? — 측정만으로는 충분하지 않다는 깨달음에서 출발해, 수학·계산·모델이 뇌 연구의 *제3의 기둥* 으로 자리잡게 된 60년의 여정.

암기할 공식은 없음. 대신 *왜 뉴런을 모델링하는가*, *어떤 종류의 모델이 어떤 질문에 답하는가* 라는 메타-질문에 대한 답을 갖추는 것이 목표.

---

## §1. Computational Neuroscience 의 정의와 세 가지 목적

**Dayan & Abbott (Preface)**: *"Theoretical analysis and computational modeling are important tools for characterizing **what** nervous systems do, determining **how** they function, and understanding **why** they operate in particular ways."*

이 한 문장 안에 모든 것이 들어있다. Computational neuroscience 는 다음 세 가지 *수준* 의 질문을 동시에 다루는 학문이다 — 따라서 단순한 *모델링 기법* 이 아니라 *질문 설정의 방식* 자체가 이 분야의 정체성.

| 질문 | 모델 종류 | 예시 |
|---|---|---|
| **What** does it do? | *Descriptive* model | 신경 부호 (neural code) 의 통계적 기술; PSTH; tuning curve |
| **How** does it function? | *Mechanistic* model | Hodgkin–Huxley; cable theory; integrate-and-fire 회로 |
| **Why** does it work this way? | *Interpretive* model | 효율적 부호화 (efficient coding); 베이지언 추론; ICA 가설 |

**중요**: 한 모델이 세 질문을 *모두* 답하지는 않는다. McCulloch–Pitts 모델 (1943) 은 *what* 에는 강하지만 *how* 에는 약하다 — 실제 뉴런이 그렇게 동작하는지는 별개의 문제. 반대로 Hodgkin–Huxley 모델 (1952) 은 *how* 의 모범답안이지만, *why* 자연선택이 이 회로를 골랐는가에는 답하지 않는다 [Slide L2 p.17].

---

## §2. Marr 의 3 단계 — 어떤 수준에서 뇌를 이해할 것인가?

David Marr (1982, *Vision*) 는 모든 정보 처리 시스템 — 뇌 포함 — 을 세 *분리 가능* 한 수준에서 분석해야 한다고 주장했다 [Slide L2 p.34].

| 수준 | 묻는 것 | 뇌 비유 | 컴퓨터 비유 |
|---|---|---|---|
| **Computational** | *목표는 무엇이고, 왜 그것이 적절한가?* | 시각이 *3D 구조를 추정* 하는 이유 | 정렬 알고리즘이 *집합을 순서화* 하는 이유 |
| **Algorithmic / representational** | *입력→출력을 어떤 표현·절차로 변환하는가?* | edge detector → contour → object | 퀵소트 vs 머지소트 |
| **Implementational** | *어떤 물리적 메커니즘이 그 절차를 실행하는가?* | 시상-V1-V2 회로의 시냅스 가중치 | CPU 게이트, transistor |

세 수준은 *동일한 시스템의 동일한 행동* 에 대한 *서로 다른 설명* 이다 — 어느 하나가 다른 것을 *대체* 하지 않는다. **시험 함정**: "Marr 의 3 levels 중 어느 것이 가장 중요한가?" 라는 질문에는 *셋 다 필수* 라고 답해야 함. Marr 자신이 강조한 것은 *세 수준 사이의 *느슨한* 연결* — 같은 알고리즘이 여러 implementation 으로 구현될 수 있고, 같은 computational goal 이 여러 알고리즘으로 달성될 수 있다.

> **연결고리**: 이후 lectures 에서 우리가 다룰 HH model 은 *implementational* 수준의 모범답안이고, LIF model (L7) 은 같은 phenomenon 을 *algorithmic* 수준으로 *abstract* 한 것이다. L8 의 neural codes 는 본격적으로 *computational* 수준 — *왜* 시간 부호 vs 발화율 부호인가? — 를 다룬다.

---

## §3. Computational Neuroscience vs Neural Networks — 과학 vs 공학

이 둘은 *겉보기에 비슷하지만 목적이 다르다* [Slide L2 p.12].

- **Computational neuroscience**: *뇌를 이해하기 위한 시뮬레이션* (a "simulation for understanding the brain"). 모델은 실험 데이터에 *합치* 해야 하며, 가정의 변경은 *생물학적 근거* 를 요구함.
- **Neural networks** (artificial): *뉴런으로부터 영감받은 컴퓨터 알고리즘 개발* (developing computer algorithms inspired by neurons and the brain). 성능이 좋으면 *생물학적으로 부정확해도 무방*.

전자는 *과학*, 후자는 *공학*. 하지만 둘은 *상호 영감* — Hopfield network (1982) 는 통계 물리에서 시작해 신경과학으로 전염되었고, deep learning 의 성공은 시각 시스템 모델링에 영감을 주었다.

**용어 함정**: "neural network" 가 학회 발표나 논문 제목에 등장하면, *어느 의미인지* 첫 단락에서 반드시 결정해야 한다. 이는 한국어 학술 글쓰기에서도 같음 — "신경망" vs "인공신경망" vs "신경회로망" 으로 구분.

---

## §4. 뉴런을 모델링하는 4 가지 이유

[Slide L2 p.16–17] 에서 명시적으로 다루는 *왜 모델링인가* 의 4 가지 답:

1. **데이터 압축 (Descriptive compression)** — 수십 개의 실험 변수를 *몇 개의 매개변수* 로 요약. 예: HH 4-변수 ODE 가 squid axon 의 voltage clamp 데이터 수백 trace 를 4 개 함수로 압축.

2. **메커니즘 발견 (Mechanistic insight)** — 모델이 *틀릴* 때, 어떤 가정이 잘못됐는지가 새 연구 가설이 됨. 예: HH 모델이 dendrite 신호 전파를 정확히 예측하지 못한 것이 *active dendrite* 발견의 출발점.

3. **정량적 예측 (Quantitative prediction)** — 측정 불가능한 변수를 추정하는 도구. 예: cable theory (L6) 가 dendrite 의 *공간적 전압 분포* 를 측정 없이 계산.

4. **공학적 영감 (Engineering inspiration)** — 뇌의 부호화 원리를 추출해 *인공 시스템 설계* 에 활용. 예: spiking neural network 칩, neuromorphic computing.

**시험 함정**: "neural modeling 의 *유일한* 목적은 prediction 이다" 는 *틀림*. Predictive power 는 *충분 조건이 아닌 필요 조건*; understanding 과 mechanistic insight 가 함께 평가됨. Open the toggle below for a deeper look.

<details>
<summary><em>(펼쳐서 복습) "모델이 좋다 = 예측이 정확하다" 라는 명제의 한계</em></summary>

이 명제는 *공학적 시각* 에서는 옳지만 *과학적 시각* 에서는 부분적이다. *Descriptive* 모델은 *예측* 만으로 충분하지만, *mechanistic* 모델은 *왜 그런 예측이 나오는지* 를 *물리적·생물학적 근거* 로 정당화해야 한다. 즉, 좋은 mechanistic model 은 (a) 예측 정확도, (b) 생물학적 plausibility, (c) parsimony (Occam's razor) 의 *세 축* 에서 평가됨.
</details>

---

## §5. 역사적 이정표 — 60년의 narrative

각 사건의 *왜* 를 머릿속에 정리해둘 것. 시험에는 *연도 암기* 보다 *왜 이 시점에 이 발견이 가능했는가* 가 자주 출제됨.

- **1907 — Lapicque, integrate-and-fire 모델**: 개구리 신경의 자극-반응 데이터를 *capacitor 충전 곡선* 으로 환원. 신경흥분성을 처음으로 *전자공학적 회로* 로 본 사건. 발화 *시점* 만이 정보를 전달한다는 가정 — 이는 100 년이 지난 LIF 모델 (L7) 의 직접 조상 [Slide L2 p.19].

- **1943 — McCulloch & Pitts, formal neuron**: 신경 활동을 *논리 연산* 으로 환원. *모든 finite 논리식* 이 McCulloch–Pitts 뉴런 네트워크로 표현 가능함을 증명. *이진 출력 + 임계값 + 가중치* 의 3 요소만으로 뇌-컴퓨터 등가성을 처음 주장. 인공신경망의 탄생점 [Slide L2 p.20–24].

- **1949 — Hebb, "Cells that fire together wire together"**: 학습은 *공동 발화에 의한 시냅스 강화*. 분자 수준 LTP (Lomo, 1966) 발견 전 *17 년* 이미 가설 제시. 학습 규칙의 *함수형* 을 처음 명시 [Slide L2 p.25–28].

- **1952 — Hodgkin & Huxley, action potential 모델**: squid giant axon 의 voltage clamp 실험 + 4-변수 ODE 로 *최초의 정량적 mechanistic neuron model*. Nobel 1963. 이 모델 하나로 1950년대-1980년대의 cellular neurophysiology 가 통일됨 [Slide L2 p.30–32].

- **1959 — Rall, cable theory**: dendrite 가 *수동적 전선이 아니라* 능동적 통합 장치임을 수학적으로 증명. dendrite 위치에 따라 시냅스 입력이 *다르게 가중* 됨을 처음 정량화 [Slide L2 p.33].

- **1982 — Marr, *Vision* 출판**: 분석의 3 수준 framework. 이후 인지과학·comp-neuro 모두의 *공통 언어* 가 됨.

- **1985 — Schwartz, "computational neuroscience" 용어 정착**: Systems Development Foundation 학회에서 처음 공식화. 그 전엔 "neural modeling", "brain theory" 등 분산되어 있었음 [Slide L2 p.35].

- **1980s–1990s — 시뮬레이터 등장**: GENESIS, NEURON 시뮬레이터 (Bower, Hines). 첫 *Computational and Systems Neuroscience (Cosyne)* 학회 + *Neural Computation* journal [Slide L2 p.36].

- **2000s–현재 — 빅데이터·뇌 지도·deep learning 통합**: Allen Brain Atlas, BRAIN initiative; deep learning이 시각 모델링과 만나 *re-convergence* [Slide L2 p.37–40].

<details>
<summary><em>(펼쳐서 복습) Marr 가 1982 년에 *Vision* 을 출판할 수 있었던 *시대적* 이유</em></summary>

Marr 는 1980 년에 35 세에 백혈병으로 요절한다. *Vision* 은 그가 죽기 전 마지막 5 년의 작업을 정리한 책. 그가 가능했던 이유는 (a) 1970 년대 단일 뉴런 측정 기술 성숙 (Hubel-Wiesel V1 receptive field), (b) 1970 년대 후반 인공지능의 *상징적 추론* 패러다임이 시각 인식에 한계를 보임, (c) Marr 자신이 신경해부학·심리물리·AI 셋 모두에 노출. *세 분야의 통합 시점* 이 그였음.
</details>

---

## §6. 모델 평가 기준 — 어떤 모델이 *좋은* 모델인가?

좋은 모델은 다음 *네 축* 에서 평가된다 — 어느 하나만 만족해서는 안 됨:

1. **데이터 일치도** (data fit) — 모델 출력이 실험 측정치와 *수치적으로* 일치하는가?
2. **Parsimony** (Occam's razor) — 같은 fit 을 다른 모델이 더 적은 매개변수로 달성하면 그 쪽이 우월. McCulloch–Pitts 보다 deep network 가 fit 은 좋지만, 단순성 면에선 McCulloch–Pitts 가 우월.
3. **Predictive power** — 학습 데이터에 없던 *새 조건* 에 대해 정확히 예측하는가? (HH 모델이 학습되지 않은 axon 직경에 대해서도 conduction velocity 를 예측한 것이 *결정적* 인 검증.)
4. **Biological plausibility** — 모델 매개변수가 *측정 가능한 생물학적 양* 인가? 매개변수가 *순수한 수학적 fit-knob* 이면 mechanistic insight 를 잃음.

이 네 축은 *서로 trade-off*. 가령 LIF 모델은 (1) (3) 를 어느 정도 만족하지만 (4) 가 약하고, HH 모델은 (4) 가 강하지만 (2) 가 약함. 좋은 모델 *선택* 이란 곧 *어느 trade-off 를 받아들일 것인가* 의 결정.

<details>
<summary><em>(펼쳐서 복습) "biological plausibility" 가 항상 절대적 미덕인가? — Anderson Hill 의 비판</em></summary>

Hill 등 (1959) 은 "biological plausibility" 가 너무 강조되면 *물리학자가 진자 운동을 설명하는 데 진자의 분자 구성을 고려하라* 는 격이 된다고 비판. 적절한 *추상화 수준* 을 선택하는 것이 modelling 의 *예술적* 측면. 이 trade-off 가 곧 Marr 의 3 levels (각 level 마다 다른 추상화) 의 핵심.
</details>

---

## §7. 흔한 오해와 시험 함정

1. *"Computational neuroscience = AI/ML"* — *틀림*. 둘은 *상호 영감* 관계지만 목적이 다름 (§3 참조).

2. *"Marr 의 3 levels 는 위계적이다"* — *부분적으로 틀림*. 셋은 위계가 아니라 *상보적*. Computational level 이 algorithmic level 을 *완전히 결정* 하지 않음 (같은 목표, 여러 알고리즘).

3. *"좋은 모델은 모든 데이터를 설명한다"* — *틀림*. 좋은 모델은 *적절한 데이터* 를 *parsimonious 하게* 설명하고, *틀리는 데이터* 가 *생산적으로 틀림* (다음 가설을 제공함).

4. *"Hodgkin–Huxley 가 가장 정확한 모델이다"* — *맥락 의존적*. squid axon scale 에서는 정확하나, 피질 추체 dendrite 의 *back-propagating action potential* 은 HH 만으로 부족 — active conductance 가 dendrite 에 분산되어 있음.

5. *"인공신경망의 backpropagation 은 뇌의 학습 규칙이다"* — *현재까지 직접 증거 없음*. Hebbian rule + reinforcement signal 이 더 *biologically plausible* 한 후보. backpropagation 의 dendrite-수준 구현 가능성은 활발한 연구 주제 (예: Lillicrap *et al.*, 2016).

---

## §8. 논술 서술형 대비 (Essay-style problem prep)

L2 는 시험 출제 비중에서 *논술 서술형* 또는 *open-ended* 문제가 차지하는 비율이 높다. 본 절에서 6 개의 *대표 essay 문제* 와 *답안 작성 골격* 을 제공한다. 각 답안은 *(a) 정의 명시 → (b) 구조 제시 → (c) 예시 1–2 개 → (d) 한계 또는 cross-reference* 의 4 단계로 작성하면 안전하다.

---

### 문제 1. **Computational neuroscience 와 neural networks 의 차이를 *목적·방법·검증 기준* 의 3 축으로 비교 설명하시오.**

**답안 골격:**
- (a) 정의: comp-neuro = 뇌 이해를 위한 시뮬레이션; neural networks (인공) = 뇌 영감을 받은 알고리즘 개발 [Slide L2 p.12].
- (b) 3 축 비교 표:
  | 축 | comp-neuro | neural networks |
  |---|---|---|
  | 목적 | *understanding* | *performance* |
  | 방법 | mechanistic + biological constraint | engineering + computational efficiency |
  | 검증 | 실험 데이터 일치 | benchmark accuracy |
- (c) 예시: HH 모델 (comp-neuro) vs ResNet (NN).
- (d) 두 분야의 상호 영감 — Hopfield (1982) 가 통계물리에서 신경과학으로; deep learning 이 시각피질 모델링에 영감.
- **참고**: D&A Preface; Slide L2 p.12.

---

### 문제 2. **Marr 의 3 가지 분석 수준을 정의하고, *시각 인식* 시스템에 대해 각 수준에서 어떤 질문을 하는지 구체적 예시와 함께 서술하시오.**

**답안 골격:**
- (a) 3 수준 정의 (computational / algorithmic / implementational) [Slide L2 p.34].
- (b) 시각 인식 예:
  - Computational: *왜* 시각 시스템이 3D 구조를 추정하는가? (생존을 위한 거리·물체 인식)
  - Algorithmic: *어떻게* edge → contour → object 의 표현 변환을 수행하는가?
  - Implementational: V1 simple cell → complex cell → IT cortex 의 어떤 회로가 실행하는가?
- (c) 셋의 *분리 가능성* 강조 — 같은 algorithm 이 silicon 에서도 구현 가능 (Marr 의 multiple realizability).
- (d) 한계: 셋의 경계가 *언제나 명확한 것은 아님*; learning 을 다룰 때 algorithmic 과 implementational 이 섞임 (학습 규칙이 곧 회로 구조 변경).
- **참고**: Marr (1982); Slide L2 p.34.

---

### 문제 3. **뉴런 모델링의 4 가지 정당화 (왜 모델링인가) 를 D&A 의 *what / how / why* 프레임과 연결하여 서술하시오.**

**답안 골격:**
- (a) 4 가지: descriptive compression / mechanistic insight / quantitative prediction / engineering inspiration [Slide L2 p.16–17].
- (b) D&A *what* = descriptive (1); *how* = mechanistic (2) + predictive (3); *why* = interpretive (often modeled as 4 의 inverse — 자연이 풀고 있는 최적화 문제).
- (c) 예시: spike-triggered average (descriptive *what*); HH model (mechanistic *how*); efficient-coding hypothesis (interpretive *why*).
- (d) 셋이 *상호 보완* — *what* 없이 *how* 못 만들고, *why* 는 *how* 의 자연선택적 정당화.
- **참고**: D&A Preface (p.2 영문판); Slide L2 p.16–17.

---

### 문제 4. **McCulloch–Pitts (1943) 와 Hodgkin–Huxley (1952) 모델을 비교하되, 각 모델이 *어느 Marr level* 에 위치하는지를 핵심 논점으로 삼아 서술하시오.**

**답안 골격:**
- (a) M–P: 이진 입력·임계값·가중치의 *논리* 모델. HH: 4-변수 ODE 의 *물리* 모델.
- (b) Marr level: M–P 는 *algorithmic / computational* 경계 — 어떤 논리식이 가능한지를 다룸. HH 는 *implementational* — 막의 ionic 메커니즘을 묘사.
- (c) *왜 동시대인이 다른 level 을 선택했는가*: 1940 년대엔 ionic 측정 기술 부재, formal logic 이 시대정신; 1950 년대엔 voltage clamp 기술 (Marmont, Cole) 이 등장하며 mechanistic level 가능.
- (d) 두 모델의 *상보성*: M–P → 어떤 *기능* 이 가능한가 (functional capacity); HH → 그 기능이 *어떻게* 구현되는가 (mechanism). 이후 LIF 모델 (L7) 이 둘 사이의 *중간 추상화* 로 자리잡음.
- **참고**: Slide L2 p.20–24, p.30–32.

---

### 문제 5. **Hebbian learning rule 의 *생물학적 plausibility* 와 *engineering 적 활용* 을 모두 평가하되, *현재까지 알려진 한계* 를 포함하시오.**

**답안 골격:**
- (a) Hebb 가설 인용 [Slide L2 p.26]: "When an axon of cell A is near enough to excite cell B and repeatedly or persistently takes part in firing it, some growth process or metabolic change takes place..."
- (b) 생물학적 검증: LTP (Lomo, 1966) 가 Hebbian rule 의 분자 수준 구현; NMDA receptor 가 *coincidence detector* 로 작동.
- (c) Engineering 활용: Hopfield network, Kohonen self-organizing map, recently *unsupervised pre-training* 의 일부.
- (d) 한계 1 — *unstable*: Hebb-only 는 발화율이 무한 증폭됨 → BCM rule, *normalization* 필요. 한계 2 — *causality gap*: A → B 만이 강화되어야 하는데, Hebbian rule 은 단순한 correlation 으로 정의되어 spurious 시냅스 강화 발생 가능 (STDP 가 일부 해결).
- **참고**: Hebb (1949); Lomo (1966); Slide L2 p.25–28.

---

### 문제 6. **Computational neuroscience 가 *과학* 으로 정착하기까지의 *학문사적 조건* 을 1907 (Lapicque) → 1985 (Schwartz) 사이의 핵심 사건 3 개 이상으로 논술하시오.**

**답안 골격:**
- (a) 학문 정의: 1985 Schwartz 가 *Systems Development Foundation* 학회에서 "computational neuroscience" 용어 정착 [Slide L2 p.35].
- (b) 학문사적 조건 3 가지:
  1. *측정 기술 성숙* — voltage clamp (Cole, Marmont, 1949) → HH (1952). 측정 없이는 모델 검증 불가.
  2. *수학적 도구 성숙* — 이산 logic (M–P, 1943), 연속 ODE (HH, 1952), partial differential equation (Rall, 1959). 시기마다 사용 가능한 수학이 모델의 한계를 결정.
  3. *컴퓨팅 자원* — 1980 년대 mini-computer 보급으로 수치 시뮬레이션 가능; GENESIS, NEURON.
- (c) 1985 사건이 *charter event* 인 이유: 분산되어 있던 "neural modeling", "brain theory", "neural networks" 을 *통합 학문 정체성* 으로 묶음.
- (d) *왜 그 시기였는가*: AI winter (1970s 말 ~ 1980s 초) 와 동시기 — 상징주의 AI 의 한계가 분명해지면서 *생물학적* 단서를 다시 찾음.
- **참고**: Slide L2 p.19, p.30–32, p.34–36.

---

## §9. 추가 학습 자료 — D&A Preface 에서 강조하는 핵심 표현

논술 답안에 인용하기 좋은 *원문 표현* (영문):

- *"Theoretical analysis and computational modeling are important tools for characterizing **what** nervous systems do, determining **how** they function, and understanding **why** they operate in particular ways."* — D&A Preface, p.1.
- *"Models can be **descriptive**, **mechanistic**, or **interpretive** depending on the question they address."* — D&A Preface, p.2.
- *"This book is organized into three parts on the basis of general themes: **neural encoding** (Part I), **neurons and neural circuits** (Part II), and **adaptation and learning** (Part III)."* — D&A Preface, p.2.

영문 원문을 직접 인용하면 *답안의 학술적 무게* 가 늘어남 — 단, *반드시* 답안 끝에 (D&A Preface, p.X) 형식으로 출처 표시.

---

## §10. 한 줄 요약

> Computational neuroscience 는 "뇌가 *무엇을* 하는지 (descriptive), *어떻게* 하는지 (mechanistic), *왜 그렇게* 하는지 (interpretive) 를 *수학·시뮬레이션* 으로 답하는 학문" 이다. Marr 의 3 levels 는 이 세 질문의 *분리 가능한* 분석 수준이며, comp-neuro 는 *과학* (이해 추구) 이고 neural network engineering 은 *공학* (성능 추구) — 다만 *상호 영감* 의 60년 역사를 함께 갖는다.

[Slide L2 p.6–17, p.34, D&A Preface p.1–3]
"""


def main():
    conn = psycopg2.connect(DB_DSN)
    try:
        with conn.cursor() as cur:
            # Lookup or upsert
            cur.execute("""
                INSERT INTO lecture_summaries (lecture, lecture_title, summary, sources, generated_at)
                VALUES (%s, %s, %s, %s::jsonb, NOW())
                ON CONFLICT (lecture)
                DO UPDATE SET
                    lecture_title = EXCLUDED.lecture_title,
                    summary = EXCLUDED.summary,
                    sources = EXCLUDED.sources,
                    generated_at = NOW()
            """, (
                'L2',
                'L2 — Computational Neuroscience: 왜, 무엇을, 어떻게',
                L2_SUMMARY,
                '{"slides":["L2 p.6","L2 p.12","L2 p.16","L2 p.17","L2 p.19","L2 p.20-24","L2 p.25-28","L2 p.30-32","L2 p.33","L2 p.34","L2 p.35","L2 p.36"],"textbook":["D&A Preface p.1-3"]}',
            ))
            conn.commit()
            print(f"L2 summary upserted ({len(L2_SUMMARY)} chars)")
    finally:
        conn.close()


if __name__ == '__main__':
    main()
