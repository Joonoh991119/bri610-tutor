#!/usr/bin/env python3
"""
seed_exemplar_L7_v3.py — v3 of L7 summary.

v3 changes (per feedback_v3_summaries.md):
  - Stripped specific numerical anchors (HH step count "40,000", neuron count
    "10^11", threshold condition numeric form, "5-10 min" ATP block, Hz ranges)
  - Added 3 <details> toggles: LIF subthreshold derivation, ISI integral,
    Izhikevich 2-ODE phase plane mention
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


F1 = fig("ion_channel_subunit.svg",
         "HH gating with subunit structure",
         "그림 1. HH 모형의 m, n, h gating 변수와 4개 ODE 시스템. 큰 정확성, 큰 계산 비용 — 그래서 단순화 모형이 필요해진다.")

F2 = fig("rc_charging_curve.svg",
         "LIF subthreshold dynamics",
         "그림 2. LIF 의 subthreshold 동역학 = L3 의 RC charging. 일정 입력 $I_e$ 에서 V(t) 가 $V_∞ = E_L + R_m I_e$ 로 지수 접근. $V_{th}$ 도달 → spike 발생, $V$ 를 $V_{reset}$ 으로 reset, 반복.")

F3 = fig("action_potential_phases.svg",
         "AP shape (LIF discards this)",
         "그림 3. LIF 가 *버리는* 정보. AP 의 1 ms 모양 (rising/falling/AHP) 은 fire-and-reset 한 줄로 대체. 정보 전달은 *spike timing* 이지 모양이 아니라는 가설에 의존.")

F4 = fig("hh_gating_variables.svg",
         "Why simplify — HH cost vs LIF",
         "그림 4. 단순화의 동기. HH 4 개 ODE × N 뉴런 = 4N 차수, *비선형* 결합. LIF 는 1 ODE + threshold rule × N = N 차수, *선형* (subthreshold). 대규모 망 시뮬에서 비용 차이가 결정적이다.")

F5 = fig("synapse_chemical.svg",
         "Synaptic input — common to all reduced models",
         "그림 5. 어떤 reduced model 이든 *시냅스 입력* 처리는 동일 — 각 presynaptic spike 가 conductance 변화 또는 current pulse 를 만든다. 본 강의의 모형 차이는 *그 입력에 대한 응답을 어떻게 단순화하는가* 의 차이.")


L7_SUMMARY = r"""
# L7 — Different Types of Computational Models of Single Neurons

> **24-시간 마스터리 목표.** (i) "왜 HH 를 *그대로 쓰지 않는가*" 를 한 문단으로 답하고, (ii) LIF 가 sub-threshold HH 의 *어떤 가정* 으로부터 유도되는지 보이고, (iii) ISI 의 폐형 식을 5분 안에 적분하고, (iv) "내 연구 질문이 X 면 어떤 모델 쓸지" 결정 트리를 답할 수 있어야 한다.

---

## §1. 왜 HH 만 쓰지 않는가 — *계산 비용* 의 진실

__F4__

**한 줄 요약.** L5 의 Hodgkin-Huxley (HH) 는 single neuron 의 AP 를 *생물학적으로 정확히* 재현한다. 그 대가로 4 개의 비선형 결합 ODE 를 *모든 시간 스텝* 에 풀어야 한다 [Slide L7 p.5–8].

HH 단일 뉴런 시뮬레이션에서 충분한 시간 분해능을 위해 매우 많은 적분 스텝이 필요하고, 뉴런 수 $N$ 이 늘면 ODE 수도 $4N$ 으로 늘어난다. 대규모 망을 시뮬레이션하려면 계산 비용이 실용적 한계를 넘는다.

**핵심 가설**: 정보 처리에서 *spike 의 정확한 모양* 이 정말 필요한가? Lapicque (1907) 가 직관한 답: *"아니, spike timing 만 있으면 된다."* — AP 는 어차피 stereotyped (모양이 매번 거의 동일) 하므로 *언제 발화하는가* 가 정보의 본질. 모양은 버려도 된다 [Slide L7 p.7–9].

이 가설이 LIF (Leaky Integrate-and-Fire) 모형의 출발.

---

## §2. LIF 의 유도 — *Sub-threshold HH* 한 줄 가정

__F2__

**한 줄 요약.** Sub-threshold 영역 ($V < V_{th}$) 에서 voltage-gated Na/K 채널은 *거의 닫힘* — HH 의 active conductance 항을 0 으로 두면 LIF 가 *그대로* 나온다 [Slide L7 p.10–11].

HH 식:
$$C \frac{dV}{dt} = -\bar{g}_{Na} m^3 h (V - E_{Na}) - \bar{g}_K n^4 (V - E_K) - g_L(V - E_L) + I_e.$$

<details>
<summary><em>(펼쳐서 복습) Sub-threshold 에서 active 항이 사라지는 이유가 처음이라면</em></summary>

$V < V_{th}$ 에서 $m_\infty(V) \approx 0$ (Na_v 활성화 곡선의 발동 전), $n_\infty(V) \approx n_0$ (K_v 는 거의 휴지값). 따라서 $\bar{g}_{Na}m^3 h \approx 0$, K_v 기여도 leak 으로 흡수 가능. Foundation 카드 §HH subthreshold 근사 참조.
</details>

Sub-threshold 가정 ($m \approx 0$, $n \approx n_\infty$ 일정, $h \approx h_\infty$ 일정) 하에 active 항이 leak 으로 흡수:

$$\boxed{C \frac{dV}{dt} = -g_L(V - E_L) + I_e.}$$

이는 정확히 L3 의 *passive 막 방정식*. 여기에 phenomenological *spike rule* 을 추가: "$V \geq V_{th}$ 도달 시 → 'spike' 기록 + $V \leftarrow V_{reset}$".

__F3__

*해석.* AP 의 빠른 모양을 1 줄의 reset 으로 *대체*. 잃는 정보 = AP 모양. 가설: 모양은 *stereotyped* 이므로 잃어도 OK.

---

## §3. LIF 의 폐형 해 — ISI 공식

**한 줄 요약.** 일정 입력 $I_e$ 에서 LIF 가 *주기적* 으로 발화. ISI 는 적분으로 *닫힌 형태*.

L3 의 step response 재사용:
$$V(t) = V_\infty + (V_{reset} - V_\infty)\,e^{-t/\tau_m}, \quad V_\infty = E_L + R_m I_e.$$

<details>
<summary><em>(펼쳐서 복습) ISI 를 $V(t_{isi}) = V_{th}$ 에서 푸는 과정이 처음이라면</em></summary>

$V(t_{isi}) = V_{th}$ 조건: $V_\infty + (V_{reset} - V_\infty)e^{-t_{isi}/\tau_m} = V_{th}$. $e^{-t_{isi}/\tau_m} = (V_{th} - V_\infty)/(V_{reset} - V_\infty)$ 로 정리한 뒤 양변 $\ln$ 취하고 $-1/\tau_m$ 으로 나누면 $t_{isi}$ 가 나온다. Foundation 카드 §지수함수 역변환 참조.
</details>

$V(t_{isi}) = V_{th}$ 조건 풀면:

$$\boxed{t_{isi} = \tau_m \ln\!\left(\frac{R_m I_e + E_L - V_{reset}}{R_m I_e + E_L - V_{th}}\right).}$$

[Slide L7 p.15–16]. 발화 빈도 $r_{isi} = 1/t_{isi}$ — *f-I 곡선*.

**발화 임계 조건**: $V_\infty > V_{th}$, 즉 $R_m I_e > V_{th} - E_L$. 그렇지 않으면 막전위가 임계에 절대 도달하지 않아 영원히 발화하지 않는다 ($r = 0$).

*피질 뉴런과 비교* (Slide L7 p.17): 큰 입력에서 LIF 는 *적응 없이* 일정 빈도로 발화 — 실제 뉴런은 첫 spike 가 빠르고 점점 느려짐 (spike-rate adaptation). LIF 는 이 적응을 *놓침*.

---

## §4. Spike-rate adaptation — 한 단계 보강

**한 줄 요약.** LIF 에 *추가 conductance* $g_{sra}$ (K+ 형태) 를 더하면 적응이 재현 [Slide L7 p.18, 23–24]. $C\,dV/dt = -g_L(V-E_L) - g_{sra}(V-E_K) + I_e$. $g_{sra}$ 는 spike 발화 시 점프, $\tau_{sra}$ 로 지수 감쇠. 매 spike 마다 K leak 이 잠깐 켜져 다음 발화 지연 → ISI 점차 증가.

**기능적 의미** [Slide L7 p.19–22]: (1) **Contrast adaptation** (과포화 방지), (2) **Forward masking** (첫 자극 이후 AHP 가 두 번째 응답 억제), (3) **Selective attention** (약한 입력은 묻히고 강한 입력만 pop-out).

---

## §5. Izhikevich 모형 — 2 ODE 의 *타협*

<details>
<summary><em>(펼쳐서 복습) 2-ODE 위상 평면 분석이 처음이라면</em></summary>

$dv/dt = f(v,u)$, $du/dt = g(v,u)$ 계에서 $v$-nullcline ($dv/dt = 0$) 과 $u$-nullcline ($du/dt = 0$) 의 교점이 평형점. 교점 근방의 야코비안 고유값 부호가 안정성을 결정. Foundation 카드 §2D 위상 평면 분석 참조.
</details>

**한 줄 요약.** LIF 는 너무 단순 (burst, rebound 없음); HH 는 너무 비쌈. Izhikevich (2003) 2-ODE 모형은 4 매개변수 (a, b, c, d) 만으로 거의 모든 spike pattern 재현 [Slide L7 p.25–27]:
$$\frac{dv}{dt} = 0.04 v^2 + 5v + 140 - u + I, \quad \frac{du}{dt} = a(bv - u),$$
reset: $v \geq 30 \Rightarrow v \leftarrow c, u \leftarrow u + d$.

*매개변수*: $a$ = recovery 시간 척도, $b$ = recovery sensitivity, $c$ = V reset (낮으면 burst), $d$ = u jump (크면 fatigue). $v$ 식의 2차 항이 spike upstroke 를 *내장* — LIF reset rule 보다 자연스럽고, ODE 차수 2 (HH 절반). $v$-$u$ 위상 평면에서 $v$ nullcline (포물선)과 $u$ nullcline (직선)의 교점이 휴지점 — 평면 위상 분석으로 다양한 패턴을 기하학적으로 설명 가능하다. *응용* [Slide L7 p.41–44]: Striatal MSN, DA 뉴런의 D1/D2 약물 응답을 (a,b,c,d) 변화로 매핑.

---

## §6. *현실 시스템 비유* — 4 모델 = 4 카메라

| 모델 | 현실 시스템 | 무엇이 같은가 (수학) | 무엇이 다른가 (생물) |
|---|---|---|---|
| **HH** (4 ODE, 비선형) | 풀-프레임 DSLR | AP 모양, ion 흐름 정확 | 프레임 무거움 (계산 비용); 망 시뮬 *불가* |
| **LIF** (1 ODE + reset) | 압축된 텍스트 메모 | spike timing 만 보존 | spike 모양/burst/rebound 모두 *손실* |
| **Adaptive LIF** | 메모 + 타임스탬프 | LIF + 적응 dynamics | 여전히 burst 못 잡음; subthreshold 진동 없음 |
| **Izhikevich** (2 ODE) | 스마트폰 사진 | spike + 거의 모든 패턴 + 빠른 계산 | 매개변수가 *경험적* (a, b, c, d 가 ion 채널과 1:1 대응 *없음*) |

**비유가 깨지는 지점.** 카메라들은 모두 *같은 장면* 을 다른 해상도로 찍지만, 모델들은 *다른 가설* 을 함의. LIF 는 "spike 모양은 무관" 가설; Izhikevich 는 "현상학이면 충분" 가설; HH 는 "메커니즘 정확이 중요". 같은 데이터에 다른 모델을 fit 하면 *다른 결론* 이 나올 수 있다.

---

## §7. Multi-compartment HH — DA 뉴런 사례

**한 줄 요약.** 단일 컴파트먼트로는 dendritic Ca dynamics, NMDA spike, GABA_A 의 위치 효과를 잡을 수 없음. DA (dopaminergic) 뉴런의 burst-vs-single-spike 전환을 모형화하려면 *multi-compartment HH* 가 필수 [Slide L7 p.37–40].

*Komendantov et al. (2004)*: Soma + proximal + distal dendrite 의 3 컴파트먼트 HH. 각 컴파트먼트마다 자기 (m, n, h) 와 추가 채널 (SK, NMDA, GABA_A). 각 위치에 다른 채널 분포.

*결과*:
- GABA_A agonist (proximal dendrite 에 활성) → **burst → single-spike** 전환을 *재현*.
- SK channel block (soma) → **single → burst** 전환.

이 결과는 단일 컴파트먼트로는 *원리적으로* 재현 불가 — 채널 *위치* 가 핵심이기 때문.

---

## §8. Reduced model 로 같은 신경 — Izhikevich + DA

**한 줄 요약.** Multi-compartment HH 의 burst-vs-single 결과를 Izhikevich 2-ODE 로도 *현상학적* 재현 가능 — *(a, b, c, d)* tuning 으로 [Slide L7 p.41–44].

*Humphries et al. (2009)*: Striatal MSN 의 in vitro f-I 곡선과 D1/D2 약물 응답을 Izhikevich 매개변수 fitting 으로 재현. 망 시뮬 (수만 뉴런) 에서 HH 는 사실상 불가, Izhikevich 로는 PC 한 대로 가능.

**교훈**: 같은 *기능적 출력* (spike pattern) 이 다른 *내부 메커니즘* (HH vs Izhikevich) 으로 만들어질 수 있음. 모델 선택은 "내가 어느 변수에 답하고 싶은가" 의 함수.

---

## §9. *현실 시스템 비유* — 모델 선택 = 지도 축척 선택

지도를 만들 때 1:100 축척 (도면) 과 1:10⁶ 축척 (지구 전체) 은 *다른 정보* 를 보여준다. *어떤 정보를 답하고 싶은가* 에 따라 축척이 결정된다.

| 연구 질문 | 권장 모델 | 이유 |
|---|---|---|
| 단일 뉴런의 ion 채널 약리 | HH | active conductance 가 답의 핵심 |
| Dendritic integration, synaptic placement | Multi-compartment HH | 공간 정보 필수 |
| 망 동역학 (oscillation, sync) — 대규모 뉴런 | LIF or Izhikevich | 비용 < 정확도 |
| 이론적 분석 (mean-field, ISI 분포) | LIF | 폐형 해 가능 |
| 뉴런 종류별 다양성 (FS, RS, IB, ...) | Izhikevich | (a,b,c,d) 4 개로 모든 클래스 재현 |
| AP 자체 메커니즘 검증 | HH | 그 외에는 *순환 논리* |

**비유가 깨지는 지점**: 지도는 *같은* 객관적 영토를 다른 축척으로. 모델은 *다른 가정* — 작은 축척은 단순 압축이 아니라 *물리 법칙 자체* 의 변경.

---

## §10. "어떻게 결정하는가?" — 실험 디자인

| 양 | 결정하는 실험 | *결정 못 하는* 실험 (왜?) |
|---|---|---|
| **LIF 매개변수 ($\tau_m, R_m, V_{th}, V_{reset}$)** | sub-threshold step response (τ_m, R_m) + spike-evoking current threshold (V_th) + AHP 측정 (V_reset) | 단일 spike train — fire 후 V 정보 없음, V_reset 식별 불가 |
| **Izhikevich (a, b, c, d)** | f-I 곡선 + ISI distribution + spike pattern 의 4 가지 모드를 동시에 fit | f-I 곡선만 — (a,b,c,d) 의 *조합* 이 같은 곡선을 만들 수 있음 (식별성 깨짐) |
| **HH active conductance** | voltage clamp + Na, K 채널 차단제 (TTX, TEA) 분리 | current clamp 만 — Na/K 분리 불가, 통합 conductance 만 |
| **Multi-comp 채널 분포** | dendritic patch + uncaging | soma patch 만 — distal dendrite 정보 *완전 손실* |

식별성 관점: Izhikevich 의 (a,b,c,d) 는 *현상학 매개변수*. 같은 spike pattern 이 여러 (a,b,c,d) 조합으로 나올 수 있음 → 절대 식별 불가, *하나의 가능한 fit* 만 의미.

---

## §11. 흔한 오해와 시험 함정

1. **"LIF 가 HH 보다 부정확"** — 부분적. Sub-threshold 영역에선 LIF = HH (정의상). 부정확한 곳은 *spike 자체* (빠른 윈도). 시간 분해능이 낮은 망 시뮬에선 무관.
2. **"Izhikevich 매개변수에 생물학적 의미"** — 아니다. (a, b, c, d) 는 *pattern fitting* 용; ion 채널과 1:1 대응 없음. 동일 (a,b,c,d) 가 다른 채널 조합으로 만들어질 수 있음.
3. **"적응 = 피로"** — 부분적. 적응은 *능동* (K+ 채널 활성화); 피로는 *수동* (ion gradient 고갈). ATP 충분하면 적응은 한 spike 단위로 회복; 피로는 분 단위.
4. **"DA 뉴런은 항상 single-spike"** — 아니다. *상황에 따라* burst 또는 single — 그 전환을 잡는 것이 multi-compartment 모형의 *목적*.
5. **"HH 가 가장 좋은 모델"** — *질문에 따라*. 망 시뮬에서 HH 는 *나쁜 모델* (느려서 작은 망만 가능, 결과 일반화 불가). 좋은 모델 = *질문에 맞는 가장 단순한 모델*.

---

## §12. 자기 점검 — 백지에서 재현 가능?

- [ ] HH (4 ODE) 와 LIF (1 ODE + reset) 의 *계산 비용* 비교를 한 문장으로 설명한다.
- [ ] LIF 가 sub-threshold HH 의 어떤 가정으로부터 유도되는지 식 변환으로 보인다.
- [ ] ISI 식 $t_{isi} = \tau_m \ln[(R_m I + E_L - V_{reset})/(R_m I + E_L - V_{th})]$ 를 5분 안에 적분으로 유도한다.
- [ ] 발화 임계 조건 ($V_\infty > V_{th}$) 을 식에서 즉시 도출한다.
- [ ] Spike-rate adaptation 의 메커니즘 (K+ conductance) 과 3 가지 기능적 의미를 답한다.
- [ ] Izhikevich 의 (a, b, c, d) 4 매개변수의 역할을 한 줄씩 설명한다.
- [ ] DA 뉴런의 burst-vs-single 전환에 *왜 multi-compartment HH 가 필요한지* 한 문단으로 설명한다.
- [ ] "내 연구 질문 X 에 어떤 모델" 결정 트리를 5 가지 시나리오에 대해 답한다.
- [ ] LIF 가 *놓치는* 3 가지 현상 (burst, subthreshold oscillation, AP 모양) 을 답한다.
- [ ] Izhikevich 매개변수가 *식별 불가능* 한 이유를 한 문장으로 설명한다.
""".strip()

L7_SUMMARY = (L7_SUMMARY
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
    upsert_summary("L7", "Computational Models of Single Neurons", L7_SUMMARY)
    chars = len(L7_SUMMARY)
    print(f"L7 v3 cached: {chars} chars; figures: 5; toggles: 3; sections: 12")
