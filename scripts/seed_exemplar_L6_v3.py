#!/usr/bin/env python3
"""
seed_exemplar_L6_v3.py — v3 of L6 summary.

v3 changes (per feedback_v3_summaries.md):
  - Stripped specific numerical anchors (lambda ~0.5 mm example values with
    specific R_m/R_i plugged in, AP speed numeric anchors used as calibration,
    compartment count arithmetic 1mm/500um→20)
  - Added 3 <details> toggles: cable KCL setup, spatial steady-state separation,
    length constant derivation
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


F1 = fig("membrane_rc_circuit.svg",
         "Single-compartment passive membrane",
         "그림 1. L3 의 단일 컴파트먼트는 *모든 위치에서 V 가 동일* 하다고 가정. 길쭉한 dendrite/axon 에서는 이 가정이 깨진다 — 그 한계에서 cable theory 가 출발한다.")

F2 = fig("cable_decay_spatial.svg",
         "Steady-state V(x) along a passive cable",
         "그림 2. Semi-infinite cable 에 x=0 에서 일정 전류 주입 시 정상상태 막전위. V(x) = V₀ · exp(-x/λ) — 거리 λ 마다 1/e ≈ 37% 로 감쇠. 이 *공간 감쇠* 가 dendritic input 의 attenuation 본질.")

F3 = fig("ap_propagation_unmyelinated.svg",
         "Unmyelinated axon — AP propagation as a wave",
         "그림 3. Unmyelinated axon 의 AP 전파. 한 지점의 depolarization 이 *cable current* 로 옆 지점을 임계 위로 끌어올림 → Na 채널 재점화 → 새 AP. 결과: AP 가 *감쇠 없이* 일정 진폭으로 전파 (passive 감쇠 ≠ AP).")

F4 = fig("ap_propagation_myelinated.svg",
         "Myelinated axon — saltatory conduction",
         "그림 4. Myelin 으로 절연된 internode 는 capacitor 가 *얇아지고* leak 이 줄어든 cable. AP 가 Node of Ranvier 에서만 재점화 — *건너뛰는* (saltatory) 전파.")

F5 = fig("ohmic_iv.svg",
         "Ohmic ion current — leak channel",
         "그림 5. Cable 의 *radial* leak 은 단위 길이당 g_m (V - V_rest) 의 ohmic 전류. 이 항이 cable PDE 의 dissipation 을 만든다 — 즉 V 가 무한히 멀리 가지 못하게 막는 *유출*.")


L6_SUMMARY = r"""
# L6 — Cable Theory & Action Potential Propagation

> **24-시간 마스터리 목표.** (i) cable PDE 를 KCL + Ohm + capacitor 로 30초 안에 유도하고, (ii) 정상상태 해 $V(x) = V_0\,e^{-x/\lambda}$ 와 $\lambda = \sqrt{d R_m / 4 R_i}$ 의 *물리적 의미* 를 설명하고, (iii) unmyelinated 와 myelinated AP 속도가 *왜 크게 차이나는지* 두 메커니즘으로 답할 수 있어야 한다.

---

## §1. 단일 컴파트먼트의 한계 — 왜 cable theory 가 필요한가

__F1__

**한 줄 요약.** L3 의 단일 컴파트먼트 모형은 "세포 전체가 동일한 V" 라고 가정. *둥근 soma* 에서는 OK 지만 *길쭉한 dendrite/axon* 에서는 즉시 깨진다 [Slide L6 p.2–3].

피라미드 뉴런의 apical dendrite 는 길이 1 mm, 직경 1 μm. 한쪽 끝 시냅스 입력이 soma 까지 *attenuated + delayed* 로 도착 — 그 정도가 cable theory 의 답이다. 본질: cytoplasm 자체가 axial 저항 $R_i$ 를 가지므로 *옴 강하* 누적 → 먼 점은 덜 충전됨.

---

## §2. Cable PDE — 3-step 유도

__F2__

**한 줄 요약.** 길이 dx 의 cable 조각에 KCL 을 적용하면 cable PDE 가 *유도*된다.

<details>
<summary><em>(펼쳐서 복습) cable 조각의 KCL 설정이 처음이라면</em></summary>

위치 $x$ 에서 $dx$ 조각을 분리하면: 왼쪽에서 들어오는 axial 전류 $I_a(x)$, 오른쪽으로 나가는 $I_a(x+dx)$, 막을 통해 나가는 $i_m\,dx$. KCL: $I_a(x) - I_a(x+dx) = i_m\,dx$, 좌변 = $-(\partial I_a/\partial x)\,dx$. Foundation 카드 §KCL on a segment 참조.
</details>

*유도 (3 단계)*:

**Step 1 — 축 방향 전류 (axial current):** 위치 x 에서의 cytoplasm 전류는 옴의 법칙으로 $I_a(x) = -\frac{1}{r_i} \frac{\partial V}{\partial x}$, 여기서 $r_i$ = 단위 길이당 axial resistance (Ω/cm).

**Step 2 — 단위 길이당 막 전류 (KCL):** dx 조각의 막에서 빠져나가는 전류 = 들어오는 axial 전류와 나가는 axial 전류의 *차이*:
$$i_m(x,t) = -\frac{\partial I_a}{\partial x} = \frac{1}{r_i} \frac{\partial^2 V}{\partial x^2}.$$

**Step 3 — 막의 구성:** 단위 길이당 $i_m = c_m \partial V/\partial t + (V-V_{rest})/r_m$ (capacitor + leak). 두 표현을 같다고 놓으면 **Cable PDE**:
$$\boxed{\tau_m \frac{\partial V}{\partial t} = \lambda^2 \frac{\partial^2 V}{\partial x^2} - (V - V_{rest}) + r_m i_{inj}(x,t),}$$

단 $\tau_m = r_m c_m$, $\lambda = \sqrt{r_m / r_i}$ [Slide L6 p.8–10]. L3 ODE 대비 새 항은 $\lambda^2 \partial^2 V/\partial x^2$ 하나 — *공간 확산*. Cable = "L3 막 + Fick 확산".

---

## §3. λ 의 의미 — *얼마나 멀리 신호가 가는가*

**한 줄 요약.** 공간 상수 $\lambda$ 는 정상상태에서 막전위가 1/e (≈37%) 로 감쇠하는 거리.

직경 $d$, specific resistances 로 환산:
$$\lambda = \sqrt{\frac{d \cdot R_m}{4 R_i}}.$$

*직관*: 굵을수록 ($d\uparrow$) axial 저항이 *단면적에 반비례* 로 줄어 멀리 간다. 막 저항 ($R_m\uparrow$) 이 클수록 옆으로 새지 않아 멀리 간다. Cytoplasm 저항 ($R_i\uparrow$) 이 크면 가까이 못 간다. 세포 종류와 막 채널 발현에 따라 $\lambda$ 는 수십 μm 에서 수 mm 에 걸쳐 크게 다르다.

---

## §4. 정상상태 해 — $V(x) = V_0\,e^{-x/\lambda}$

**한 줄 요약.** $i_{inj}$ 가 시간 무관, semi-infinite cable, x=0 에 일정 전류 주입 시 정상상태 ($\partial V/\partial t = 0$) 해는 *지수 감쇠* [Slide L6 p.10–12].

<details>
<summary><em>(펼쳐서 복습) 공간 ODE $\lambda^2\,d^2u/dx^2 = u$ 의 일반해가 처음이라면</em></summary>

$u = V - V_\text{rest}$ 로 치환하면 $\lambda^2 u'' = u$, 특성방정식 $\lambda^2 k^2 = 1$ → $k = \pm 1/\lambda$. 일반해 $u = Ae^{x/\lambda} + Be^{-x/\lambda}$. $x\to\infty$ 에서 $u\to 0$ 조건 → $A=0$, $u = Be^{-x/\lambda}$. Foundation 카드 §2차 ODE 지수 해 참조.
</details>

PDE 에서 시간 미분 0:
$$\lambda^2 \frac{d^2 V}{dx^2} = V - V_{rest}.$$

경계조건 (x=0 에서 $V = V_0$, $x \to \infty$ 에서 $V \to V_{rest}$) 의 해:
$$\boxed{V(x) - V_{rest} = V_0 \, e^{-x/\lambda}.}$$

**실험적 의미.** Dendrite 끝에 EPSP 가 들어와도 soma 에 도달할 때까지 *지수적으로 감쇠*. 거리 $\lambda$ 마다 37%, $2\lambda$ 마다 14% 로 줄어든다. *멀리 있는 시냅스 입력은 단순 합산으로는 spike 를 만들기 어려움* — 이것이 active dendrite (NMDA spike, Ca spike) 의 진화적 동기.

---

## §5. *현실 시스템 비유* — Cable 은 *새는 정원 호스* 다

| Cable element | 현실 시스템 | 무엇이 같은가 (수학) | 무엇이 다른가 (생물) |
|---|---|---|---|
| **$r_i$** (axial 저항) | 호스 내부 좁은 직경 | 압력차 / 단위 길이당 흐름 (옴) | 호스는 단순 유체, cable 은 ion 별 *선택적* 흐름 |
| **$r_m$** (막 저항) | 호스 벽의 작은 구멍들 | 새는 양 ∝ 압력 / 저항 | 막의 구멍 (channel) 은 *전압-게이트* — 호스 구멍은 정적 |
| **$\lambda$** (공간 상수) | "물이 새기 전 갈 수 있는 거리" | $\sqrt{1/(\text{누설/축저항})}$ | 호스는 *직경 굵기에 선형* 의존, cable 은 $\sqrt{d}$ |
| **$i_{inj}$** (주입 전류) | 호스 입구 펌프 | 입력의 시공간 분포 | 펌프는 단방향, 시냅스는 양극 (흥분/억제) |

**비유가 깨지는 지점.** 호스의 누설은 *완전히 수동* — 압력차 0 이면 흐름 0. 막의 leak 은 *상시* (Na/K ATPase 가 농도 기울기를 유지하는 한 항상 누출). 더 결정적으로 — 호스에는 *AP 같은 능동 재점화* 가 없다. AP 는 cable 위에서 *자기 자신을 재생* 하는 비선형 파동 (§6).

---

## §6. AP 전파 — *수동 cable 위의 능동 파동*

__F3__

<details>
<summary><em>(펼쳐서 복습) cable 위 행진파의 속도가 처음이라면</em></summary>

Cable 의 행진파 속도 $v \propto \sqrt{d/(\tau_m r_i)}$. 직경 $d$ 를 4배 늘리면 속도가 2배. Myelin 은 $c_m$ (= $\tau_m$의 일부) 을 줄이고 $r_m$ 을 늘려 같은 $d$ 에서 속도를 크게 높인다. Foundation 카드 §cable 행진파 속도 참조.
</details>

**한 줄 요약.** AP 는 cable PDE 에 *전압 의존 Na/K conductance* (L5 HH) 가 추가된 비선형 PDE 의 *행진파* 해 [Slide L6 p.15–18].

*전파 메커니즘* (3 단계): (1) $x_0$ 에서 AP 발화 → V 가 양의 큰 값으로. (2) Cable 전류가 $x_0+\Delta x$ 의 막을 *임계 위로* depolarize. (3) Voltage-gated Na 채널 열림 → 새 AP. 반복.

**핵심 통찰.** 전파되는 것은 "전압 자체" 가 아니라 *AP 발화 사건*. 매 위치에서 새 AP 가 *재생* 되므로 진폭 감쇠 없이 끝까지 도달. Unmyelinated axon 의 전도 속도는 직경과 막 특성에 따라 결정된다 — 좌골신경처럼 긴 경로에서는 이 속도가 행동 반응 시간의 하한이 된다.

---

## §7. Saltatory conduction — 진화의 해법

__F4__

**한 줄 요약.** Myelin 은 internode 의 capacitance 를 줄이고 leak 을 막아 *수동 cable 전파* 를 빠르게 하고, AP 재점화는 Node of Ranvier 에서만 일어난다 [Slide L6 p.21–22].

**왜 빠른가?** 두 효과: (1) Internode 의 $c_m$ 이 myelin 두께에 반비례 → 충전할 전하 적음 → $\tau_m$ 짧음. (2) Internode 의 $r_m$ 증가 → $\lambda$ 길어짐 → cable 전류가 멀리 도달. AP 가 internode 를 *전선처럼* 빠르게 통과하고 다음 Node 에서 *재점화*.

*포유류 특성*: 얇은 axon + myelin 조합으로 같은 단면적 내에서 더 많은 빠른 axon 을 패킹할 수 있다. Myelin 이 없는 동일 직경의 axon 보다 전도 속도가 한 차수 이상 빠르다.

---

## §8. Multi-compartment 모형 — 수치 해법

**한 줄 요약.** Cable PDE 의 *해석해* 는 단순 cable 만 가능. 분지된 실제 dendrite 는 짧은 cylinder 들의 *컴파트먼트 chain* 으로 푼다 [Slide L6 p.13–14]. 각 컴파트먼트 i:
$$C_m \frac{dV_i}{dt} = -\frac{V_i - V_{rest}}{R_m} + \sum_{j \in N(i)} g_{ij}(V_j - V_i) + I_{inj,i},$$

$g_{ij}$ 는 i-j 간 axial coupling. NEURON/GENESIS 가 자동 빌드. *선택 기준*: 컴파트먼트 길이 $\ll \lambda$ (보통 $0.1\lambda$). 더 짧게 나눌수록 정확하지만 ODE 수가 늘어 계산 비용이 증가한다.

---

## §9. Ion 누설 — Cable PDE 의 dissipation 항

__F5__

**한 줄 요약.** Cable PDE 의 $-(V-V_{rest})$ 항이 공간 감쇠의 본질. 만약 $r_m \to \infty$ (leak 0) 이면 정상상태 해는 $V(x) = V_0$ — *감쇠 없음*, 무한 도달. 실제는 항상 leak 이 있어 $\lambda$ 가 유한.

---

## §10. "어떻게 측정하는가?" — 실험 설계

식별성 대신 *실험 디자인* 의 관점:

| 양 | 결정하는 실험 | *결정 못 하는* 실험 (왜?) |
|---|---|---|
| **$\lambda$** | 두 위치에서 simultaneous 전압 측정, $V_2/V_1 = e^{-\Delta x / \lambda}$ | 한 점에서만 측정 — 공간 정보 없음 |
| **$R_m$** vs **$R_i$** 따로 | time-dependent 응답 (transient charging) — 둘이 다른 시간 척도로 기여 | *정상상태 V(x)* 만 — 비율 $\sqrt{R_m/R_i}$ 만 식별, 따로 결정 불가능 |
| **AP 속도** | 두 지점 사이 latency 측정 | 단일 위치 측정만 — 시간 정보만, 공간 정보 없음 |
| **Saltatory 여부** | Node 에서 Na 채널 차단 (TTX local 적용) → 다음 node 에서 AP 사라지는지 | 끝점에서만 보면 *느려졌다* 만 알지 saltatory 메커니즘 증명 불가 |

이 표의 두 번째 행이 "L3 에서 cable 로 넘어가야 하는 *실험적 동기*". 정상상태 측정만으로는 $R_m, R_i$ 가 *식별 불가능* — time-dependent 측정 (transient EPSP shape) 이 *반드시* 필요하다.

---

## §11. 흔한 오해와 시험 함정

1. **"AP 가 cable 로 *확산* 한다"** — 아니다. AP 는 매 위치에서 *재점화* 되는 행진파. 확산은 시간에 따라 진폭이 감소; AP 는 일정 진폭 유지.
2. **"굵은 axon 이 항상 빠르다"** — 부분적 사실. $\lambda \propto \sqrt{d}$ 이므로 100배 굵게 해야 10배 속도. Myelin 은 같은 직경에서 훨씬 큰 속도 향상 — *훨씬 효율적*.
3. **"$\lambda$ 는 막 시상수 $\tau_m$ 의 공간판"** — 별개의 물리. $\tau_m = R_m C_m$ (시간), $\lambda = \sqrt{d R_m / 4 R_i}$ (공간). 둘 다 $R_m$ 에 의존하지만 *독립 변수*.
4. **"Multi-compartment 가 더 정확하면 항상 multi 써야"** — 아니다. 컴파트먼트 수가 늘면 ODE 차수도 늘어 *시뮬 시간 증가*. 질문이 "soma spike 발화" 면 단일 컴파트먼트가 충분. 질문이 "dendritic Ca spike" 라야 multi 가 필요.
5. **"Myelin 은 단순한 절연체"** — 너무 단순. Schwann/oligodendrocyte 가 *능동* 으로 axon 직경 조절, 채널 분포 결정 (Na 는 Node 에 고농도). Pathology (MS) 시 saltatory 무너짐 — *수동 cable 전파만* 남아 속도 급감.

---

## §12. 자기 점검 — 백지에서 재현 가능?

- [ ] Cable PDE 를 KCL + Ohm + capacitor 정의로부터 30초 안에 유도한다.
- [ ] $\lambda = \sqrt{d R_m / 4 R_i}$ 의 각 인자가 *왜 그 자리에 있는지* 30초 안에 설명한다.
- [ ] 정상상태 해 $V(x) = V_0\,e^{-x/\lambda}$ 를 cable PDE 의 시간 미분 0 으로부터 유도한다.
- [ ] "AP 는 확산이 아니라 파동" 을 한 문장으로 설명한다.
- [ ] Unmyelinated vs myelinated AP 속도 차이를 *두 메커니즘* 으로 설명한다 (capacitance 감소 + leak 감소).
- [ ] 정상상태 V(x) 측정만으로는 $R_m, R_i$ 가 식별 불가능한 이유를 한 문장으로 설명한다.
- [ ] Multi-compartment 모형의 컴파트먼트 길이를 어떻게 정하는지 한 문장으로 답한다 ($\ll \lambda$).
""".strip()

L6_SUMMARY = (L6_SUMMARY
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
    upsert_summary("L6", "Cable Theory & Action Potential Propagation", L6_SUMMARY)
    chars = len(L6_SUMMARY)
    print(f"L6 v3 cached: {chars} chars; figures: 5; toggles: 3; sections: 12")
