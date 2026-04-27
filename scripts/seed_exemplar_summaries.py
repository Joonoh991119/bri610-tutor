#!/usr/bin/env python3
"""
seed_exemplar_summaries.py — Opus 4.7 hand-authored exemplar summaries for L3 / L5.

These are seeded into `lecture_summaries` so the Summary tab shows immediate gold-
standard quality. They demonstrate the analogy + scientific-reasoning depth the
agent's SUMMARY_PROMPT should match. Slide-only citations (no Dayan & Abbott).
"""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "backend"))
from db_pool import acquire, release  # noqa: E402


L3_SUMMARY = r"""
# L3 — Neural Membrane Biophysics I  (graduate-seminar handout)

> *24-hour-mastery target: 이 페이지를 다 읽은 뒤 학생은 백지에 (i) 막 방정식을 KCL+옴+capacitor 로부터 유도하고, (ii) Nernst 식을 Boltzmann 평형으로부터 유도하고, (iii) 시상수가 면적에 무관한 이유를 30초 안에 설명할 수 있어야 한다.*

## 1. 핵심 개념과 적용 한계

### 1.1 막전위 $V_m$ 의 정의 [Slide L3 p.15]
**정의**: $V_m(t) = V_{\text{interior}}(t) - V_{\text{exterior}}(t)$.
바깥쪽을 0 으로 놓는 *부호 규약* 이다 — 휴지 막전위가 \"−65 mV\" 라는 음수 값으로 표현되는 이유.

**가정**: 막 양쪽이 *공간적으로 등전위* (single compartment). 실제 dendrite 에서는 깨진다 — 그것이 L6 cable theory 가 손볼 영역.

**언제 깨지는가**: (a) 매우 빠른 transient (ns scale, 마이크로파 대역) — 회로 모델 자체가 lumped 가 아닌 distributed 가 됨; (b) 막전위의 *공간 비균질성* — long dendrite 또는 axon.

### 1.2 Lipid bilayer = 평행판 capacitor [Slide L3 p.13, p.17]
**정의**: 정전용량 $C = Q/V$. 양쪽에 분리된 전하 $Q$ 가 만드는 전위차 $V$ 의 비.
**유도되는 가정**: 두 도체면이 평행, 그 사이는 균일 절연체.
**뉴런 대응**: 두 도체면 = bilayer 의 inner / outer leaflet 표면의 정렬된 전하; 절연체 = bilayer 의 hydrophobic core (3–4 nm 두께).
**전형값**: $C_m \approx 1\,\mu\text{F/cm}^2$ — *모든 동물 세포에서 거의 상수*. Bilayer 두께가 진화적으로 보존되었기 때문이다.

**핵심 비유**: 막 = "얇은 콘덴서 종이". 콘덴서 종이는 굵기가 작을수록 같은 전압에 더 많은 전하를 저장 (반비례). 신경막의 두께가 매우 작기 때문에 단위 면적당 capacitance 가 극단적으로 큼 — 같은 전압을 만들기 위해 조금만 전하 불균형이 있어도 됨.

### 1.3 Capacitive current $I_C = C_m \, dV/dt$ [Slide L3 p.19–20]
$Q = CV$ 의 양변을 시간 미분: $dQ/dt = C \, dV/dt$. 좌변이 곧 *전류* 의 정의이므로:
$$I_C = C_m \, dV/dt.$$

**물리적 의미**: 막전위가 *변하는 동안에만* capacitor 가 전류를 받는다. 정상상태 ($dV/dt=0$) 에선 capacitor는 전류 시점에서 보이지 않음.

**중요한 정량 결과 (슬라이드 p.20)**: $1\,\text{nA}$ 가 $C_m = 1\,\text{nF}$ 뉴런을 $1\,\text{mV/ms}$ 로 변화시킨다. 이 사실 하나로 voltage-clamp 실험의 시간 분해능 한계가 결정됨.

### 1.4 Membrane resistance $R_m$ [Slide L3 p.21–22]
**정의**: 작은 step current $I_e$ 에 대한 정상상태 전압 변화: $\Delta V = I_e \, R_m$.
**유도되는 가정**: subthreshold (active conductance 활성화 안 됨), 선형 응답.
**뉴런 대응**: 휴지 상태에서 *열려 있는* ion channel 들의 합산 conductance 의 역수. 주로 K leak 채널 (K2P 계열). 휴지 막의 \"누설 통로 총 면적\" 의 역수.
**전형값**: $R_m \approx 1\,\text{M}\Omega \cdot \text{cm}^2 \sim 1\,\text{G}\Omega \cdot \text{cm}^2$ — 세포마다 *극단적으로 다름* (10×–1000×). 채널 발현 패턴이 \"세포 흥분도\" 의 본질.

### 1.5 막 시간상수 $\tau_m = R_m C_m$ [Slide L3 p.23]
**정의**: 1차 RC 회로의 e-folding 시간. 막전위가 변화 후 $1/e \approx 37\%$ 까지 \"잊혀지는\" 시간.
**핵심 수학적 사실**: $C_m, R_m$ 모두 표면적 $A$ 에 *반비례 / 비례* 하므로 곱하면 면적이 *상쇄* — $\tau_m$ 은 *세포 크기 무관*. 큰 세포든 작은 세포든 같은 회로 시간 척도를 갖는다.
**전형값**: 10 – 100 ms.

**핵심 비유 — 댐 + 수문**: capacitor = 댐 자체 (수위 = 전압), resistor = 수문 (열림 정도 = conductance). 댐 위로 비 (input current) 가 갑자기 쏟아지면 수위가 *즉시* 점프하지 않는다 — capacity 가 buffer 역할. 수위가 올라가면 수문이 새는 양도 늘어 새로운 평형으로 수렴. $\tau_m$ = "수위 응답 시간 = 댐 크기 / 수문 누수율" 의 유한 비.

## 2. 막 방정식 — KCL 로부터의 직접 유도 [Slide L3 p.20, p.22]

키르히호프 전류 법칙 (KCL): 막을 가로지르는 모든 전류의 합 = 외부에서 주입한 전류.
$$I_{inj} \;=\; \underbrace{C_m \frac{dV}{dt}}_{I_C} \;+\; \underbrace{\frac{V - V_{rest}}{R_m}}_{I_{leak}}.$$

이 식에서 capacitive 항은 1.3, leak 항은 ohmic (1.4 + 평형으로의 driving force). 정리:
$$\boxed{C_m \frac{dV}{dt} = -\frac{V - V_{rest}}{R_m} + I_{inj}.}$$
양변에 $R_m$ 곱하고 $\tau_m$ 도입:
$$\tau_m \frac{dV}{dt} = -(V - V_{rest}) + R_m I_{inj}.$$

**Step input 에 대한 폐형 해**: $V(t) = V_\infty + (V_0 - V_\infty)\,e^{-t/\tau_m}$, $V_\infty = V_{rest} + R_m I_{inj}$.
유도는 분리변수 + 변수 변환 $u = V - V_\infty$ — Foundation 카드 #41–#42, walkthrough `membrane_equation` 의 5단계 참고.

## 3. 직관적 매핑 (Expert Intuitive Mapping)

| 막 회로 element | 등가 시스템 | 공유하는 수학 구조 | 차이점 / 어디서 깨지는가 |
|---|---|---|---|
| $C_m \, dV/dt$ | 얇은 콘덴서 종이의 충전 | $i = C \, dV/dt$ 동일 | 콘덴서 종이는 절연체 — 막은 ion channel 통해 \"새는 콘덴서\" |
| $V - V_{rest}$ over $R_m$ | 댐 수문의 누수 | 수위차 비례 흐름 (Fick / Darcy) | 댐은 단방향 ($V$ > 0 만), 막은 양방향 (negative $V$ 도 누수 가능) |
| $\tau_m = R_m C_m$ | 댐 응답 시간 | 1차 lowpass | 댐은 거시적, 막은 분자 수준 stochastic underlying — 평균만 일치 |
| $V_{rest}$ | 댐의 자연 수위 | 시스템의 평형점 | 댐 평형은 강 유량으로 수동 결정, $V_{rest}$ 는 능동적 (Na/K ATPase 가 농도 기울기를 *능동적* 으로 유지) |

## 4. Nernst 식 — Boltzmann 평형으로부터의 유도 [Slide L3 p.27–29]

**문제**: 이온 $X$ 가 농도 기울기 $[X]_o > [X]_i$ (혹은 반대) 를 갖는 채널 양쪽. 막을 가로지르는 *전기 chemical 평형* 에서 막전위는?

**유도** (3 줄):
1. 각 이온의 화학 퍼텐셜: $\mu = \mu^0 + RT \ln[X] + zF\phi$ (기체상수 + 농도 항 + 전기 항).
2. 평형 조건: $\mu_o = \mu_i$ (양쪽 동일).
3. 정리: $RT \ln[X]_o + zF\phi_o = RT \ln[X]_i + zF\phi_i$ → 양변 빼고 정의 $E_X \equiv \phi_i - \phi_o$:
$$\boxed{E_X = \frac{RT}{zF} \ln \frac{[X]_o}{[X]_i}.}$$

**수치적 결과 (체온 310 K)**:
- $K^+$: $[K]_o = 5.5$ mM, $[K]_i = 150$ mM → $E_K \approx -83$ mV.
- $Na^+$: $[Na]_o = 150$, $[Na]_i = 15$ → $E_{Na} \approx +58$ mV.

**유도되는 가정**:
- (i) 단일 이온만 투과 (다른 이온 무시);
- (ii) 활동도 = 농도 (이상 용액 가정 — 고농도에서 깨짐);
- (iii) 양쪽 reservoir 가 *고정* (시간이 지나도 농도 안 변함; 실제로 이온이 흘러도 농도 변화는 무시할 만큼 적음).

**언제 깨지는가**: 다중 이온 동시 투과 → GHK 식이 받음 (1.5 절). 비이상 용액 (cytoplasmic crowding) → 활동계수 보정 필요.

## 5. GHK voltage equation — 다이온 일반화 [Slide L3 p.30]

다중 이온 (Na, K, Cl) 이 동시에 투과하는 경우 *steady-state* 전압 (net current = 0):
$$V_m = \frac{RT}{F} \ln \frac{p_K [K]_o + p_{Na}[Na]_o + p_{Cl}[Cl]_i}{p_K[K]_i + p_{Na}[Na]_i + p_{Cl}[Cl]_o}.$$
$p_X$ = ion $X$ 의 *투과도(permeability)*. **휴지 상태에서 $p_K \gg p_{Na}, p_{Cl}$** 이므로 $V_m \approx E_K$ (그래서 휴지 전위가 $E_K$ 와 가까움).

**핵심 비유 — 가중평균 평형, 단 *log domain* 에서**: GHK 는 \"각 이온의 Nernst 평형의 가중 평균\" *처럼* 보이지만 산술 평균이 아니라 **log-domain 가중 평균** — 분자/분모가 permeability × concentration 의 1차 결합. 이 차이 때문에 \"trivial linear interpolation\" 이 아닌 *비선형* 관계.

**GHK 가 Nernst 로 환원되는 케이스**: 단일 이온 투과 ($p_X = 0$ for others) 면 두 식 동일.

## 6. 식별성 & 추정 이슈

| 양 | 측정 방법 | 식별 가능 조건 | 흔한 실패 |
|---|---|---|---|
| $C_m$ (specific) | impedance / capacitance compensation in patch-clamp | bilayer geometry 보존 | 거의 없음 — universal 1 μF/cm² |
| $R_m$ (specific) | subthreshold step current 의 V-I 기울기 | active conductance 비활성 영역 | 근방 spike 발화로 active 진입; 신호 평균 시 발화 분리 필요 |
| $\tau_m$ | step response 의 e-folding time | 단일 1차 ODE 가정 | dendrite 는 multi-time-constant — 단일 fit 시 평균 시간만 추출 |
| $V_{rest}$ | current-clamp at $I = 0$ | silent neuron, no synaptic input | 자발적 시냅스 활동이 \"가짜 fluctuation\" 추가 |
| $E_X$ | reversal potential at zero net current | 해당 이온만 dominant | 다른 ion contamination → GHK 보정 |

## 7. 흔한 오해와 시험 함정

1. **\"막 전위가 점프할 수 있다\"** — 아니다. Capacitor 양단 전압은 *연속*. 점프는 $dV/dt$ 만.
2. **\"$V_{rest}$ 는 고유 상수\"** — 아니다. Na/K ATPase 가 *능동적으로 유지*. ATP 차단 (ischemia) 시 $V_{rest}$ 가 0 으로 무너짐.
3. **\"$\tau_m$ 이 큰 세포 = 더 느린 세포\"** — 아니다. $\tau_m$ 은 면적 무관, 채널 밀도 (specific $R_m$) 만 의존. 거대한 운동 뉴런과 작은 interneuron 이 같은 $\tau_m$ 을 가질 수 있다.
4. **\"GHK = Nernst 의 평균\"** — 아니다. log-domain 가중. \"$E_K + E_{Na}$ 의 산술 평균\" 결과와 GHK 결과가 일치하는 것은 trivial 케이스만.
5. **\"휴지 전위가 음수인 이유는 K가 양성이라서\"** — 너무 단순. $V_{rest} < 0$ 은 $E_K < 0$ 때문이고, $E_K < 0$ 인 이유는 $[K]_o < [K]_i$ 라 K 가 *밖으로 나가려는* 농도 기울기가 안쪽 음전하를 남김.

## 8. 자기 점검 (백지 재현 가능?)

- [ ] $C_m, R_m, \tau_m$ 의 정의를 SI 단위까지 1분 안에 적을 수 있다.
- [ ] $\tau_m$ 이 *세포 크기 무관* 한 이유를 30초 안에 설명할 수 있다.
- [ ] $I_C = C \, dV/dt$ 를 $Q = CV$ 로부터 1줄로 유도할 수 있다.
- [ ] Nernst 식을 Boltzmann 평형으로부터 5분 안에 유도할 수 있다.
- [ ] $E_K = -83$ mV, $E_{Na} = +58$ mV 의 표준값을 즉시 답할 수 있다 (+ 농도 가정).
- [ ] GHK 가 Nernst 의 단순 평균이 *아닌* 이유를 한 문장으로 설명할 수 있다.
- [ ] Step current 응답 $V(t) = V_\infty + (V_0 - V_\infty)e^{-t/\tau_m}$ 을 백지에서 유도할 수 있다 — 분리변수 + 변수변환 트릭 포함.
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
    upsert_summary("L3", "Neural Membrane Biophysics I", L3_SUMMARY)
    print(f"L3 exemplar summary cached ({len(L3_SUMMARY)} chars)")
