#!/usr/bin/env python3
"""
seed_exemplar_L5_L7_L8.py — Opus 4.7 hand-authored exemplar summaries for L5 / L7 / L8.

Graduate-seminar handouts intended for 24-hour mastery from the handout alone.
Slide-only citations ([Slide L5/L7/L8 p.X]); no Dayan & Abbott, no Fundamental
Neuroscience. Original papers cited only when explicitly named in slides.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "backend"))
from db_pool import acquire, release  # noqa: E402


L5_SUMMARY = r"""
# L5 — Action Potential & Hodgkin-Huxley Theory  (graduate-seminar handout)

> *24-hour-mastery target: 학생은 (i) HH 4-ODE 시스템을 KCL + ohmic ionic current + voltage-gated conductance 의 조합으로부터 백지에서 유도하고, (ii) $g_K = \bar g_K\,n^4$ 와 $g_{Na} = \bar g_{Na}\,m^3 h$ 의 4-subunit / activation × inactivation 조합론적 기원을 1분 안에 설명하고, (iii) 양성 피드백(Na) 대 음성 피드백(K-delayed) 의 시간 척도 분리가 \"all-or-none\" 스파이크를 어떻게 만드는지 그림 없이 말로 설명할 수 있어야 한다.*

## 1. 핵심 개념과 적용 한계

### 1.1 HH 모델의 위상 [Slide L5 p.2, p.6]
1952년 Hodgkin & Huxley 논문 (J. Physiol. 117, 500–544) 은 *오징어 거대축삭(squid giant axon)* 에서 voltage-clamp 데이터를 정량 모델로 압축한 첫 시도이며, **(i) 컴퓨터 기반 정량 신경과학 도입, (ii) 실험 예측 가능, (iii) 분자 메커니즘과 시스템 동역학을 연결** 한 점에서 모델링 표준이 됐다 [Slide L5 p.6].

**적용 한계**: (a) single-compartment — 공간 변화는 L6 cable theory 영역; (b) 결정론적 — 채널 stochasticity 는 평균으로 흡수 ($N \gg 1$); (c) squid 데이터(18.5°C) fit; 포유류는 rate function 재추정 필요; (d) Na, K-delayed + leak 만 — A-type, M-type, Ca-dependent 는 별도 추가.

### 1.2 단일 뉴런 막의 등가 회로 [Slide L5 p.13, p.29]
Single-compartment HH = capacitor $C_m$ + 3 평행 ionic 가지 (Na transient, K delayed-rectifier, leak) + 외부 전류 $I_e(t)$. 각 ionic 가지: $g_X(V,t)\cdot(V-E_X)$.

### 1.3 두 시간 척도 분리가 spike 를 만든다 [Slide L5 p.7, p.8, p.31]
- **빠른 양성 피드백**: depolarization → $m$ ↑ ($\tau_m \sim 0.1$ ms) → $g_{Na}$ ↑ → Na influx → 더 큰 depolarization. 자기증폭이 threshold 를 넘으면 *all-or-none* spike 의 상승상.
- **느린 음성 피드백**: 같은 depolarization 이 (a) $h$ ↓ ($\tau_h \sim 1$ ms) — Na 차단, (b) $n$ ↑ ($\tau_n \sim$ 수 ms) — K efflux → repolarization, undershoot.

핵심은 $\tau_m \ll \tau_h, \tau_n$ 의 시간 척도 분리: Na 가 \"먼저 먹고\" K/inactivation 이 \"나중에 청소\" 한다.

## 2. 핵심 유도 — HH 4-ODE 시스템 백지 재현 [Slide L5 p.4, p.18–p.29]

### 2.1 KCL 부터 시작
막을 가로지르는 모든 전류의 합 = 외부 주입:
$$C_m \frac{dV}{dt} = -(I_{Na} + I_K + I_L) + I_e(t).$$
부호 규약: 양이온 *유출* 이 양의 막전류 (slide L3 p.32).

### 2.2 Ohmic ion currents [Slide L5 p.29, eq. on p.4]
각 ion current 는 conductance × driving force:
$$I_X = g_X(V,t)\,(V - E_X), \quad X \in \{Na, K, L\}.$$
Leak 은 $g_L = \bar g_L$ (상수); 나머지는 voltage / time 의존.

### 2.3 K delayed-rectifier — 4-subunit Markov chain → $g_K = \bar g_K\,n^4$ [Slide L5 p.17–p.19]
**Setup**: K 채널은 4개의 *동일하고 독립적인* subunit 으로 구성. 채널이 열리려면 *4개 모두* 활성화 conformation 이어야 함.

**Single-subunit kinetics** (state diagram, 2-state):
$$\text{closed}\;\underset{\beta_n(V)}{\overset{\alpha_n(V)}{\rightleftharpoons}}\;\text{open}.$$
$n(V,t)$ = 한 subunit 이 열린 상태일 확률. Master equation:
$$\frac{dn}{dt} = \alpha_n(V)(1-n) - \beta_n(V)\,n. \quad (*)$$

**Binomial 채널 개방 확률**: subunit 들이 독립이므로, 채널이 열려 있을 (= 4 subunit 모두 open) 확률 = $n^4$. 거시적 conductance:
$$\boxed{g_K(V,t) = \bar g_K\,n(V,t)^4.}$$

**(\*)의 표준형 변형** [Slide L5 p.22]: 양변을 $\alpha_n + \beta_n$ 으로 나눠
$$\tau_n(V)\,\frac{dn}{dt} = n_\infty(V) - n,\quad \tau_n = \frac{1}{\alpha_n + \beta_n},\;n_\infty = \frac{\alpha_n}{\alpha_n + \beta_n}.$$
Voltage clamp 에서 $V$ 고정 시 $n(t) = n_\infty - (n_\infty - n_0)e^{-t/\tau_n}$.

### 2.4 Na transient — activation × inactivation → $g_{Na} = \bar g_{Na}\,m^3 h$ [Slide L5 p.25–p.27]
Na 채널은 *두 게이트* 가 직렬:
- **Activation gate (m)**: 3개의 동일 subunit, depolarization 시 *열림* ($m_\infty(V)$ 증가).
- **Inactivation gate (h)**: 1개, depolarization 시 *닫힘* ($h_\infty(V)$ 감소). \"ball-and-chain\" 모델 — ball 이 채널 안쪽으로 들어가 막음.

두 게이트 독립 가정 → 채널이 conducting 일 확률 = (m 게이트 모두 열림) × (h 게이트 안 막힘) = $m^3 h$.
$$\boxed{g_{Na}(V,t) = \bar g_{Na}\,m^3 h.}$$

각 게이트 변수는 (\*) 형태의 1차 ODE 를 따른다:
$$\frac{dm}{dt} = \alpha_m(V)(1-m) - \beta_m(V)\,m, \quad \frac{dh}{dt} = \alpha_h(V)(1-h) - \beta_h(V)\,h.$$
$\alpha_m, \beta_m$ 는 $m$ 이 depolarization 에서 증가, $\alpha_h, \beta_h$ 는 $h$ 가 depolarization 에서 감소하도록 fit (slide L5 p.27, p.28 의 specific functional forms).

### 2.5 합쳐서 — HH 4-ODE 시스템 [Slide L5 p.4, p.29]
$$\boxed{\;
\begin{aligned}
C_m \frac{dV}{dt} &= -\bar g_L (V - E_L) - \bar g_K\,n^4 (V - E_K) - \bar g_{Na}\,m^3 h\,(V - E_{Na}) + I_e(t),\\
\frac{dn}{dt} &= \alpha_n(V)(1-n) - \beta_n(V)\,n,\\
\frac{dm}{dt} &= \alpha_m(V)(1-m) - \beta_m(V)\,m,\\
\frac{dh}{dt} &= \alpha_h(V)(1-h) - \beta_h(V)\,h.
\end{aligned}\;}$$
4-차원 nonlinear ODE. $n^4$, $m^3 h$ 의 비선형성과 $\alpha, \beta$ 의 voltage 의존성이 한꺼번에 만든다.

### 2.6 Voltage-clamp 로부터 $\alpha(V), \beta(V)$ 추출 [Slide L5 p.10, p.23, p.24]
**핵심 트릭**: $V$ 를 *고정* 하면 ODE (\*) 가 *선형 1차* → $n(t)=n_\infty-(n_\infty-n_0)e^{-t/\tau_n}$. Step clamp 응답을 이 함수로 fit 하면 각 $V$ 에서 ($n_\infty(V), \tau_n(V)$) 추출, 그리고
$$\alpha_n(V) = \frac{n_\infty(V)}{\tau_n(V)},\quad \beta_n(V) = \frac{1 - n_\infty(V)}{\tau_n(V)}.$$
$m, h$ 도 동일 — 단 Na 는 TEA/TTX 약리 차단 또는 early peak vs late decay 시간 분해 fit 으로 분리. **이것이 voltage clamp 가 \"channel kinetics 의 결정적 도구\" 인 이유**.

## 3. 직관적 매핑 (Expert Intuitive Mapping)

| HH 요소 | 등가 시스템 | 공유 수학 구조 | 어디서 깨지는가 |
|---|---|---|---|
| $g_K = \bar g_K\,n^4$ | 동전 4개를 던져 *모두* 앞면이 나올 확률 | 독립 베르누이의 곱 | 실제 K 채널 subunit 은 *완전 독립이 아닐 수도* — cooperative gating 시 $n^k$ exponent 가 정수가 아니거나 더 복잡 [Slide L5 p.19] |
| $g_{Na} = \bar g_{Na}\,m^3 h$ | \"3개의 자물쇠 + 1개의 마개\" 모두 풀려야 통과 | activation × inactivation 분리 | ball-and-chain 모델은 단순화 — 분자 구조상 inactivation 도 voltage sensor 와 부분 결합. 매우 짧은 spike 간 간격에서 어긋남 |
| 양성 피드백 (Na) | 화재 — 불씨가 더 큰 불 만들고 다시 더 큰 불씨 | autocatalytic loop | Na 가 *고갈* 되거나 reversal $E_{Na}$ 에 도달하면 자동 종료 — 진짜 화재와 달리 self-quenching |
| 음성 피드백 (K delayed, h ↓) | 소화전 — 불난 후 *지연 후* 살수 | low-pass filtered antagonist | K rate 가 너무 빨라지면 (e.g. fast K mutation) spike 자체가 shunting 으로 못 일어나 — *임계 비율* 의존 |
| Threshold | 산등성이(saddle) | bistability 의 unstable manifold | HH 는 *진짜 threshold 가 없음* — 매끄럽지만 양성 피드백이 가팔라 \"보이는\" 임계값처럼 작동 |
| All-or-none | 핵폭발 임계 질량 | bifurcation (sub-Hopf) | 잡음/slow 변수가 진폭 변조 — 진짜 \"불변\" 진폭은 없음 |

## 4. 식별성 & 추정 이슈

| 양 | 측정 방법 | 식별 가능 조건 | 흔한 실패 |
|---|---|---|---|
| $\bar g_K, \bar g_{Na}, \bar g_L$ | voltage-clamp 의 정상상태 I-V (ion 별 약리학적 분리) | TEA / TTX 가 *완전한* 차단 | 부분 차단 시 leak 에 잔류 ion current 흡수 — $g_L$ 과혼동 |
| $E_X$ | reversal potential (zero current crossing) | 단일 ion dominant in clamp window | 다른 ion contamination → 겉보기 reversal 가 평균쪽으로 끌림 |
| $\alpha_X(V), \beta_X(V)$ | step clamp 의 시간 fit → $n_\infty, \tau$ → 대입 | 단일 1차 ODE 가정 | activation/inactivation 분리가 안 되면 effective $\tau$ 가 두 시간상수의 평균 |
| Na 의 $m$ 과 $h$ 분리 | TTX 부분 + 빠른 onset 외삽 | activation 이 inactivation 보다 충분히 빠를 것 | 온도 ↓ 시 $\tau_m, \tau_h$ 가 모두 늘어 분리도 떨어짐 |
| threshold | depolarizing ramp 의 spike 발화 시점 | slow ramp | 빠른 ramp 시 *동적* threshold (accommodation) |

## 5. 흔한 오해와 시험 함정

1. **\"$n^4$ 의 4 는 분자 4-subunit 의 정확한 반영\"** — HH 는 *fitting exponent 로서 도입*; 분자생물학의 4-fold 대칭 확인은 후행 [Slide L5 p.19].
2. **\"Na inactivated = closed\"** — 다르다. *closed* (m=0) 와 *inactivated* (h=0) 는 분자적으로 다른 상태. Inactivated 는 hyperpolarization 으로 *recover* 필요 — refractory period 의 분자 기원.
3. **\"Threshold 가 절대 상수\"** — 아니다. 직전 발화 / slow conductance / ramp 속도에 따라 동적.
4. **\"Spike amplitude 가 정보를 운반\"** — 거의 아니다. 진폭은 stereotyped, 정보는 *발화 시점/빈도* 에 (L8 의 코딩 논의로 직결).
5. **\"HH 모델은 stochastic 이다\"** — 슬라이드 p.14 가 명시: 채널 개별은 stochastic 이지만 HH 는 *결정론적 평균장*. Stochastic HH 는 별도 영역.
6. **\"Voltage clamp 가 spike 를 측정한다\"** — 반대다. 막전위를 *고정* 해 spike 를 *못 일어나게* 한 다음 ionic current 를 측정. Current clamp 가 자연 spike 측정.

## 6. 자기 점검 (백지 재현 가능?)

- [ ] HH 4-ODE 시스템을 KCL + ohmic + voltage-gated conductance 로부터 5분 안에 백지 유도할 수 있다.
- [ ] $g_K = \bar g_K\,n^4$ 를 \"4 independent subunit, 모두 open 해야 채널 conducts\" 로 1줄 정당화할 수 있다.
- [ ] $g_{Na} = \bar g_{Na}\,m^3 h$ 의 $m^3$ 와 $h$ 가 각각 무엇이고 voltage 의존이 *반대 방향* 임을 설명할 수 있다.
- [ ] 단일 게이트 ODE $dn/dt = \alpha(1-n) - \beta n$ 을 voltage-clamp step 응답 $n_\infty - (n_\infty-n_0)e^{-t/\tau}$ 로 풀 수 있다.
- [ ] $\alpha_n(V) = n_\infty/\tau_n,\ \beta_n(V) = (1-n_\infty)/\tau_n$ 의 변환을 즉시 적을 수 있다.
- [ ] 빠른 양성 피드백(Na activation) vs 느린 음성 피드백(Na inactivation + K delayed) 의 시간 척도 분리가 all-or-none spike 와 refractory period 를 어떻게 만드는지 30초 안에 설명할 수 있다.
- [ ] HH 시뮬레이션 (slide L5 p.30) 에서 \"m 가 1 로 점프, h 는 transient 0 으로 하락, n 은 늦게 상승\" 의 시간 순서를 그릴 수 있다.
- [ ] Inactivated state 가 closed state 와 *분자적으로 다른* 이유 + refractory period 와의 관계를 설명할 수 있다.
""".strip()


L7_SUMMARY = r"""
# L7 — Different Types of Computational Models of Single Neurons  (graduate-seminar handout)

> *24-hour-mastery target: 학생은 (i) sub-threshold HH 로부터 leaky integrate-and-fire(LIF) 식과 그 ISI 폐형 해를 백지에서 유도하고, (ii) Izhikevich 2-ODE 모델의 4 파라미터 (a/b/c/d) 가 어떤 dynamics 를 조절하는지 정확히 짚고, (iii) 주어진 연구 질문(이온채널 / 스파이크 타이밍 / 대규모 네트워크) 에 대해 HH / aLIF / Izhikevich / multi-compartment 중 어느 것을 골라야 하는지 명확히 정당화할 수 있어야 한다.*

## 1. 핵심 개념과 적용 한계

### 1.1 왜 단순화가 필요한가 [Slide L7 p.7, p.8]
HH 모델은 정량적이지만 (i) 4-ODE × 다채널 × multi-compartment 시 *계산 불가능* 수준으로 비싸고, (ii) spike 의 *세부 모양* 은 정보 운반에 거의 무관 — \"spike 발생 사실 + 시점\" 만 다음 뉴런에 전달됨 (synapse 가 본질적으로 event-triggered). 따라서 **(a) 대규모 네트워크 시뮬레이션 가능, (b) spike timing 의 본질만 추출** 하는 reduced model 들이 필요하다.

### 1.2 모델 클래스의 위계 [Slide L7 p.5]
1. **HH (full)** — ion channel 분자 메커니즘, 진짜 conductance.
2. **Multi-compartment HH** — HH + cable. DA 뉴런 (Komendantov 2004), AD 피라미드(Morse/Migliore 2010).
3. **Izhikevich (2-ODE)** — phenomenological, 분기 분류로 다양한 firing pattern 재현.
4. **Adaptive LIF (aLIF)** — LIF + $g_{sra}$. Spike-rate adaptation 추가.
5. **LIF (passive)** — 가장 단순, 막 적분 + threshold reset.

### 1.3 \"Spike 모양은 단순화 안전 영역\" [Slide L7 p.8]
이유: spike 는 stereotyped (HH 의 nonlinearity 가 magnitude 를 거의 일정하게 함) → 정보가 \"있다 / 없다 + 시점\" 에 압축됨. 단점: spike 의 *width / 후극화 깊이* 가 시냅스 vesicle 방출 / Ca 진입에 영향을 주기 때문에, 시냅스 가소성 / Ca 동역학을 다룰 때엔 부적절.

### 1.4 적용 한계 — 모델 별 [Slide L7 p.45]
- **LIF**: 이온채널 / 스파이크 모양 / 적응 / burst 못 함.
- **aLIF**: 위 + 적응 추가; burst, sub-threshold oscillation 못 함.
- **Izhikevich**: 다양한 패턴 재현 가능하지만 *생물물리 의미 약함*; 약리 실험과 매핑 불가.
- **HH (single)**: 공간 변화 없음 — backpropagating AP, dendritic spike 못 함 (L6 영역).
- **Multi-compartment HH**: 가장 정확하지만 *식별성 문제* 큼 (수십~수백 파라미터).

## 2. 핵심 유도 — Sub-threshold HH → LIF, 그리고 ISI 폐형 해

### 2.1 LIF 식의 유도 [Slide L7 p.10–p.14]
HH membrane equation:
$$C\frac{dV}{dt} = -g_L(V-E_L) - \bar g_K\,n^4(V-E_K) - \bar g_{Na}\,m^3 h\,(V-E_{Na}) + I_{ext}.$$
**Sub-threshold 가정**: $V$ 가 firing threshold 아래일 때 $m \approx 0$ (Na deactivated), $n \approx n_\infty(V_{rest})$ ≈ 작음 → active 항 ≈ 0:
$$C\frac{dV}{dt} = -g_L(V-E_L) + I_{ext}.$$
양변에 specific membrane resistance $R_m = 1/g_L$ 곱하고 $\tau_m = R_m C$:
$$\boxed{\tau_m \frac{dV}{dt} = -(V - E_L) + R_m\,I_{ext}.}$$
**Threshold + reset 규칙** [Slide L7 p.9]: $V(t) \geq V_{th}$ 인 순간 spike 기록 → $V \leftarrow V_{reset} (< V_{th})$. Reset 이 spike 의 \"falling phase\" 를 phenomenologically 흡수 — Lapicque 1907 의 원본 형태.

### 2.2 Constant input 의 폐형 해 [Slide L7 p.15]
$I_e$ 상수, 초기조건 $V(0) = V_0$ 분리변수 → 1차 선형 ODE:
$$V(t) = E_L + R_m I_e + (V_0 - E_L - R_m I_e)\,e^{-t/\tau_m}.$$
$V_\infty \equiv E_L + R_m I_e$ 가 점근 평형.

### 2.3 ISI 폐형 해 (interspike interval) [Slide L7 p.16]
Reset 직후 ($V(0) = V_{reset}$) 에서 시작해 $V(t_{isi}) = V_{th}$ 인 시점:
$$V_{th} = E_L + R_m I_e + (V_{reset} - E_L - R_m I_e) e^{-t_{isi}/\tau_m}.$$
정리:
$$\boxed{t_{isi} = \tau_m \ln\left(\frac{R_m I_e + E_L - V_{reset}}{R_m I_e + E_L - V_{th}}\right).}$$
**조건**: $R_m I_e > V_{th} - E_L$ — 이걸 못 넘기면 $V_\infty < V_{th}$ → 영원히 발화 안 함 ($t_{isi} = \infty$, firing rate 0).
**Firing rate**: $r_{isi} = 1/t_{isi}$. 그래서 \"current → rate\" curve 가 입력 임계 위에서 시작해 로그 형태로 saturate.

### 2.4 aLIF 에 spike-rate adaptation 추가 [Slide L7 p.23]
스파이크 후 점진적 발화 빈도 감소 (적응) 를 K-like conductance $g_{sra}$ 로 모델:
$$\tau_m \frac{dV}{dt} = -(V-E_L) - r_m g_{sra}(V - E_K) + R_m I_e,$$
$$\tau_{sra}\frac{dg_{sra}}{dt} = -g_{sra}, \quad \text{매 spike 시}\ g_{sra} \mathrel{+}= \Delta g_{sra}.$$
직관: 매 spike 마다 K-conductance 가 calibrated step 만큼 늘어 hyperpolarize (Ca-activated K / Kv7 와 일치) → 다음 spike 까지 시간이 길어짐 [Slide L7 p.21, p.24]. 적응의 기능적 의미: contrast adaptation, forward masking, selective attention [Slide L7 p.19–p.22].

### 2.5 Izhikevich 2-ODE 모델 [Slide L7 p.25–p.27]
$$\frac{dv}{dt} = 0.04 v^2 + 5v + 140 - u + I,\quad \frac{du}{dt} = a(b v - u),$$
$$\text{if } v \geq 30\,\text{mV}: v \leftarrow c,\ u \leftarrow u + d.$$
- $a$: recovery 변수의 시간 척도. 작을수록 $u$ 느려져 burst / slow recovery.
- $b$: $v$-$u$ coupling 민감도 — sub-threshold oscillation / resonator 결정.
- $c$: spike 후 $v$ reset 값. 더 depolarized 면 burst 경향.
- $d$: spike 후 $u$ jump — fatigue 강도. 클수록 적응 강.

**철학**: 분기 이론(bifurcation theory) 으로 다양한 firing pattern (regular spiking, fast spiking, intrinsic bursting, chattering, low-threshold spiking, …) 을 (a,b,c,d) 4-D 격자에서 재현. HH 보다 ~$10^2$ 빠름.

## 3. 직관적 매핑 (Expert Intuitive Mapping)

| 모델 | 비유 / 등가 시스템 | 공유 수학 | 어디서 깨지는가 |
|---|---|---|---|
| LIF | RC 회로 + 스파크 갭(spark gap) — 콘덴서 충전, 임계 도달 시 방전 후 리셋 | 1차 선형 ODE + threshold map | 스파크 갭은 진짜 \"순간\" 방전; LIF 도 spike 모양 0폭 이상화 — burst, after-hyperpolarization 미반영 |
| aLIF | 위 + 매 방전마다 \"피로해지는 도화선\" — 다음 방전이 점점 늦어짐 | 추가 slow K state 변수 | 적응의 분자 기원 (Kv7, SK, M-current) 무시 — pharmacology 실험과 직접 매핑 불가 |
| Izhikevich | 4-knob 신디사이저 — (a,b,c,d) 로 \"음색\" (firing pattern) 만 재현 | 2-D quadratic + reset; 분기 분류 기반 | 4 파라미터가 *실측 가능한 생리량과 무관* — Komendantov 같은 channel-knockout 실험 못 답함 |
| Multi-compartment HH | 미니어처 송전망 — 각 compartment 가 변전소, 사이가 transmission line (cable) | HH × 다수 + cable PDE | 수십~수백 fitting 파라미터 → 식별성 / overfitting 문제; 시뮬 비용 큼 |
| HH (single) | 단일 변전소 모델 — 매우 정확하지만 \"공간\" 없음 | 4-ODE | 축삭/수상돌기 지연·감쇠 못 함 (L6 영역) |

## 4. 식별성 & 추정 이슈

| 양 | 측정 방법 | 식별 가능 조건 | 흔한 실패 |
|---|---|---|---|
| LIF: $\tau_m, R_m, E_L$ | sub-threshold step current 의 V(t) fit | active conductance 비활성 | spike 근방까지 fit 시 active current 가 $\tau$ 추정값 왜곡 |
| LIF: $V_{th}, V_{reset}$ | spike 직전 / 직후 V 측정 | 단일 threshold 가정 | dynamic threshold (입력 history 의존) → fixed value fit 시 ISI variance 과소추정 |
| aLIF: $\tau_{sra}, \Delta g_{sra}$ | constant step 동안의 ISI 시퀀스 fit | 단일 적응 timescale 가정 | 다중 timescale (Ca, M-current 동시) 시 effective $\tau$ 만 추출 |
| Izhikevich: $a,b,c,d$ | 다양한 input 의 firing pattern 일치 fit | 비교적 강한 phenotype 차이 | 파라미터 *식별성 자체가 없음* — 동일 firing pattern 을 만드는 (a,b,c,d) 무한 — 약리 실험과 매핑 불가 |
| Multi-compartment HH | 다채널 dye/voltage imaging + 부위별 channel block | 부위별 channel density 데이터 가용 | 식별성 폭발 (수십 파라미터). Komendantov 2004 도 \"plausible\" set 만 제시 |

## 5. 흔한 오해와 시험 함정

1. **\"LIF 가 sub-threshold HH 와 정확히 같다\"** — 아니다. Active conductance 를 무시한 *근사*. Threshold 근처에서는 Na/K가 살짝 활성화 → effective $\tau$ 변화. \"slow\" 영역에서만 정확.
2. **\"LIF 에 적응이 자연 포함\"** — 아니다. Passive LIF 는 constant current 에 *constant ISI* (스파이크-레이트 적응 없음). aLIF 가 추가로 필요.
3. **\"Izhikevich 가 HH 의 단순화\"** — 의미가 다르다. Izhikevich 는 *분기 분류 기반의 phenomenological reduction*. 분자 / 약리 실험과는 매핑되지 않음.
4. **\"a,b,c,d 가 측정 가능한 생리량\"** — 아니다. 4 파라미터는 fitting knob; 같은 firing 패턴을 만드는 (a,b,c,d) 가 무한.
5. **\"Multi-compartment HH 가 항상 더 정확\"** — 데이터가 충분할 때만. 식별성이 무너지면 *덜 정확한 fit 의 환상* 이 생김.
6. **\"Spike 모양은 단순화해도 안전\"** — 일반적으로는 그렇지만, 시냅스 vesicle 방출 / Ca 동역학을 다룰 땐 spike width 가 결정적 → reduced model 부적절.
7. **\"ISI 식의 $r_{isi} = 0$ 조건은 단순히 $I_e=0$\"** — 아니다. $R_m I_e \leq V_{th} - E_L$ 이 임계. 양의 입력이라도 임계 이하면 발화 못 함.
8. **\"Izhikevich 가 HH 보다 단순한 만큼 덜 강력\"** — 다양성 측면에선 더 풍부하다 — 동일 (a,b,c,d) 격자에서 burst / chattering / RS / FS 모두 분기 이동만으로 가능.

## 6. 자기 점검 (백지 재현 가능?)

- [ ] HH membrane equation 으로부터 sub-threshold 가정으로 LIF 식을 5분 안에 유도할 수 있다.
- [ ] LIF 의 ISI 폐형 해 $t_{isi} = \tau_m \ln\bigl((R_m I_e + E_L - V_{reset})/(R_m I_e + E_L - V_{th})\bigr)$ 와 발화 조건 $R_m I_e > V_{th} - E_L$ 을 즉시 적을 수 있다.
- [ ] Spike-rate adaptation 의 aLIF 형태 $\tau_{sra}\,dg_{sra}/dt = -g_{sra}$ + spike-triggered 점프 $\Delta g_{sra}$ 를 정당화할 수 있다.
- [ ] Izhikevich 의 2-ODE 형태 + reset 규칙 + (a, b, c, d) 의 의미를 1분 안에 설명할 수 있다.
- [ ] DA 뉴런 (Komendantov 2004, multi-compartment HH) vs 선조체 MSN (Humphries 2009, Izhikevich) 이 *왜 다른 모델 클래스* 를 골랐는지 정당화할 수 있다 (channel-level question vs. population firing-pattern question).
- [ ] 적응의 3 기능적 의미 — contrast adaptation, forward masking, selective attention — 을 1줄씩 답할 수 있다.
- [ ] 주어진 연구 질문에 모델 선택 결정 트리 적용: \"이온채널 약리실험 → HH / multi-compartment HH; spike timing 만 → LIF; firing pattern 다양성 + 큰 네트워크 → Izhikevich; 공간 dynamics → multi-compartment\".
- [ ] LIF 와 sub-threshold HH 가 *어디서 갈라지는지* (threshold 근처 active conductance 활성) 를 한 문장으로 설명할 수 있다.
""".strip()


L8_SUMMARY = r"""
# L8 — Neural Codes: Rate, Temporal, Phase, Synchrony, Multiplexed  (graduate-seminar handout)

> *24-hour-mastery target: 학생은 (i) 4 가지 코드 유형(rate / temporal / phase / synchrony) 의 정의·증거·한계를 즉시 답하고, (ii) firing rate 의 3 가지 정의(time / trial / population average) 를 구별하고 각각의 적용 가능 영역을 짚고, (iii) Mainen & Sejnowski 1995 의 \"reliability paradox\" 를 in vivo 변동성 vs 결정론적 모델의 모순으로 정확히 진술할 수 있어야 한다.*

## 1. 핵심 개념과 적용 한계

### 1.1 신경 코드란? [Slide L8 p.5–p.10]
\"외부 세계가 뇌에서 어떻게 표현되는가?\" — spike 생성의 biophysics 는 잘 알려져 있지만 *정보 표현* 은 미해결. 4 가지 질문 [Slide L8 p.7]: (1) 무엇이 인코딩, (2) 어떤 코드, (3) 신뢰성, (4) 후속 활용.

**근본 한계 [Slide L8 p.73]**: 같은 spike train 도 *다른 뉴런 / 시점* 에선 다른 의미. → **보편 신경 코드는 없다**.

### 1.2 4 코드 유형 — 한 줄 정의 [Slide L8 p.16, p.30]
- **Rate**: 단위 시간당 spike 수.
- **Temporal**: 개별 spike 의 *정확한 시점* 이 정보 (1 ms scale).
- **Phase**: 기준 진동에 대한 spike *위상* 이 정보.
- **Synchrony**: 여러 뉴런 간 spike 동기화가 정보.

상호배타적이 아니라 in vivo 에선 *동시 발생* — multiplexed code [Slide L8 p.61].

### 1.3 적용 한계
- Rate: 빠른 행동(< 400 ms) 에 시간 평균 불가 [Slide L8 p.27].
- Temporal: 밀리초 정밀도 / 잡음 분리 어려움.
- Phase: 신뢰할 진동 기준 (theta, gamma) 필요.
- Synchrony: 다중 뉴런 동시 기록 필요 — Neuropixels [Slide L8 p.57].

## 2. Rate code — 3 가지 정의의 분리 [Slide L8 p.20–p.25]

### 2.1 정의 1: 시간 평균 (spike count) [Slide L8 p.21]
$$\nu = \frac{n_{sp}(T)}{T},\quad T \in \{100, 500\} \text{ ms}.$$
**Adrian (1926)** stretch receptor: 근육 장력 ↑ → spike 수 ↑. Tuning curve 의 표준 단위 [Slide L8 p.19].
- **잘 작동**: 입력이 *상수 / 천천히 변할 때*.
- **깨지는가**: 빠른 입력 변동 (saccade) — $T$ 동안 입력 비정상.

### 2.2 정의 2: trial 평균 (spike density / PSTH) [Slide L8 p.23, p.24]
$$\rho(t) = \frac{1}{n_K\Delta t}\,\langle\,\text{spikes in } (t, t+\Delta t)\,\rangle_{\text{trials}}.$$
같은 stimulus 를 반복 → peri-stimulus-time histogram (PSTH).
- **장점**: 시간 의존 stimulus 에도 작동.
- **한계**: 단일 trial 디코딩 불가 — 개구리가 파리 잡을 때 \"500 trial 평균을 기다릴 수 없다\" [Slide L8 p.24].

### 2.3 정의 3: 인구 평균 (population rate) [Slide L8 p.25]
같은 입력 / 출력 통계를 가진 neuron population $m \to n$ 사이.
$$A_m(t) = \frac{1}{N_m}\sum_{i \in m} \text{spikes}_i(t).$$
- **장점**: 단일 trial 가능, 빠른 신호 디코딩.
- **가정**: population 이 \"identical and exchangeable\" — 사실상 mean-field 근사.

### 2.4 Rate code 의 어려움 [Slide L8 p.26–p.28]
- 인간이 시각 장면 *< 400 ms* 인지·반응 — V1→IT→motor stage 당 ~10–20 ms 만 허용 → 시간 평균 거의 불가능 [p.27].
- Saccade 등 입력 자체가 비정상 → 시간창 평균 모호 [p.28].

## 3. Temporal / Phase / Synchrony Code

### 3.1 Time-to-first-spike [Slide L8 p.32–p.34, Thorpe 1996]
- **가설**: 처리 단계마다 *첫 스파이크의 시점* 만 정보 운반. 후속 스파이크는 inhibition 으로 차단.
- **증거**: V1 simple cell 에서 first-spike timing 만으로 stimulus 정보 대부분 추출 [Slide L8 p.34, Thorpe 1996].
- **함의**: rate 는 spike 수 셀 시간 필요; first-spike 는 단일 spike 만으로 신호.

### 3.2 Phase code & phase precession [Slide L8 p.35–p.46]
- **메커니즘**: 어떤 population oscillation (theta, gamma) 이 *시간 기준* 으로 작동, 개별 뉴런 spike 의 *위상* 이 신호 운반 [Slide L8 p.35].
- **대표 사례 — 해마 place cell**: O'Keefe & Recce 1993. 동물이 place field 를 통과하는 동안 spike 가 *theta cycle 의 점점 이른 위상* 으로 이동 — **phase precession** [Slide L8 p.39, p.40].
- **공간 시퀀스 → preplay / replay**: 행동 중 sequential activation 이 휴식 / 수면 중 *압축 재생* 되며, *경험 이전* 의 preplay 도 보고됨 → 학습 가속화 가설 [Slide L8 p.41–p.46].

### 3.3 Synchrony code & binding problem [Slide L8 p.47–p.55]
- **현상**: 두 뉴런 spike 가 *시간적으로 동기화* — cross-correlogram peak [Slide L8 p.48–p.50].
- **Binding problem [Slide L8 p.51]**: \"빨간 사각형\" 의 \"빨강\" 과 \"사각형\" 이 같은 객체임을 어떤 메커니즘이 보장하나? *동기화* 가 한 후보 — 함께 발화 = 같은 객체.
- **회로 사례**: Prefrontal-Hippocampal pathway 동기화가 기억 처리에서 [Slide L8 p.52–p.54].

### 3.4 Multiplexed code [Slide L8 p.61, p.62, Panzeri 2015]
- 4 코드는 *상호배타적이 아니라 동시* 발생 — 같은 spike train 의 *다른 통계* 가 다른 정보 운반.
- **Barrel cortex 사례** [Slide L8 p.62]: whisker 자극 시 L4 는 firing rate 변조 (rate), L5/6 는 spike 시점 (temporal), L4–L5/6 는 동기화 (synchrony) — 세 코드 동시 운반.
- **Jang 2020 [Slide L8 p.66–p.69]**: iSR (동기화) × iFR (순간 firing rate) profile 로 layer-specific multiplexed pattern. L5/L6 가 모든 firing rate 범위에서 L4 와 동기.

## 4. 직관적 매핑 (Expert Intuitive Mapping)

| 코드 | 비유 | 공유 수학 / 통계 | 어디서 깨지는가 |
|---|---|---|---|
| Rate (time avg) | 라디오 AM (진폭 변조) — 진폭이 정보 | 시간창 평균 | 빠른 변동 (saccade, 400 ms 인지) — 시간창 잡을 수 없음 |
| Rate (trial avg, PSTH) | 사진 *여러 장 합친 long-exposure* | trial-axis 평균 | 단일 trial 에서 디코딩 불가 — 행동 동물에는 못 씀 |
| Rate (population) | 합창단 — 평균 데시벨 | population-axis 평균 | population 이 *동질* 가정. 다양한 뉴런 타입 시 깨짐 |
| Temporal (first-spike) | 100m 달리기 — *결승선 통과 순간* 만 기록 | spike time 정밀도 | 단일 spike 잡음에 취약 — Mainen & Sejnowski 1995 의 reliability 가 핵심 |
| Phase | 시계의 분침 위치 — 시간 자체가 아니라 *어느 시점인가* | reference oscillation phase | 진동 기준이 무너지면 (mid-task LFP 변화) phase 자체 의미 모호 |
| Synchrony | 군악대 — 같이 박자 맞춰 두드리면 \"한 팀\" 이라는 신호 | cross-correlation peak | 두 뉴런 모두 동시 측정 필요; 단일전극으론 불가능 |
| Multiplexed | 다중 채널 라디오 — 같은 송신에 AM/FM/위상 동시 | 위 통계의 *복합* | 하나의 통계만 측정하면 *다른 채널의 정보를 잃음* |

## 5. Mainen & Sejnowski 1995 — Reliability Paradox [Slide L8 p.74]

**Setup**: 같은 신경에 같은 *fluctuating* current 반복 주입 시 spike pattern 이 trial 간 매우 reliable (밀리초 일치). 반대로 *constant* current 는 spike timing variability 큼.
**Paradox**: 확률적 ion channel 을 가진 뉴런이 어떻게 reliable spike timing 을 만드나? 또 in vivo 시각 자극 응답은 trial-to-trial *high variability* — 정보는 어떻게 안정 전달되나?
**해석 [Slide L8 p.70–p.73]**: 정보 운반에는 *fluctuating, time-structured* 입력이 필요. Constant input 에선 spike timing 이 잡음만 반영. → temporal code 의 신뢰성은 *입력 통계* 가 결정.

## 6. 식별성 & 추정 이슈

| 양 | 측정 방법 | 식별 가능 조건 | 흔한 실패 |
|---|---|---|---|
| Spike rate (time) | spike count / window | 입력이 stationary on $T$ | 빠른 입력 변동 시 평균 의미 모호 |
| PSTH | trial 반복 + bin 평균 | trial 간 stimulus 일치 | 동물 internal state 변동 (각성도, attention) → trial 비등가 |
| Phase | reference LFP + Hilbert transform | 진동이 *지속적* | phase resetting / oscillation 부재 시 phase 의미 무너짐 |
| Phase precession | 단일 뉴런 spike + theta phase, place 의존 | place field 내부 통과 | non-stationary speed → phase-place 관계 왜곡 |
| Synchrony | 다전극 cross-correlogram, jitter test | 동시 측정 (Neuropixels 등) | 단일 전극으로는 *불가능*; firing rate 변화에 의한 chance coincidence 보정 필요 |
| Multiplexed | iSR × iFR (Jang 2020) 등 다지표 | 정확한 spike timing + LFP/oscillation | 한 지표만으로 fit 시 *다른 코드 채널 누락* |
| in vivo reliability | 동일 stimulus 의 trial-to-trial variability | stimulus 정의 일관 | 자연 시각 입력은 reproduce 어려움 — Mainen 의 *current injection* 트릭 필요 |

## 7. 흔한 오해와 시험 함정

1. **\"Rate code 는 단 하나의 정의\"** — 아니다. *시간 / 시행 / 인구* 평균 3 종 — 적용 영역 다름. 시험에서 \"rate code\" 만 쓰면 어느 평균인지 명시해야.
2. **\"Phase precession 이 단순히 위치 정보\"** — 아니다. *시간 압축 sequence* 도 운반 (replay 와 직결). place 정보 + sequence 정보 *둘 다*.
3. **\"Synchrony 가 binding 의 정답\"** — 아니다. *후보* 일 뿐. 직접 인과 증거는 약하고 논쟁 진행 중 [Slide L8 p.51].
4. **\"4 코드 중 하나만 선택해야 한다\"** — 아니다. 실제 in vivo 는 multiplexed [Slide L8 p.61, Panzeri 2015].
5. **\"Time-to-first-spike 가 rate code 와 정반대\"** — 아니다. *연속선*. 평균 firing rate 가 높으면 first-spike 도 일찍 [Slide L8 p.56]. 둘은 \"독립 정보\" 가 아니다.
6. **\"동물이 동일 자극에 동일 응답\"** — 아니다. trial-to-trial variability 가 본질 [Slide L8 p.70]. 잡음 원: stochastic ion channel, vesicle release, network background activity [Slide L8 p.71, p.72, Faisal 2008].
7. **\"PSTH 가 단일 trial 디코딩 도구\"** — 정의상 *불가능*. PSTH 는 ensemble 통계.
8. **\"Spike train 이 같으면 정보가 같다\"** — 아니다. **회로 / 맥락 의존**. 같은 train 이 다른 뉴런 / 다른 시점에 다른 의미 [Slide L8 p.73].

## 8. 자기 점검 (백지 재현 가능?)

- [ ] 4 코드 (rate / temporal / phase / synchrony) 의 정의와 각각의 대표 증거를 1분 안에 답할 수 있다.
- [ ] Rate code 의 3 정의 (time / trial / population avg) 를 구분하고, 각각이 *언제 적용 불가* 한지 짚을 수 있다.
- [ ] Time-to-first-spike 가 빠른 처리 시간(< 400 ms) 에 필요한 이유를 Thorpe 1996 의 핵심 발견과 함께 설명할 수 있다.
- [ ] Phase precession 이 무엇인지 (O'Keefe & Recce 1993 의 place cell 사례) + replay/preplay 와의 연결을 설명할 수 있다.
- [ ] Binding problem 이 무엇이며 synchrony 가 *후보 솔루션* 이라는 위치를 정확히 진술할 수 있다.
- [ ] Mainen & Sejnowski 1995 의 reliability paradox 를 \"fluctuating vs constant input\" 의 대비로 30초 안에 설명할 수 있다.
- [ ] Multiplexed code 의 barrel cortex 사례 (Crandall/Bieler/Jang) — L4 vs L5/6 의 rate / temporal / synchrony 분담 — 을 1분 안에 답할 수 있다.
- [ ] \"보편 신경 코드는 없다\" 의 의미 — 같은 spike train 이 *맥락 / 회로 위치* 에 따라 다른 정보 — 를 한 문장으로 설명할 수 있다.
- [ ] 잡음 원 3 가지 (channel stochasticity, vesicle release, network background) 를 즉시 답할 수 있다.
""".strip()


def upsert_summary(lecture, lecture_title, summary_md):
    conn = acquire()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO lecture_summaries (lecture, lecture_title, summary, sources, generated_at)
                VALUES (%s,%s,%s,%s::jsonb,now())
                ON CONFLICT (lecture) DO UPDATE
                SET summary = EXCLUDED.summary,
                    lecture_title = EXCLUDED.lecture_title,
                    sources = EXCLUDED.sources,
                    generated_at = now()
                """,
                (lecture, lecture_title, summary_md, json.dumps([])),
            )
        conn.commit()
    finally:
        release(conn)


if __name__ == "__main__":
    upsert_summary("L5", "Action Potential and Hodgkin-Huxley Theory", L5_SUMMARY)
    print(f"L5 exemplar summary cached ({len(L5_SUMMARY)} chars)")
    upsert_summary(
        "L7", "Different Types of Computational Models of Single Neurons", L7_SUMMARY
    )
    print(f"L7 exemplar summary cached ({len(L7_SUMMARY)} chars)")
    upsert_summary(
        "L8", "Neural Codes — Rate, Temporal, Phase, Synchrony, Multiplexed", L8_SUMMARY
    )
    print(f"L8 exemplar summary cached ({len(L8_SUMMARY)} chars)")
