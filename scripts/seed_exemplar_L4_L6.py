#!/usr/bin/env python3
"""
seed_exemplar_L4_L6.py — Opus 4.7 hand-authored exemplar summaries for L4 / L6.

Same shape as seed_exemplar_summaries.py. Slide-only citations.
Korean primary + English technical terms in parentheses on first use.
Graduate-seminar register.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "backend"))
from db_pool import acquire, release  # noqa: E402


L4_SUMMARY = r"""
# L4 — Neural Membrane Biophysics II: Ion Channels, Synaptic Transmission & Circuit Models (graduate-seminar handout)

> *24-hour-mastery target: 이 페이지를 마친 학생은 (i) 막 방정식(membrane equation) $\tau_m \dot V = -(V-V_{rest}) + R_m I_{inj}$ 을 KCL 한 줄에서 백지 유도하고, (ii) 4종 ion channel (leak / voltage-gated / pump / transmitter-gated) 의 전기적 등가소자가 무엇인지 즉답하며, (iii) conductance-based 시냅스 항 $g_{syn}(t)\bigl(V-E_{syn}\bigr)$ 이 *왜* current source 가 아니라 voltage-dependent current 인지 설명하고, (iv) alpha function $A\,t\,e^{-t/t_{peak}}$ 의 $t_{peak}$ 가 함수의 peak time 임을 미분으로 보일 수 있어야 한다.*

## 1. 핵심 개념과 적용 한계 (Core Concepts and Regime of Validity)

### 1.1 Single-compartment 가정 [Slide L4 p.2]
**가정**: 뉴런 전체가 하나의 등전위(equipotential) 점 — 공간 변수 $x$ 가 사라짐. 결과적으로 막전위(membrane potential) $V_m(t)$ 는 시간만의 함수.
**언제 깨지는가**: dendrite/axon 처럼 길이 $L \gtrsim \lambda$ (length constant) 인 구조. 그 영역은 L6 cable theory 가 떠맡는다.
**왜 여전히 쓰는가**: soma-near 사건 (spike threshold crossing, somatic recording) 의 일차 근사로 충분하며, 해석해(closed form) 가 존재.

### 1.2 KCL 기반 등가회로 [Slide L4 p.2–4]
**구성요소** (병렬 연결):
- 막 capacitor $C_m$ — bilayer 의 정전용량(capacitance).
- Leak resistor $R_m = 1/g_L$ — 항상 열린 leak channel 의 합산 전도도.
- 외부 전류원(current source) $I_{inj}(t)$.
**Kirchhoff 전류법칙(KCL)**: 한 마디(node) 에 들어오고 나가는 전류 합 = 0:
$$I_{cap} + I_{leak} = I_{inj}, \qquad I_{cap} = C_m \frac{dV_m}{dt}, \quad I_{leak} = \frac{V_m - V_{rest}}{R_m}.$$
**가정**: lumped element (회로 크기 $\ll$ 신호 파장). 100 kHz 미만 생물학적 시간 스케일에서 정확.

### 1.3 Ion channel 4분류 [Slide L4 p.6–14]
| 종류 | 게이팅 트리거 | 등가소자 | 대표 예 |
|---|---|---|---|
| Leakage | 없음 (항상 열림) | 고정 conductance $g_L$ | K2P, Na leak |
| Voltage-gated | $V_m$ | $g(V,t)$ — 비선형 시변 | Na$_V$, K$_V$, Ca$_V$ |
| Ion pump | ATP | 비-옴 전류원 | Na$^+$/K$^+$-ATPase (3 Na out, 2 K in) |
| Transmitter-gated | 리간드(ligand) 결합 | $g(t)\cdot$ binding kinetics | AMPA, NMDA, GABA$_A$ |

**Pump 의 비-옴 특성**: ATP 가수분해로 *농도 기울기에 거스르는* 방향으로 이온 이동 → $I$-$V$ 곡선이 원점을 지나지 않음. 이것이 `R_m` 회로에 들어가지 않고 *별도 전류원* 으로 모델링되는 이유.

**Voltage-gated 채널의 분자적 본질** [Slide L4 p.11–14]: Na$_V$ 는 단일 폴리펩타이드의 4 도메인(I–IV), 각 6개 transmembrane segment(S1–S6); S4 의 양전하 arginine 이 voltage sensor; MacKinnon (Jiang et al. Nature 2003) 의 charged paddle 모델이 voltage sensing 의 분자 기전을 확립. K$_V$ 는 동일한 4 subunit 의 homo-tetramer.

## 2. 핵심 유도 (Key Derivations)

### 2.1 막 방정식 [Slide L4 p.2–4]
1.2 의 KCL 식에 정의를 대입:
$$C_m \frac{dV_m}{dt} + \frac{V_m - V_{rest}}{R_m} = I_{inj}(t).$$
양변에 $R_m$ 을 곱하고 $\tau_m = R_m C_m$ 도입:
$$\boxed{\tau_m \frac{dV_m}{dt} = -\bigl(V_m - V_{rest}\bigr) + R_m I_{inj}(t)}\quad [\text{Slide L4 p.4}].$$
1차 선형 ODE — 적분인자(integrating factor) $e^{t/\tau_m}$ 으로 풀린다.

**Step 입력 해**: $I_{inj}(t)=I_0 \,\Theta(t)$, $V_m(0)=V_{rest}$ 일 때
$$V_m(t) = V_{rest} + R_m I_0\bigl(1 - e^{-t/\tau_m}\bigr).$$
점근값(asymptote) $V_\infty = V_{rest} + R_m I_0$, e-folding 시간 $\tau_m$.

### 2.2 Conductance-based 시냅스 [Slide L4 p.27–30]
시냅스 전류는 *current source 가 아니다* — driving force 에 비례하는 voltage-dependent 전류:
$$I_{syn}(t) = g_{syn}(t)\bigl(V_m(t) - E_{syn}\bigr).$$
$E_{syn}$ = 해당 채널의 reversal potential (AMPA $\approx 0$ mV, GABA$_A$ $\approx -70$ mV). $V_m$ 이 $E_{syn}$ 에 가까워질수록 *같은 conductance 가 더 작은 전류만* 만들어 낸다 — synaptic shunting 의 수학적 근원.

**Alpha function** [Slide L4 p.27]: $g_{syn}(t) = A\,t\,e^{-t/t_{peak}}$. $dg/dt=0$ 풀면 $t = t_{peak}$ 에서 최대 — $t_{peak}$ 라는 이름의 유래.
**Peak amplitude**: $g_{max} = A\,t_{peak}\,e^{-1}$. 즉 $A$ 와 $t_{peak}$ 만으로 진폭과 시간경과가 결정된다.
**전형값**: AMPA / GABA$_A$ 는 $t_{peak} \approx 0.5\text{–}2$ ms.

### 2.3 시냅스 회로 ODE [Slide L4 p.29–31]
Dendritic compartment 를 leak + transmitter-gated 두 conductance 의 병렬로 모델링:
$$C_m \frac{dV_m}{dt} = -g_L\bigl(V_m - V_{rest}\bigr) - g_{syn}(t)\bigl(V_m - E_{syn}\bigr).$$
$g_{syn}(t)$ 가 시변(time-varying) 이므로 막 방정식이 *시변 계수* ODE 로 바뀜 → 해석해 일반적으로 부재; 슬라이드의 MATLAB Euler scheme [Slide L4 p.31] 으로 수치 적분.

## 3. 직관적 매핑 (Expert Intuitive Mapping)

| L4 개념 | 비유 (analogy) | 공유하는 수학 구조 | 어디서 깨지는가 |
|---|---|---|---|
| Leak channel ($g_L$) | 항상 열린 누수 밸브 | 옴(Ohm) 의 법칙 $I = gV$ | 실제로는 single-channel stochastic; 거시 평균만 일치 |
| Voltage-gated channel | 압력 센서가 달린 자동 밸브 | 압력→밸브 개폐, $g=g(V,t)$ | 밸브는 단일 임계값; 채널은 sigmoidal + inactivation 까지 |
| Ion pump (Na/K-ATPase) | 펌프 + 발전기 | 외부 에너지 (ATP) 로 농도 기울기 유지 | 발전기는 일정 출력; pump 는 [Na]$_i$, ATP, $V_m$ 모두에 의존 |
| AMPA / GABA$_A$ (ionotropic) | 키→자물쇠 직접 연결 (1단계) | 빠른 게이팅, $\sim$0.5–2 ms | NMDA 는 voltage-gated 추가 (Mg$^{2+}$ block); 이중 조건 |
| GABA$_B$ / mGluR (metabotropic) | 키→릴레이 회로→자물쇠 (2단계, second messenger) | 느린 게이팅 ($10^2$ ms 스케일) | second messenger 는 cytoplasm 확산 → 공간적 spread; 점-회로 가정 깨짐 |
| $g_{syn}(V-E_{syn})$ | 콘덴서로 흐르는 *전류* 가 아니라 *밸브를 통한 압력차 흐름* | $I = g \Delta V$ | 압력 비유는 단방향; 시냅스는 driving force 부호에 따라 양/음 모두 |
| Alpha function $A\,t\,e^{-t/t_p}$ | 전등 끈 이후 형광등 잔광 | rise + 지수 decay 단일 시간상수 | 실제 채널은 다중 시간상수 (rise vs decay 분리) — biexponential 이 더 정확 |

## 4. 식별성 & 추정 이슈 (Identifiability & Estimation)

| 추정 대상 | 측정 방법 | 식별 조건 | 흔한 오류 |
|---|---|---|---|
| $g_L, V_{rest}$ | subthreshold V-I curve, current clamp | active conductance 비활성, 시냅스 입력 침묵 | 자발 EPSP 가 baseline 을 끌어올림 — sample mean 만 쓰면 bias |
| $\tau_m$ | step 응답의 e-folding time | 단일 1차 시스템 가정 | dendrite 가 multi-time-constant; 단일 fit 은 실효(weighted) 평균만 |
| $g_{syn}(t)$ kinetics | voltage clamp 에서 $V_m = E_{syn}$ 외 값 고정 후 $I_{syn}(t)$ 측정 | clamp 가 빠르고 공간적으로 균일 | dendritic synapse 는 space clamp 깨짐 → kinetics 가 *느려 보임* (filter artifact) |
| $E_{syn}$ | $I_{syn}=0$ 되는 reversal $V_m$ 검색 | 해당 채널만 활성, 다른 conductance 차단 | AMPA 측정 시 NMDA 동반 활성 — $E_{syn}$ 추정에 bias |
| Alpha 의 $A, t_{peak}$ | peak amplitude + peak time 직접 측정 | low-noise, 단일 시냅스 사건 | multi-vesicular release → $A$ 가 이산적으로 점프 (quantal) |
| NMDA $g(V)$ | Mg$^{2+}$ 농도 다른 조건의 I-V 곡선 fit | extracellular [Mg$^{2+}$] 정밀 제어 | low-Mg 조건 → block 사라져 V-dependence *없는 것처럼* 보임 |

## 5. 흔한 오해와 시험 함정 (Common Misconceptions)

1. **"시냅스 입력 = 일정한 외부 전류"** — 아니다. $I_{syn} = g_{syn}(V_m - E_{syn})$ 으로 $V_m$ 에 의존. 같은 $g_{syn}$ 도 $V_m$ 가 $E_{syn}$ 에 가까우면 거의 0 에 수렴 — *shunting inhibition* 의 핵심.
2. **"GABA = 항상 억제"** — 아니다. 발달기 뉴런이나 세포내 [Cl$^-$] 가 높은 상황에서 $E_{Cl} > V_{rest}$ 이면 GABA$_A$ 가 *탈분극* 을 일으킬 수 있음. 부호는 *driving force* 가 결정한다.
3. **"NMDA 가 voltage-gated"** — 정확히는 *coincidence detector*: 리간드 결합 *그리고* 충분한 탈분극 (Mg$^{2+}$ block 해제) 이 동시에 필요 [Slide L4 p.21]. 단일 트리거가 아닌 AND 게이트.
4. **"Pump 가 막전위를 직접 만든다"** — 부분적 사실. Pump 자체 전류는 small (3:2 비율로 약간의 hyperpolarizing 기여). $V_{rest}$ 의 본체는 *pump 가 만든 농도 기울기* + leak channel 의 ion selectivity (주로 $E_K$).
5. **"Alpha function 의 $t_{peak}$ = decay time"** — 아니다. $t_{peak}$ 는 *피크에 도달하는 시간*. Decay 의 e-folding 도 우연히 $t_{peak}$ 와 같지만, 이는 alpha 함수 형태의 결과지 정의가 아니다.
6. **"Ionotropic 이 metabotropic 보다 항상 강하다"** — 아니다. Ionotropic 은 *빠르고* metabotropic 은 *지속적*. Long-lasting modulation (e.g. attention gating) 은 metabotropic 이 더 효과적.
7. **"막 방정식에 시냅스를 더하면 여전히 1차 선형"** — 아니다. $g_{syn}(t)$ 가 시변이라 *비제차(non-homogeneous) 비자율(non-autonomous)* 1차 ODE — 일반적으로 폐형 해 없음. Numerical integration 필수 [Slide L4 p.31].

## 6. 자기 점검 (24h-Mastery Checklist)

- ☐ 막 방정식 $\tau_m \dot V = -(V-V_{rest}) + R_m I_{inj}$ 을 KCL 한 줄에서 백지 유도할 수 있다.
- ☐ Step current 응답 $V(t) = V_{rest} + R_m I_0(1 - e^{-t/\tau_m})$ 을 적분인자로 5분 안에 풀 수 있다.
- ☐ Ion channel 4종 (leak, voltage-gated, pump, transmitter-gated) 각각의 등가소자와 대표 예를 즉답한다.
- ☐ $I_{syn} = g_{syn}(V-E_{syn})$ 이 *왜* current source 가 아닌지 driving force 개념으로 설명할 수 있다.
- ☐ Alpha function $A\,t\,e^{-t/t_{peak}}$ 의 peak time 이 $t_{peak}$ 임을 미분으로 1줄 증명한다.
- ☐ Ionotropic / metabotropic 의 시간 스케일 차이 ($<$1 ms vs $10^2$ ms) 와 그 분자적 이유 (직접 vs 2차 messenger) 를 답한다.
- ☐ NMDA 가 *AND 게이트* (리간드 + 탈분극) 인 이유와 Mg$^{2+}$ block 의 역할을 설명한다.
- ☐ Shunting inhibition 의 메커니즘 — driving force 가 0 에 가까워질 때 *전류는 작아도 conductance 는 크다* — 를 한 문장으로 정리한다.
""".strip()


L6_SUMMARY = r"""
# L6 — Cable Theory and Action Potential Propagation (graduate-seminar handout)

> *24-hour-mastery target: 이 페이지를 마친 학생은 (i) 1차원 cable equation $\lambda^2 \partial_x^2 V - \tau_m \partial_t V - V = -R_m I_{inj}$ 을 단위 길이당 직렬 axial 저항 + 평행 막 RC 로부터 유도하고, (ii) 정상상태(steady-state) 에서 길이상수(length constant) $\lambda = \sqrt{r_m/r_a}$ 의 의미와 $\lambda \propto \sqrt{a}$ (반지름) 라는 스케일링을 손으로 보이며, (iii) 활동전위(action potential) 가 *재생성(regenerative)* 으로 전파되는 이유와 myelination 이 속도를 어떻게 끌어올리는지 cable + Na channel cluster 관점에서 설명할 수 있어야 한다.*

## 1. 핵심 개념과 적용 한계 (Core Concepts and Regime of Validity)

### 1.1 왜 single-compartment 모델이 깨지는가 [Slide L6 p.2–3, p.7]
**현상**: 실제 뉴런에서 막전위 $V_m(x,t)$ 는 *공간 변수 $x$* 에 따라 크게 다르다. 한 점에서 측정한 PSP(postsynaptic potential) 가 다른 점에서는 attenuated/delayed 로 관찰됨 [Slide L6 p.4–5].
**원인**: dendrite 와 axon 은 가늘고 긴 cable 구조 — 내부 cytoplasmic resistance 가 무시할 수 없음. 한 점의 전류 주입이 다른 점에 도달하기 전에 *axial resistance* 로 인해 감쇠 + 시간 지연.
**적용 한계**: cable theory 는 (a) 막이 *수동적(passive)*, (b) 단면이 균일, (c) 1차원 (반지름 $\ll$ 길이) 일 때 정확. Active conductance 가 켜지면 비선형으로 바뀌어 일반적으로 수치 해법(다중 compartment) 이 필요 [Slide L6 p.13–14].

### 1.2 단위 길이당 회로 매개변수 [Slide L6 p.7–9]
원통형 cable 을 길이방향으로 잘게 쪼개면 각 조각에 다음 4 매개변수:
- $r_m$ [Ω·cm]: 단위 길이당 *막 저항* — 큰 $r_m$ = 막을 통한 누수가 적음.
- $c_m$ [F/cm]: 단위 길이당 *막 capacitance*.
- $r_a$ [Ω/cm]: 단위 길이당 *axial(축 방향) 저항* — 가는 축돌기일수록 큼 ($r_a \propto 1/a^2$, $a$=반지름).
- $i_{inj}(x,t)$ [A/cm]: 단위 길이당 외부 전류 밀도.

**스케일링 핵심**: $r_m = R_m/(2\pi a)$ (둘레에 반비례), $r_a = \rho_a/(\pi a^2)$ (단면적에 반비례). 두 비율이 길이상수를 결정.

### 1.3 길이상수와 시간상수 [Slide L6 p.10–12]
**Length constant** $\lambda = \sqrt{r_m/r_a}$ — 정상상태에서 막전위가 $1/e$ 로 감쇠하는 거리.
$$\lambda = \sqrt{\frac{R_m a}{2 \rho_a}} \;\Rightarrow\; \lambda \propto \sqrt{a}.$$
**Time constant** $\tau_m = r_m c_m = R_m C_m$ — single-compartment 와 동일 (면적 무관).
**전형값**: dendrite $\lambda \sim 0.1$–1 mm, $\tau_m \sim 10$–30 ms. 가는 dendrite 에서 멀리 떨어진 시냅스의 EPSP 는 soma 에 도달할 때 양·시간 모두 큰 손실.

## 2. 핵심 유도 (Key Derivations)

### 2.1 Cable equation 의 유도 [Slide L6 p.8–10]
**Step 1 — Axial 전류와 막전위의 관계 (Ohm)**: 길이 $\Delta x$ 구간의 axial 전류
$$I_a(x) = -\frac{1}{r_a} \frac{\partial V_m}{\partial x}.$$
부호 = 양의 $\partial V/\partial x$ 는 *왼쪽 → 오른쪽* 방향 양전류.
**Step 2 — 막을 가로지르는 전류 (KCL)**: 구간 $\Delta x$ 내에서 axial 전류의 *발산(divergence)* = 막을 통해 빠져나가는 전류:
$$\frac{\partial I_a}{\partial x} \Delta x = -\bigl(i_{m} - i_{inj}\bigr)\Delta x,$$
여기서 막 전류 밀도(per unit length) $i_m = c_m \partial_t V + (V - V_{rest})/r_m$ (capacitive + leak).
**Step 3 — 결합**: Step 1 을 Step 2 에 대입, $V \equiv V_m - V_{rest}$ 로 놓으면
$$\frac{1}{r_a}\frac{\partial^2 V}{\partial x^2} = c_m \frac{\partial V}{\partial t} + \frac{V}{r_m} - i_{inj}.$$
양변에 $r_m$ 을 곱하고 $\lambda^2 = r_m/r_a$, $\tau_m = r_m c_m$ 도입:
$$\boxed{\lambda^2 \frac{\partial^2 V}{\partial x^2} - \tau_m \frac{\partial V}{\partial t} - V = -r_m i_{inj}}\quad [\text{Slide L6 p.8}].$$

### 2.2 Steady-state 해 (semi-infinite cable) [Slide L6 p.10–11]
$\partial_t = 0$, $i_{inj} = 0$ for $x > 0$, $V(0) = V_0$:
$$\lambda^2 V'' - V = 0 \;\Rightarrow\; V(x) = V_0 \, e^{-x/\lambda}.$$
**해석**: 멀리 떨어진 시냅스 입력은 지수적으로 감쇠. $x = \lambda$ 에서 약 $37\%$, $x = 3\lambda$ 에서 $\sim 5\%$.

### 2.3 Pulse 입력의 시간-의존 해 [Slide L6 p.12]
순간(impulse) 전류 주입에 대한 Green 함수는 *위치 $x$ 에서 Gaussian, 시간에 따라 폭이 $\sqrt{t}$ 로 퍼짐* (diffusion-like). $\lambda^2/\tau_m$ 이 *유효 확산계수*. Cable 은 단순 wave equation 이 *아닌* diffusion + decay 의 합성.

### 2.4 활동전위 전파 [Slide L6 p.15–20]
**가설** [Slide L6 p.15, Hermann 1899]: 한 점에서 만들어진 AP 의 cable 전류가 인접 영역을 임계값(threshold) 위로 탈분극 → 그 영역의 voltage-gated Na$^+$ channel 이 열려 *재생성* 으로 새 AP 발화. Hodgkin (1937) 이 직접 실험적으로 입증.
**비-수동성**: AP 전파는 cable equation 만으로는 안 풀린다 — Na/K active conductance 가 매 지점에서 켜져야 신호가 *감쇠 없이 끝까지 도달*. 그래서 cable equation 의 수치 해 + 다중 compartment 의 HH dynamics 결합 [Slide L6 p.13–14, p.20].
**전형 속도**: 무수신경(unmyelinated) axon 에서 $\sim 0.4$ m/s [Slide L6 p.20: 4 mm axon 을 5 ms 안에 약 2 mm 전파].

### 2.5 Myelination [Slide L6 p.21–22]
**Myelin 의 효과**: 절연체로 작용하여 *유효 $r_m$* 증가, *유효 $c_m$* 감소 → $\lambda$ 증가, $\tau_m$ 감소. Node of Ranvier 에 Na$^+$ channel 이 cluster.
**Saltatory conduction**: AP 가 node 에서 node 로 \"점프\" — 노드 간격을 cable equation 의 passive spread 로 계산 가능.
**모델링** [Slide L6 p.22]: myelin 을 두꺼운 cell membrane 으로 치환 (effective $C_m \downarrow$).

## 3. 직관적 매핑 (Expert Intuitive Mapping)

| L6 개념 | 비유 | 공유하는 수학 구조 | 어디서 깨지는가 |
|---|---|---|---|
| Axial resistance $r_a$ | 좁은 호스의 마찰 | Hagen-Poiseuille 와 동형: 흐름 ∝ 압력 기울기, $r_a \propto 1/a^2$ | 호스는 점성 (속도 기울기) — cable 은 옴 저항 (정전기) |
| Membrane leak ($r_m$) | 호스 옆벽의 작은 구멍들 | 옴 누수 | 실제 누수는 ion-selective; 호스는 비선택적 |
| Cable equation | 막대를 따라 퍼지는 *열* | Heat/diffusion + decay $\partial_t u = D \partial_x^2 u - u/\tau$ | 열은 항상 확산만; active conductance 가 켜지면 *재생성* (wave-like) |
| Length constant $\lambda$ | 잉크가 모래사장에 퍼지는 반경 | Diffusion length $\sqrt{D\tau}$ | 잉크는 3D 등방; cable 은 1D + 단면 균일 |
| AP 전파 (regenerative) | 도화선(fuse) 화염 전파 | Bistable reaction-diffusion (FitzHugh-Nagumo) | 도화선은 1회용; axon 은 refractory 후 재발화 |
| Myelin saltatory | 광섬유의 주기적 repeater | passive 전송 + 주기적 재증폭 | repeater 는 op-amp 증폭; node 는 *재생성 ion current* |
| Multi-compartment 모델 | 1차원 막대의 *finite difference* 격자 | $\Delta x \to 0$ 극한에서 PDE 회복 | 큰 $\Delta x$ → spatial aliasing; 분기점 boundary condition |

## 4. 식별성 & 추정 이슈 (Identifiability & Estimation)

| 추정 대상 | 측정 방법 | 식별 조건 | 흔한 오류 |
|---|---|---|---|
| $\lambda$ | 거리에 따른 정상상태 전압 감쇠를 $\ln V$ vs $x$ 로 회귀 | 막이 *수동* 이고 정상상태 도달 | active conductance 가 켜지면 감쇠 곡선이 \"부풀음\" — $\lambda$ 과대평가 |
| $\tau_m$ | 단일 compartment 와 동일하나 dendrite 영향 보정 필요 | 신호가 등전위 도달 (long pulse) | 짧은 pulse 는 cable propagation 와 시상수가 섞임 |
| $r_a$ ($\rho_a$) | dual electrode (서로 다른 두 점에서 동시 기록) | 두 전극 사이 dendrite 가 균일 단면 | dendrite 분기 → effective $r_a$ 가 거리 따라 변함 |
| AP 전파속도 | 두 지점 동시 기록 시간차 | propagation 이 stationary | inhomogeneous Na density → 속도 변동, 단일값 부적합 |
| Myelin g-ratio | axon 직경 / myelin 포함 직경 | myelin 균일, node 간격 일정 | demyelination (MS) 에서 g-ratio 분포 bimodal |
| Multi-compartment 매개변수 | morphology + electrophysiology fit | recording 점이 compartment 수만큼 | 가는 dendrite 는 *unobservable*; 모델 비유일성 |

## 5. 흔한 오해와 시험 함정 (Common Misconceptions)

1. **"Cable equation 은 wave equation 이다"** — 아니다. $\partial_x^2$ 는 있지만 $\partial_t^2$ 가 *없다*. Diffusion equation + linear decay 의 합성. 진정한 wave-like 행동은 active conductance 가 추가되어야 나옴.
2. **"$\lambda$ 가 크면 신호가 더 빨리 간다"** — 아니다. $\lambda$ 는 *공간 감쇠 거리*; 전파 속도는 $\lambda/\tau_m$ (passive) 또는 active dynamics 에 의해 결정. 큰 $\lambda$ = 신호가 *덜 감쇠하면서 멀리 도달*, 시간과는 다른 축.
3. **"Myelin 이 신호를 증폭한다"** — 아니다. Myelin 은 *수동 절연체*; 증폭은 node 의 Na$^+$ channel 이 한다. Myelin 자체는 정보 손실을 *줄일* 뿐.
4. **"Saltatory = AP 가 진짜로 점프"** — 정확히는 *passive cable spread* 가 node 간격을 빠르게 메우고, 다음 node 의 Na channel 이 *재발화*. \"점프\" 는 효과적 비유.
5. **"Multi-compartment = 무한 정확"** — 아니다. compartment 수가 늘면 정확하지만 PDE 의 spatial discretization error 는 항상 존재. 분기점(branch point) 의 boundary condition 처리가 더 큰 오차원.
6. **"AP 가 한 번 발화하면 양방향 전파"** — cable theory 상으로는 yes, 그러나 *refractory period* 가 직전 발화 영역을 일시적으로 비흥분 상태로 만들어 *역전파(antidromic)* 를 차단. 결과: *실제로는* 단방향 (orthodromic).

## 6. 자기 점검 (24h-Mastery Checklist)

- ☐ Cable equation $\lambda^2 \partial_x^2 V - \tau_m \partial_t V - V = -r_m i_{inj}$ 을 axial Ohm + 막 KCL 로부터 백지 유도할 수 있다.
- ☐ Length constant $\lambda = \sqrt{r_m/r_a} = \sqrt{R_m a / 2\rho_a}$ 와 $\lambda \propto \sqrt{a}$ 스케일링을 한 줄로 보일 수 있다.
- ☐ Steady-state 해 $V(x) = V_0 e^{-x/\lambda}$ 를 5분 안에 풀고, $x = \lambda, 3\lambda$ 에서의 잔존비를 즉답한다.
- ☐ Cable equation 이 *wave equation 이 아닌 이유* (시간 2계 미분 부재) 를 한 문장으로 설명한다.
- ☐ AP 전파가 *재생성* 인 이유 — 매 지점의 Na$^+$ channel 이 다시 발화 — 와 cable spread 가 \"점화 도화선\" 역할임을 그림 없이 설명한다.
- ☐ Myelination 이 $r_m \uparrow, c_m \downarrow$ 을 통해 어떻게 $\lambda \uparrow, \tau_m \downarrow$ 를 만드는지 부등식 한 줄로 보인다.
- ☐ Saltatory conduction 의 "점프" 가 실제로는 *passive spread + node 재발화* 임을 설명한다.
- ☐ Multi-compartment 모델이 cable equation 의 *finite difference 근사* 임을 보이고, $\Delta x \to 0$ 극한이 PDE 임을 안다.
- ☐ 무수신경 axon 의 전형 속도 ($\sim 0.4$ m/s [Slide L6 p.20]) 를 즉답한다.
""".strip()


def upsert_summary(lecture, lecture_title, summary_md):
    conn = acquire()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO lecture_summaries (lecture, lecture_title, summary, sources, generated_at)
                VALUES (%s,%s,%s,%s::jsonb,now())
                ON CONFLICT (lecture) DO UPDATE
                SET summary = EXCLUDED.summary,
                    lecture_title = EXCLUDED.lecture_title,
                    sources = EXCLUDED.sources,
                    generated_at = now()
            """, (lecture, lecture_title, summary_md, json.dumps([])))
        conn.commit()
    finally:
        release(conn)


if __name__ == "__main__":
    upsert_summary(
        "L4",
        "Neural Membrane Biophysics II — Ion Channels, Synaptic Transmission & Circuit Models",
        L4_SUMMARY,
    )
    print(f"L4 exemplar summary cached ({len(L4_SUMMARY)} chars)")
    upsert_summary(
        "L6",
        "Cable Theory and Action Potential Propagation",
        L6_SUMMARY,
    )
    print(f"L6 exemplar summary cached ({len(L6_SUMMARY)} chars)")
