#!/usr/bin/env python3
"""
seed_exemplar_L5_v3.py — v3 of L5 summary.

v3 changes (per feedback_v3_summaries.md):
  - Stripped specific numerical anchors (single-channel conductance pS value,
    Hz firing rate ranges, patch clamp diameter reference, absolute/relative
    refractory ms values used as anchors rather than concepts)
  - Added 3 <details> toggles: 2-state Markov ODE, n^4 binomial reasoning,
    voltage-clamp dV/dt=0 logic
  - Preserved equations, symbolic relationships, narrative tone, tables, figures
"""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "backend"))
from db_pool import acquire, release  # noqa: E402


def fig(src, alt, caption):
    return (
        '<figure>\n'
        '<img src="/figures/' + src + '" alt="' + alt + '" '
        'style="max-width:100%;height:auto;display:block;margin:0.6em auto;background:#ffffff;'
        'border-radius:6px;border:1px solid var(--color-border-soft);" />\n'
        '<figcaption>' + caption + '</figcaption>\n'
        '</figure>'
    )


F1 = fig("action_potential_phases.svg",
         "Action potential phases",
         "그림 1. AP 의 4 국면. 임계 → 빠른 탈분극 (Na 유입) → Na 비활성화 + K 유출 → undershoot → 휴지 [Slide L5 p.7–9].")

F2 = fig("ion_channel_subunit.svg",
         "K_v vs Na_v topology",
         "그림 2. K_v = 4 동등 subunit → P_open = n⁴; Na_v = 단일 polypeptide 의 4 도메인 → P_open = m³h [Slide L5 p.17, p.27].")

F3 = fig("hh_gating_variables.svg",
         "m_∞, h_∞, n_∞ vs V",
         "그림 3. 게이팅 변수의 V 의존성. $m$ 가파른 활성화, $h$ 비활성화 (탈분극 시 ↓), $n$ 천천히 활성화. $h$ 와 $m$ 의 *반대 부호* 가 AP 자가 종료의 핵심.")

F4 = fig("voltage_clamp_protocol.svg",
         "Voltage clamp — V command vs I trace",
         "그림 4. Voltage clamp: V 고정 → $dV/dt = 0$ → capacitive 항 제거 → ionic 전류만 분리 [Slide L5 p.10–11]. HH 1952 의 측정 기반.")

F5 = fig("rc_charging_curve.svg",
         "First-order kinetics of n(t)",
         "그림 5. 게이팅 변수 $n(t)$ 의 1차 동역학. V 고정 시 $n(t)=n_\\infty + (n_0-n_\\infty)e^{-t/\\tau_n}$ — RC 충전과 *동일* 모양.")

F6 = fig("nernst_diffusion_balance.svg",
         "Driving force (V − E_X)",
         "그림 6. Driving force = V − E_X. AP peak 에서 $E_K$ 와 차이가 크면 강한 K 외향 전류, $E_{Na}$ 와 차이가 작아지면 Na 내향 전류 약화 — falling phase 의 동력.")


L5_SUMMARY = r"""
# L5 — Action Potential & Hodgkin-Huxley Theory

> **24-시간 마스터리.** (i) AP 4 국면을 *어떤 채널이 어떤 시점에 어떤 방향으로* 흐르는지로 설명, (ii) HH 4 변수 ODE 백지 재현, (iii) $n^4$ 와 $m^3 h$ 의 지수가 *왜 그 숫자*인지 채널 구조 (L4 §5) 로 답, (iv) voltage clamp 가 *왜* HH 측정을 가능케 했는지 한 문장 설명.

---

## §1. AP 4 국면 — 그림 1을 외우면 절반은 끝

__F1__

**한 줄 요약.** AP 는 4 국면 — 임계 → upstroke → repolarization → undershoot. 각 국면을 *어떤 채널의 게이팅* 이 만드는지 외우는 것이 L5 의 절반 [Slide L5 p.7–9].

| 국면 | V 변화 | 주도 채널 | 이온 흐름 |
|---|---|---|---|
| **휴지** | $\approx V_\text{rest}$ | leakage K | 미세 K 외향 ≈ 미세 Na 내향 |
| **Upstroke** | 임계 → 양의 값 (1 ms) | Na_v ($m\uparrow$, $h$ 아직 1) | Na 강한 내향 — *양의 피드백* |
| **Repolarization** | 양의 값 → 휴지 방향 (1 ms) | Na_v 비활성화 ($h\downarrow$) + K_v ($n\uparrow$) | Na 멈춤, K 강한 외향 |
| **Undershoot** | $V<V_\text{rest}$ (수 ms) | K_v 천천히 닫힘 | K 외향 지속 → $V\to E_K$ |

**핵심**: upstroke ↔ falling phase 전환점은 "$h$ 떨어지고 $n$ 올라온 순간". $\tau_h$ 와 $\tau_n$ 의 차이가 AP 모양 전체를 결정한다.

---

## §2. *양의 피드백* 사이클 — 왜 all-or-none 인가

**한 줄 요약.** ΔV↑ → Na_v 더 열림 → $I_\text{Na}$↑ → ΔV↑↑ 의 자기촉진 사이클. 임계 도달 시 폭주, 미달 시 leakage 가 다시 끌어내림 [Slide L5 p.7–8].

이 사이클이 임계 전위 $V_\text{thr}$ 를 넘어야 자기충족. **Spike 모양이 세포마다 동일한 이유**: 양의 피드백이 일단 시작되면 Na_v 가 거의 다 열릴 때까지 멈추지 않음 → peak 가 $E_\text{Na}$ 에 가까이 정해짐 (driving force 가 → 0 이 되는 지점). 이것이 "all-or-none" 의 분자 정체.

**음의 피드백 (느린)**: K_v 가 *지연되어* 열림 ($\tau_n > \tau_m$) — 이 지연이 시간상 분리되어 spike 가 종료 [Slide L5 p.8].

---

## §3. Voltage clamp — HH 가 *측정을 가능케 한* 트릭

__F4__

**한 줄 요약.** V 를 실험자가 고정 → 막을 유지하기 위한 전류 측정. $dV/dt=0$ → capacitive 항 제거 → *ionic 전류만* 분리 [Slide L5 p.10–11].

<details>
<summary><em>(펼쳐서 복습) 왜 voltage clamp 가 $dV/dt = 0$ 을 보장하는가</em></summary>

막 방정식 $C_m dV/dt = I_\text{ion} + I_\text{clamp}$. Voltage clamp 회로가 $V$를 목표값으로 유지하면 $dV/dt \to 0$, 따라서 $I_\text{clamp} = -I_\text{ion}$. 측정한 $I_\text{clamp}$ 가 곧 ionic 전류. Foundation 카드 §voltage clamp 원리 참조.
</details>

자유 막에서는 $V$ 와 $g(V,t)$ 가 동시에 변해 분리 불가. Voltage clamp 가 V 를 고정하면 $g(t)$ 만 시간 의존, $g(V)$ 는 step 별로 따로 측정. **Patch clamp** (Neher–Sakmann, 1991 노벨상): 기가옴 sealing 으로 단일 채널의 *계단형* opening 까지 분리할 수 있다 [Slide L5 p.10–11].

이 두 도구가 1950–1990 사이에 HH 4 변수 ODE 의 *모든 매개변수* 를 결정했다.

---

## §4. 게이팅 변수 — 1 차 동역학

__F5__

**한 줄 요약.** $n$ (또는 $m$, $h$) 는 한 voltage 에서 1차 ODE — RC charging 과 *동일 모양* [Slide L5 p.20–22].

<details>
<summary><em>(펼쳐서 복습) 2-상태 Markov ODE 가 처음이라면</em></summary>

채널 게이트가 closed(C) ↔ open(O) 두 상태를 확률로 전이. $n$ = P(open). $dn/dt = \alpha_n(1-n) - \beta_n n$. 정상상태 $n_\infty = \alpha_n/(\alpha_n+\beta_n)$, 시상수 $\tau_n = 1/(\alpha_n+\beta_n)$. 이를 표준형으로 쓰면 RC 충전과 동일 식. Foundation 카드 §2-state Markov 카드 참조.
</details>

$$\frac{dn}{dt} = \alpha_n(V)(1-n) - \beta_n(V)\,n.$$

표준화: $\tau_n = 1/(\alpha_n+\beta_n)$, $n_\infty = \alpha_n/(\alpha_n+\beta_n)$.

해 (V 고정):
$$n(t) = n_\infty(V) + [n_0 - n_\infty(V)]\,e^{-t/\tau_n(V)}.$$

**친숙함**: L3 §5 의 RC step response 와 *수학적 동일*. 막전위가 정상상태로 가는 곡선과 게이팅 변수가 $n_\infty$ 로 가는 곡선이 같은 형태.

---

## §5. $n^4$ 와 $m^3 h$ — 채널 구조에서 *직접* 유도

__F2__

**한 줄 요약.** $n^4$ = K_v 의 4 동등 subunit 모두 활성화 확률, $m^3 h$ = Na_v 의 3 활성화 게이트 + 1 비활성화 안 닫힘 [Slide L5 p.17, p.27].

L4 §5 의 채널 구조가 여기서 *지수 그대로* 나타난다.

<details>
<summary><em>(펼쳐서 복습) 독립 이항 게이트의 확률 곱이 처음이라면</em></summary>

K_v 의 4 subunit 가 *독립적으로* 각각 확률 $n$ 으로 열린다면, 4개 모두 열릴 확률 = $n \times n \times n \times n = n^4$. 독립 사건의 동시 확률은 곱. Foundation 카드 §독립 확률 곱 참조.
</details>

*K_v* (delayed rectifier): 4 개 subunit 각각 독립 게이팅 변수 $n$. 채널 열림 = $n^4$. 결과: $g_K = \bar g_K\,n^4(V-E_K)$.

*Na_v* (transient): 단일 polypeptide 4 도메인. 3 활성화 게이트 = $m$, 별도 inactivation ball = $h$. 결과: $g_\text{Na} = \bar g_\text{Na}\,m^3 h\,(V-E_\text{Na})$.

**$m$ vs $h$ 의 반대 voltage 의존성**: $m_\infty(V)$ 탈분극 시 ↑, $h_\infty(V)$ 탈분극 시 ↓. 이 비대칭이 Na_v 의 *열렸다 닫히는* 일과적 거동을 만든다.

---

## §6. HH 4 변수 ODE

__F3__

**한 줄 요약.** HH = 막 방정식 1 + 게이팅 ODE 3. 총 4 변수 결합 ODE [Slide L5 p.4, p.29].

$$C_m\,\frac{dV}{dt} = -\bar g_L(V-E_L) - \bar g_K\,n^4(V-E_K) - \bar g_\text{Na}\,m^3 h\,(V-E_\text{Na}) + I_\text{ext},$$

$$\frac{dx}{dt} = \alpha_x(V)(1-x) - \beta_x(V)\,x \quad (x=m,h,n).$$

HH 1952 의 $\alpha, \beta$ 함수꼴은 thermodynamic 형태에 *실험 데이터를 fit* 한 것이다 [Slide L5 p.23–28]. 포유류에서는 온도 차이($Q_{10}$ factor)로 속도 상수가 달라진다.

---

## §7. 비유 — AP 는 화재경보의 도미노

| 막 element | 현실 시스템 | 같은 점 (수학) | 다른 점 (생물) |
|---|---|---|---|
| **임계 ($V_\text{thr}$)** | 화재 센서 | 비선형 — 미달 무반응, 도달 폭주 | 센서 한 점; 채널 수만 개의 통계적 임계 |
| **Na_v 양의 피드백** | 도미노 | 자기촉진 사이클 | 공간 vs *V-시간* 도메인 |
| **Na_v inactivation ($h$)** | 경보 수동 락 | refractory | 락 영구; $h$ 는 수 ms 자동 회복 |
| **K_v 지연** | 스프링클러 | 지연된 음의 피드백 | 기계적 vs 분자적 |
| **Undershoot** | 과잉 냉각 | 진압 OFF 지연 | K_v 느린 비활성화 — refractory 의 본질 |

**비유 깨지는 지점**: 도미노는 복원 안 됨. AP 는 수 ms 후 복원 → 다음 spike 가능. 이 차이가 신경의 반복 발화를 가능케 한다.

---

## §8. AP 가 반복 가능한 이유 — Refractory period

__F6__

**한 줄 요약.** AP 직후 $h\approx 0$ → 다음 AP *불가능* (absolute refractory). 이후 $h$ 부분 회복 + $n$ 아직 열림 → AP *어려움* (relative refractory) [Slide L5 p.31].

| 시간 | $h$ | $n$ | 다음 AP |
|---|---|---|---|
| 직후 | ≈ 0 | ≈ peak | 불가능 (absolute) |
| 이후 수 ms | 0→회복 중 | 감소 중 | 어려움 (relative) — 더 강한 자극 필요 |
| 충분 후 | ≈ 1 | 휴지값 | 정상 |

**결과**: 신경 발화에 *상한*이 존재한다. 이 상한이 L8 의 rate code 가 다룰 신호 대역의 한계가 된다.

---

## §9. HH 의 수치 시뮬레이션 — Spike train 생성

**한 줄 요약.** HH 4 변수 ODE 를 Euler/RK4 적분 → $I_\text{ext}$ 함수로 spike train 자동 생성. f-I 곡선이 입출력 [Slide L5 p.30].

- $I_\text{ext} < I_\text{thr}$: 발화 없음.
- $I_\text{ext} \gtrsim I_\text{thr}$: 일정 빈도 spike train (stable limit cycle).
- $I_\text{ext}$ 증가 → 빈도 증가 (보통 sub-linear).

**HH 가 컴퓨테이션 신경과학의 *foundation* 인 이유**:
1. 채널 구조 (L4 §5) 에서 지수 $n^4, m^3 h$ 가 *직접* 도출.
2. 게이팅 ODE 가 voltage clamp 로 *분리 측정* 가능.
3. 4 변수 ODE 가 실제 AP 모양을 ms 단위로 재현.
4. 후속 모델 (Morris-Lecar, Wang-Buzsáki, Izhikevich) 이 모두 HH 의 축약·단순화.

---

## §10. "이 양을 어떻게 측정하는가?"

| 양 | 결정하는 실험 | 결정 못 하는 실험 (왜?) |
|---|---|---|
| **$\bar g_K$** | voltage clamp + TTX (Na 차단) → 정상상태 K 전류 | TTX 없이 — Na 가 섞임 |
| **$\bar g_\text{Na}$** | voltage clamp + TEA (K 차단) → Na peak | TEA 없이 — K 가 섞임 |
| **$\tau_n(V)$** | voltage clamp 후 $I_K$ e-folding fit | current clamp — V 가 변해 $\tau_n(V)$ 분리 안 됨 |
| **$n_\infty, m_\infty, h_\infty$** | voltage clamp $t\to\infty$ 정상상태 | transient 만 — 정상상태 미도달 |
| **단일 채널 $\gamma$** | patch clamp 단일 채널 | 전체 세포 — 평균만 |
| **$E_K, E_\text{Na}$** | reversal potential | 농도 변경 없이 — Nernst 검증 불가 |

**식별성 깨지는 전형 예**: TTX 없이 측정한 "K 전류" 는 $g_K n^4(V-E_K) + (\text{Na leak})(V-E_\text{Na})$ 의 *합* — fit ambiguity. HH 1952 가 가능한 이유는 (1) 오징어 거대 축삭으로 *공간 클램프*, (2) TTX/TEA 발견으로 K, Na 의 약리학적 분리.

---

## §11. 흔한 오해

1. **"Na 와 K 가 순서대로"** — 둘이 동시 흐르며 *상대 비율* 이 시간에 따라 변한다.
2. **"$m^3 h$ 의 3·1 은 임의 fit"** — Na_v 의 4 도메인 구조에서 직접 (3 활성화 + 1 inactivation).
3. **"AP 가 막전위 전체를 reset"** — AP 는 국소 사건 (μm). 전파는 L6 cable theory.
4. **"양의 피드백 = 무한 폭주"** — $E_\text{Na}$ 가 상한. $V\to E_\text{Na}$ 면 driving force → 0.
5. **"Refractory = 단일 값"** — absolute + relative 두 가지, 메커니즘이 다르다 ($h$ 비활성화 vs $n$ 잔류).
6. **"HH 매개변수가 보편적"** — HH 1952 는 *오징어* 저온 fit. 포유류 체온에서는 속도 상수가 더 빠르다.

---

## §12. 자기 점검 (백지 재현)

- [ ] AP 4 국면 V(t) + 각 국면의 채널·이온 방향.
- [ ] 양의 피드백 4 단계 + *왜 all-or-none* 한 문장.
- [ ] HH 4 변수 ODE 백지 ($V, m, h, n$).
- [ ] $n^4$, $m^3 h$ 의 지수가 *왜* 그 숫자 (채널 구조).
- [ ] $m_\infty, h_\infty, n_\infty$ 모양 + 부호.
- [ ] Voltage clamp 가 *왜* HH 측정을 가능케 했는지.
- [ ] TTX, TEA 약리학적 역할.
- [ ] Refractory absolute/relative 를 ($h, n$) 으로 설명.
- [ ] $n(t)$ 식 백지 + RC 와 *왜 같은지*.
- [ ] HH 가 신경과학 *foundation* 인 이유 3.
""".strip()

L5_SUMMARY = (L5_SUMMARY
              .replace("__F1__", F1)
              .replace("__F2__", F2)
              .replace("__F3__", F3)
              .replace("__F4__", F4)
              .replace("__F5__", F5)
              .replace("__F6__", F6))


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
    upsert_summary("L5", "Action Potential & Hodgkin-Huxley Theory", L5_SUMMARY)
    chars = len(L5_SUMMARY)
    print(f"L5 v3 cached: {chars} chars; figures: 6; toggles: 3; sections: 12")
