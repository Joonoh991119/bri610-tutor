#!/usr/bin/env python3
"""Seed L2 lecture narrations (8 steps) — Opus 4.7 hand-authored in this session.

L2 has 0 narration steps prior to this script; L3-L8 each have 8. Steps mirror
the v0.5 narration schema: lecture, step_id, step_kind, title_ko, slide_refs,
narration_md (with embedded enhanced format: original + 🖼 figure + 🔁 변주 + ❓ Q&A).
"""
import psycopg2

DB_DSN = 'dbname=bri610 user=tutor password=tutor610 host=localhost'

L2_STEPS = [
    {
        'step_id': 1,
        'step_kind': 'expose',
        'title_ko': 'Computational Neuroscience 란 무엇인가',
        'slide_refs': ['L2 p.4', 'L2 p.5', 'L2 p.6'],
        'narration_md': '''1️⃣ **출발 질문**: 뇌라는 *세상에서 가장 복잡한 정보 처리 장치* 를 우리는 어떻게 *이해* 할 수 있을까? 측정 데이터만으로는 충분하지 않다 — 수십억 개의 뉴런이 만드는 패턴을 *언어로 환원* 할 수 있어야 한다 [Slide L2 p.4–5].

2️⃣ Computational Neuroscience 는 그 환원 언어로 *수학·계산·모델* 을 사용하는 분야. 1985 년 Schwartz 가 명명한 이래 *뇌 연구의 제3의 기둥* 으로 자리잡았다 (실험 ↔ 이론 ↔ 계산). 다른 두 기둥 (실험 측정, 이론적 분석) 만으로는 *예측 가능한 모델* 을 만들 수 없다.

3️⃣ Computational Neuroscience 가 답하려는 *질문 종류*: (i) 무엇이 일어나는가 (descriptive — tuning curve, PSTH), (ii) 어떻게 일어나는가 (mechanistic — HH, cable theory), (iii) 왜 그렇게 일어나는가 (interpretive — sparse coding, predictive coding) [Slide L2 p.5].

4️⃣ 핵심 인식: *모델은 뇌가 아니다*. 모델은 *질문에 답하기 위한 도구* — "어떤 질문을 묻느냐" 에 따라 *최적 추상화 수준* 이 달라진다. 단일 보편 모델은 존재하지 않는다.

5️⃣ 즉 이 강의의 출발점은 *겸손한 관점*: 우리가 다루는 것은 뇌의 *모델* 이지 뇌 자체가 아니다. 그러나 잘 만든 모델은 *예측 + 통찰* 을 동시에 제공한다 [Slide L2 p.6].

→ 다음: Marr 의 3 단계 framework 가 *어떻게 모든 정보 처리 시스템* 을 분석하는 *공통 언어* 를 제공하는지.

## 🖼 Figure
*(L2 p.4–6 은 제목 슬라이드 위주 — figure 생략, 텍스트만)*

## 🔁 변주

**변주 1 (역사적 비유).** 17세기 천문학에서 Galileo 의 망원경이 *측정* 도구를, Newton 의 미적분이 *모델* 도구를 제공했듯이, 신경과학에서 patch clamp · two-photon imaging 이 측정 도구를, ODE / PDE / 정보이론이 모델 도구를 제공한다. 측정 + 모델의 결합이 *과학적 환원* 의 정수.

**변주 2 (소프트웨어 비유).** Computer scientist 는 *컴파일러* 를 통해 high-level code 를 machine code 로 *환원* 한다. Computational neuroscientist 는 *모델* 을 통해 spike train 을 *수학적 객체* 로 환원한다. 단 차이점: 컴파일러는 *우리가 만든 시스템* 을 분석하지만, 우리는 *진화가 만든 시스템* 을 역공학 (reverse-engineer) 한다.

## ❓ 점검 Q&A

**Q:** Computational neuroscience 가 *수학적 신경과학* 과 같은 말인가?
**A:** 부분적으로 같다. 그러나 computational neuroscience 는 더 좁은 *알고리즘적·계산적* 관점에 무게가 있다 — Marr 의 *Algorithmic + Computational level* 을 함께 다룬다. 순수 *수학적 신경과학* (e.g., Wilson-Cowan equations) 은 동역학 분석에 집중하지만, computational 은 *정보 처리* 의 함수적 의미를 묻는다.

**Q:** "측정만으로는 부족하다" 는 명제의 가장 강력한 증거는?
**A:** 1990s 의 *연결성 데이터 과잉* — 거대한 connectome 데이터가 쌓여도 *기능* 을 자동으로 알려주지 않았다는 사실. C. elegans 의 302 개 뉴런 connectome 이 1986 년에 완성되었지만, 30 년이 지나도 모든 행동을 *예측* 하지 못한다. 측정은 *제약* 을 주지만, *모델* 만이 *왜* 그 회로인지를 묻고 답한다.''',
    },
    {
        'step_id': 2,
        'step_kind': 'expose',
        'title_ko': 'Marr 의 3 단계 — 시스템 분석의 공통 언어',
        'slide_refs': ['L2 p.34', 'L2 p.35'],
        'narration_md': '''1️⃣ **David Marr (1982, *Vision*)** 는 *모든 정보 처리 시스템* — 뇌·컴퓨터 둘 다 — 을 *3 가지 분리 가능* 한 수준에서 분석해야 한다고 주장 [Slide L2 p.34].

2️⃣ 세 수준은 위에서 아래로:
- **Computational level**: *왜 그것이 적절한 목표인가* — 시스템이 *해결해야 할 논리적 문제·목표* 가 무엇인가? (Goal specification.)
- **Algorithmic level**: *어떻게* — 어떤 *표상 + 알고리즘* 으로 그 목표를 달성하는가? (Representation + algorithm.)
- **Implementational level**: *어디서* — 어떤 *물리적 회로 + 동역학* 으로 그 알고리즘을 구현하는가? (Physical realization.)

3️⃣ Marr 의 핵심 통찰: *이 세 수준은 분리 가능* — 같은 *computational goal* 이 여러 *algorithmic* 으로, 같은 algorithm 이 여러 *implementation* 으로 풀릴 수 있다. 따라서 한 수준에서 본 답이 자동으로 다른 수준의 답을 주지 않는다.

4️⃣ V1 orientation selectivity 예시:
- **Computational**: "edge 정보를 추출하는 함수" (자연영상 통계 + sparse code 가 정당화).
- **Algorithmic**: "Gabor filter convolution" — 위치 + 방향이 결합된 표상.
- **Implementational**: "LGN center cell 들이 elongated 배열로 수렴해 simple cell 을 만든다" (Hubel-Wiesel 회로).

5️⃣ Marr 의 3 단계가 *모든 정보 처리 시스템* 의 공통 언어가 된 이유 — 신경과학·심리학·AI 가 *같은 framework* 로 대화 가능. AI 의 deep CNN 이 V1 simple cell 과 통계적으로 유사하다는 *수렴* 증거 (Yamins-DiCarlo 2014) 도 이 framework 위에서 의미를 갖는다.

→ 다음: Marr 의 *Computational* 과 Dayan-Abbott 의 *Why (Interpretive)* 는 정확히 어떻게 대응하는가?

## 🖼 Figure
*(Marr 3-level 도식은 텍스트로만 표현 — Slide L2 p.34 참조)*

## 🔁 변주

**변주 1 (자동차 비유).** Marr 의 3 단계를 자동차로 비유하자.
- **Computational**: 자동차의 *목적* — "사람을 A 에서 B 로 효율적으로 운반".
- **Algorithmic**: *작동 방식* — "내연 기관 + 4 바퀴 + 핸들로 바퀴 회전을 제어".
- **Implementational**: *부품* — "구체적인 piston, cam shaft, alloy wheel". 다른 자동차 모델 (전기차) 도 같은 computational goal 에 다른 algorithmic + implementational 답을 갖는다.

**변주 2 (정렬 알고리즘).** 정렬은 다른 예시.
- Computational: "리스트를 작은 → 큰 순서로 배치" (목적).
- Algorithmic: "merge-sort, quick-sort, bubble-sort 등" (알고리즘).
- Implementational: "x86 CPU의 cache + memory access pattern" (회로).
같은 computational goal 이 다른 algorithm + implementation 의 무한히 많은 조합을 허용한다 — 이것이 *Marr 의 자유도* 분리.

## ❓ 점검 Q&A

**Q:** Marr 의 3 단계 중 *Computational level 이 가장 추상적* 이라고 하는 이유는?
**A:** Computational 은 *what* 과 *why* 만 명시 — *how* 와 *where* 는 자유. 따라서 computational specification 은 그 자체로 무한히 많은 algorithmic / implementational 답을 허용한다. 추상도 = "이 수준에서 결정 안 한 것의 양". Computational 이 가장 적게 결정하므로 가장 추상적.

**Q:** Marr 가 "implementational level 이 무관하다" 라고 한 적은 없다 — 왜 사람들이 종종 그렇게 오해하는가?
**A:** Marr 는 *분리 가능성* 을 주장했지 *무관성* 을 주장한 적은 없다. 그러나 *알고리즘 분석을 implementation 디테일 없이 시작할 수 있다* 는 그의 주장이 종종 "implementation 은 안 봐도 된다" 로 잘못 단순화된다. 사실 *제약* 으로서 implementation 은 algorithm 의 가능 공간을 좁힌다 — biological constraint 가 ML 으로부터 computational neuroscience 를 분기시키는 핵심.''',
    },
    {
        'step_id': 3,
        'step_kind': 'intuition_check',
        'title_ko': '같은 V1 뉴런 — 세 모델 관점',
        'slide_refs': ['L2 p.17', 'L2 p.18'],
        'narration_md': '''1️⃣ Dayan & Abbott (2001) 의 3 가지 모델 유형: **Descriptive (What), Mechanistic (How), Interpretive (Why)**. Marr 의 *Algorithmic ≈ Mechanistic*, *Computational ≈ Interpretive* 로 대응한다 (단, 별개 체계로 오해 금물 — §1 표 참조).

2️⃣ V1 orientation selective 뉴런을 세 관점에서 동시에 보자:

**Descriptive (What)** 답: "이 V1 뉴런의 *tuning curve* 는 45° 에서 최대 발화율 40 Hz, FWHM 30° 의 Gaussian 형태" — *현상의 정량적 기술*. 뉴런의 *모양* 만 본다.

3️⃣ **Mechanistic (How)** 답: "LGN 에서 오는 ON/OFF center cell 들이 *특정 공간 배열* 로 수렴하여 orientation 선호를 만들어낸다 (Hubel-Wiesel 회로 가설)" — *회로 메커니즘*. 어떤 입력 + 연결이 만드느냐.

4️⃣ **Interpretive (Why)** 답: "자연 영상의 *edge 통계* 가 *sparse code* 를 선호하기 때문에, ICA-유사 최적화가 edge detector 를 *해로 갖는다* (Olshausen-Field 1996)" — *기능적 정당화*. 진화·학습이 왜 이 회로를 골랐느냐.

5️⃣ **결정적 통찰**: 세 답은 *서로 모순되지 않는다* — 같은 뉴런의 *서로 다른 측면* 을 본다. *질문이 모델을 결정* — 한 모델이 세 질문을 모두 답하지 않으며, 답하려고 시도하면 어느 하나도 *명확히* 답하지 못한다.

→ 다음: 그렇다면 *Computational Neuroscience* 와 *Neural Networks (artificial)* 은 어디서 분기하는가? 같은 수학을 쓰는데 정체성이 다른 이유.

## 🖼 Figure

<figure><img src="/figures/synapse_chemical.svg" alt="화학 시냅스 6단계 도식 — V1 의 LGN→cortex 연결 메커니즘 예시" /><figcaption>그림: V1 뉴런의 *mechanistic* 관점에서, LGN 에서 오는 시냅스 연결의 6 단계 cascade. 이 회로 디테일이 Hubel-Wiesel 가설의 분자적 실현. <em>Interpretive</em> 관점은 이 회로가 진화적으로 왜 선택되었는지 (edge 통계) 를 묻는다.</figcaption></figure>

## 🔁 변주

**변주 1 (요리 레시피 비유).** 같은 *카르보나라 파스타* 를 세 관점에서:
- **Descriptive**: "삶은 면 + 베이컨 + 달걀노른자 + 후추 + 치즈, 끈적한 텍스처, 짭짤한 맛".
- **Mechanistic**: "달걀 단백질이 70°C에서 변성 → 면의 전분 + 치즈 지방과 emulsion 형성 → 끈적함의 분자적 기원".
- **Interpretive**: "이탈리아 노동자들이 단백질·탄수화물·지방을 한 그릇에 효율적으로 농축 → 영양 + 보존성의 진화적 선택".

세 답은 다른 수준의 질문 — 통합 시 비로소 *완전한 이해*.

**변주 2 (수식과 그림).** V1 뉴런의 응답: $r(\\theta) = r_0 \\exp(-(\\theta - \\theta_0)^2 / 2\\sigma^2)$ 라는 Gaussian — 이건 *descriptive*. Mechanistic 은 $r = f(\\sum w_{ij} \\text{LGN}_j)$ 의 weighted sum + nonlinearity. Interpretive 는 *natural image dataset* 에서 ICA 가 자동으로 만들어낸 basis functions 이 V1 의 receptive field 와 일치한다는 통계적 *수렴*.

## ❓ 점검 Q&A

**Q:** 만약 *Hodgkin-Huxley* 모델로 V1 의 orientation selectivity 를 설명하려 하면 어디가 어색한가?
**A:** HH 는 *spike 생성 메커니즘* (single neuron level) 이고, V1 orientation 은 *회로 수준 + 학습 수준* 의 현상. HH 는 "왜 이 V1 뉴런이 45° 를 선호하는지" 에 답할 수 없다 (다른 V1 뉴런이 90° 를 선호하는 차이는 *입력 연결 가중치* 에서 오므로). 즉 HH 는 *implementational level* 의 도구 — orientation selectivity 의 *algorithmic* 또는 *computational* 답이 아니다. *모델 선택 = 질문 선택* 의 정확한 사례.

**Q:** Descriptive 와 Mechanistic 가 종종 혼동되는데, 결정적 차이는?
**A:** Descriptive 는 *입력 → 출력* 의 통계적 매핑만 — 메커니즘 무관. Mechanistic 은 *입력 → 내부 상태 → 출력* 의 *인과적* 단계를 명시. 예: "이 뉴런이 edge 에 반응한다" (descriptive) vs "이 뉴런은 LGN 의 6 개 ON cell + 4 개 OFF cell 입력을 받아 edge 에 반응한다" (mechanistic). Mechanistic 은 *조작실험* (특정 입력 차단) 의 결과를 예측한다.''',
    },
    {
        'step_id': 4,
        'step_kind': 'expose',
        'title_ko': 'Computational Neuroscience vs Neural Networks 의 분기',
        'slide_refs': ['L2 p.12'],
        'narration_md': '''1️⃣ **표면적 유사성**: Computational Neuroscience (CN) 와 Neural Networks (NN, artificial) 모두 *수학적 모델 + spike-like activations + 학습* 을 사용. 둘 다 1980s deep learning re-convergence 시기에 *공통 수학* (backprop, ReLU, gradient descent) 을 공유.

2️⃣ **결정적 차이**: 가정 변경 시 *생물학적 근거* 를 요구하는가의 차이 [Slide L2 p.12].

- **CN**: "왜 이 가정이 진화적으로 가능한가?" — 막전위, ion channel, synapse, wiring constraint 가 모델을 *제약*.
- **NN**: "왜 이 가정이 *공학적으로* 효율적인가?" — backprop 의 양방향 정보 흐름, 무제한 weight precision, instant global optimization 등 *생물학적으로 어려운* 가정도 자유롭게 사용.

3️⃣ 구체 사례 — **Backpropagation**: NN 에선 효율적 gradient 계산을 위해 자유롭게 사용. CN 에선 *생물학적 backprop 은 어렵다* — postsynaptic 정보가 presynaptic 으로 *역방향* 전달되는 분자 메커니즘이 부재. 대안: Hebbian, predictive coding, equilibrium propagation 등 *생물학적 근거* 를 갖춘 학습 규칙 탐색.

4️⃣ **수렴 사례**: 2010s deep learning re-convergence — CNN 의 receptive field 가 V1 simple cell 과 통계적으로 유사 (Yamins-DiCarlo 2014). *망구조 + 자연 통계* 가 *비슷한 표상으로 수렴* 한다는 강력한 증거. 두 분야가 같은 답에 *독립* 도달.

5️⃣ **발산 사례**: GPT-style transformer 의 self-attention. *메모리 + 시퀀스 처리* 에서 매우 강력하지만, 뇌의 어떤 회로와도 직접 대응 어려움 (특히 K-V cache 의 *모든 과거 input 동시 접근* 은 생물학적으로 부적절). 두 분야가 *같은 수학을 공유* 하더라도 *질문의 분기* 에 따라 발산.

→ 다음: 그렇다면 *왜* 뉴런을 모델링하는가? 4 가지 동기 ("압-발-예-영").

## 🖼 Figure
*(분기 도식은 §3 표로 표현 — figure 생략)*

## 🔁 변주

**변주 1 (생물학 vs 공학).** NN 은 *비행기* 다 — 새의 비행을 영감으로 받았지만 *공기역학적 효율* 만이 설계 기준. 깃털은 무관. CN 은 *조류학* 이다 — 새의 *왜* (진화적 적응) 와 *어떻게* (근육 구조) 를 함께 묻는다. 비행기 엔지니어는 깃털을 무시할 수 있지만 조류학자는 *왜 깃털인가* 를 답해야 한다.

**변주 2 (학습 규칙 비교 표).**
| 학습 규칙 | NN 사용 | CN 사용 | 생물학적 정당성 |
|---|---|---|---|
| Backprop | ✓ 표준 | ✗ 어려움 | 양방향 wiring 부재 |
| Hebbian | ✗ 약함 | ✓ 표준 | LTP / spike-timing |
| Predictive coding | △ 일부 | ✓ 활발 | top-down / bottom-up 수직 회로 |
| STDP | ✗ 거의 없음 | ✓ 일부 | spike timing 에 직접 의존 |

## ❓ 점검 Q&A

**Q:** ReLU 활성화 함수는 신경과학적으로 정당화될 수 있는가?
**A:** *부분적으로 가능*. 실제 뉴런의 *firing rate* 는 음수가 될 수 없음 (rate ≥ 0 하한), threshold 이상에서 *거의 선형*. 그러나 sigmoidal saturation, refractory period, adaptation 같은 *실제 nonlinearity* 는 ReLU 에 없음. *근사 정당화* 는 가능하지만 정확하지 않음 — softplus, GeLU 등 다른 활성화 함수가 더 좋은 근사일 수 있다.

**Q:** 두 분야가 *수렴* 한다면 결국 같아질 것인가?
**A:** *기술적으로 일부 수렴* 하지만, *질문의 분기* 가 본질이다. NN 은 *왜 이것이 효율적인가* 를 묻고, CN 은 *왜 이것이 생물학적으로 가능한가* 를 묻는다. 동일한 backprop 모델이라도 두 분야의 *수용 기준* 이 다르므로, 어느 한쪽이 다른 쪽으로 환원되지 않는다. 미래에는 *neuromorphic computing* 처럼 두 분야가 *공동 영역* 에서 수렴하지만, 각자의 정체성은 유지될 것이다.''',
    },
    {
        'step_id': 5,
        'step_kind': 'expose',
        'title_ko': '뉴런을 모델링하는 4 가지 이유 — "압-발-예-영"',
        'slide_refs': ['L2 p.7', 'L2 p.8'],
        'narration_md': '''1️⃣ 왜 뉴런을 *모델링* 하는가? 단순히 "측정만으로 충분하지 않다" 의 답을 4 가지 동기로 분해 [Slide L2 p.7]:

2️⃣ **압축 (Compression)** — 측정 데이터의 *환원*. 1 초당 수천 spike 를 기록하는 multi-electrode array 의 데이터를 *firing rate, ISI distribution, tuning curve* 같은 소수의 *통계량* 으로 환원. 이는 곧 *information compression* — 데이터의 본질을 추출. *Descriptive* 모델의 핵심 역할.

3️⃣ **발견 (Discovery)** — 모델이 만들어내는 *비자명한 예측* 으로 *새로운 현상* 을 찾는다. Hodgkin-Huxley 모델이 spike 의 *threshold + refractory* 를 자동으로 예측한 것이 대표 사례. 모델이 없었다면 이 두 현상이 *같은 메커니즘* 에서 나온다는 사실을 발견하지 못했을 것이다. *Mechanistic* 모델의 핵심 역할.

4️⃣ **예측 (Prediction)** — 새로운 조건에서의 행동을 *정량* 예측. 약물이 Na 채널 동역학을 어떻게 바꿀지 → AP 모양 변화 → 행동 변화. 임상 신경과학 / 신약 개발의 핵심. *예측력 = 모델의 검증 기준*.

5️⃣ **영감 (Inspiration)** — 뇌의 원리에서 *공학적 영감* 을 얻어 인공 시스템 (NN, neuromorphic chip) 을 설계. CNN 이 V1 receptive field 에서 영감을 얻은 것이 대표. 이 동기는 신경과학을 *AI 의 가설 생성기* 로 사용하는 관점.

→ 다음: 60 년의 역사적 이정표 — Lapicque (1907) 의 LIF 부터 Allen Brain Atlas (2010s) 까지의 narrative.

## 🖼 Figure

<figure><img src="/figures/membrane_rc_circuit.svg" alt="막의 RC 등가 회로 — \"압축\" 의 대표 사례" /><figcaption>그림: 막의 RC 등가 회로. 수십 종의 막 단백질, 수백 종의 ion 분포, 수만 개의 단일 채널 측정을 *3 개의 매개변수* (C_m, R_m, E_L) 와 *1 개의 ODE* 로 압축. 이것이 뉴런 모델링의 "압축" 동기의 원형. [Slide L2 p.21]</figcaption></figure>

## 🔁 변주

**변주 1 (4 동기의 인수분해).**
- 압축: 데이터 → 모델 (소실 압축, lossy summarization)
- 발견: 모델 → 새 현상 (predictive discovery)
- 예측: 모델 + 새 조건 → 정량 예측
- 영감: 뇌 → 인공 시스템 설계

각 동기는 *서로 다른 방향의 정보 흐름* 을 가진다. 같은 모델이 4 동기 모두를 만족하면 *완전체* — 그러나 대부분은 1-2 개에 특화.

**변주 2 (HH 모델의 4-동기 평가).**
- 압축: ✓ — 수많은 voltage clamp 측정을 4 변수 ODE 로 환원.
- 발견: ✓ — refractory + threshold 가 *동시* 출현하는 비자명한 결과.
- 예측: ✓ — TTX, TEA 인가 시 V(t) 정확 예측.
- 영감: △ — direct AI 영감은 약하지만, neuromorphic chip 의 spike-based 표현에 영향.

HH 가 *교과서적 모델* 인 이유: 4 동기 중 3 을 강하게 만족.

## ❓ 점검 Q&A

**Q:** "압축" 동기와 "예측" 동기가 종종 모순되는 이유는?
**A:** 압축은 *데이터를 단순한 형태로* 환원하는 동기 — 단순성을 우선. 예측은 *새 조건에서 정확* 해야 하는 동기 — 모델이 충분히 *복잡* 해야 일반화. 둘은 *bias-variance trade-off* 의 두 극단. 너무 단순한 모델 (낮은 variance, 높은 bias) 은 압축은 잘하지만 예측 부정확; 너무 복잡한 모델 (낮은 bias, 높은 variance) 은 예측 가능하지만 *과적합* 으로 압축 실패. *최소 충분 복잡도 (Occam's razor)* 가 두 동기의 균형점.

**Q:** 4 동기 중 *영감* 이 신경과학에서 종종 *주변* 으로 취급되는데, 그 이유는?
**A:** 영감은 *뇌 → AI* 의 단방향 — 신경과학 자체로는 *자명한 가치* 가 없다 (가설 생성에 머무름). 그러나 영감이 *역으로* AI 발전 → AI 모델이 신경과학 가설 생성기로 작용 (e.g., transformer 가 계층적 attention 의 회로 가설 영감) 의 *순환* 이 시작되며 영감의 가치가 재평가되고 있다. NeurIPS 의 *NeuroAI* sub-track 이 이 순환을 명시.''',
    },
    {
        'step_id': 6,
        'step_kind': 'expose',
        'title_ko': '역사적 이정표 — 60 년의 narrative',
        'slide_refs': ['L2 p.20', 'L2 p.21', 'L2 p.22', 'L2 p.30', 'L2 p.32'],
        'narration_md': '''1️⃣ Computational neuroscience 의 60 년 역사를 핵심 이정표로 정리 [Slide L2 p.20–32]:

2️⃣ **1907 Lapicque** — *Leaky Integrate-and-Fire (LIF)* 모델. 막전위 측정 *불가* 시기에 근육 수축 + 자극 강도 데이터만으로 "$V$ 가 임계 도달 시 발화" 라는 *블랙박스 추상화*. 측정 한계 → 모델 단순성 강제의 원형.

3️⃣ **1952 Hodgkin–Huxley** — *Voltage clamp + giant squid axon + radio-tracer* 의 결합으로 ion-specific kinetics 직접 측정 → 4 변수 ODE 모델. *분야 정체성* 의 시작 — "측정 + 수학 + 모델 = 새 학문" 정립. 1963 노벨상.

4️⃣ **1982 Marr** — *Vision* 출판. 3 levels framework 가 신경과학·심리학·AI 의 *공통 언어* 로 자리잡음. 분야 *정체성 사건*.

5️⃣ **1985 Schwartz** — *"Computational Neuroscience"* 용어 정착 (SDF 학회). 분산된 분야가 통합 명칭을 갖게 됨.

→ 다음: 1980s-90s 시뮬레이터 시대 + 2000s-현재 빅데이터 시대로 이어진다.

## 🖼 Figure
*(타임라인 도식은 §5 표로 표현 — figure 생략)*

## 🔁 변주

**변주 1 (측정 기술이 추상화를 강제).** *각 시대의 모델 추상화 수준은 그 시대의 측정 기술 가용성에 의해 강제된다* — 일반화 원칙.
- 1907 Lapicque: intracellular 측정 부재 → LIF 의 1-변수 블랙박스 추상화.
- 1952 HH: voltage clamp 등장 → 4-변수 ion-specific 모델 가능.
- 2010s+: 단일세포 RNA-seq + connectomics + patch-seq → 다세포 회로 + 분자 다양성 모델.

측정 기술이 *접근 가능한 변수의 집합* 을 결정 → 추상화 수준 *강제*.

**변주 2 (1980s-90s 시뮬레이터 시대).**
- *GENESIS* (Bower, 1990s), *NEURON* (Hines, 1989) — multi-compartment 시뮬레이션.
- *Cosyne* 학회 + *Neural Computation* 저널 창간 → 분야 *시민권* 확립.
- 시뮬레이션이 실험·이론과 *동등한 제3의 기둥* 으로.

**변주 3 (2000s-현재).** Allen Brain Atlas (2003-), BRAIN initiative (2013-), deep learning re-convergence (2012 AlexNet, 2014 Yamins-DiCarlo) — 빅데이터 + 인공신경망의 재수렴. 신경과학과 AI 가 *공동 영역* 에서 협력 (NeuroAI).

## ❓ 점검 Q&A

**Q:** 만약 1952 년에 voltage clamp 가 *발명되지 않았다면* HH 모델이 만들어질 수 있었을까?
**A:** *원리적으로 어렵다*. HH 의 4 변수 ($V, m, h, n$) 분리는 voltage clamp 의 *V 고정 → ionic 전류만 분리* 트릭에 의존. Current clamp (자유 막) 만으론 $g_\\text{Na}, g_K$ 분리가 식별 불가능 (한 식 두 미지수). 1947 Marmont-Cole 의 voltage clamp 발명이 *측정 가능성 → 모델 추상화* 의 결정적 단계. 다른 방법 (e.g., pharmacology 만, single-channel patch clamp 후의 1980s 도달) 이라면 모델이 30 년 늦어졌을 것이다.

**Q:** "1985 Schwartz 의 용어 정착" 이 단순 *naming* 사건인가, 아니면 *학문적* 사건인가?
**A:** 둘 다지만 *학문적* 사건의 측면이 더 크다. 명명 자체가 *연구비 분배 * (NSF, NIH 의 분과 코드), *학회 구조* (SDF), *교과서 분류* (Dayan-Abbott Chapter 1 도입부) 의 인프라를 만들어냄. 명명 없이 분산된 *수학적 신경과학 + 모델링 워크샵 + 시뮬레이션 그룹* 만 있던 1970s 보다 *공동 정체성* 을 갖춘 1990s 가 분야 발전 속도를 *수배* 가속.''',
    },
    {
        'step_id': 7,
        'step_kind': 'derive',
        'title_ko': '모델 평가 기준 — 어떤 모델이 *좋은* 모델인가',
        'slide_refs': ['L2 p.13', 'L2 p.14'],
        'narration_md': '''1️⃣ *좋은 모델* 의 평가 기준을 4 가지 항목으로 정리 [Slide L2 p.13–14]:

2️⃣ **(i) 최소 충분 복잡도 (Parsimony, Occam's razor)** — 더 단순한 모델이 같은 현상을 설명하면 우선. *Realism ≠ 좋은 모델*. 망 동역학을 묻는다면 LIF 가 HH 보다 적합 — *식별 가능성, 계산 비용, 해석 용이성* 모두 우월.

3️⃣ **(ii) 검증 가능성 (Falsifiability)** — 모델이 *틀릴 수 있는* 예측을 만들어야 한다 (Popper). 모든 결과를 설명하는 모델은 *과학이 아니다*. 좋은 모델은 *어떤 실험이 모델을 무너뜨리는지* 명시한다.

4️⃣ **(iii) 식별 가능성 (Identifiability)** — 매개변수가 *데이터로부터 유일하게 결정* 되어야 한다. LIF 의 4 매개변수는 표준 실험 (sub-threshold step + rheobase) 으로 분리 가능 (식별 ✓). Izhikevich 의 4 매개변수 (a, b, c, d) 는 같은 f-I 곡선에 무한히 많은 조합 가능 (식별 ✗).

5️⃣ **(iv) 질문 적합성 (Fit-to-purpose)** — *질문이 모델을 결정*. 망 진동 → LIF, channel kinetics → HH, spike pattern → Izhikevich, dendrite 비선형성 → multi-compartment. 한 모델이 모든 질문을 답하지 않는다.

→ 다음: 이 framework 위에서 L3 으로 진입 — 막 생체물리학으로 첫 *mechanistic* 모델을 구축.

## 🖼 Figure

<figure><img src="/figures/f_i_curve_rheobase.svg" alt="LIF f-I 곡선 — 식별성과 단순성의 결합" /><figcaption>그림: LIF 의 f-I 곡선. 4 매개변수 ($V_\\text{th}, V_\\text{reset}, R_m, \\tau_m$) 가 *명확히 분리* 된 측정 (rheobase, sub-threshold step, refractory) 으로 결정 가능. 식별 가능성과 최소 충분 복잡도가 결합된 좋은 모델의 사례. [Slide L7 §3]</figcaption></figure>

## 🔁 변주

**변주 1 (Bias-variance 균형).** 평가 기준 4 가지를 통계학 언어로 재표현.
- 단순성 (Occam) ↔ *낮은 variance, 높은 bias* — 과소적합 위험.
- 검증 가능성 ↔ *큰 prediction sample space* — falsification 가능 영역.
- 식별성 ↔ *적은 multicollinearity* — 매개변수 직접 분리 가능.
- 질문 적합성 ↔ *taskbias 정렬* — 모델 capacity 가 task 와 일치.

좋은 모델 = bias-variance + identifiability + task alignment 의 4 축 균형.

**변주 2 (모델 선택 의사결정 트리).**
1. 질문은? → 추상화 수준 결정.
2. 데이터는? → 식별 가능 매개변수 수 결정 (보통 *측정 자유도* 의 절반 이하).
3. 계산 비용은? → 수십~수백만 뉴런 시뮬이면 LIF, 단일 뉴런 정밀 분석이면 HH.
4. 검증 실험은? → 모델이 *틀릴 수 있는* 자극·조건 명시.

이 4 단계가 *질문 → 모델* 의 합리적 선택 알고리즘.

## ❓ 점검 Q&A

**Q:** "현실에 가장 가까운 모델이 가장 좋은 모델" 이라는 흔한 오해의 평가는?
**A:** *틀리다*. *Realism ≠ 좋은 모델*. (i) 너무 복잡한 모델은 식별 불가능 (overparameterized), (ii) 망 시뮬레이션에서 계산 불가능 (HH 4 변수 × 10^7 뉴런 = 4×10^7 ODE), (iii) *해석적 통찰* 불가능 (블랙박스화). 좋은 모델은 *질문에 가장 단순한 추상화* — Einstein: "as simple as possible, but not simpler".

**Q:** Izhikevich 모델이 *식별 불가능* 한데도 널리 쓰이는 이유는?
**A:** *질문이 다르다*. Izhikevich 의 강점은 *spike pattern variety* (RS, IB, FS, LTS 등 21 가지) 표현 — *유일 매개변수* 분리는 부차적. 만약 질문이 "이 뉴런이 어느 카테고리에 속하는가" 라면 식별 가능성보다 *카테고리화 력* 이 우선. 따라서 *질문 적합성* 기준에선 Izhikevich 가 LIF 보다 우월할 수 있다 — 평가 기준은 *질문에 따라* 가중치가 달라진다.''',
    },
    {
        'step_id': 8,
        'step_kind': 'connect',
        'title_ko': 'L3 으로의 다리 — 막 생체물리학으로 진입',
        'slide_refs': ['L2 p.21', 'L2 p.30', 'L2 p.32'],
        'narration_md': '''1️⃣ L2 에서 우리는 *왜 모델을 만드는가* 의 framework 를 정립했다: Marr 3 단계 + D&A 3 types + 4 동기 + 4 평가 기준. 이제 *어떻게 만드는가* 의 첫 사례 — 막 생체물리학.

2️⃣ L3 부터 우리는 *mechanistic* 모델을 한 단계씩 구축한다:
- L3: 단일 컴파트먼트 *passive* 막 (RC 회로) + Nernst/GHK 평형.
- L4: Ion channel 4 종 + 시냅스.
- L5: Hodgkin-Huxley *active* 막 (4-변수 ODE).
- L6: Cable theory — 공간 확장.
- L7: 모델 추상화 (LIF/Izhikevich/HH 비교).
- L8: 신경 부호화 — 출력 표현.

3️⃣ 이 6 단계를 완주하면, *낮은 추상화* (분자) 에서 *높은 추상화* (정보 부호) 까지의 *추상화 사다리* 를 직접 오를 수 있다 [Slide L2 p.30].

4️⃣ L3 의 첫 질문: *왜 뉴런은 전기적인가*? 답: *lipid bilayer 가 절연체 + capacitor* 이기 때문. 단순한 RC 회로 모델로 출발하지만, 이 모델이 *왜 뉴런 막전위가 음수인가*, *왜 시간상수가 ms 단위인가*, *왜 spike 가 가능한가* 의 모든 답의 출발점.

5️⃣ **L2 의 결론을 한 문장으로**: 모델은 *질문에 답하기 위한 도구* 이고, *측정 + 수학 + 모델* 의 결합이 신경과학의 제3의 기둥. *질문이 모델을 결정* 한다는 원칙을 기억하면 L3-L8 의 모든 모델 선택을 *원리* 로 이해할 수 있다.

→ 다음 강의 [L3 §1](#summary?lecture=L3): *lipid bilayer 가 capacitor 처럼 행동하는 이유* 부터 시작.

## 🖼 Figure

<figure><img src="/figures/bilayer_capacitor.svg" alt="Lipid bilayer 가 평행판 capacitor 로서 — L3 출발점" /><figcaption>그림: 다음 강의 (L3) 의 출발점. Lipid bilayer 의 두 표면에 정렬된 전하층이 평행판 capacitor 를 이루고, 단위면적당 정전용량 $C_m \\approx \\varepsilon\\varepsilon_0/d$ 가 결정된다. 이 단순한 회로 요소가 뉴런 막전위 모델의 모든 출발점.</figcaption></figure>

## 🔁 변주

**변주 1 (사다리 비유).** L3-L8 은 *추상화 사다리* — 매 강의가 한 단계 위로:
- L3: 분자 (lipid bilayer + ion)
- L4: 회로 요소 (channel + synapse)
- L5: 단일 뉴런 동역학 (HH 4-ODE)
- L6: 공간적 확장 (cable PDE)
- L7: 추상화 비교 (LIF/Izh/HH)
- L8: 정보 부호 (rate/temporal/phase/synchrony)

각 단계는 *전 단계의 추상화* 를 가정으로 사용. L3 없이 L5 를 이해할 수 없고, L6 없이 L8 의 multi-channel coding 을 이해할 수 없다.

**변주 2 (질문 → 모델 매핑).** L2 의 framework 가 L3-L8 에서 어떻게 작동하는지:
- L3 막전위 음수성 → mechanistic (Nernst + GHK) + interpretive (K leak 진화).
- L5 spike all-or-none → mechanistic (HH 양의 피드백) + computational (binary signaling 의 효율).
- L8 phase precession → mechanistic (theta + place cell) + interpretive (sequence 학습의 압축).

각 강의에서 *어느 평가 기준이 우선* 인지 의식하면, 같은 현상의 *서로 다른 모델 답* 을 정리할 수 있다.

## ❓ 점검 Q&A

**Q:** L3-L8 의 강의 순서가 *왜 단순 → 복잡* 으로 정렬되었는가? 다른 순서도 가능한가?
**A:** 단순 → 복잡 순서는 *추상화 의존성* 을 따른다. L5 의 HH 는 L3 의 Nernst/GHK 를 가정으로 사용 (E_Na, E_K 가 어떻게 결정되는지 모르면 HH 의 driving force 항을 이해할 수 없다). L6 의 cable theory 는 L3 의 RC 를 공간 확장. L8 의 phase code 는 L5-L7 의 spike 동역학 위에서 의미를 갖는다. *역순* (L8 → L3) 은 *현상 → 메커니즘* 의 reverse-engineering 으로 가능하지만, *학습 효율* 측면에서 단순 → 복잡 이 우월.

**Q:** L2 에서 가장 "L3-L8 전체에 영향을 미치는" 핵심 통찰을 하나만 꼽는다면?
**A:** *질문이 모델을 결정한다* (= "Realism ≠ 좋은 모델"). 이 원칙은 L3 (Nernst vs GHK 선택), L5 (HH 의 4 변수 vs 더 정확한 Markov 모델), L7 (LIF vs Izhikevich vs HH), L8 (rate vs temporal code) 의 모든 *모델 선택 결정* 을 통일된 원리로 환원한다. 학생이 강의를 듣다가 *왜 이 모델인가* 가 막힐 때마다 이 원칙으로 돌아가면 항상 답이 보인다.''',
    },
]


def main():
    conn = psycopg2.connect(DB_DSN)
    try:
        with conn.cursor() as cur:
            for step in L2_STEPS:
                cur.execute("""
                    INSERT INTO lecture_narrations
                      (lecture, step_id, step_kind, title_ko, slide_refs, narration_md, model)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (lecture, step_id) DO UPDATE SET
                      step_kind = EXCLUDED.step_kind,
                      title_ko = EXCLUDED.title_ko,
                      slide_refs = EXCLUDED.slide_refs,
                      narration_md = EXCLUDED.narration_md,
                      model = EXCLUDED.model,
                      generated_at = now()
                """, (
                    'L2', step['step_id'], step['step_kind'], step['title_ko'],
                    step['slide_refs'], step['narration_md'],
                    'anthropic/claude-opus-4-7|enhanced',
                ))
        conn.commit()
        print(f'L2: {len(L2_STEPS)} steps seeded (Opus 4.7 hand-authored, enhanced format)')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
