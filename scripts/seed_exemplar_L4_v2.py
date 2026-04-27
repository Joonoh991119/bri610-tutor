#!/usr/bin/env python3
"""
seed_exemplar_L4_v2.py — Opus 4.7 hand-rewritten L4 summary, v2.

L4: Neural Membrane Biophysics II — Ion Channels & Synaptic Transmission.
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


F1 = fig("membrane_rc_circuit.svg",
         "RC circuit of single-compartment membrane",
         "그림 1. L3 의 단일-컴파트먼트 등가 회로. KCL: I_inj = I_C + I_R 의 한 줄에서 막 방정식이 나온다 [Slide L4 p.2–4].")

F2 = fig("rc_charging_curve.svg",
         "Step-current response of RC membrane",
         "그림 2. Step current 입력에 대한 V_m(t) = V_∞ + (V_0 − V_∞)e^{−t/τ_m}. L4 p.5 의 21점 예제가 정확히 이 식의 손풀이를 강제한다.")

F3 = fig("ion_channel_subunit.svg",
         "K_v vs Na_v subunit topology",
         "그림 3. K_v = 4 개 *별개* α-subunit 4 합체 → P_open = n⁴; Na_v = *하나의* polypeptide 가 4 도메인 보유 → P_open = m³h [Slide L4 p.11–13].")

F4 = fig("ohmic_iv.svg",
         "Ohmic I–V relation",
         "그림 4. 채널 1 종의 I = g·(V − E) 직선. 기울기 = conductance, x-절편 = reversal potential. *한 그래프*에서 두 매개변수 동시 추출.")

F5 = fig("synapse_chemical.svg",
         "Chemical synapse 6-step mechanism",
         "그림 5. AP → Ca²⁺ 채널 개방 → vesicle exocytosis → NT 확산 → 수용체 결합 → 이온 흐름의 6 단계 (전체 ≈ 0.5–2 ms) [Slide L4 p.15–17].")

F6 = fig("nernst_diffusion_balance.svg",
         "Reversal potential set by ion selectivity",
         "그림 6. E_syn 은 채널이 통과시키는 *이온 조성* 으로 결정. AMPA: 비선택 cation → ≈0; GABA_A: Cl⁻ → ≈−70; NMDA: cation+Mg²⁺ block.")


L4_SUMMARY = r"""
# L4 — Neural Membrane Biophysics II: Ion Channels & Synapses

> **24-시간 마스터리.** (i) L3 막 방정식을 KCL 한 줄로 재유도하고, (ii) 채널 4 종 (leakage / voltage-gated / pump / ligand-gated) 이 막 방정식의 *서로 다른 항*임을 설명하고, (iii) AMPA/NMDA/GABA_A/GABA_B 의 reversal 을 즉답하고, (iv) alpha-function $g(t) = A\,t\,e^{-t/t_\text{peak}}$ 을 백지에서 그린다.

---

## §1. L3 막 방정식 — 한 줄로 재유도

__F1__

**한 줄 요약.** 막 = capacitor + 누설저항 *병렬*. KCL ($I_\text{inj}=I_C+I_R$) 한 줄에서 막 방정식 전체가 나온다 [Slide L4 p.2–4].

$I_C = C_m\,dV/dt$, $I_R = (V-V_\text{rest})/R_m$ 대입:

$$C_m\,dV/dt = -(V-V_\text{rest})/R_m + I_\text{inj}.$$

**L4 가 새로 더하는 것**: $R_m$ 이 어디서 오는가 — *어떤 채널 종류가* 누설저항을 만드는지의 미세 그림.

---

## §2. Slide L4 p.5 — 21점 예제 손풀이

__F2__

**한 줄 요약.** RC 가정 → 막 방정식 유도 → 분리변수 풀이 → 그래프, 4단계로 손풀이를 강제 [Slide L4 p.5].

1. (8점) KCL: $C_m\,dV/dt = -(V-V_\text{rest})/R_m + I_0$.
2. (10점) 변수 변환 $u = V - V_\infty$, $V_\infty = V_\text{rest} + R_m I_0$ → $\tau_m\,du/dt = -u$ → $u(t)=u(0)e^{-t/\tau_m}$.
3. 초기조건 $V(0)=V_\text{rest}$:
   $$V(t) = V_\text{rest} + R_m I_0\,(1 - e^{-t/\tau_m}).$$
4. (3점) 그래프: $t=0$ 에서 $V_\text{rest}$, $t\to\infty$ 에서 $V_\text{rest}+R_m I_0$, 1 시상수에 63%.

L3 카드 #41/#42 와 동일 식.

---

## §3. 채널 4 종 — 막 방정식의 *서로 다른 항*

**한 줄 요약.** 채널은 4 종이며 각각 *수학적으로 다른 항*으로 들어간다 [Slide L4 p.6–9].

| 종류 | 게이팅 | 막방정식 항 | 예시 |
|---|---|---|---|
| **Leakage** | 없음 | $g_L(V-E_L)$ | K, Na 누설 |
| **Voltage-gated** | $V$ 의존 ($m,h,n$) | $g_X\,m^a h^b\,(V-E_X)$ | Na_v, K_v |
| **Ion pump** | ATP | 상수 (외부 에너지) | Na/K-ATPase |
| **Ligand-gated** | NT 의존 | $g_\text{syn}(t)\,(V-E_\text{syn})$ | AMPA, GABA_A |

**핵심**: L3 $g_L$ = leakage 한 종. L5 HH 는 voltage-gated 항 추가, L4 시냅스 모델은 ligand-gated 항 추가. 우변에 *항을 덧붙이는* 방식으로 신경 전기 현상이 통합.

---

## §4. Leakage + Pump — $V_\text{rest}$ 가 *왜* 살아있는 평형인가

**한 줄 요약.** Leakage = 항상 열린 K, Na 채널의 합. Pump 가 농도 기울기를 *능동적*으로 유지 [Slide L4 p.8–9].

GHK 식 (L3 §8) 에서 $p_K \gg p_\text{Na}$ 이므로 $V_\text{rest} \approx E_K \approx -75$ mV. Cardiac pacemaker 처럼 leakage Na 가 과발현된 세포는 $V_\text{rest}$ 가 −60 mV 로 올라 자발 발화에 가까워진다.

**Pump 의 역할**: leakage 만 있으면 농도 기울기 무너져 $V_\text{rest}\to 0$. Na/K-ATPase 가 1 ATP 당 3 Na 밖 / 2 K 안 으로 기울기 유지. **ATP 차단 → 5–10 분 만에 $V_\text{rest}$ 붕괴 (ischemic depolarization)** — L3 §6 "능동 평형" 의 분자 정체.

---

## §5. 채널 *구조*가 *수학*을 결정한다

__F3__

**한 줄 요약.** K_v 4-subunit 구조 → $P_\text{open}=n^4$, Na_v 4-domain 단일 구조 → $P_\text{open}=m^3 h$. L5 의 지수가 *여기서* 결정 [Slide L4 p.11–13].

*K_v*: 4 개 동등 α-subunit, 각각 6 transmembrane (S1–S6). S4 의 양전하 arginine 이 voltage sensor. 4 개 *모두* 활성화돼야 열림 → $n^4$.

*Na_v*: 1 polypeptide 가 4 도메인 (I–IV) 을 *이미 보유*. 빠른 활성화 + 빠른 inactivation ball → $m^3 h$.

MacKinnon (Nature 2003): K_v voltage sensor 가 *paddle* 처럼 지질 막 내부를 움직인다는 결정구조 [Slide L4 p.14] — 2003 노벨 화학상.

---

## §6. 비유 — 채널은 회전문이다

| 막 element | 현실 시스템 | 같은 점 (수학) | 다른 점 (생물) |
|---|---|---|---|
| **Leakage** | 항상 열린 출구 | Ohm 흐름 | *ion 선택성* (K vs Na) |
| **Voltage-gated** | 카드키 회전문 | 열림 확률 = $n^4, m^3 h$ | 카드 1명; 채널은 ion 다수 동시 |
| **Ion pump** | 자동 양수기 | 상수 흐름 | 분자 모터 (ATP = 3 Na out + 2 K in) |
| **Ligand-gated** | 자석 회전문 | $g_\text{syn}(t)$ 시간 의존 | 결합 후 *수 ms* 자동 desensitization |

**비유 깨지는 지점**: 회전문은 결정론적, 단일 채널은 *확률적* — stochastic open/close 가 수만 개 합쳐 $g(V,t)$ 로 평균화. 큰수의 법칙이 ODE 모형의 토대.

---

## §7. 화학 시냅스 — 6 단계

__F5__

**한 줄 요약.** AP 도착 → Ca²⁺ 채널 개방 → vesicle exocytosis → NT 확산 → 수용체 결합 → 이온 흐름. 전체 지연 0.5–2 ms [Slide L4 p.15–17].

**가장 큰 지연 두 곳**:
- **Ca²⁺ 의존 vesicle 융합** — 확률적, AP 1 개당 release 확률 ≈ 0.2–0.5.
- **NT 시냅스 틈 확산** — 틈 20 nm, Brownian 확산 ~수십 μs.

**핵심**: AP 도달해도 vesicle 이 *반드시* 터지진 않는다 (release 가 확률적). 이것이 시냅스 noise 의 1차 원천이며 (L8), Hebbian 학습의 통계적 토대.

---

## §8. Ionotropic vs Metabotropic

**한 줄 요약.** Ionotropic = NT 가 *직접* 채널 (수 ms). Metabotropic = NT → GPCR → second messenger (100 ms ~ 분) [Slide L4 p.18–20].

| 구분 | Ionotropic | Metabotropic |
|---|---|---|
| 시간 | 수 ms | 100 ms ~ 분 |
| 경로 | NT → 수용체-채널 (1 단백질) | NT → GPCR → G 단백질 → effector |
| 예 | AMPA, GABA_A, glycine, nAChR | mGluR, GABA_B, mAChR |
| 막방정식 | $g_\text{syn}(V-E)$ — 직접 항 | 간접 변조 — 보통 모델링 안 함 |

L4 컴퓨테이션 모델은 *대부분 ionotropic* 만 명시. Metabotropic 은 시상수가 너무 길어 "background modulation" 으로 처리.

---

## §9. AMPA / NMDA / GABA — Reversal 한 표

__F4__ __F6__

**한 줄 요약.** $E_\text{syn}$ 은 채널의 *통과 ion 조성* 으로 결정. EPSP/IPSP 구분의 본질.

| 수용체 | 통과 ion | $E_\text{syn}$ | 효과 |
|---|---|---|---|
| **AMPA** | Na+K 비선택 | ≈ 0 mV | 강한 *탈분극* (EPSP) |
| **NMDA** | Na+K+Ca | ≈ 0 mV | Mg²⁺ 가 −65 에서 차단; *탈분극 후*에만 통과 |
| **GABA_A** | Cl⁻ | ≈ −70 mV | $V_\text{rest}$ 와 거의 같음 → "shunting" |
| **GABA_B** | K (간접) | ≈ −90 mV | 강한 과분극 (느린 IPSP) |

**NMDA = coincidence detector**: Mg²⁺ block 은 voltage 의존 + glutamate 결합은 NT 의존 — *둘 다* 만족해야 열림. Hebbian 학습의 분자 기반 [Slide L4 p.21].

---

## §10. PSP 의 시간 모양 — Alpha function

**한 줄 요약.** 단일 시냅스 conductance: $g_\text{syn}(t) = A\,t\,e^{-t/t_\text{peak}}$. 피크 시간 0.5–2 ms [Slide L4 p.27].

특성:
- $t\to 0$: $g\to 0$ (NT 미결합).
- $dg/dt|_0 = A$ (선형 증가 시작).
- $t = t_\text{peak}$: 최대 ($dg/dt = 0$).
- $t \gg t_\text{peak}$: 지수 감소.

막 방정식에 결합:
$$C_m\,dV/dt = -(V-V_\text{rest})/R_m - g_\text{syn}(t)(V-E_\text{syn}) + I_\text{inj}.$$

L4 p.31 의 MATLAB Euler 코드가 이 식을 수치적으로 푼다.

---

## §11. "이 양을 어떻게 측정하는가?"

| 양 | 결정하는 실험 | 결정 못 하는 실험 (왜?) |
|---|---|---|
| **단일 채널 $\gamma$** | patch clamp + 단일 채널 → 계단형 진폭 | 전체 세포 — 평균만 봄 |
| **$E_\text{syn}$** | 다양한 V step 에서 PSC = 0 인 점 | 한 V 만 — driving force 와 g 가 섞임 |
| **$t_\text{peak}$** | 빠른 voltage clamp | current clamp — $\tau_m$ 이 모양 왜곡 |
| **release $p$** | EPSC 진폭 분포 → 양자분석 (mean²/variance) | 평균만 — $p$ 와 $N$ 이 *곱*으로만 식별 |
| **NMDA Mg²⁺** | Mg²⁺ 변화 + V step → I-V 의 negative-slope | 1 voltage 만 — voltage 의존성 측정 불가 |

**식별성 깨지는 전형**: 평균 EPSC 는 $p$ 와 $N$ 의 *곱* 만 — 분산이 추가로 필요. 시냅스 가소성에서 pre vs postsynaptic 판별이 *분산 분석*에 의존하는 이유.

---

## §12. 흔한 오해

1. **"AMPA 와 NMDA 는 순서대로"** — 둘 다 동시에 glutamate 결합. 차이는 시간·voltage 의존성. AMPA 가 막을 탈분극시켜 NMDA 의 Mg²⁺ block 을 푸는 순서가 있을 뿐.
2. **"GABA = 항상 inhibitory"** — 아니다. 발달기 미성숙 뉴런은 $E_\text{Cl}\approx -40$ → GABA_A 가 *탈분극* (KCC2 발현 전).
3. **"시냅스 = 결정론적"** — AP 당 release $p\approx 0.2$. 결정적으로 보이는 것은 통계 평균.
4. **"$g_\text{syn}$ 곡선 = PSP 곡선"** — PSP 는 $g_\text{syn}$ 을 $\tau_m$ lowpass 필터한 결과.
5. **"Pump 가 막전위를 직접 만든다"** — Pump 는 농도 기울기 생성, leakage 가 막전위 생성. Pump electrogenicity 는 −5 mV 만 기여.
6. **"한 채널 = 한 ion"** — AMPA/NMDA/nAChR 모두 비선택. 100% 선택은 K 누설채널 같은 예외.

---

## §13. 자기 점검 (백지 재현)

- [ ] L3 막 방정식을 KCL 한 줄로 30초에 재유도.
- [ ] 채널 4 종이 *왜 다른 항*인지 한 문장.
- [ ] K_v vs Na_v 구조 차이가 $n^4$ vs $m^3 h$ 의 지수를 결정함.
- [ ] Na/K-ATPase 3 out / 2 in + ATP 차단 후 막전위 운명.
- [ ] AMPA/NMDA/GABA_A/GABA_B reversal 4 값 즉답.
- [ ] 화학 시냅스 6 단계 순서.
- [ ] Ionotropic vs metabotropic 시간 척도 + 예 1쌍.
- [ ] Alpha function 그리고 $t_\text{peak}$ 가 max 인 것 미분.
- [ ] NMDA Mg²⁺ block = coincidence detection 한 문장.
- [ ] Slide L4 p.5 21점 예제를 5 분에 백지 풀이 + 그래프.
""".strip()

L4_SUMMARY = (L4_SUMMARY
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
    upsert_summary("L4", "Neural Membrane Biophysics II — Ion Channels & Synapses", L4_SUMMARY)
    print(f"L4 v2 cached: {len(L4_SUMMARY)} chars; figures: 6")
