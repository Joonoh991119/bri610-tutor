#!/usr/bin/env python3
"""
seed_exemplar_L3_v2.py — Opus 4.7 hand-rewritten L3 summary, v2.

Rewrite for readability + inline figures + plain-language jargon.
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


# Figure helpers
F1 = fig("bilayer_capacitor.svg",
         "Lipid bilayer as parallel-plate capacitor",
         "그림 1. Lipid bilayer 의 hydrophobic core 가 ion 통과를 거의 막고, 양쪽 surface 에 정렬된 전하가 평행판 capacitor 를 형성한다.")

F2 = fig("rc_charging_curve.svg",
         "RC charging curve",
         "그림 2. Step current 입력에 대한 막의 응답. t=0+ 에서 기울기는 I_inj/C_m (capacitor 가 모든 전류를 받음). t=τ_m 에서 정상상태까지의 거리의 63% 를 채운다. t→∞ 에서 누설이 입력과 균형 → V_∞.")

F3 = fig("membrane_rc_circuit.svg",
         "Equivalent RC circuit of a membrane",
         "그림 3. 단일-컴파트먼트 passive 막의 등가 회로. KCL: I_inj = I_C + I_R, 즉 외부에서 들어온 전류는 capacitor 충전과 leak 누설로 갈라진다.")

F4 = fig("nernst_diffusion_balance.svg",
         "Nernst — diffusional vs electrical force balance",
         "그림 4. Nernst 평형의 본질: 농도 기울기로 인한 확산력 (K+ 을 밖으로) 과 막 양쪽 전위차로 인한 전기력 (음전하 cytoplasm 이 K+ 을 안으로) 이 정확히 균형.")

F5 = fig("ghk_weighted_log.svg",
         "GHK — log-domain weighted average",
         "그림 5. Goldman–Hodgkin–Katz 식은 Na/K/Cl 각 이온의 평형 전위를 log-도메인 가중평균으로 결합. 가중치는 각 이온의 투과도 p_X. 휴지 상태에서 p_K ≫ p_Na 이므로 V_m ≈ E_K.")


L3_SUMMARY = r"""
# L3 — Neural Membrane Biophysics I

> **24-시간 마스터리 목표.** 이 핸드아웃을 다 읽은 직후 학생은 (i) 막 방정식을 KCL + Ohm + capacitor 정의로부터 30초 안에 적고, (ii) Nernst 식을 Boltzmann 평형 한 줄로 유도하고, (iii) "왜 시상수 τ_m 이 세포 크기 무관한가" 를 한 문장으로 설명할 수 있어야 한다.

---

## §1. 막은 *얇은 콘덴서 종이* 다

__F1__

**한 줄 요약.** Lipid bilayer 는 ion 이 통과하지 못하는 *절연체* (3–4 nm 두께), 그 양쪽 표면에 분리된 전하가 평행판 capacitor 를 만든다 [Slide L3 p.13].

이 사실 하나로 "왜 막에 전압이 존재하는가" 가 설명된다. Capacitor 에 전하 $Q$ 가 분리되면 그 사이에 전압 $V = Q/C$ 가 자동으로 생긴다. 신경막의 두께가 *매우 작기* 때문에 단위 면적당 정전용량 $C_m$ 이 극단적으로 크고, 따라서 *작은* 전하 불균형으로도 *큰* 막전위 (-65 mV) 를 만들 수 있다.

전형값: $C_m \approx 1\,\mu\mathrm{F/cm}^2$ — *모든 동물 세포* 에서 거의 상수. Bilayer 두께가 진화적으로 보존되었기 때문이다 [Slide L3 p.18].

---

## §2. 전류는 막전위가 *변할 때만* 흐른다

**한 줄 요약.** $Q = CV$ 양변을 시간 미분하면 $I_C = C_m \, dV/dt$ — capacitor 를 흐르는 전류는 *전압 변화 속도* 에 비례.

직관적으로: capacitor 양쪽에 쌓인 전하가 *같은 만큼* 유지되면 (정상상태) 들어가는 전하와 나오는 전하가 균형 → 알짜 전류 0. 막전위가 *변할 때만* capacitor 가 "전류를 먹는다."

*정량적 결과* (꼭 외울 것): $C_m = 1\,\mathrm{nF}$ 뉴런에 $1\,\mathrm{nA}$ 흘리면 $dV/dt = 1\,\mathrm{mV/ms}$ [Slide L3 p.20]. 이 한 숫자가 voltage-clamp 실험의 시간 분해능, EPSP 모양, 그리고 spike 발화 임계 시간을 모두 결정한다.

---

## §3. 막 저항 $R_m$ — *열린 채널들* 의 합산 저항

**한 줄 요약.** 휴지 상태에서 *열려 있는* ion channel 들이 leak 통로를 만들고, 그 합산 conductance 의 역수가 $R_m$.

$R_m$ 은 $C_m$ 과 달리 *세포마다 극단적으로 다르다*. 같은 종류의 뉴런이라도 K leak channel 발현량에 따라 10×–1000× 차이. 이 변동성이 "같은 입력에 다르게 반응하는 세포 종류" 의 본질 [Slide L3 p.22].

전형값: 슬라이드 L3 p.22 — $R_m \approx 1\,\mathrm{M}\Omega\cdot\mathrm{mm}^2$ (specific membrane resistance, 단위에 *주의* — `mm²` 이지 `cm²` 가 아니다). $1\,\mathrm{cm}^2 = 100\,\mathrm{mm}^2$ 이므로 면적 단위 환산 시 $\approx 10\,\mathrm{k}\Omega\cdot\mathrm{cm}^2$. 세포마다 약 1–100 $\mathrm{k}\Omega\cdot\mathrm{cm}^2$ 범위.

---

## §3.5. *왜* 휴지 막전위는 $E_K$ 와 같지 않은가? — Na 누설의 효과

**한 줄 요약.** 휴지 막에 K 채널만 있으면 $V_\mathrm{rest} = E_K$. 하지만 *작지만 0이 아닌* Na 투과도가 막전위를 $E_K$ 와 $E_{Na}$ 사이로 끌어당긴다.

각 ion 채널의 conductance $g_X$ 는 *병렬* 로 연결되어 있다. KCL 정상상태:
$$g_K (V_\infty - E_K) + g_{Na}(V_\infty - E_{Na}) = 0.$$

$V_\infty$ 에 대해 풀면 *conductance-가중 평균*:
$$V_\infty = \frac{g_K E_K + g_{Na} E_{Na}}{g_K + g_{Na}}.$$

휴지에서 $g_K \gg g_{Na}$ (K leak 채널 우세, $g_K / g_{Na} \approx 25$) 이므로 $V_\infty$ 는 $E_K = -83$ mV 에서 약간만 양의 방향으로 끌려 최종적으로 $\approx -65$ mV 에 안착. 이 *15 mV의 차이* 가 Na 누설의 직접적 결과 [Slide L3 p.30].

이 conductance-가중 평균식은 §8 의 GHK 식의 *간단한 버전* — GHK 는 $V$ 의존 conductance 까지 포함한 *log-도메인* 일반화이다.

---

## §3.6. 휴지 = 능동적 평형, 죽은 게 아니다

**한 줄 요약.** $V_\mathrm{rest}$ 는 *수동* 평형이 아니다. Na/K ATPase 가 ATP 를 소비해 농도 기울기를 *유지*해주기에 비로소 Nernst 평형이 가능하다.

뉴런의 *총 ATP 소비의 약 절반* 이 Na/K ATPase 에 쓰인다 — 막을 통한 잔여 누설 (Na 안쪽 / K 바깥쪽으로의 끊임없는 흐름) 을 *능동적* 으로 되돌리기 위해. 펌프가 멈추면 (저산소·허혈 상태) 농도 기울기가 무너지고 $V_\mathrm{rest}$ 는 0 으로 향한다 (\"ischemic depolarization\", 뇌졸중에서 관찰).

이것이 \"세포가 살아 있다\" 의 정량적 정의: *전기화학 평형이 능동적으로 유지된다*.

---

## §4. 막 시상수 $\tau_m = R_m C_m$ — 응답 속도의 척도

__F2__

**한 줄 요약.** $\tau_m = R_m C_m$ 은 막이 *변화에 응답하는 시간 척도*. 1 시간상수 후 $V$ 는 정상상태까지 거리의 63% 를 채운다.

*핵심 수학적 사실*: $C_m$ 과 $R_m$ 모두 단위 면적당 양의 *specific* 형태로 정의되면, 세포 면적 $A$ 가 곱과 나누기로 *상쇄* — $\tau_m$ 은 면적 무관 [Slide L3 p.23]. 거대한 운동 뉴런과 작은 interneuron 이 같은 $\tau_m$ 을 가질 수 있다.

전형값: 10–100 ms.

---

## §5. 막 방정식 — 30초 유도

__F3__

**한 줄 요약.** 키르히호프 전류 법칙 (KCL: 한 노드로 들어가는 전류 합 = 0) 을 그림 3 의 회로에 쓰면 막 방정식이 *유도*된다.

$$I_{inj} = \underbrace{C_m \frac{dV}{dt}}_{\text{capacitor (§2)}} + \underbrace{\frac{V - V_{rest}}{R_m}}_{\text{leak — Ohm 의 법칙}}.$$

정리:

$$\boxed{C_m \frac{dV}{dt} = -\frac{V - V_{rest}}{R_m} + I_{inj}.}$$

양변에 $R_m$ 곱하고 $\tau_m = R_m C_m$ 로 정규화:

$$\tau_m \frac{dV}{dt} = -(V - V_{rest}) + R_m I_{inj}.$$

*Step input 의 폐형 해*: $V(t) = V_\infty + (V_0 - V_\infty)\,e^{-t/\tau_m}$, 단 $V_\infty = V_{rest} + R_m I_{inj}$. 분리변수법 + 변수 변환 $u = V - V_\infty$ 로 5분 안에 풀 수 있다 (foundation 카드 #41/#42 에 단계별).

---

## §6. *현실 시스템 비유* — 막은 댐 + 수문이다

| 막 element | 현실 시스템 | 무엇이 같은가 (수학) | 무엇이 다른가 (생물) |
|---|---|---|---|
| **$C_m$** (capacitor) | 댐 자체 (수위 = 전압) | 충전된 양 ∝ 전위차 | 댐은 단방향 (수위↓만), 막은 양방향 (V 가 음수도 가능) |
| **$1/R_m$** (conductance) | 수문 (열린 정도) | 흐름 = 압력 / 저항 (Ohm) | 수문은 한 종류, ion channel 은 *수십 가지 다른 ion 별* 채널이 동시에 |
| **$\tau_m = R_m C_m$** | 댐 응답 시간 | 1차 lowpass — 빠른 변화 평탄화 | 댐 응답은 *분 단위*, $\tau_m$ 은 *밀리초 단위* (속도 차이 10⁵) |
| **$V_{rest}$** | 댐 자연 수위 | 평형점 = 입출력 균형 | 댐 평형은 *수동* (강 유량), $V_{rest}$ 는 *능동* (Na/K ATPase 가 ATP 로 농도 기울기 유지) |

**비유가 깨지는 지점**: 댐은 1방향 흐름과 *수동* 평형. 막은 양방향 흐름과 *능동* 평형 — 이 차이가 "세포가 *살아 있다*" 는 표시. ATP 차단 시 막은 댐이 *터지듯이* 무너진다 (ischemic depolarization).

---

## §7. Nernst 평형 — Boltzmann 한 줄 유도

__F4__

**한 줄 요약.** 화학 퍼텐셜 $\mu = \mu^0 + RT \ln C + zF\phi$ 가 막 양쪽 동일 ($\mu_o = \mu_i$) 이라는 평형 조건에서 막전위가 자동으로 결정된다.

*유도 (3 단계)* — [Slide L3 p.27–29]:

1. 막 양쪽 동일 화학 퍼텐셜:
   $$RT \ln[X]_o + zF\phi_o = RT \ln[X]_i + zF\phi_i.$$

2. 양변에서 $\mu^0$ (이온 종류만의 함수) 가 상쇄, 정리:
   $$RT \ln \frac{[X]_o}{[X]_i} = zF (\phi_i - \phi_o).$$

3. 정의 $E_X \equiv \phi_i - \phi_o$ (안 - 바깥):
   $$\boxed{E_X = \frac{RT}{zF} \ln \frac{[X]_o}{[X]_i}.}$$

*수치* (체온 310 K):
- $K^+$: $[K]_o = 5.5$ mM / $[K]_i = 150$ mM → $E_K \approx -83$ mV.
- $Na^+$: $[Na]_o = 150$ / $[Na]_i = 15$ → $E_{Na} \approx +58$ mV.

휴지 상태 막은 K leak channel 이 dominant 이므로 $V_{rest} \approx E_K \approx -80$ mV — 이것이 "왜 휴지 막이 음수인가" 의 답.

---

## §8. GHK — Nernst 의 다이온 일반화

__F5__

**한 줄 요약.** 다이온 막에서 net current = 0 인 막전위는 GHK 식으로 결정 — Nernst 의 *log-domain 가중평균*.

$$V_m = \frac{RT}{F} \ln \frac{p_K [K]_o + p_{Na}[Na]_o + p_{Cl}[Cl]_i}{p_K[K]_i + p_{Na}[Na]_i + p_{Cl}[Cl]_o}.$$

[Slide L3 p.30]. *주의*: GHK 는 Nernst 들의 *산술* 평균이 아니라 *log-도메인 결합*. 휴지에서 $p_K$ 가 dominant 이므로 $V_m$ 이 $E_K$ 에 가까이; 자극 받으면 $p_{Na}$ 증가 → $V_m$ 이 $E_{Na}$ 쪽으로 끌려간다. 이것이 *AP 의 양의 피드백 사이클* 의 출발.

---

## §9. "이 양을 어떻게 측정하는가?" — 실험 디자인 점검

식별성(identifiability) 이라는 어려운 단어 대신, *훨씬 더 유용한 질문*: "내가 어떤 실험을 하면 이 양을 *결정* 할 수 있는가?" 그리고 "어떤 실험에서는 이 양이 *나타나지 않는가*?"

| 양 | 결정하는 실험 | *결정 못 하는* 실험 (왜?) |
|---|---|---|
| **$C_m$** | step current 입력 후 $dV/dt$ 측정 → $I/(\dot V)$ | DC 측정 (변화 없음 → capacitor 는 보이지 않음). $C_m$ 은 *변화* 신호에서만 드러남 |
| **$R_m$** | sub-threshold step current 의 *정상상태* 전압 측정 → $\Delta V / I$ | 매우 짧은 transient (10 μs) — 정상상태 도달 안 함, capacitor 가 dominant |
| **$\tau_m$** | step current 후 e-folding 시간 직접 fit | 단일 1차 ODE 가정 깨지면 (dendrite 의 multi-time-constant) 단일 fit 은 *평균값* 만 줌 |
| **$E_X$ (예: $E_K$)** | reversal potential — net current = 0 인 voltage step | 다른 ion 도 흐르면 (e.g., Na 누설) 측정한 reversal 이 *진짜 $E_X$* 가 아니라 GHK 결과 |
| **$V_{rest}$** | 자극 없는 silent 뉴런의 current-clamp at zero | 시냅스 입력 활발하면 fluctuation 추가 — 평균값만 신뢰 가능 |

"식별성이 깨진다" 는 한 마디로: *측정 가능한 모든 데이터에 의해 동일하게 설명되는 다른 매개변수 조합이 존재* 한다는 뜻.

예: cable equation 의 $R_m$ 과 $R_i$ 는 정상상태 V(x) 만으로는 따로 결정 불가능 (둘의 비율 $R_m/R_i$ 만 식별됨) — 이 사실이 L6 cable theory 의 실험 디자인을 *time-dependent* 로 가게 만든다.

---

## §10. 흔한 오해와 시험 함정

1. **"막 전위가 점프할 수 있다"** — 아니다. Capacitor 양단 전압은 *연속*. 점프하는 것은 $dV/dt$ 만이다 (charge conservation).
2. **"$V_{rest}$ 는 고유 상수"** — 아니다. Na/K ATPase 가 *능동적으로* 농도 기울기 유지. ATP 끊기면 $V_{rest}$ 가 0 으로 무너진다.
3. **"$\tau_m$ 큰 세포 = 더 느림"** — 아니다. $\tau_m$ 은 *세포 크기 무관*. specific $R_m$ 만 의존.
4. **"GHK = Nernst 들의 평균"** — 아니다. *log-도메인* 가중평균. 산술평균 결과와 일반적으로 *다르다*.
5. **"휴지 막이 음수인 이유는 K 가 양성이라서"** — 너무 단순. $[K]_i > [K]_o$ 농도 기울기가 K 가 *밖으로 나가려는* 추진력을 만들고, 그 결과 cytoplasm 에 음전하가 남는다.

---

## §11. 자기 점검 — 백지에서 재현 가능?

- [ ] $C_m, R_m, \tau_m$ 을 SI 단위까지 1분 안에 적는다.
- [ ] $\tau_m$ 이 *세포 크기 무관* 한 이유를 30초 안에 설명한다.
- [ ] $I_C = C \, dV/dt$ 를 $Q = CV$ 로부터 1줄로 유도한다.
- [ ] Nernst 식을 Boltzmann 평형으로부터 5분 안에 유도한다.
- [ ] $E_K = -83$, $E_{Na} = +58$ mV 표준값을 즉시 답한다.
- [ ] GHK 가 Nernst 평균이 *아닌 이유* 를 한 문장으로 설명한다.
- [ ] Step current 응답 $V(t) = V_\infty + (V_0 - V_\infty)e^{-t/\tau_m}$ 을 백지에서 유도한다.
- [ ] $C_m$ 을 결정하기 위해 어떤 실험이 필요한지 한 문장으로 설명한다.
""".strip()

# Inject figures
L3_SUMMARY = (L3_SUMMARY
              .replace("__F1__", F1)
              .replace("__F2__", F2)
              .replace("__F3__", F3)
              .replace("__F4__", F4)
              .replace("__F5__", F5))


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
    upsert_summary("L3", "Neural Membrane Biophysics I", L3_SUMMARY)
    print(f"L3 v2 cached: {len(L3_SUMMARY)} chars; figures: 5")
