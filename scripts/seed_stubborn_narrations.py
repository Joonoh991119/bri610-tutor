#!/usr/bin/env python3
"""Hand-author the 3 stubborn narrations DeepSeek V4 Pro returned empty for.

After 2 retry passes the following steps still failed (returned 0 chars):
  L5 step 2: AP 의 양·음 피드백 사이클
  L5 step 7: 전체 HH 식 + 시뮬레이션
  L8 step 2: Rate code — Adrian 1926

Likely the original prompt + content triggered a quality / safety filter on
DeepSeek's side. Hand-authoring these as Opus 4.7 in this session.
"""
import psycopg2

DB_DSN = 'dbname=bri610 user=tutor password=tutor610 host=localhost'

STUBBORN = [
    # L5 step 2 — AP 의 양·음 피드백 사이클
    ('L5', 2, '''1️⃣ **AP 의 핵심은 두 피드백 루프의 시간 분리**.
- *양의 피드백* (positive): $V \\uparrow \\to m \\uparrow \\to g_\\text{Na} \\uparrow \\to I_\\text{Na}$ inward $\\uparrow \\to V \\uparrow \\uparrow$. 빠른 시간 척도 ($\\tau_m \\approx 0.1$ ms).
- *음의 피드백* (negative): $V \\uparrow \\to h \\downarrow$ (Na inactivation, 느림 ~1 ms) AND $V \\uparrow \\to n \\uparrow \\to g_K \\uparrow \\to V \\downarrow$. 느린 시간 척도 ($\\tau_n \\approx 1$ ms).

2️⃣ 시간 분리 ($\\tau_m \\ll \\tau_n$) 가 곧 *AP 의 가능 조건*. 두 피드백이 동시 활성화면 막은 *graded* 응답만 가능 — spike 없음. *fast positive + slow negative* 의 비대칭이 *limit cycle* 을 만든다.

3️⃣ 4 국면 시퀀스:
- Rest: $m \\approx 0$, $h \\approx 1$, $n \\approx 0$ — K leak 우세, $V \\approx -70$ mV.
- Upstroke: $V$ 임계 도달 → $m$ 폭발적 증가 → 자기증폭 → $V \\to E_\\text{Na}$ 방향.
- Falling: $h$ 따라잡으며 inactivation + $n$ 활성화 → K efflux → 재분극.
- AHP: $n$ 천천히 닫히는 동안 $V < V_\\text{rest}$ → $h$ 회복 시간 제공.

4️⃣ 사이클 종료 조건: $h$ 가 충분히 회복 ($h > 0.4$) AND $n$ 충분히 닫힘 ($n < 0.3$). 이 조건이 *refractory period* 의 분자적 정의.

5️⃣ Phase plane ($V, n$) 관점: nullcline 교차점이 *불안정 saddle* + *안정 limit cycle* 을 만들어 spike trajectory 를 위상공간 곡선으로 시각화. *Bifurcation* 분석에서 $I_e = I_\\text{thr}$ 가 saddle-node 분기점.

→ 다음: 이 양·음 피드백 사이클을 측정하기 위한 voltage clamp + pharmacology 트릭.

## 🖼 Figure

<figure><img src="/figures/action_potential_phases.svg" alt="AP 4국면과 양·음 피드백 사이클" /><figcaption>그림: AP voltage trace 의 4 국면 — rest / upstroke / falling / AHP. 빨간 점선 = $E_\\text{Na} = +58$ mV (상한), 파란 점선 = $E_K = -83$ mV (하한). Upstroke 의 자기증폭은 양의 피드백, falling 의 재분극은 음의 피드백의 결과.</figcaption></figure>

## 🔁 변주

**변주 1 (자기제동 자동차).** Spike 는 *자기제동 시스템* 이 있는 자동차와 같다. 가속 페달 (양의 피드백, $m$ 활성화) 을 밟으면 차가 빠르게 가속하지만, *가속 자체* 가 브레이크 (음의 피드백, $h$ inactivation + $n$ K 활성화) 를 *지연 작동* 시킨다. 시간 분리가 없다면 — 즉 가속과 브레이크가 동시에 작동한다면 — 차는 절대 큰 속도에 도달 못 한다. AP 의 *all-or-none* 는 이 자기제동의 timing 비대칭이 만든다.

**변주 2 (수식 → 시각 변환).** 양·음 피드백을 한 도식으로:
$$\\underbrace{V \\to m \\to g_\\text{Na} \\to V}_\\text{양의 피드백 (빠름)} \\quad \\text{vs} \\quad \\underbrace{V \\to h^{-1} + n \\to g_K \\to V^{-1}}_\\text{음의 피드백 (느림)}.$$
시간 분리 $\\tau_m \\ll \\tau_n$ 이 두 화살표가 *순차* 작동하도록 보장 → spike. $\\tau_n \\to \\tau_m$ 한계에서 두 화살표가 *병렬* → 균형 → spike 사라짐.

## ❓ 점검 Q&A

**Q:** 만약 $h$ inactivation 이 *없다면* AP 가 어떻게 달라지는가?
**A:** Na 활성화의 자기증폭이 *멈출 메커니즘 부재* → $V$ 가 $E_\\text{Na} = +60$ mV 까지 *상승 후 머무름*. K_v 가 활성화되어 $V$ 가 떨어져도 $m$ 도 같이 작아져 self-termination 이 *불완전*. 결과: *영구 spike 또는 bistable* — 더 이상 transient AP 가 아닌 *2-state* 회로. $h$ 가 곧 spike 의 *시간 종료자*.

**Q:** Phase plane 에서 saddle-node bifurcation 이 의미하는 *생물학적 직관* 은?
**A:** 정상상태 (resting) 와 spike trajectory 는 위상공간의 *별개 영역*. Saddle 점은 임계 — 약간의 자극은 rest 로 회귀, 임계 초과 자극은 limit cycle 로 진입. 이것이 *all-or-none* 의 동역학적 기반: 자극이 saddle 의 *어느 쪽* 에 떨어지느냐가 결과를 *quantize*. 작은 입력 변동이 *큰 결과 차이* 를 만드는 비선형 임계화의 정수.'''),

    # L5 step 7 — 전체 HH 식 + 시뮬레이션
    ('L5', 7, '''1️⃣ **HH 4-변수 ODE 시스템 정리**:
$$C_m \\frac{dV}{dt} = -\\bar g_\\text{Na} m^3 h (V - E_\\text{Na}) - \\bar g_K n^4 (V - E_K) - g_L (V - E_L) + I_\\text{ext}$$
$$\\frac{dx}{dt} = \\frac{x_\\infty(V) - x}{\\tau_x(V)}, \\quad x \\in \\{m, h, n\\}.$$
4 ODE, 표준 매개변수 (Hodgkin-Huxley 1952): $\\bar g_\\text{Na} = 120$, $\\bar g_K = 36$, $g_L = 0.3$ mS/cm², $E_\\text{Na} = 50$, $E_K = -77$, $E_L = -54.4$ mV, $C_m = 1$ μF/cm².

2️⃣ **Step current 시뮬레이션 결과**:
- $I_e = 0$: rest 안정, $V \\approx V_\\text{rest}$.
- $I_e = $ rheobase: 첫 spike 후 정상 발화 시작. 발화율은 5-10 Hz (slow).
- $I_e = 5 \\bar g_L \\cdot$ rheobase: 발화율 50-100 Hz (fast).
- $I_e \\to \\infty$: $1/\\tau_\\text{ref} \\approx 200$ Hz 로 포화.

3️⃣ **3 가지 동역학 사례 재현**:
- **Refractory period**: spike 직후 ~1 ms (absolute) + ~3-5 ms (relative). $h$ 회복 곡선이 결정.
- **AHP**: spike 후 $V \\approx -90$ mV 까지 끌려갔다가 ~10 ms 이내 복귀. $n$ 의 느린 닫힘이 결정.
- **Spike-frequency adaptation**: HH 자체엔 *없음* — 추가 $g_\\text{sra}$ (slow K, $Ca^{2+}$-activated) 이 필요. L7 §7 에서 LIF 에 SFA 추가.

4️⃣ **시뮬레이션 검증 — Hodgkin-Huxley 의 예측력**: 실험에서 *측정* 한 $g_\\text{Na}, g_K$ 동역학 매개변수 + voltage clamp $\\alpha, \\beta$ 함수를 ODE 에 *대입* → 예측한 $V(t)$ 가 *current clamp* (자유 막) 측정과 일치 — 1952 노벨상 수상 핵심 결과. *모델이 측정 외의 조건을 정확 예측* 하는 것이 *과학적 모델의 정의*.

5️⃣ **HH 의 한계와 후속**: HH 는 squid axon (giant) 기준 — 포유류 뉴런은 추가 채널 ($K_v$ subtypes, $Ca^{2+}$ channels, HCN, slow K) 필요. *Modified HH* (Pinsky-Rinzel 1994 multi-compartment, Mainen-Sejnowski 1996, Hay et al. 2011) 가 cortical pyramidal 뉴런 정확 재현. 그러나 *기본 framework* (4-변수 + voltage-gated kinetics) 는 모든 후속 모델의 *공통 기반*.

→ 다음: HH 모델이 *왜 4 변수만으로 충분한가*, 그리고 voltage clamp + pharmacology 의 *식별성* 트릭.

## 🖼 Figure

<figure><img src="/figures/hh_gating_variables.svg" alt="HH 의 3 게이팅 변수 m, h, n 의 V 의존성" /><figcaption>그림: $m_\\infty(V)$ (Na 활성화, 가파른 증가), $h_\\infty(V)$ (Na 비활성화, 감소), $n_\\infty(V)$ (K 활성화, 천천히 증가). 세 sigmoid 의 *시간 + 전압* 의존성이 spike 의 모든 동역학을 결정. [Slide L5 p.18]</figcaption></figure>

## 🔁 변주

**변주 1 (오케스트라 비유).** HH 4-변수 시스템은 4 명의 음악가가 협연하는 오케스트라 — 각자 자기 시간 척도로 활동하며 *전체 spike 멜로디* 를 만든다.
- $V$ (지휘자, ms): 전체 흐름.
- $m$ (바이올린, 0.1ms): 빠르고 날카로운 melody onset.
- $h$ (첼로, ~1ms): 느리고 깊은 melody 종료.
- $n$ (피아노, ~1ms): 후반의 풍부한 화음 (재분극 + AHP).
시간 분리가 없다면 — 모두 같은 박자로 — 시끄러운 잡음만 생성. *시간 비대칭* 이 음악을 만든다.

**변주 2 (NumPy 시뮬레이션 의사코드).**
```python
# Forward Euler, dt = 0.01 ms
for t in range(N):
    I_Na = g_Na_bar * m**3 * h * (V - E_Na)
    I_K  = g_K_bar  * n**4 * (V - E_K)
    I_L  = g_L      * (V - E_L)
    dV = (I_ext - I_Na - I_K - I_L) / C_m
    dm = (m_inf(V) - m) / tau_m(V)
    dh = (h_inf(V) - h) / tau_h(V)
    dn = (n_inf(V) - n) / tau_n(V)
    V += dV * dt
    m += dm * dt
    h += dh * dt
    n += dn * dt
```
이 ~10 줄 코드가 spike 의 *모든 측정 가능 특성* (peak, AHP, refractory, frequency-current curve) 을 재현. 모델 = *압축 + 예측* 의 정수.

## ❓ 점검 Q&A

**Q:** 왜 $m$ 은 cubed ($m^3$) 인데 $h$ 는 power 1 ($h^1$) 인가? 같은 sigmoid 인데?
**A:** 분자 구조의 *직접 반영* — $Na_v$ 채널은 단일 polypeptide 의 4 도메인 중 *3 개의 voltage sensor* (도메인 I, II, III) 가 활성화 → $m^3$. *4 번째 도메인* 의 S4 는 별개의 ball-and-chain inactivation 메커니즘 → $h^1$. 즉 $m$ 과 $h$ 는 *같은 채널* 의 *다른 분자 부위* 를 표현. 이 정확히 분리가 voltage clamp + 단일 채널 측정으로 *검증* 된 분자 진실 [Slide L5 p.21].

**Q:** HH 의 ODE 가 *해석적으로* 풀릴 수 없는 이유는?
**A:** $\\alpha_x(V), \\beta_x(V)$ 가 비선형 sigmoidal — *선형 ODE 시스템이 아님*. 또한 4 변수 모두 서로 결합 ($m, h, n$ 가 $V$ 에 의존, $V$ 가 모두에 의존). *Closed-form* 해가 없음 → numerical integration 필요. 그러나 *phase plane* (2 차원 reduction, e.g. $V, n$ 만) 에서 *bifurcation analysis* 로 *질적* 동역학 (spike 가능 여부, oscillation 영역) 은 해석 가능. 정량 = numerical, 정성 = analytical.'''),

    # L8 step 2 — Rate code — Adrian 1926
    ('L8', 2, '''1️⃣ **Adrian (1926, 노벨상 1932)** 의 발견: 청개구리 근방 받침 신경 fiber 에서 spike 를 처음 측정. *자극 강도* (근육 stretch) 가 증가하면 *spike 빈도* 가 단조 증가. 이로부터 *rate code* 가설 정립 — "정보 = 시간 평균 발화율 ($\\bar r$)" [Slide L8 p.7].

2️⃣ **Rate 의 정의 (3 종류)**:
- **Spike count rate**: $r = N/T$, 시간 $T$ 내 spike 수. *정상 자극* + 충분한 $T$ ($\\gg 100$ ms) 필요. 가장 단순.
- **PSTH (peri-stimulus time histogram)**: trial 평균 spike density. *반복 가능한* 자극 필수. 자극 onset 으로부터의 시간별 발화 확률.
- **Population rate**: 동시 활성 뉴런들의 *순간 평균*. 단일 trial OK, 그러나 *해당 정보 처리 회로의 모든 뉴런* 을 동시 측정해야.

3️⃣ **Rate code 의 강점**:
- *robust*: spike timing 의 *small jitter* 에 무관 (ISI 변동 OK).
- *integrator-friendly*: downstream 뉴런이 시간 합산만으로 디코드.
- *측정 용이*: 단일 전극, 짧은 시간으로 추정 가능.

4️⃣ **Rate code 의 한계**:
- *느림*: 100 ms 이상의 *통합 시간* 필요. 200 ms 안에 결정해야 하는 행동 (e.g. 빠른 시각 인지) 에선 부적합.
- *시간 정밀도 무시*: ISI 패턴, 첫 spike 잠복기, burst 같은 정보 차원 *손실*.
- *고밀도 정보 부적합*: 채널 용량이 $\\log_2(\\text{ISI bins})$ 만큼 작아짐.

5️⃣ **현대 신경과학에서의 rate code**: 운동 신경 (firing rate ↔ 근수축 강도), V1 tuning curve (선호 자극에서 max rate), prefrontal cortex 의 working memory (rate sustained representation) 등 *여전히 핵심 도구*. 그러나 청각·hippocampal 같은 *고속 시간 정밀* 시스템에선 부족 → temporal/phase code 와 multiplex.

→ 다음: PSTH 가 어떻게 자극 시간 구조를 *trial-averaged* 로 추출하는지 — 구체적 절차.

## 🖼 Figure

<figure><img src="/figures/rate_vs_temporal_codes.svg" alt="같은 spike 개수, 다른 timing 패턴 — rate code 의 한계" /><figcaption>그림: 두 raster 가 같은 spike 개수 (= 같은 rate) 를 갖지만 *다른 ISI 패턴*. 청각 sound localization 같은 시스템은 ISI 의 sub-ms 차이를 정보로 사용 — *rate 만 보면 동일* 한 두 신호가 *다른 의미*. 이것이 rate code 가 *충분 조건이 아닌* 사례. [Slide L8 §3]</figcaption></figure>

## 🔁 변주

**변주 1 (라디오 비유).** Rate code 는 AM 라디오의 *진폭* — 신호의 강도가 정보. Temporal code 는 FM 라디오의 *주파수* — 정확한 시간 변조가 정보. 같은 carrier wave 위에서 두 정보가 *동시* 실릴 수 있다 (multiplex). 진화는 시스템에 따라 어느 쪽을 강조할지 선택 — 운동 신경은 AM (rate), 청각은 FM (timing).

**변주 2 (정보이론 관점).** Rate code 의 채널 용량:
$$C_\\text{rate} = \\log_2(N_\\text{rate}) \\approx \\log_2(r_\\text{max} T)$$
$T \\approx 100$ ms, $r_\\text{max} \\approx 200$ Hz → 최대 ~$\\log_2(20) \\approx 4.3$ bit. Temporal code:
$$C_\\text{temporal} = \\log_2(T/\\Delta t)$$
sub-ms timing precision ($\\Delta t \\approx 1$ ms) → $\\log_2(100) \\approx 6.6$ bit. 즉 *temporal* 이 *rate* 보다 ~50% 더 많은 정보 가능. 이 정량적 우위가 *왜 진화가 multiplex 를 선호하는가* 의 이유.

## ❓ 점검 Q&A

**Q:** Adrian 의 *rate code 발견* 이후 100 년 동안 *비판* 이 왜 누적되었는가?
**A:** 측정 기술의 진화가 누적을 만들었다. 초기 (1920s-60s): 단일 전극 → rate 측정만 가능 → rate code 가 자연. 1980s+: multi-electrode array, paired recording → *상호 spike timing* 관찰 가능. 1990s+: optical voltage imaging, 광유전학 → *sub-ms precision* 측정 가능. 새 측정이 새 *정보 차원* 을 노출 → temporal/phase code 가설이 검증 가능해짐. 즉 "rate code 만이 옳다" 는 1960s 의 *측정 한계의 산물* 이지 *진실의 정확한 표현* 이 아니다.

**Q:** PSTH 와 spike count rate 의 *결정적* 차이는?
**A:** PSTH 는 *시간별 동역학* 정보를 보존 — 자극 onset 후 50ms 에 peak, 200ms 에 sustained 등. Spike count rate 는 *시간 정보 모두 평균* — 같은 PSTH 를 만드는 *서로 다른* spike count rate (e.g. early peak vs late peak) 가 존재할 수 있다. PSTH = 시간 + rate, count rate = rate 만. 따라서 *temporal code 의 첫 단계* 가 PSTH 의 *시간 분해능* 활용.'''),
]


def main():
    conn = psycopg2.connect(DB_DSN)
    try:
        with conn.cursor() as cur:
            for lec, sid, narration in STUBBORN:
                cur.execute("""
                    UPDATE lecture_narrations
                    SET narration_md = %s,
                        model = 'anthropic/claude-opus-4-7|enhanced',
                        generated_at = now()
                    WHERE lecture = %s AND step_id = %s
                """, (narration, lec, sid))
                print(f'{lec}/step {sid}: hand-authored ({len(narration)} chars)')
        conn.commit()
        print(f'\nDone — 3 stubborn steps replaced.')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
