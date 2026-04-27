#!/usr/bin/env python3
"""L8 quiz bank — Neural Codes: Rate, Temporal, Phase, Synchrony."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from generate_quiz_bank import insert_quiz_items, insert_take_home, DB_DSN
import psycopg2

L8_QUIZ = [
    {
        'position': 1, 'kind': 'mcq', 'difficulty': 1, 'bloom': 'Remember',
        'topic_tag': 'rate-code',
        'prompt_md': '*Rate code* 의 정의로 가장 정확한 것은?',
        'choices_json': [
            {'key': 'A', 'text': '한 spike 의 timing 이 정보 단위.', 'correct': False},
            {'key': 'B', 'text': '*시간 평균 발화율* 이 정보 단위 — spike 시기 자체는 무관.', 'correct': True},
            {'key': 'C', 'text': '두 뉴런의 동시 발화.', 'correct': False},
            {'key': 'D', 'text': '발화 진동의 위상.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': 'Rate code: 메시지 = $\\bar r$ (시간 평균 spike 수). 정보 단위는 *시간당 spike 개수* 만 — 어느 정확 시점에 발화했는지는 무관. 운동신경, V1 firing rate-tuning 이 전형 [Slide L8 §1].',
        'slide_ref': '[Slide L8 §1]',
    },
    {
        'position': 2, 'kind': 'mcq', 'difficulty': 2, 'bloom': 'Understand',
        'topic_tag': 'psth',
        'prompt_md': 'PSTH (peri-stimulus time histogram) 이 *반복 가능한* 자극을 요구하는 이유는?',
        'choices_json': [
            {'key': 'A', 'text': '단일 시행으로는 발화율을 계산할 수 없어서.', 'correct': False},
            {'key': 'B', 'text': '여러 trial 의 spike 시각을 *자극 onset 기준* 정렬하여 *시간 bin 별* 평균 spike 밀도를 추출하기 때문.', 'correct': True},
            {'key': 'C', 'text': '뉴런이 학습하기 위해.', 'correct': False},
            {'key': 'D', 'text': '계산 시간 절약.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': 'PSTH 는 *trial-averaged* spike density. 같은 자극을 반복 인가 → 각 trial 의 spike 시각을 *자극 onset = 0* 으로 정렬 → bin (e.g., 20 ms) 별 spike 수 합산. 결과 = "자극 후 시간 t 에서 발화 확률". *반복 자극이 없으면* trial 평균 자체 불가능 — single-trial decoding 은 PSTH 로 못 함 [Slide L8 §2].',
        'slide_ref': '[Slide L8 §2]',
    },
    {
        'position': 3, 'kind': 'mcq', 'difficulty': 3, 'bloom': 'Analyze',
        'topic_tag': 'temporal-code',
        'prompt_md': '*같은 spike 개수* 를 가진 두 raster 가 *다른* 정보를 나를 수 있는 이유는?',
        'choices_json': [
            {'key': 'A', 'text': 'Rate 가 같으므로 정보가 같다.', 'correct': False},
            {'key': 'B', 'text': '*Spike 사이 간격 (ISI) 패턴* 이 정보를 나를 수 있다 — temporal code.', 'correct': True},
            {'key': 'C', 'text': '두 raster 는 항상 동일.', 'correct': False},
            {'key': 'D', 'text': 'Rate 가 정보의 유일한 단위.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': '*Rate ≠ 정보의 전부*. ISI 분포, burst 패턴, 첫 spike 잠복기 등이 추가 정보 차원. 청각 뉴런: 같은 rate 에 다른 sound 가 다른 ISI 패턴 → temporal precision (sub-ms) 이 핵심. 운동신경 같은 *적분기* 는 rate 만 중요, 청각/시각 *고속 신호 검출* 은 timing 도 중요 [Slide L8 §3].',
        'slide_ref': '[Slide L8 §3]',
    },
    {
        'position': 4, 'kind': 'mcq', 'difficulty': 3, 'bloom': 'Apply',
        'topic_tag': 'phase-code',
        'prompt_md': '*Phase precession* (place cell) 이 *temporal compression* 을 만든다는 것의 의미는?',
        'choices_json': [
            {'key': 'A', 'text': 'AP 가 더 빨리 전파된다.', 'correct': False},
            {'key': 'B', 'text': '*수 초 분량의 공간 sequence* (place field 통과) 가 *100 ms (1 theta cycle) 안에 sub-ms 간격의 spike sequence* 로 압축됨 — 학습 가능한 *압축 표현*.', 'correct': True},
            {'key': 'C', 'text': '발화율이 감소한다.', 'correct': False},
            {'key': 'D', 'text': '동기화 자체가 정보.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': 'Theta cycle ($\\sim 8$ Hz, 125 ms): 한 cycle 에서 여러 place cell 이 위상 순서대로 발화 — 즉 *공간 순서* 가 *시간 순서* 로 매핑. 행동 속도 (수 초) → cycle 내 시간 (100 ms) 으로 *수십 배 압축*. 이 압축이 hippocampal *replay/preplay* 의 기초 — sleep 중 sequence 가 더 빠르게 재생 [Slide L8 §B].',
        'slide_ref': '[Slide L8 §B]',
    },
    {
        'position': 5, 'kind': 'mcq', 'difficulty': 4, 'bloom': 'Analyze',
        'topic_tag': 'mainen-sejnowski',
        'prompt_md': 'Mainen & Sejnowski (1995) 의 *trial-to-trial reliability paradox* 의 핵심 발견은?',
        'choices_json': [
            {'key': 'A', 'text': '뉴런은 항상 신뢰할 수 없다.', 'correct': False},
            {'key': 'B', 'text': '*뉴런 자체* 는 sub-ms 정확도로 신뢰 가능 — *DC 자극* 에선 trial 마다 timing 변동, *frozen noise* (시간 구조 있는 자극) 에선 trial 마다 *정확히 동일* spike timing.', 'correct': True},
            {'key': 'C', 'text': '뉴런은 randomness 를 만든다.', 'correct': False},
            {'key': 'D', 'text': '실험 오류였다.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': '*Paradox*: in vivo 발화는 trial 마다 다른 timing 으로 보임 → 뉴런이 noisy 라는 가설. 그러나 in vitro 에서 *frozen noise* (반복 가능한 시간 구조) 인가 → spike timing 이 trial 마다 *정확히 동일* (sub-ms). 결론: variability 는 *뉴런 자체* 가 아니라 *flat (DC) 자극* 의 결과 — 채널 noise 가 임계 도달 timing 을 결정 → 시간 구조 없으면 noise 가 보이고, 있으면 input 이 spike 를 *고정*. **함의**: Temporal code 가 *원리적으로 가능* — 자극이 시간 구조를 가지면 [Slide L8 §11].',
        'slide_ref': '[Slide L8 §11]',
    },
    {
        'position': 6, 'kind': 'mcq', 'difficulty': 3, 'bloom': 'Apply',
        'topic_tag': 'synchrony-code',
        'prompt_md': 'Synchrony code 의 *Binding problem* 에 대한 가설로 가장 정확한 것은?',
        'choices_json': [
            {'key': 'A', 'text': '뉴런이 학습으로 묶인다.', 'correct': False},
            {'key': 'B', 'text': '*동시 발화* (synchrony) 가 *어떤 객체에 속하는가* 의 신호 — 빨간 사각형 = 빨간 뉴런과 사각형 뉴런이 동기 발화.', 'correct': True},
            {'key': 'C', 'text': 'Population rate 가 binding 신호.', 'correct': False},
            {'key': 'D', 'text': 'Phase precession 이 binding.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': 'Singer 의 *binding problem* 가설: 뇌가 객체의 *여러 특징* (색, 모양, 운동, 위치) 을 어떻게 *하나의 객체* 로 묶는가? 답 (가설): 동기 발화 — 같은 객체에 속한 특징을 처리하는 뉴런들이 ms 정확도로 동시 발화 → downstream 이 "이 spike 들은 한 객체" 로 인식. Hippocampal-PFC theta sync 가 이런 cross-area binding 의 신경 증거 [Slide L8 §6].',
        'slide_ref': '[Slide L8 §6]',
    },
    {
        'position': 7, 'kind': 'mcq', 'difficulty': 3, 'bloom': 'Analyze',
        'topic_tag': 'multiplexed',
        'prompt_md': 'Multiplexed code 가 *boundary case* 가 아닌 *일반적* 코드인 이유는?',
        'choices_json': [
            {'key': 'A', 'text': '특수 뉴런만 multiplex 가능.', 'correct': False},
            {'key': 'B', 'text': '*같은 spike train* 위에 rate / temporal / phase / synchrony 의 *4 채널이 동시에* 정보를 나르므로 — 한 spike 가 여러 정보 차원에 동시 기여.', 'correct': True},
            {'key': 'C', 'text': '망 진동에서만 발생.', 'correct': False},
            {'key': 'D', 'text': 'Multiplex 는 인공적 개념.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': 'CA1 place cell 의 *3 채널 동시 발화*: (1) Rate channel — field 중심에서 max rate ("어디 근처"), (2) Phase channel — field 진입 = late θ, 진출 = early θ ("field 내 위치"), (3) Synchrony channel — 같은 field 의 cell 들이 *theta cycle 내 함께* 발화 ("어느 장소 멤버"). Jang et al. (2020) 정보이론 분해로 *각 채널이 독립 정보* 를 나름을 확인. 즉 multiplex 가 일반 — 단일 채널만 보는 것이 *부분 분석* [Slide L8 §B.2].',
        'slide_ref': '[Slide L8 §B.2]',
    },
    {
        'position': 8, 'kind': 'mcq', 'difficulty': 4, 'bloom': 'Evaluate',
        'topic_tag': 'common-misconception',
        'prompt_md': '*"보편 신경 부호 (universal code) 가 존재한다"* — 평가하라.',
        'choices_json': [
            {'key': 'A', 'text': '맞다. Rate code 가 보편.', 'correct': False},
            {'key': 'B', 'text': '*틀리다*. *맥락별 지배 부호* 만 있다 — 운동 = rate, 청각 = temporal, hippocampal = phase + multiplex, 시각 binding = synchrony. 영역·시기·행동에 따라 가변.', 'correct': True},
            {'key': 'C', 'text': '맞다. Temporal code 가 보편.', 'correct': False},
            {'key': 'D', 'text': '관련 없는 두 개념.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': '"보편 부호" 는 단순화 — 진화는 *문제별 최적 부호* 를 선택. 청각의 sub-ms 정확성 (sound localization) 은 rate 로 불가, 시각의 binding 은 synchrony, hippocampal 의 sequence learning 은 phase compression. *맥락 의존성* 이 일반 원칙 — 한 채널이 *항상* 지배하지 않는다 [Slide L8 §D].',
        'slide_ref': '[Slide L8 §D]',
    },
    # Short-answer
    {
        'position': 9, 'kind': 'short_answer', 'difficulty': 1, 'bloom': 'Remember',
        'topic_tag': 'four-codes',
        'prompt_md': '4 가지 신경 부호화 방식을 영어로 나열하라.',
        'correct_text': 'rate, temporal, phase, synchrony',
        'accept_patterns': [
            r'(?i)rate\s*[,;]?\s*temporal\s*[,;]?\s*phase\s*[,;]?\s*synchrony',
            r'(?i).*rate.*temporal.*phase.*synchrony',
        ],
        'rationale_md': '*Rate* (시간 평균 발화율), *Temporal* (정확한 spike timing), *Phase* (진동에 대한 위상), *Synchrony* (다중 뉴런 동시 발화). 이 4 채널이 *multiplexed* 로 동시 작동 가능.',
        'slide_ref': '[Slide L8 §1, §3, §B, §6]',
    },
    {
        'position': 10, 'kind': 'short_answer', 'difficulty': 2, 'bloom': 'Apply',
        'topic_tag': 'theta-frequency',
        'prompt_md': 'Hippocampal theta 진동의 표준 주파수 (Hz) 와 cycle 길이 (ms) 를 답하라.',
        'correct_text': '~8 Hz, 125 ms',
        'accept_patterns': [
            r'(?i)\b8\s*Hz.*125\s*ms',
            r'(?i)\b125\s*ms.*8\s*Hz',
            r'(?i)6.{0,5}8\s*Hz.*100.{0,5}170\s*ms',
        ],
        'rationale_md': 'Theta: 4–10 Hz (전형 ~8 Hz). 1/8 Hz = 125 ms. 이 cycle 내에서 phase precession 이 *공간 sequence* 를 *시간 sequence* 로 압축. Sleep 중 replay 는 theta 가 사라지고 *sharp-wave ripples* (140-200 Hz) 가 등장.',
        'slide_ref': '[Slide L8 p.39]',
    },
    {
        'position': 11, 'kind': 'short_answer', 'difficulty': 2, 'bloom': 'Apply',
        'topic_tag': 'psth',
        'prompt_md': 'PSTH 의 표준 bin width (수 ms 단위) 를 답하라 (전형값).',
        'correct_text': '20 ms',
        'accept_patterns': [
            r'\b1[0-9]\s*ms\b',
            r'\b2[0-5]\s*ms\b',
            r'\b1\s*[-~]\s*5\d\s*ms\b',
        ],
        'rationale_md': '전형 bin = 10–50 ms (가장 흔히 20 ms). Bin 너무 작으면 spike 빈도가 0/1 로 변동 (noise), 너무 크면 시간 구조 사라짐 (over-smoothing). *Optimal bin* 은 자극 시간 척도 + 발화율 + trial 수에 따라 trade-off.',
        'slide_ref': '[Slide L8 p.20–25]',
    },
    {
        'position': 12, 'kind': 'mcq', 'difficulty': 4, 'bloom': 'Analyze',
        'topic_tag': 'common-misconception',
        'prompt_md': '*"DC 자극에서 spike timing 변동은 뉴런이 noisy 하다는 증거다"* — 평가하라.',
        'choices_json': [
            {'key': 'A', 'text': '맞다. 뉴런은 본질적으로 noisy.', 'correct': False},
            {'key': 'B', 'text': '*틀리다*. Mainen & Sejnowski 가 보였듯이 — *frozen noise* (시간 구조 있는 자극) 에선 spike timing 이 trial 마다 정확히 동일. DC 의 변동은 *flat 자극이 임계 도달 시각을 결정 못 함* 의 결과 — 뉴런 자체는 sub-ms 정확.', 'correct': True},
            {'key': 'C', 'text': '맞다. DC 자극이 noisy.', 'correct': False},
            {'key': 'D', 'text': '관련 없다.', 'correct': False},
        ],
        'correct_key': 'B',
        'rationale_md': '뉴런 noise (channel noise) 는 *항상 존재* — 그러나 *sharp 시간 구조 자극* 이 있으면 임계 도달 시각이 *입력에 의해 결정* 되어 noise 의 영향이 작다. *Flat (DC)* 자극은 임계 근처에서 noise 가 결정적 → trial 마다 timing 변동. 이 *의외의 통찰* 이 in vivo (cortical) variability 와 in vitro (slice, frozen noise) 의 차이를 설명 [Slide L8 §11].',
        'slide_ref': '[Slide L8 §11]',
    },
]


L8_TAKE_HOME = [
    {
        'position': 1, 'kind': 'derivation', 'difficulty': 4, 'max_points': 12, 'expected_time_min': 20,
        'topic_tag': 'fano-factor',
        'prompt_md': '''Spike count statistics 와 *Fano factor* 분석:
(a) (3점) Rate $r$ 인 *Poisson* 과정에서 시간 $T$ 안의 spike 수 $n$ 의 분포 $P(n)$ 작성. 평균과 분산 표현.
(b) (4점) **Fano factor** $F = \\text{Var}(n) / \\text{E}[n]$ 정의. Poisson 의 경우 $F = 1$ 임을 증명.
(c) (3점) *실제* cortical 뉴런은 흔히 $F < 1$ (*sub-Poisson*) 또는 $F > 1$ (*super-Poisson*) 을 보인다. 각 경우의 *생물학적 의미* 를 한 문장씩.
(d) (2점) 만약 *refractory period* 가 있으면 Fano factor 는 보통 1 보다 큰가 작은가? 직관 설명.''',
        'model_answer_md': '''(a) **Poisson 분포**: $P(n) = (rT)^n e^{-rT}/n!$. 평균 $\\langle n \\rangle = rT$, 분산 $\\text{Var}(n) = rT$ (Poisson 의 정의적 성질 — 평균 = 분산).

(b) **Fano factor**: $F = \\text{Var}(n)/\\langle n \\rangle$. Poisson: $F = rT/rT = 1$. 즉 *분산이 평균과 같음* — Poisson 의 signature. *증명*: $\\text{Var}(n) = \\sum n^2 P(n) - \\langle n \\rangle^2 = \\sum n(n-1) P(n) + \\langle n \\rangle - \\langle n \\rangle^2 = (rT)^2 + rT - (rT)^2 = rT$.

(c) **실제 뉴런의 Fano factor**:
- $F < 1$ (sub-Poisson, 흔히 0.3-0.7): 뉴런이 *더 규칙적* 으로 발화 — refractory period 가 short ISI 를 제거 → 분산 < 평균. 운동신경, fast-spiking interneuron 에서 흔함.
- $F > 1$ (super-Poisson): 뉴런이 *bursty* 또는 *slow rate fluctuation* 으로 발화 — burst 사이의 long silence 가 분산을 키움. Cortical pyramidal, hippocampal 에서 흔함.

(d) **Refractory period 의 효과**: 짧은 ISI 가 차단되어 *short-interval 변동* 감소 → 분산 < 평균 → $F < 1$. 직관: refractory 가 *spike 정렬* 을 부분적으로 강제하여 (\"규칙적\") Poisson 의 *완전 random* 보다 변동이 작다. **함의**: $F$ 측정만으로 spike 통계 — Poisson, regular, bursty — 가능한 분류기.''',
        'rubric_md': '''총 12점.
- (a) 3점: Poisson 분포 정확 (1점) + 평균 = rT (1점) + 분산 = rT (1점).
- (b) 4점: Fano factor 정의 (1점) + 평균/분산 대입 (1점) + 1 결론 (1점) + 증명 (Var = E[n²] − E[n]²) (1점).
- (c) 3점: F < 1 의 의미 + 예 (1점) + F > 1 의 의미 + 예 (1점) + 두 케이스 비교 (1점).
- (d) 2점: refractory 가 short ISI 차단 (1점) + Fano < 1 결론 (1점).''',
        'slide_ref': '[Slide L8 §2]',
    },
    {
        'position': 2, 'kind': 'derivation', 'difficulty': 4, 'max_points': 12, 'expected_time_min': 20,
        'topic_tag': 'phase-as-circular',
        'prompt_md': '''*Phase code* 의 통계 분석은 *원형 통계* (circular statistics) 가 필수임을 보이라:
(a) (3점) Phase $\\phi \\in [0, 2\\pi)$ 가 *원* 위의 점이라는 것이 무엇을 의미하는가? 단순 빼기로 *위상 차이* 를 계산할 때 어떤 문제 발생?
(b) (4점) *Circular mean* (mean direction) 의 정의: $\\bar\\phi = \\arg(\\sum e^{i\\phi_k})$. 위상 0.1, 6.2 (라디안) 의 *circular mean* 을 *산술* 평균 vs *circular* 평균으로 비교.
(c) (3점) **Mean resultant length** $\\bar R = |\\sum e^{i\\phi_k}|/N \\in [0, 1]$ 의 의미. $\\bar R \\to 1$ 과 $\\bar R \\to 0$ 의 차이.
(d) (2점) Mainen-Sejnowski 의 *frozen noise reliability* 측정에 circular mean 을 어떻게 적용할 수 있는가?''',
        'model_answer_md': '''(a) **원 위의 점**: $\\phi = 0$ 과 $\\phi = 2\\pi$ 가 *동일* 한 점 — 원이 닫혀 있다. 단순 빼기 문제: $\\phi_1 = 0.1$, $\\phi_2 = 6.2$ → 차이 $|0.1 - 6.2| = 6.1$ 라디안 ≈ 350°. 그러나 *원형 거리* 는 $2\\pi - 6.1 = 0.18$ 라디안 ≈ 10° — *훨씬 가까움*. 산술 빼기는 *원의 닫힘* 을 무시.

(b) **Circular mean**: $\\bar\\phi = \\arg(\\sum e^{i\\phi_k})$. 두 위상 0.1, 6.2:
- *산술 평균*: $(0.1 + 6.2)/2 = 3.15$ — 거의 정반대 ($\\pi$).
- *Circular*: $e^{i \\cdot 0.1} + e^{i \\cdot 6.2} = (\\cos 0.1 + \\cos 6.2) + i(\\sin 0.1 + \\sin 6.2) \\approx (0.995 + 0.997) + i(0.0998 - 0.0832) \\approx 1.992 + 0.017 i$. $\\arg \\approx 0.0085$ 라디안 — 거의 0 (원래 두 점의 *원형* 평균 위치).

차이가 *질적* 으로 다름 — 산술은 잘못된 답.

(c) **Mean resultant length** $\\bar R$:
- $\\bar R \\to 1$: 모든 $\\phi_k$ 가 *같은 방향* → 강한 phase locking. e.g., 모든 spike 가 theta peak 에서 발화.
- $\\bar R \\to 0$: $\\phi_k$ 가 원 위에 *고르게 분포* → 위상 정보 없음 (random). e.g., spike timing 이 진동과 무관.
*Phase locking strength* 를 정량화하는 표준 측정. Rayleigh test 의 통계량.

(d) **Mainen-Sejnowski 적용**: Frozen noise 인가 시 trial 마다 spike timing 측정. 각 trial 의 spike 시각을 *자극 시간 구조* 의 위상으로 변환 → $\\phi_k$ collection. *Circular mean* 의 $\\bar R$ 가 1 에 가까우면 → spike 가 trial 마다 *정확히 같은 위상* 에 발화 → *temporal reliability* 입증. $\\bar R \\to 0$ 이면 random — 뉴런이 noisy. M-S 의 결과: frozen noise 에서 $\\bar R \\approx 0.95+$, DC 에서 $\\bar R \\to 0$. 이 *원형 통계* 가 paradox 를 *정량* 으로 해결.''',
        'rubric_md': '''총 12점.
- (a) 3점: 원 위의 점 의미 (1점) + 단순 빼기의 잘못 (1점) + 0.1 vs 6.2 거리 직관 (1점).
- (b) 4점: Circular mean 정의 (1점) + 산술 평균 계산 (1점) + circular 계산 (1점) + 두 결과의 차이 강조 (1점).
- (c) 3점: $\\bar R$ 정의 (1점) + R → 1 의미 (1점) + R → 0 의미 (1점).
- (d) 2점: M-S 측정에 적용 (1점) + R 값으로 reliability 정량 (1점).''',
        'slide_ref': '[Slide L8 §B; circular statistics 응용]',
    },
    {
        'position': 3, 'kind': 'essay', 'difficulty': 3, 'max_points': 10, 'expected_time_min': 15,
        'topic_tag': 'ttfs',
        'prompt_md': '''*TTFS* (time-to-first-spike) 가 rate code 의 *변형* 인가 *별개 부호* 인가 — 정보이론 관점에서 분석:
(a) (3점) TTFS 의 정의와 측정 방법.
(b) (3점) TTFS 가 *rate 와 monotonic* (1:1 매핑) 인 시나리오 — 정보 내용상 *동등* 함을 논증.
(c) (4점) TTFS 가 rate 와 *분리* 되는 시나리오 — 같은 rate 라도 다른 TTFS 가 다른 정보를 나르는 경우. 청각 sound localization 의 *interaural time difference* (ITD) 를 예시로.''',
        'model_answer_md': '''(a) **TTFS**: 자극 onset 후 첫 spike 까지의 *잠복기* (latency). 측정: 자극 시작 = 0, 첫 spike 시각 = $t_1$. Trial 평균 또는 single-trial decoding 으로 분석. 시간 단위 ms ~ tens of ms.

(b) **Rate 와 monotonic (1:1) 시나리오**: LIF 같은 *integrator* 에서 자극 강도 ↑ → $V_\\infty$ ↑ → 임계 도달 시간 ↓ → TTFS ↓. 동시에 ISI 도 ↓ → rate ↑. 즉 TTFS 와 rate 가 자극 강도의 *반비례* monotonic 함수. 정보 이론적으로 *어느 쪽을 측정하든 같은 정보* — 단조 변환은 정보 손실 없음 (decoder 만 다름). 이 시나리오에서 TTFS = "rate 의 빠른 추정" — long observation 없이 single spike 로 자극 강도 *추정* 가능 (실시간 decoding 장점).

(c) **Rate 와 분리되는 시나리오 — Sound localization**:
청각 시스템 (특히 medial superior olive, MSO) 에서 *양 귀* 의 sound 도착 시간 차이 (ITD, ~10-700 μs) 가 sound 위치 정보. MSO 뉴런이 양 귀의 첫 spike timing 차이를 coincidence detector 로 처리. 여기서:
- *Rate*: 양 귀의 신호 강도 (loudness)
- *TTFS*: 양 귀의 sound 도달 *시각 차이*

같은 rate 라도 ITD = 0 (정면) vs ITD = 500 μs (옆) 가 *다른 위치* 정보를 나름. 즉 TTFS 가 rate 와 *독립* 정보 차원. 이 case 에서 TTFS 는 *rate 의 변형이 아닌 별개 부호*.

**일반화**: TTFS 가 *rate 변형* 인지 *별개 부호* 인지는 *시스템에 따라 다름*. Integrator (rate-tuning V1) 에선 monotonic redundancy, Coincidence detector (MSO, hippocampal CA1 phase precession) 에선 별개 정보 차원. 이는 multiplexed code 의 *맥락 의존성* 을 보여주는 사례.''',
        'rubric_md': '''총 10점.
- (a) 3점: TTFS 정의 (1점) + 측정 방법 (1점) + 시간 단위 (1점).
- (b) 3점: integrator 에서 monotonic (1점) + 정보 이론 동등 (1점) + 빠른 decoding 장점 (1점).
- (c) 4점: ITD + MSO 예시 (2점) + 같은 rate 다른 TTFS = 다른 정보 (1점) + 별개 부호 결론 (1점).''',
        'slide_ref': '[Slide L8 §11]',
    },
    {
        'position': 4, 'kind': 'essay', 'difficulty': 4, 'max_points': 12, 'expected_time_min': 20,
        'topic_tag': 'multiplexed-implications',
        'prompt_md': '''Multiplexed code 의 *함의* — 뇌의 정보 처리 원칙 관점:
(a) (3점) 한 spike 가 *동시* 에 4 채널 (rate/temporal/phase/synchrony) 의 정보를 나를 수 있다는 것의 *진화적 효율성* — 채널당 별도 spike 보다 *bandwidth* 가 어떻게 늘어나는가.
(b) (4점) Downstream 뉴런 (e.g., CA1 → PFC) 이 *어떤 채널을 읽는지* 어떻게 결정되는가? Coincidence detection vs rate integration vs phase locking 의 *분자/회로* 메커니즘.
(c) (5점) 인공 신경망 (RNN, transformer) 이 multiplexed code 를 *재현하는가*? 차이점과 함의. (특히 spike-based encoding 의 부재)''',
        'model_answer_md': '''(a) **진화적 효율성 — bandwidth 증가**: 단일 spike 의 정보 용량 = $\\log_2(\\text{distinguishable states})$. 만약 4 채널이 *독립* 으로 정보를 나르면 (rate × temporal × phase × synchrony 각 N states), 총 정보 = $\\sum \\log_2 N_i$ — *덧셈* 이 아닌 *곱셈* 으로 늘어난다 (각 차원이 독립일 때). e.g., rate 16 levels + phase 16 levels = 단일 spike 에 4 + 4 = 8 bits. 별도 spike 였다면 16 × 16 = 256 spike 가 필요 — *32 배* 효율. 진화는 *제한된 spike count* (energy 제약) 하에서 *정보 용량 최대화* — multiplex 가 자연스러운 해.

(b) **Downstream selectivity**:
- **Rate integration**: 큰 시간상수 ($\\tau_m \\sim$ 수십 ms), 다수 입력 합산. *Slow* dendrite 시상수 + *high* synaptic density. 운동피질, posterior parietal 의 적분 회로.
- **Coincidence detection**: 짧은 시간상수, 적은 시냅스, *AND-gate* 동역학. NMDA-매개 *coincidence* (양쪽 입력 동시 → 큰 plateau). MSO (auditory) 의 sub-ms 정확도 binding 검출.
- **Phase locking**: GABAergic 회로의 *fast inhibition* 으로 진동 reset, *narrow integration window* 형성. Theta-locked CA1, gamma-locked PV+ basket cells.
회로 수준에서 *시간상수 + inhibition pattern + dendrite 비선형성* 의 결합이 어느 채널을 읽을지 결정. 같은 정보가 *여러 다른 회로* 에 의해 *다른 채널로 추출* 됨 — broadcasting + selective listening 모델.

(c) **인공 신경망 재현?**:
- **RNN**: Continuous activations, *no spikes*. Rate code 만 가능 — temporal precision (sub-ms), phase coding 부재. 시간상수가 *학습된 매개변수* 이지만 *spike timing* 차원이 없음.
- **Transformer**: 자기회귀 token 단위, 시간 = position embedding. *Phase precession* 같은 *동시 다중 정보* 표현 어려움 — 단일 채널 (token activation) 에 모든 정보 압축.
- **Spiking NN (SNN)**: rate + temporal + (이론상) phase 가능. 그러나 학습 알고리즘 미숙 (STDP 가 backprop 만큼 강력하지 않음).

**함의**: 현재 LLM 의 *능력 vs 효율* 차이의 일부는 *single-channel* (rate-equivalent, dense activations) vs *multi-channel* (sparse, multiplexed spikes) 의 표현 패러다임 차이. SNN + multiplex 가 미래의 *neuromorphic* AI 의 핵심 — 인간 뇌가 20 W 로 GPT 급 추론을 하는 비밀의 일부. **결론**: multiplexed code 는 단순한 "흥미로운 사실" 이 아닌 *효율적 정보 처리의 정수* — 인공 시스템이 못 따라잡은 진화적 통찰.''',
        'rubric_md': '''총 12점.
- (a) 3점: 채널당 정보 용량 (1점) + 곱셈 vs 덧셈 표현 (1점) + 효율성 결론 (energy-bandwidth) (1점).
- (b) 4점: rate integration 회로 (1점) + coincidence detection 회로 (1점) + phase locking 회로 (1점) + broadcasting + selective listening 통합 (1점).
- (c) 5점: RNN 의 spike 부재 (1점) + transformer 의 single-channel 한계 (1점) + SNN 의 잠재력 (1점) + multiplex = 효율 비밀 (1점) + neuromorphic AI 함의 (1점).''',
        'slide_ref': '[Slide L8 §B, §D]',
    },
]


def main():
    conn = psycopg2.connect(DB_DSN)
    try:
        insert_quiz_items(conn, 'L8', L8_QUIZ)
        insert_take_home(conn, 'L8', L8_TAKE_HOME)
        print(f'L8: {len(L8_QUIZ)} quiz items + {len(L8_TAKE_HOME)} take-home items')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
