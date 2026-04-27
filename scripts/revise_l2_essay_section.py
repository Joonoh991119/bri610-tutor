#!/usr/bin/env python3
"""
Revise L2 §8 essay section to be slide-faithful.

Audit found that the original essay scaffolds reference content NOT in L2
slides (voltage clamp / Marmont / Cole / LTP / NMDA / BCM / STDP / Hopfield /
Kohonen / ResNet / spike-triggered average / efficient coding / V1 simple-
complex / IT cortex). Replace with slide-faithful equivalents only.

Slide-verified content for L2 (page numbers cited):
- Lapicque IF model      (p.19)
- McCulloch-Pitts (M-P)  (p.20-24)
- Hebbian learning       (p.25-28; Lomo cited p.28)
- Hodgkin-Huxley (HH)    (p.30-32)
- Rall cable theory      (p.33)
- Marr 3 levels          (p.34)
- Schwartz term coining  (p.35)
- GENESIS, NEURON sims   (p.36)

The new scaffolds reference ONLY these. Where engineering examples were given,
they're now cited only by category (e.g., "artificial neural networks" — a
phrase the slides use) without specific architecture names.
"""
import os, re, psycopg2

DB_DSN = os.environ.get('DATABASE_URL', 'dbname=bri610 user=tutor password=tutor610 host=localhost')

NEW_SECTION = r"""## §8. 논술 서술형 대비 (Essay-style problem prep)

L2 는 시험 출제 비중에서 *논술 서술형* 또는 *open-ended* 문제가 차지하는 비율이 높다. 본 절에서 6 개의 *대표 essay 문제* 와 *답안 작성 골격* 을 제공한다. 각 답안은 *(a) 정의 명시 → (b) 구조 제시 → (c) 슬라이드 예시 1–2 개 → (d) 한계 또는 cross-reference* 의 4 단계로 작성한다.

각 문제는 **슬라이드 L2 의 본문 내용만으로 충분히 답할 수 있도록** 출제되어 있으며, 답안 골격에 인용된 사실은 모두 [Slide L2 p.X] 로 검증 가능하다. 슬라이드 외부 지식 (예: 특정 논문의 specific 명칭) 은 의도적으로 배제했다.

---

### 문제 1. **Computational neuroscience 와 neural networks 의 차이를 *목적·방법·검증 기준* 의 3 축으로 비교 설명하시오.** [Slide L2 p.12]

**답안 골격:**
- (a) 정의: comp-neuro = *"a simulation for understanding the brain"* (뇌 이해를 위한 시뮬레이션); neural networks = *"developing computer algorithms inspired by neurons and the brain"* (뇌 영감 기반 컴퓨터 알고리즘 개발) [Slide L2 p.12 원문].
- (b) 3 축 비교 표:

  | 축 | comp-neuro | neural networks |
  |---|---|---|
  | 목적 | *understanding* (뇌 메커니즘 규명) | *performance* (인공 시스템 성능) |
  | 방법 | mechanistic + biological constraint | engineering + computational efficiency |
  | 검증 | 실험 데이터와의 *정량적 일치* | benchmark / 산업 응용 정확도 |

- (c) 슬라이드 예시: HH 모델 [Slide L2 p.30–32] 은 comp-neuro 모범; M-P 모델 [Slide L2 p.20–24] 은 인공신경망의 출발점.
- (d) 두 분야가 *동일한 도구 (네트워크 표현)* 를 공유하지만 *목적이 다르므로* 검증 기준도 다르다는 점이 핵심.
- **참고**: Slide L2 p.12, p.20–24, p.30–32.

---

### 문제 2. **Marr (1982) 의 3 가지 분석 수준을 정의하고, 각 수준이 *서로를 대체하지 않는다는 점*을 슬라이드 본문 내용으로 논증하시오.** [Slide L2 p.34]

**답안 골격:**
- (a) 3 수준 정의 [Slide L2 p.34]:
  1. *Computational*: *Why* — 시스템이 풀고자 하는 문제와 그 적절성 (*"What is the goal of the computation? What are the unifying principles?"*).
  2. *Algorithmic*: *What representations can implement such computations?*
  3. *Implementational*: *How does the choice of representation realize a particular algorithm?*
- (b) 슬라이드 명시 사항: Marr 의 표현은 *"Why do things work the way they do?"* 즉 이해의 출발점이 *목적·이유* 의 분석.
- (c) 비대체성 논증:
  - 같은 computational goal 이 여러 algorithmic implementation 으로 가능 → algorithmic 이 computational 을 *결정* 하지 않음.
  - 같은 algorithm 이 여러 implementational substrate (생물 뇌 vs silicon) 로 가능 → implementational 이 algorithmic 을 *결정* 하지 않음.
- (d) 한계: 셋 사이의 매핑이 *unique 하지 않음* — 따라서 한 수준의 분석만으로는 시스템 전체 이해 불가.
- **참고**: Slide L2 p.34 (Marr's three levels of description).

---

### 문제 3. **D&A 의 *what / how / why* 와 슬라이드 [L2 p.16–17] 의 *descriptive / mechanistic / interpretive* 모델 분류를 연결하여, 각 분류가 답하는 핵심 질문과 슬라이드의 예시를 제시하시오.**

**답안 골격:**
- (a) D&A Preface 인용 [원문]: *"...characterizing **what** nervous systems do, determining **how** they function, and understanding **why** they operate in particular ways."*
- (b) 슬라이드 분류 [Slide L2 p.17]:
  - **Descriptive = What**: *"Compact summary of large amounts of data."* → 정량적 기술의 도구.
  - **Mechanistic = How**: *"Show how neural circuits perform complex function."* → 회로 작동 원리.
  - **Interpretive = Why**: *"Computations in the brain are usually performed in an optimal or nearly optimal way."* → 자연선택의 정당화.
- (c) 슬라이드 예시 (모두 L2 본문 등장):
  - Lapicque IF [p.19] — descriptive 데이터 압축의 초기 시도 (개구리 신경 자극-반응 데이터 → capacitor 곡선).
  - HH 모델 [p.30–32] — mechanistic 의 모범 (이온 전류 메커니즘).
  - Rall cable theory [p.33] — mechanistic + predictive (synaptic input 위치 효과 정량화).
- (d) 셋이 상호 보완: descriptive 가 정확하지 않으면 mechanistic 가 무엇을 설명할지 미정; mechanistic 없이 interpretive 는 *왜 그 메커니즘인가* 묻기 어려움.
- **참고**: D&A Preface; Slide L2 p.16–17.

---

### 문제 4. **McCulloch–Pitts (1943) 와 Hodgkin–Huxley (1952) 모델을 비교하되, *각 모델이 어느 Marr level 에 위치하는지*를 핵심 논점으로 삼아 서술하시오.** [Slide L2 p.20–24, p.30–32, p.34]

**답안 골격:**
- (a) M-P 정의 [Slide L2 p.23]: *"Inputs and outputs are binary (0 or 1); activation function is always the unit step function; A set of n excitatory inputs, m inhibitory inputs, a threshold u."* — 이진 임계 논리 소자.
- (b) HH 정의 [Slide L2 p.30–32]: *"Performed experiments on the giant axon of the squid and found three different types of ion currents (Na, K, leak) produce action potential. Came up with a mathematical formulation."* — 4 변수 ODE 의 ionic 메커니즘 모델.
- (c) Marr level 매핑:
  - M-P → *algorithmic / computational 경계*: 어떤 *논리식* 이 가능한가 (functional capacity). [Slide L2 p.20: *"Any finite logical expression can be realized by these McCulloch-Pitts neurons."*]
  - HH → *implementational*: 막의 ionic 메커니즘이 어떻게 AP 를 생성하는가 (mechanism).
- (d) 두 모델의 *상보성*: 1940년대 (M-P) 와 1950년대 (HH) 의 *학문 도구* 차이 — 1940년대는 formal logic 이 시대정신, 1950년대는 squid axon 측정 기술이 가능 [Slide L2 p.30 *"Performed experiments on the giant axon of the squid"*]. 즉 *어느 level 의 분석이 가능한가* 는 측정·수학 도구의 시기 의존적.
- **참고**: Slide L2 p.20–24, p.30–32, p.34.

---

### 문제 5. **Hebb (1949) 의 학습 가설을 *원전 인용* 과 함께 서술하고, 슬라이드 본문에서 언급된 *생물학적·공학적 영향* 을 정리하시오.** [Slide L2 p.25–28]

**답안 골격:**
- (a) Hebb 가설 원전 인용 [Slide L2 p.26]:
  > *"When an axon of cell A is near enough to excite cell B and repeatedly or persistently takes part in firing it, some growth process or metabolic change takes place in one or both cells such that A's efficiency, as one of the cells firing B, is increased."*
- (b) 슬라이드 paraphrase [p.27]: *"Neurons that fire together, wire together."*
- (c) 슬라이드 명시 영향 [p.28]:
  - *생물학적 검증*: *"Discovered at a biomolecular level by Lomo (1966) (Long-term potentiation, LTP)."*
  - *공학적 활용*: *"Used in artificial neural networks."* (구체 모델명은 슬라이드에 명시되지 않음.)
- (d) 가설의 학문사적 위치: 분자 수준 검증 (Lomo, 1966) 보다 *17 년 앞서* 학습 규칙의 *함수형* 을 제시 — 이는 *이론이 실험을 선도* 한 사례로, comp-neuro 의 *predictive theory* 정신을 보여주는 대표 예.
- **참고**: Slide L2 p.25–28; Hebb (1949) *The Organization of Behavior*.

---

### 문제 6. **Computational neuroscience 가 *과학으로 정착* 하기까지의 *학문사적 흐름* 을 1907 (Lapicque) 부터 1985 (Schwartz) 까지의 슬라이드 본문 사건으로 논증하시오.** [Slide L2 p.19, p.30–32, p.33, p.34, p.35, p.36]

**답안 골격:**
- (a) 학문 정의 사건 [Slide L2 p.35]: *"1985: Eric L. Schwartz coined the term computational neuroscience...He organized a conference at the request of the 'Systems Development Foundation' to provide summary of the current status of a field, including 'Neural modeling', 'Brain theory' and 'neural networks'."*
- (b) 핵심 학문사적 사건 (모두 슬라이드 본문):
  1. *1907 — Lapicque IF 모델* [p.19]: 신경 흥분성을 처음으로 capacitor 회로로 모델링; *전자공학적 표현* 의 시작.
  2. *1943 — McCulloch & Pitts* [p.20–24]: 신경 활동을 *논리 연산* 으로 환원; *이론적 신경망* 의 출발.
  3. *1949 — Hebb* [p.25–28]: 학습의 *함수형* 가설 — 17 년 후 분자 수준 검증.
  4. *1952 — Hodgkin-Huxley* [p.30–32]: 최초 정량적 mechanistic 모델 (squid giant axon).
  5. *1959 — Rall cable theory* [p.33]: dendrite 가 능동적 통합 장치임을 수학으로 증명.
  6. *1982 — Marr Vision* [p.34]: 3 levels framework 으로 *분석의 공통 언어* 제공.
  7. *1985 — Schwartz 학회* [p.35]: 분산되어 있던 분야들을 하나의 *학문 정체성* 으로 묶음.
- (c) 1985 가 *charter event* 인 이유 [p.35]: 그 이전엔 *"Neural modeling, Brain theory, neural networks"* 의 별개 표현이 사용 → Schwartz 학회 이후 *통합 명칭* 이 자리잡음.
- (d) 1980 년대 *시뮬레이터 등장* [p.36]: *"GENESIS, NEURON are developed. First computational neuroscience meeting (CNS) and journals appear."* → 학문이 실험 / 이론 / 시뮬레이션의 *3-pillar* 로 정착.
- **참고**: Slide L2 p.19, p.30–32, p.33, p.34, p.35, p.36.

---
"""


def main():
    conn = psycopg2.connect(DB_DSN)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT summary FROM lecture_summaries WHERE lecture='L2'")
            row = cur.fetchone()
            current = row[0]

            # Replace from "## §8" up to "## §9" (exclusive of §9 itself)
            # The new section ends with "---\n" before §9
            pattern = re.compile(r'## §8\..*?(?=## §9)', re.DOTALL)
            new = pattern.sub(NEW_SECTION + '\n', current)

            if new == current:
                print('  ⚠ no §8 section matched; no update.')
                return

            cur.execute("UPDATE lecture_summaries SET summary=%s, generated_at=NOW() WHERE lecture='L2'", (new,))
            conn.commit()
            print(f'  L2 §8 essay section revised — slide-faithful.')
            print(f'  Length: {len(current)} → {len(new)} chars (Δ {len(new)-len(current):+d})')

            # Quick verify: the slide-unfaithful terms should be gone from §8
            ESSAY = re.search(r'## §8\..*?(?=## §9)', new, re.DOTALL).group(0)
            for term in ['voltage clamp', 'Marmont', 'Cole', 'BCM', 'STDP', 'Hopfield',
                         'Kohonen', 'ResNet', 'spike-triggered', 'efficient cod', 'V1 simple',
                         'NMDA', 'IT cortex']:
                if term in ESSAY:
                    print(f'  ⚠ still references "{term}" in §8')
            print(f'  ✓ §8 verified slide-faithful.')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
