#!/usr/bin/env python3
"""Seed core_summaries (1-page exam-ready) + recall_quiz (must-memorize facts).

Opus 4.7 hand-authored in this session per user mandate. Both tables built
together so cross-references stay aligned.
"""
import json, psycopg2

DB_DSN = 'dbname=bri610 user=tutor password=tutor610 host=localhost'

# ──────────────────────────────────────────────────────────────────
# Core summaries (1-page condensed)
# ──────────────────────────────────────────────────────────────────

CORE_SUMMARIES = {
    'L2': {
        'title': 'Computational Neuroscience — What & Why',
        'one_line': '뇌 모델링은 *질문에 따라* 추상화 수준을 달리하는 도구; *Marr 3 단계 + D&A 3 types* 가 공통 분석 언어.',
        'summary_md': '''## 핵심
- *Computational Neuroscience* = 뇌의 정보 처리를 *수학·계산·모델* 로 환원하는 학문 [Slide L2 p.4–5].
- **Marr (1982) 3 단계**: *Computational* (왜 — 목표·문제) → *Algorithmic* (어떻게 — 표상·알고리즘) → *Implementational* (어디서 — 회로). 추상도 ↓.
- **Dayan & Abbott 3 model types**: *Descriptive* (what), *Mechanistic* (how), *Interpretive* (why). Marr Computational ≈ D&A Interpretive.

## 핵심 통찰
- *측정 + 모델 + 이론* = 신경과학의 제3의 기둥.
- *측정 한계가 모델 추상화 수준을 강제* (1907 Lapicque LIF, 1952 HH, 2010s+ multi-scale).
- *Computational Neuroscience* vs *Neural Networks*: *가정 변경 시 생물학적 근거* 요구 여부가 차이.
- *모델 평가 4 기준*: 최소 충분 복잡도 (Occam) + 검증 가능성 (Popper) + 식별 가능성 + 질문 적합성.

## 4 가지 모델링 동기 ("압-발-예-영")
- **압축** (Compression): 데이터 → 통계량.
- **발견** (Discovery): 모델 → 비자명 예측.
- **예측** (Prediction): 새 조건의 정량 답.
- **영감** (Inspiration): 뇌 → AI 설계.

## 한 줄 요약
> *"질문이 모델을 결정한다"*. 단일 보편 모델은 없다 — 한 모델이 세 질문 모두를 답하지 않으며, 답하려 하면 어느 하나도 명확히 답하지 못한다.''',
        'must_memorize': [
            {'fact': 'Marr 의 3 단계: Computational, Algorithmic, Implementational', 'hint': '왜 → 어떻게 → 어디서', 'slide_ref': 'L2 p.34'},
            {'fact': 'Dayan & Abbott 의 3 model types: Descriptive, Mechanistic, Interpretive', 'hint': 'What / How / Why', 'slide_ref': 'L2 §1'},
            {'fact': 'Specific membrane capacitance ≈ 1 μF/cm²', 'hint': 'lipid bilayer 두께 ~3-4 nm', 'slide_ref': 'L3 p.18'},
            {'fact': '신경과학의 제3의 기둥 = computational/modeling', 'hint': '나머지 둘: 실험, 이론', 'slide_ref': 'L2 p.5'},
            {'fact': 'CN vs NN 차이: 가정 변경 시 생물학적 근거 요구', 'hint': 'NN은 공학적 효율 만 요구', 'slide_ref': 'L2 p.12'},
        ],
    },
    'L3': {
        'title': 'Neural Membrane Biophysics I',
        'one_line': '*Lipid bilayer 가 capacitor + 누설 저항 + Nernst 평형* 으로 막전위를 만든다 — 단일 RC 회로 + GHK 가중평균.',
        'summary_md': '''## 핵심 식
- 막 방정식 (KCL form): $C_m \\frac{dV}{dt} = I_\\text{inj} - \\frac{V - E_L}{R_m}$
- 시간상수: $\\tau_m = R_m C_m$ (1 시간상수 후 정상상태의 63% 도달).
- 정상상태: $V_\\infty = E_L + R_m I_\\text{inj}$.
- Nernst 식: $E_X = \\frac{RT}{zF} \\ln \\frac{[X]_o}{[X]_i}$.
- GHK 식: $V_m = \\frac{RT}{F} \\ln \\frac{p_K[K]_o + p_\\text{Na}[Na]_o + p_\\text{Cl}[Cl]_i}{p_K[K]_i + p_\\text{Na}[Na]_i + p_\\text{Cl}[Cl]_o}$.

## 표준 값
- $C_m \\approx 1\\,\\mu\\text{F}/\\text{cm}^2$ (모든 척추동물 뉴런).
- $E_K \\approx -90$ mV, $E_\\text{Na} \\approx +60$ mV, $E_\\text{Cl} \\approx -70$ mV.
- $V_\\text{rest} \\approx -70$ mV (휴지 K leak 우세).
- $RT/F \\approx 26$ mV at 37°C.

## 핵심 통찰
- *$C_m$ 은 $dV/dt$ 항에서만 보임* → steady state 에선 측정 불가능, *transient 에서만* 식별.
- *$V_\\text{rest} \\neq E_K$* 인 이유: 작지만 0 이 아닌 $p_\\text{Na}/p_K \\approx 0.04$ 가 막을 약 +20 mV 끌어올림.
- *Reversal potential* (단일 채널 net current = 0) ≠ *Nernst equilibrium* (단일 이온 net flux = 0). AMPA 같은 비선택 cation 채널에서 reversal 이 더 정확.

## 한 줄 요약
> 막 = capacitor + 평행 leak — *steady state 에선 GHK 가중평균 으로 끌려가고, transient 에선 RC 충전으로 응답*. 휴지 막전위 음수성은 K leak 우세의 결과.''',
        'must_memorize': [
            {'fact': '$C_m \\approx 1$ μF/cm²', 'hint': '진화적 보존', 'slide_ref': 'L3 p.18'},
            {'fact': '$E_K \\approx -90$ mV', 'hint': '척추동물 K 농도비 ~35', 'slide_ref': 'L3 p.27'},
            {'fact': '$E_\\text{Na} \\approx +60$ mV', 'hint': 'AP peak 의 이론적 상한', 'slide_ref': 'L3 p.27'},
            {'fact': '$\\tau_m = R_m C_m$', 'hint': 'RC 시간상수', 'slide_ref': 'L3 p.24'},
            {'fact': 'Nernst: $E_X = (RT/zF) \\ln([X]_o/[X]_i)$', 'hint': 'Boltzmann 평형', 'slide_ref': 'L3 p.27'},
            {'fact': '$RT/F \\approx 26$ mV (37°C)', 'hint': 'Nernst prefactor', 'slide_ref': 'L3 p.27'},
            {'fact': '63% rule: $t = \\tau_m$ 에서 $V/V_\\infty = 1 - 1/e$', 'hint': 'charging curve', 'slide_ref': 'L3 p.24'},
            {'fact': 'GHK 는 *log-domain 가중평균* (Nernst 의 산술평균이 아님)', 'hint': '비선택 채널 평형', 'slide_ref': 'L3 p.30'},
        ],
    },
    'L4': {
        'title': 'Neural Membrane Biophysics II — Ion Channels & Synapses',
        'one_line': '4 종 채널 (leak / voltage-gated / pump / ligand) 이 *병렬* 결합 — 각 항의 *$g$ 의 V/t 의존성* 만이 채널을 구분.',
        'summary_md': '''## 채널 4 종
| 종류 | $g$ 의 $V$ 의존? | $g$ 의 $t$ 의존? | $E$ |
|---|---|---|---|
| Leak | ✗ | ✗ | $E_L \\approx -60$ |
| Voltage-gated | ✓ ($m, h, n$) | ✓ ($\\tau$ 동역학) | $E_\\text{Na}, E_K$ |
| Pump (electrogenic) | ✗ | ✗ | 전류 형태 |
| Ligand-gated | ✗ (NMDA 예외) | ✓ ($g_\\text{syn}(t)$) | $E_\\text{syn}$ |

## 시냅스 reversal
- **AMPA** (비선택 cation): $E_\\text{AMPA} \\approx 0$ mV → EPSP.
- **NMDA**: $E \\approx 0$ + $\\text{Mg}^{2+}$ block (*voltage-dependent*) → coincidence detector.
- **GABA_A** ($Cl^-$): $E \\approx -70$ mV → *shunting inhibition* (휴지 근처 clamp).
- **GABA_B** ($K^+$): $E \\approx -90$ mV → hyperpolarization.

## Alpha function (PSP 시간 모양)
$$g(t) = A\\,t\\,e^{-t/t_\\text{peak}}$$
- 극대 시간: $t = t_\\text{peak}$, 극대값: $g_\\text{max} = A t_\\text{peak}/e$.
- 두 1차 지수의 합성곱 한계 ($\\tau_r \\to \\tau_d$).

## 게이팅 지수의 분자 의미
- $K_v$: $P_\\text{open} = n^4$ — *4 동등 subunit 모두 활성*.
- $Na_v$: $P_\\text{open} = m^3 h$ — *3 활성 + 1 inactivation* gate (단일 polypeptide 4 도메인).

## 한 줄 요약
> *모든 채널 = 같은 형식 ($I = g(V,t)(V-E)$)*; 채널 종류 차이는 오직 *$g$ 의 V/t 의존성 형태* 와 *$E$* 만. 진화는 이 두 변수만 조정.''',
        'must_memorize': [
            {'fact': '$E_\\text{AMPA} \\approx 0$ mV (비선택 cation)', 'hint': 'Na+K 가중평균', 'slide_ref': 'L4 p.7'},
            {'fact': '$E_\\text{GABA_A} \\approx -70$ mV ($Cl^-$)', 'hint': '$V_\\text{rest}$ 근처', 'slide_ref': 'L4 p.18'},
            {'fact': 'NMDA 의 $\\text{Mg}^{2+}$ block 은 voltage-dependent', 'hint': 'coincidence detection', 'slide_ref': 'L4 p.19'},
            {'fact': '$K_v$ 의 $P_\\text{open} = n^4$', 'hint': '4 동등 subunit', 'slide_ref': 'L5 p.21'},
            {'fact': '$Na_v$ 의 $P_\\text{open} = m^3 h$', 'hint': '3 활성 + 1 inactivation', 'slide_ref': 'L5 p.21'},
            {'fact': 'Alpha function 극대: $t = t_\\text{peak}$, $g_\\text{max} = A t_\\text{peak}/e$', 'hint': 'PSP 모양', 'slide_ref': 'L4 §10'},
            {'fact': 'Driving force = $V - E_X$ (부호가 전류 방향 결정)', 'hint': 'Ohm of channel', 'slide_ref': 'L4 p.6'},
            {'fact': 'Shunting inhibition: $g$ 증가가 다른 입력의 effective gain 을 희석', 'hint': '단순 hyperpol 보다 효율', 'slide_ref': 'L4 p.18'},
        ],
    },
    'L5': {
        'title': 'Action Potential & Hodgkin–Huxley Theory',
        'one_line': '*Fast positive (Na 활성) + slow negative (K 활성 + Na inactivation)* 의 시간 분리가 *all-or-none AP* 를 만든다.',
        'summary_md': '''## HH 4-변수 ODE
$$C_m \\frac{dV}{dt} = -\\bar g_\\text{Na} m^3 h(V - E_\\text{Na}) - \\bar g_K n^4(V - E_K) - g_L(V - E_L) + I_\\text{ext}$$
$$\\frac{dx}{dt} = \\frac{x_\\infty(V) - x}{\\tau_x(V)}, \\quad x \\in \\{m, h, n\\}.$$

## 게이팅 변수 시간 척도
- $\\tau_m \\approx 0.1$ ms (빠른 활성, $m \\to 1$).
- $\\tau_h \\approx 1$ ms (느린 inactivation, $h \\to 0$).
- $\\tau_n \\approx 1$ ms (느린 활성, $n \\to 1$).
*시간 분리 ($\\tau_m \\ll \\tau_n$) 가 spike 의 가능 조건*.

## 4 국면
1. **Rest**: K leak 우세, $V \\approx -70$ mV.
2. **Upstroke**: $V$ 임계 → $m$ 폭발 → 자기증폭 → $V \\to E_\\text{Na}$.
3. **Falling**: $h$ 따라잡기 + $n$ 활성화 → 재분극.
4. **AHP**: $n$ 천천히 닫힘 → $V < V_\\text{rest}$ → $h$ 회복 시간.

## Voltage clamp
$V$ 강제 → $dV/dt = 0$ → capacitive 항 *제거* → ionic 전류만 분리. **TTX** (Na 차단) → $g_K$ 분리; **TEA** (K 차단) → $g_\\text{Na}$ 분리.

## 핵심 통찰
- *Refractory period*: absolute (~1 ms, $h \\approx 0$) + relative (~3-5 ms, $h$ 부분 회복). $h$ 의 회복 곡선이 결정.
- *AP peak ≈ +30 mV* — $E_\\text{Na} = +60$ 도달 *못 함* (K_v 가 끼어들어 종료).
- *Spike 가능 조건*: $\\tau_m \\ll \\tau_n$ (시간 분리). 동일 시간상수면 spike 사라짐.

## 한 줄 요약
> HH 의 4 변수 ($V, m, h, n$) 가 *이온 채널의 분자 동역학* 을 직접 반영 — 양의 피드백 + 음의 피드백 *시간 분리* 가 AP 를 만든다.''',
        'must_memorize': [
            {'fact': 'HH 4 변수: $V, m, h, n$', 'hint': '막전위 + 3 게이팅', 'slide_ref': 'L5 §1'},
            {'fact': '$\\tau_m \\ll \\tau_n$ (시간 분리가 spike 가능 조건)', 'hint': '~0.1 ms vs ~1 ms', 'slide_ref': 'L5 §3'},
            {'fact': 'TTX = Na 차단 (복어 독), TEA = K 차단', 'hint': 'voltage clamp 분리 도구', 'slide_ref': 'L5 §3'},
            {'fact': 'Voltage clamp: $V$ 고정 → $dV/dt = 0$ → capacitive 제거', 'hint': 'HH 측정 결정 트릭', 'slide_ref': 'L5 §3'},
            {'fact': 'Absolute refractory: $h \\approx 0$ → spike 불가능', 'hint': '~1 ms', 'slide_ref': 'L5 §6'},
            {'fact': 'AP peak ≈ +30 mV (E_Na = +60 도달 못함)', 'hint': 'K_v 가 끼어들어 종료', 'slide_ref': 'L5 §2'},
            {'fact': 'AHP 깊이 ≈ -90 mV ($E_K$ 방향)', 'hint': '$n$ 천천히 닫힘', 'slide_ref': 'L5 §6'},
            {'fact': 'AP 4 국면: rest → upstroke → falling → AHP', 'hint': '시간 순서', 'slide_ref': 'L5 p.7-9'},
        ],
    },
    'L6': {
        'title': 'Cable Theory & AP Propagation',
        'one_line': '*Cable PDE* $\\tau_m \\partial_t V = \\lambda^2 \\partial_x^2 V - V$ — *공간상수* $\\lambda$ 가 신호 감쇠 거리, myelin 이 동시 최적화로 saltatory 전파 가능.',
        'summary_md': '''## Cable PDE
$$\\tau_m \\frac{\\partial V}{\\partial t} = \\lambda^2 \\frac{\\partial^2 V}{\\partial x^2} - (V - V_\\text{rest}) + r_m i_\\text{inj}$$
*Steady state 해*: $V(x) = V_0 e^{-x/\\lambda}$ (semi-infinite cable).

## 공간상수 $\\lambda$
$$\\lambda = \\sqrt{\\frac{d R_m}{4 R_i}}$$
- $d$: 직경. $R_m$: specific membrane resistance. $R_i$: cytoplasm 저항도.
- $\\lambda \\propto \\sqrt{d}$ (직경 *제곱근* 의존).
- *37% 거리 = $\\lambda$, 14% 거리 = $2\\lambda$* (e-folding).

## 전파 속도
- *무수초*: $v \\propto \\sqrt{d/(\\tau_m r_i)}$, 즉 $v \\propto \\sqrt{d}$.
- *수초 (saltatory)*: $v \\propto d$. Internode 의 $C_m \\downarrow$ + $R_m \\uparrow$ 동시 최적화.

## 핵심 통찰
- $\\lambda$ 는 *passive 감쇠 거리* 이지 *AP 속도* 가 아님 — 둘은 다른 양.
- *Steady state cable 측정만으론* $\\lambda$ 만 결정 → $R_m / R_i$ 비율만; 절댓값은 transient 측정 필요.
- *Distal dendrite* ($x = 2\\lambda$) 의 EPSP 는 *14% 만 도달* → active dendrite (NMDA spike, $Ca^{2+}$ plateau) 필요.
- 무수초 axon 에서 *$v$ 두 배 = 직경 4 배* 비용 → 척추동물 brain volume 한계 → myelin 진화.

## 한 줄 요약
> *공간 RC 네트워크* 가 dendrite/axon 동역학 — 두 척도 $\\tau_m$ (시간) + $\\lambda$ (공간) 가 신호 전파 결정. Myelin 이 두 변수 동시 최적화로 한 차수 빠른 saltatory 전파 가능.''',
        'must_memorize': [
            {'fact': '$\\lambda = \\sqrt{d R_m / 4 R_i}$', 'hint': '공간상수 정의식', 'slide_ref': 'L6 §3'},
            {'fact': '무수초 $v \\propto \\sqrt{d}$, 수초 $v \\propto d$', 'hint': 'saltatory advantage', 'slide_ref': 'L6 §6'},
            {'fact': '37% 거리 = $\\lambda$, 14% 거리 = $2\\lambda$', 'hint': 'e-folding', 'slide_ref': 'L6 §4'},
            {'fact': 'Cable PDE: $\\tau_m \\partial_t V = \\lambda^2 \\partial_x^2 V - V$', 'hint': 'standard form', 'slide_ref': 'L6 §3'},
            {'fact': 'Myelin: $C_m \\downarrow$ + $R_m \\uparrow$ 동시', 'hint': '두 효과 결합', 'slide_ref': 'L6 §7'},
            {'fact': 'Saltatory = "saltare" (라틴어 점프)', 'hint': 'node of Ranvier 사이', 'slide_ref': 'L6 §7'},
            {'fact': '$\\lambda$ 는 passive 감쇠 거리, AP 속도 아님', 'hint': '둘은 다른 양', 'slide_ref': 'L6 §12'},
        ],
    },
    'L7': {
        'title': 'Different Types of Computational Models of Single Neurons',
        'one_line': '*모델 선택 = 질문 선택*: LIF (망 동역학), Izhikevich (spike 패턴), HH (메커니즘) — 한 모델이 모든 답을 주지 않는다.',
        'summary_md': '''## LIF (Leaky Integrate-and-Fire)
- Sub-threshold: $C dV/dt = -g_L(V-E_L) + I_e$ (RC 충전).
- $V \\geq V_\\text{th}$ → spike + $V \\leftarrow V_\\text{reset}$ + refractory $\\tau_\\text{ref}$.
- **Rheobase**: $I_\\text{thr} = (V_\\text{th} - E_L)/R_m$.
- **f-I 곡선**: $r(I) = 1/[\\tau_\\text{ref} + \\tau_m \\ln \\frac{V_\\text{reset} - V_\\infty}{V_\\text{th} - V_\\infty}]$.
- **포화**: $r_\\text{max} = 1/\\tau_\\text{ref}$.

## Izhikevich (a, b, c, d)
- $dv/dt = f(v, u)$, $du/dt = g(v, u)$. 4 매개변수.
- 21 가지 spike 패턴 (RS, IB, FS, LTS, ...) 표현 가능.
- *식별 불가능*: 같은 f-I 곡선에 무한히 많은 (a, b, c, d) 조합.

## 모델 비교
| | LIF | Izhikevich | HH |
|---|---|---|---|
| 변수 | 1 ($V$) | 2 ($v, u$) | 4 ($V, m, h, n$) |
| 매개변수 | 4 | 4 | 30+ |
| 식별성 (표준 실험) | ✓ | ✗ | ✓ (voltage clamp + 약물) |
| Spike pattern variety | × | ✓✓ | △ |
| Biophysical 정확성 | × | × | ✓ |
| 망 시뮬 ($10^7$) | ✓ (실시간) | ✓ | ✗ (4 배 느림) |

## 핵심 통찰
- *Realism ≠ 좋은 모델*. 망 진동 → LIF, channel kinetics → HH, spike pattern → Izhikevich.
- 측정 기술이 모델 추상화 수준을 *강제* — Lapicque 1907 (LIF), HH 1952 (voltage clamp + ODE), Izhikevich 2003 (spike pattern fit).

## 한 줄 요약
> *모델은 질문에 가장 단순한 추상화*. 질문 → 추상화 수준 → 모델 선택 → 측정 → 매개변수 식별 → 검증.''',
        'must_memorize': [
            {'fact': 'LIF rheobase: $I_\\text{thr} = (V_\\text{th} - E_L)/R_m$', 'hint': '발화 시작 최소 전류', 'slide_ref': 'L7 §3'},
            {'fact': 'LIF $r_\\text{max} = 1/\\tau_\\text{ref}$', 'hint': '포화 발화율', 'slide_ref': 'L7 §3'},
            {'fact': 'LIF 변수 1, HH 변수 4 → 망에서 4 배 비용 차이', 'hint': '$10^7$ 뉴런 시뮬', 'slide_ref': 'L7 §10'},
            {'fact': 'Izhikevich 4 매개변수: a (회복속도), b (recovery sensitivity), c (V reset), d (u jump)', 'hint': '4 매개변수 spike 패턴', 'slide_ref': 'L7 §6'},
            {'fact': 'Izhikevich 식별 불가능 (f-I 곡선만으론)', 'hint': 'parameter ridge', 'slide_ref': 'L7 §10.1'},
            {'fact': '모델 선택 = 질문 선택', 'hint': '범용 모델 없음', 'slide_ref': 'L7 §11'},
        ],
    },
    'L8': {
        'title': 'Neural Codes — Rate, Temporal, Phase, Synchrony',
        'one_line': '*Multiplexed code*: 한 spike train 위에 4 채널 (rate / temporal / phase / synchrony) 정보가 *동시* 실린다 — 보편 부호는 없다.',
        'summary_md': '''## 4 부호 종류
- **Rate**: 시간 평균 발화율 ($\\bar r$). Adrian (1926). Robust + slow.
- **Temporal**: 정확 spike timing (sub-ms). 청각 sound localization 의 ITD.
- **Phase**: 진동 ($\\theta, \\gamma$) 위상 기준. Hippocampal phase precession.
- **Synchrony**: 다중 뉴런 동시 발화. Singer 의 binding hypothesis.

## PSTH (peri-stimulus time histogram)
- 자극 onset 정렬 + bin (~20 ms) 별 spike density.
- *반복 가능* 자극 필수 (single-trial 못 함).
- Rate code 의 *시간 분해* 형태.

## Mainen-Sejnowski (1995) paradox
- DC 자극: trial 마다 spike timing 변동 → 뉴런 noisy 가설.
- *Frozen noise* (시간 구조 자극): spike timing trial 간 정확 일치 (sub-ms).
- 결론: *뉴런은 sub-ms 정확*; variability 는 *flat 자극* 의 결과 → temporal code 가능.

## Phase precession (CA1 place cell)
- *수 초 분량 공간 sequence* → *125 ms (1 theta cycle) 안에 sub-ms spike sequence* 압축.
- *Temporal compression* — replay/preplay 의 기초.
- Theta 주파수: ~8 Hz.

## 한 줄 요약
> *질문이 부호를 결정*. 운동 → rate, 청각 → temporal, hippocampal → phase + multiplex, 시각 binding → synchrony. 4 채널이 *같은 spike train 위에 동시* 실릴 수 있다.''',
        'must_memorize': [
            {'fact': '4 신경 부호: rate, temporal, phase, synchrony', 'hint': '영문 정확히', 'slide_ref': 'L8 §1, §3, §B, §6'},
            {'fact': 'PSTH: 자극 onset 정렬 + bin 별 spike density', 'hint': '~20 ms bin', 'slide_ref': 'L8 §2'},
            {'fact': 'Theta 주파수 ~8 Hz, cycle 125 ms', 'hint': 'hippocampal phase', 'slide_ref': 'L8 p.39'},
            {'fact': 'Mainen-Sejnowski (1995): frozen noise → sub-ms spike timing 정확', 'hint': 'paradox 해결', 'slide_ref': 'L8 §11'},
            {'fact': 'Phase precession = temporal compression (sec → ms)', 'hint': 'replay/preplay 기초', 'slide_ref': 'L8 §B'},
            {'fact': 'Multiplexed code: 한 spike 가 여러 정보 차원 동시 표현', 'hint': '맥락별 지배', 'slide_ref': 'L8 §B.2'},
            {'fact': 'Adrian (1926): rate code 의 발견', 'hint': '청개구리, 노벨상 1932', 'slide_ref': 'L8 p.7'},
            {'fact': 'Fano factor $F = \\text{Var}/\\text{E}$. Poisson F=1, refractory 있으면 F<1', 'hint': 'spike 통계', 'slide_ref': 'L8 §2'},
        ],
    },
}


# ──────────────────────────────────────────────────────────────────
# Recall quiz — short-answer must-memorize, designed for daily SRS cycling
# ──────────────────────────────────────────────────────────────────

# Each entry: (lecture, position, fact_tag, prompt, answer, accept_patterns, slide_ref, difficulty)
RECALL = [
    # ─── L2 ───
    ('L2', 1, 'marr-3-levels', 'Marr 의 3 단계를 위에서 아래 순서로 영어로 답하라', 'Computational, Algorithmic, Implementational',
     [r'(?i).*comput(ational)?.*algorithm(ic)?.*implement(ation)?al.*'], 'L2 p.34', 1),
    ('L2', 2, 'da-3-types', 'Dayan & Abbott 의 3 model types 를 영어로 답하라', 'Descriptive, Mechanistic, Interpretive',
     [r'(?i).*descriptive.*mechanistic.*interpretive.*'], 'L2 §1', 1),
    ('L2', 3, 'cn-vs-nn', 'Computational Neuroscience 와 Neural Networks 의 결정적 차이는?', '가정 변경 시 *생물학적 근거* 를 요구하는가',
     [r'(?i).*생물학적\s*근거', r'(?i).*biological\s+(grounding|justification|constraint)', r'(?i).*가정\s*변경'], 'L2 p.12', 2),

    # ─── L3 ───
    ('L3', 1, 'cm-value', '*Specific membrane capacitance* $c_m$ 의 표준 값과 단위를 답하라', '1 μF/cm²',
     [r'(?i)\b1\s*(μ|mu|micro|u)\s*F\s*/\s*cm[2²]?'], 'L3 p.18', 1),
    ('L3', 2, 'ek-value', '$E_K$ 의 표준 값을 mV 단위로 답하라', '−90 mV',
     [r'\b[-−]\s*9[0-3]\s*mV\b', r'(?i).*minus\s+9[0-3]'], 'L3 p.27', 1),
    ('L3', 3, 'ena-value', '$E_\\text{Na}$ 의 표준 값을 mV 단위로 답하라', '+60 mV',
     [r'\+?\s*5[6-9]?6?0?\s*mV', r'\+?\s*60\s*mV', r'\+?\s*5[8-9]\s*mV'], 'L3 p.27', 1),
    ('L3', 4, 'tau-m', '시간상수 $\\tau_m$ 의 정의식을 $R_m, C_m$ 으로 답하라', 'R_m C_m',
     [r'(?i)R_?m\s*\*?\s*C_?m', r'(?i)C_?m\s*\*?\s*R_?m'], 'L3 p.24', 1),
    ('L3', 5, '63-rule', '$t = \\tau_m$ 에서 $V/V_\\infty$ 의 값은? (소수)', '0.63 (= 1 − 1/e)',
     [r'\b0[\.,]6[2-4]\b', r'(?i)1\s*[-−]\s*1\s*/\s*e', r'(?i)\b63\s*%'], 'L3 p.24', 2),
    ('L3', 6, 'rt-f', '$RT/F$ 의 값을 mV 단위로 답하라 (체온 37°C)', '26.7 mV',
     [r'\b2[5-7][\.,]?\d*\s*mV\b'], 'L3 p.27', 2),
    ('L3', 7, 'nernst-eq', 'Nernst 식의 일반형을 답하라 (수식 또는 변수명)', 'E_X = (RT/zF) ln([X]_o/[X]_i)',
     [r'(?i)RT\s*/\s*z?F\s*\*?\s*ln', r'(?i)E_?X.*RT.*\\?ln', r'(?i)Nernst.*log\s*ratio'], 'L3 p.27', 2),

    # ─── L4 ───
    ('L4', 1, 'ampa-rev', '$E_\\text{AMPA}$ 의 값과 채널 종류를 답하라', '~0 mV (비선택 cation)',
     [r'(?i).*(약\s*)?0\s*mV.*(비선택|cation)', r'(?i).*0\s*mV', r'(?i).*non[-\s]?selective\s+cation'], 'L4 p.7', 1),
    ('L4', 2, 'gabaA-rev', '$E_{\\text{GABA}_A}$ 의 값과 통과 이온을 답하라', '~−70 mV (Cl−)',
     [r'(?i).*[-−]\s*7\d\s*mV.*Cl', r'(?i)Cl.*[-−]\s*7\d', r'(?i).*shunting.*Cl'], 'L4 p.18', 1),
    ('L4', 3, 'kv-popen', '$K_v$ 채널의 $P_\\text{open}$ 식을 답하라', 'n^4',
     [r'(?i)\bn\s*\^?\s*\{?\s*4\s*\}?\b'], 'L4 p.10; L5 p.21', 1),
    ('L4', 4, 'nav-popen', '$Na_v$ 채널의 $P_\\text{open}$ 식을 답하라', 'm^3 h',
     [r'(?i)\bm\s*\^?\s*\{?\s*3\s*\}?\s*\*?\s*h\b'], 'L4 p.10; L5 p.21', 1),
    ('L4', 5, 'nmda-mg', 'NMDA 의 $\\text{Mg}^{2+}$ block 의 핵심 특성은?', 'voltage-dependent (탈분극으로 풀림)',
     [r'(?i)voltage[-\s]?dependent', r'(?i)전압\s*의존', r'(?i)\\?text\{?Mg\}?\^?2\+?.*block'], 'L4 p.19', 2),
    ('L4', 6, 'alpha-peak', 'Alpha function $g(t) = At\\,e^{-t/t_\\text{peak}}$ 의 극대 시간은?', 't_peak',
     [r'(?i)t_?\{?peak\}?', r'(?i)t\s*=\s*t_?peak'], 'L4 §10', 2),

    # ─── L5 ───
    ('L5', 1, 'hh-vars', 'HH 의 4 변수를 나열하라', 'V, m, h, n',
     [r'(?i)V\W*m\W*h\W*n', r'(?i).*\bV\b.*\bm\b.*\bh\b.*\bn\b'], 'L5 §1', 1),
    ('L5', 2, 'ttx', 'Na 채널 selective blocker 천연 독소의 이름은?', 'TTX (tetrodotoxin)',
     [r'(?i)\bTTX\b', r'(?i)tetrodotoxin'], 'L5 §3', 1),
    ('L5', 3, 'tea', 'K 채널 blocker 의 이름은?', 'TEA (tetraethylammonium)',
     [r'(?i)\bTEA\b', r'(?i)tetraethylammonium'], 'L5 §3', 1),
    ('L5', 4, 'time-asymmetry', 'AP 가 가능한 핵심 시간 조건은?', 'τ_m ≪ τ_n (시간 분리)',
     [r'(?i)\\?tau_?m.*\\?tau_?n', r'(?i)\\?tau_?m\s*<<?\s*\\?tau_?n', r'(?i)시간\s*분리'], 'L5 §3', 2),
    ('L5', 5, 'absolute-refr', 'Absolute refractory period 의 분자적 원인은?', 'h ≈ 0 (Na inactivation)',
     [r'(?i)h\s*[≈=]\s*0', r'(?i)Na\s+inactivation', r'(?i)inactivation\s*gate\s*닫'], 'L5 §6', 1),
    ('L5', 6, 'voltage-clamp', 'Voltage clamp 가 capacitive 항을 제거하는 메커니즘은?', 'V 고정 → dV/dt = 0 → C_m dV/dt = 0',
     [r'(?i)dV\s*/\s*dt\s*=\s*0', r'(?i)V\s*고정.*capacitive', r'(?i)V\s*=\s*const'], 'L5 §3', 2),
    ('L5', 7, 'ap-peak', 'AP peak 의 대략적 값은? (mV)', '+30 mV',
     [r'\+?\s*[23]\d\s*mV', r'\+?\s*30\s*mV'], 'L5 §2', 1),

    # ─── L6 ───
    ('L6', 1, 'lambda-def', '공간상수 $\\lambda$ 의 정의식을 $d, R_m, R_i$ 로 답하라', '√(d R_m / 4 R_i)',
     [r'(?i)\\?sqrt.*d.*R_?m.*4.*R_?i', r'(?i)d.*R_?m.*/\s*4\s*R_?i'], 'L6 §3', 1),
    ('L6', 2, 'unmyelin-v', '*무수초* axon 에서 AP 속도 $v$ 의 직경 의존성', 'v ∝ √d',
     [r'(?i)v\s*∝.*\\?sqrt.*d', r'(?i)v\s*~\s*\\?sqrt.*d', r'(?i)v\s*=\s*proportional.*sqrt'], 'L6 §6', 2),
    ('L6', 3, 'myelin-v', '*수초* axon 에서 AP 속도의 직경 의존성', 'v ∝ d (선형)',
     [r'(?i)v\s*∝\s*d\b(?!\s*\^)', r'(?i)v\s*~\s*d\b', r'(?i)선형'], 'L6 §6', 2),
    ('L6', 4, 'cable-pde', 'Cable PDE 의 standard form 을 작성하라', 'τ_m ∂_t V = λ² ∂_xx V − V',
     [r'(?i)\\?tau_?m.*\\?partial.*V.*=.*\\?lambda.*\\?partial.*V', r'(?i)\\?tau.*lambda\s*\^?\s*2'], 'L6 §3', 3),
    ('L6', 5, 'saltatory-meaning', '"Saltatory" 의 라틴어 어원과 뜻은?', 'saltare (점프하다)',
     [r'(?i)saltare', r'(?i)점프', r'(?i)to\s+jump', r'(?i)\bjump\b'], 'L6 §7', 1),
    ('L6', 6, 'lambda-37', '$\\lambda$ 거리에서 $V/V_0$ 의 값은? (소수)', '0.37 (= 1/e)',
     [r'\b0[\.,]3[6-8]\b', r'(?i)1\s*/\s*e', r'(?i)37\s*%'], 'L6 §4', 2),

    # ─── L7 ───
    ('L7', 1, 'lif-rheobase', 'LIF 의 rheobase $I_\\text{thr}$ 정의식', '(V_th − E_L) / R_m',
     [r'(?i)\(?\s*V_?\{?th\}?\s*[-−]\s*E_?L\s*\)?\s*/\s*R_?m'], 'L7 §3', 2),
    ('L7', 2, 'lif-rmax', 'LIF 의 최대 발화율 $r_\\text{max}$', '1/τ_ref',
     [r'(?i)1\s*/\s*\\?tau_?\{?ref\}?', r'(?i)1\s*/\s*\\?tau_?r\b'], 'L7 §3', 1),
    ('L7', 3, 'hh-vs-lif-cost', 'HH 와 LIF 의 망 시뮬 ODE 비율', '4 : 1 (HH 가 4 배)',
     [r'\b4\s*[:×x]\s*1?\b', r'(?i)4\s*배', r'(?i)4\s*times'], 'L7 §10', 2),
    ('L7', 4, 'izhikevich-params', 'Izhikevich 모델의 4 매개변수', 'a, b, c, d',
     [r'(?i)\ba\b\W+\bb\b\W+\bc\b\W+\bd\b'], 'L7 §6', 1),
    ('L7', 5, 'izhikevich-identifiability', 'Izhikevich 의 식별성 문제', '식별 불가능 (parameter ridge)',
     [r'(?i)식별\s*불가', r'(?i)not\s+identifiable', r'(?i)parameter\s+ridge', r'(?i)무한히\s*많은\s*조합'], 'L7 §10.1', 2),

    # ─── L8 ───
    ('L8', 1, 'four-codes', '4 신경 부호화 방식을 영어로 나열', 'rate, temporal, phase, synchrony',
     [r'(?i)rate\W+temporal\W+phase\W+synchrony', r'(?i).*rate.*temporal.*phase.*synchrony.*'], 'L8 §1, §3, §B, §6', 1),
    ('L8', 2, 'theta-freq', 'Hippocampal theta 주파수와 cycle 길이', '~8 Hz, 125 ms',
     [r'(?i)\b8\s*Hz.*125\s*ms', r'(?i)125\s*ms.*8\s*Hz', r'(?i)\b[6-9]\s*Hz.*1[0-7]\d\s*ms'], 'L8 p.39', 1),
    ('L8', 3, 'fano-poisson', 'Poisson 과정의 Fano factor 값', 'F = 1',
     [r'(?i)F\s*=\s*1', r'(?i)Fano.*1', r'(?i)분산\s*=\s*평균'], 'L8 §2', 2),
    ('L8', 4, 'mainen-sejnowski', 'Mainen-Sejnowski (1995) 의 핵심 발견', '뉴런은 sub-ms 정확; variability 는 flat 자극의 결과',
     [r'(?i)sub[-\s]?ms', r'(?i)frozen\s+noise.*정확', r'(?i)variabil(ity)?.*(flat|DC)\s*자극'], 'L8 §11', 2),
    ('L8', 5, 'phase-compression', 'Phase precession 이 만드는 시간 변환', '수 초 공간 sequence → ~125 ms spike sequence (압축)',
     [r'(?i)temporal\s+compression', r'(?i)압축', r'(?i)125\s*ms.*sequence'], 'L8 §B', 2),
    ('L8', 6, 'binding-singer', 'Binding problem 의 Singer 가설', '동시 발화 (synchrony) 가 binding 신호',
     [r'(?i)synchrony.*binding', r'(?i)동시\s*발화.*binding', r'(?i)Singer.*synchrony'], 'L8 §6', 2),
]


def main():
    conn = psycopg2.connect(DB_DSN)
    try:
        with conn.cursor() as cur:
            # Core summaries
            for lec, data in CORE_SUMMARIES.items():
                cur.execute("""
                    INSERT INTO core_summaries (lecture, title, summary_md, must_memorize, one_line)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (lecture) DO UPDATE SET
                      title = EXCLUDED.title,
                      summary_md = EXCLUDED.summary_md,
                      must_memorize = EXCLUDED.must_memorize,
                      one_line = EXCLUDED.one_line,
                      generated_at = now()
                """, (
                    lec, data['title'], data['summary_md'],
                    json.dumps(data['must_memorize'], ensure_ascii=False),
                    data['one_line'],
                ))
                print(f'core_summaries[{lec}]: {len(data["summary_md"])} chars + {len(data["must_memorize"])} must-memorize')

            # Recall quiz
            for entry in RECALL:
                lec, pos, tag, prompt, answer, patterns, ref, diff = entry
                cur.execute("""
                    INSERT INTO recall_quiz
                      (lecture, position, fact_tag, prompt, answer, accept_patterns, slide_ref, difficulty)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (lecture, position) DO UPDATE SET
                      fact_tag = EXCLUDED.fact_tag,
                      prompt = EXCLUDED.prompt,
                      answer = EXCLUDED.answer,
                      accept_patterns = EXCLUDED.accept_patterns,
                      slide_ref = EXCLUDED.slide_ref,
                      difficulty = EXCLUDED.difficulty
                """, (
                    lec, pos, tag, prompt, answer,
                    json.dumps(patterns, ensure_ascii=False),
                    ref, diff,
                ))
        conn.commit()
        print(f'\nrecall_quiz: {len(RECALL)} items inserted')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
