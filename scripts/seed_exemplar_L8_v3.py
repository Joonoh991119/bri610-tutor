#!/usr/bin/env python3
"""
seed_exemplar_L8_v3.py — v3 of L8 summary.

v3 changes (per feedback_v3_summaries.md):
  - Stripped specific numerical anchors (150 ms/400 ms/7-10 stage counts,
    ±10-30 ms / <1 ms timing jitter values, spike count window ms ranges,
    vesicle release probability ~0.3 anchor)
  - Added 3 <details> toggles: Poisson spike statistics (rate code),
    phase as a circular variable (phase code), mutual information / bits
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


F1 = fig("rate_vs_temporal_codes.svg",
         "Rate vs temporal coding — raster comparison",
         "그림 1. 같은 spike count, 다른 timing — rate code 는 두 패턴을 *같다고* 본다 (같은 평균). Temporal code 는 *다르다고* 본다 (다른 timing). 두 가설이 동일 raster 에 대해 다른 정보 추출.")

F2 = fig("hippocampal_phase_precession.svg",
         "Phase precession — O'Keefe & Recce 1993",
         "그림 2. 해마 place cell 의 phase precession. Theta 진동의 위상에 대해 spike 가 *앞당겨* 발화 — 위치가 place field 입구에서 출구로 이동하면 위상이 한 cycle (360°) 만큼 *후행→선행* 으로 이동. *위치 정보가 위상에 인코딩*.")

F3 = fig("synapse_chemical.svg",
         "Multiplexed code — synapse decodes simultaneously",
         "그림 3. Multiplexed code: 같은 spike train 이 rate, timing, synchrony 를 *동시에* 운반. 시냅스/postsynaptic 뉴런은 자기 시간 척도에 따라 다른 차원을 *추출*. 하나의 메시지에 여러 채널이 중첩된 라디오와 유사.")


L8_SUMMARY = r"""
# L8 — Neural Codes: Rate, Temporal, Phase and Synchrony

> **24-시간 마스터리 목표.** (i) 4 가지 신경 부호화 방식 (rate, temporal, phase, synchrony) 을 각각 *한 가지 결정적 실험* 으로 정의하고, (ii) Mainen-Sejnowski 신뢰도 패러독스를 한 문장으로 설명하고, (iii) phase precession 이 *왜 rate code 로 설명 불가능한가* 답하고, (iv) "같은 spike train 이 multiplexed 로 여러 부호를 동시 운반" 이 무엇을 의미하는지 답할 수 있어야 한다.

---

## §1. 신경 부호의 문제 — 무엇을 묻고 있는가

**한 줄 요약.** Spike 가 어떻게 *생성* 되는지는 (L5–L7) 잘 안다. *무엇을 의미* 하는지가 신경 부호의 문제 [Slide L8 p.5–7]. 4 가지 질문 [Slide L8 p.7]: (1) 무엇이 인코딩되는가, (2) 어떤 부호로 전달되는가, (3) 얼마나 신뢰 가능한가, (4) 후속 단계가 어떻게 디코드하는가. 핵심: *복수의 답* (multiplexed code) 이 동시에 옳을 수 있다.

---

## §2. Rate code — 가장 오래된 가설 (Adrian, 1926)

**한 줄 요약.** 신경 부호는 spike 의 *발화율* (firing rate) 이고, 정확한 timing 은 무관 — Edgar Adrian 의 stretch receptor 실험에서 유래 [Slide L8 p.17–19].

*증거.* 근방추 (muscle spindle) 에 가하는 힘이 클수록 발화율이 비례하여 증가. 시각피질의 *tuning curve*: 자극 방향에 따라 firing rate 가 종 모양 곡선으로 변화.

<details>
<summary><em>(펼쳐서 복습) Poisson 과정과 spike count 분포가 처음이라면</em></summary>

평균 발화율 $r$ 인 Poisson 과정에서 시간 $T$ 안의 spike 수 $n$ 은 $P(n) = (rT)^n e^{-rT}/n!$. 평균 = $rT$, 분산 = $rT$ (평균 = 분산). Fano factor = 분산/평균 = 1. 실제 뉴런의 Fano factor 가 1 과 얼마나 다른가가 rate code 신뢰도의 척도. Foundation 카드 §Poisson 통계 참조.
</details>

*3 가지 rate 정의* [Slide L8 p.20–25] — 자주 *혼동되는* 핵심 구분:

| 정의 | 평균 방향 | 윈도 | 사용처 |
|---|---|---|---|
| **Spike count rate** | 시간 평균 | 수백 ms 이상 | 정상 자극 |
| **Spike density (PSTH)** | 시행 평균 | 수 ms | time-varying 자극 |
| **Population rate** | 뉴런 평균 | 한 instant | single-trial 디코딩 |

PSTH 는 시행 평균이라 *single-trial* 디코딩에 사용 불가 (개구리는 같은 파리 잡기를 반복할 수 없음 [Slide L8 p.24]).

---

## §3. Rate code 의 문제 — 너무 느리다

__F1__

**한 줄 요약.** Spike count 평균은 충분히 긴 시간 윈도가 필요 — 그러나 인간 시각 인식은 짧은 시간 안에 완료된다 [Slide L8 p.26–28].

*Thorpe et al. (1996)*: 사람이 자연 사진에서 동물 유무를 빠르게 판단할 수 있다. 시각 경로 (망막→V1→IT→PFC) 가 여러 단계인데, rate code 의 평균 윈도보다 단계당 처리 시간이 짧을 수 있어 각 뉴런이 *소수의 spike* 만으로 정보를 전달해야 한다.

이것이 *temporal code* 의 동기.

---

## §4. Temporal code — Time-to-first-spike (Thorpe 1996)

**한 줄 요약.** 자극 시작 후 *첫 spike 까지의 잠복기* 가 정보 — 자극이 강할수록 빠른 첫 spike [Slide L8 p.32–34].

*가설.* 각 뉴런은 *단 한 번* 발화하면 그것으로 정보 전달 종료. 다음 자극이 오면 inhibition 이 풀려 다시 발화 가능. V1 simple cell 의 첫 spike timing 만으로 *모든 spike 를 합한 것과 거의 같은 정보* 추출 가능.

**왜 일관적인가.** 첫 spike 시간이 자극 강도에 강한 의존성 → 강도 → 첫 spike 시간 변환은 사실상 *log-domain rate*. 즉 "rate code 의 빠른 버전" 으로 볼 수도 있다 [Slide L8 p.56].

---

## §5. Phase code — 진동 위상에 정보 인코딩

__F2__

**한 줄 요약.** 망 차원의 진동 (e.g., theta) 이 *내부 시계* 역할. Spike 가 진동 *위상* 에 대해 어떤 시점에 발화하는가 = 부호 [Slide L8 p.35–36].

<details>
<summary><em>(펼쳐서 복습) 위상이 원형 변수인 이유가 처음이라면</em></summary>

위상 $\phi \in [0, 2\pi)$ 는 원 위의 점 — 끝과 시작이 이어진다. 따라서 위상 차이를 계산할 때는 단순 빼기가 아니라 원형 통계 (circular mean, circular variance) 를 써야 한다. $\phi = 0$ 과 $\phi = 2\pi$ 는 같은 점. Foundation 카드 §circular statistics 참조.
</details>

*해마 place cell — phase precession (O'Keefe & Recce 1993)* [Slide L8 p.39–40]:

쥐가 place field 의 입구로 들어올 때 → place cell 이 theta 의 *후기 위상* 에 발화. 쥐가 field 중앙으로 이동 → spike 가 점점 *이른 위상* 으로 이동 (precession). Field 출구에서는 *초기 위상* 에 발화. 한 traversal 동안 위상이 한 cycle 만큼 *앞당겨진다*.

**왜 rate code 로 설명 불가**: place field 의 대칭점 (입구/출구) 에서 firing rate 는 *동일* — 그러나 phase 는 *반대*. Rate 만 보면 두 위치를 구별 못 함.

*기능적 의미*: phase 가 *위치 자체* 를 미세하게 인코딩 → 후속 영역이 시간을 공간으로 변환 가능. Hippocampal *replay/preplay* (Slide L8 p.41–46) — 휴식/수면 중 sequence 의 *압축 재생* — 이 phase code 의 시간 압축 메커니즘을 활용.

---

## §6. Synchrony code — *동시* 발화의 정보

<details>
<summary><em>(펼쳐서 복습) cross-correlogram 이 처음이라면</em></summary>

두 spike train 의 cross-correlogram: train A 의 각 spike 를 기준으로 train B 의 spike 가 상대적으로 얼마나 자주 오는지 히스토그램. 두 뉴런이 독립이면 flat; synchrony 있으면 lag=0 근방에 피크. Foundation 카드 §spike train 상관분석 참조.
</details>

**한 줄 요약.** 두 뉴런이 *우연 이상* 의 정확도로 동시 발화하면, 그 동시성 자체가 부호 [Slide L8 p.49–51].

*증거.* 청각피질의 두 뉴런이 특정 톤에 응답할 때, 각자의 firing rate 는 서로 다른 정보; 그러나 두 spike 의 *상대적 시간* 에 *추가* 정보가 있음.

*Binding problem*: "빨간 사각형" 을 볼 때 빨강 뉴런과 사각형 뉴런이 *어떻게 묶여* 한 객체로 인식되는가? 가설 (Singer 등): 동시 발화 (synchrony) 가 binding 의 신호 [Slide L8 p.51].

*예: 해마-PFC sync* [Slide L8 p.54]: 메모리 처리 중 두 영역의 LFP/spike 가 theta 위상 잠금 (phase locking). 동기 = "지금 이 정보를 공유 중" 의 신호.

---

## §7. *현실 시스템 비유* — 4 부호 = 4 라디오 방식

| 신경 부호 | 현실 시스템 | 무엇이 같은가 (수학) | 무엇이 다른가 (생물) |
|---|---|---|---|
| **Rate code** | 모스 부호 발화율 | 평균 빈도 = 메시지 | 모스는 음 ON/OFF, spike 는 0/1 + 모양 stereotyped |
| **Temporal code** | 짧은 첫 음의 타이밍 | 시간 정밀도 = 정보량 | 모스는 사람이 의식적 timing, 뉴런은 자동 |
| **Phase code** | 시계 분침에 대한 위치 | 기준 cycle 에 대한 phase | 시계는 외부 (객관), theta 는 *뇌가 만든 자가 시계* |
| **Synchrony code** | 합창단 — 같은 박자 | 두 채널의 cross-correlation | 합창은 의도된 sync, 뉴런은 *물리적 결합* (gap junction, 공통 입력) 으로 자발 |

**비유가 깨지는 지점.** 라디오는 *단일* 부호화 방식 (AM 또는 FM). 뉴런은 *동시에 여러 방식* 으로 인코딩 가능 — 이것이 §10 의 multiplexed code.

---

## §8. Mainen & Sejnowski (1995) — 신뢰도 패러독스

**한 줄 요약.** 같은 자극을 반복하면 *spike 시간이 trial 마다 다르다* — 그러나 *변동하는* 자극을 같은 시간 패턴으로 반복하면 *spike 가 정확히 같은 시점에 발화* [Slide L8 p.74].

*실험*. Cortical neuron 에 (i) 일정 DC 전류, (ii) 변동하는 (white noise) 전류 — 둘 다 *반복* 주입.

*결과*:
- 일정 DC: spike timing 이 trial 마다 크게 변동 — *unreliable*.
- 변동 noise: spike timing 이 trial 마다 매우 정확하게 일치 — *highly reliable*.

**의미**. 뉴런 자체는 *충분히 정확*. Trial-to-trial 변동성은 ion channel noise 가 아니라 *자극이 평탄해서* — 막이 어떤 phase 에서 임계를 넘는지 random 결정. 자극이 변동하면 막이 *예측 가능한* 시점에서만 임계 넘김 → 정밀.

이는 temporal code 의 *물리적 가능성* 을 뒷받침. *뉴런은 sub-ms 정밀도가 가능* — 단 입력에 정보가 있어야 한다.

---

## §9. 변동성과 noise — 보편 부호는 없다

**한 줄 요약.** 같은 spike train 이 다른 뉴런에서는 *다른 정보* 를 의미할 수 있어 *보편적 (universal) 신경 부호는 없다* [Slide L8 p.70–73]. Noise 원천 (Faisal et al. 2008): channel noise (stochastic 개폐), synaptic noise (vesicle release 확률적), input noise (presynaptic 변동). Noise 와 부호의 상호작용이 측정 문제의 핵심.

---

## §10. Multiplexed code — 동시에 여러 부호

__F3__

**한 줄 요약.** 실제 뉴런은 *한 부호만* 쓰지 않고 rate, temporal, phase, synchrony 를 *동시에* 운반 — 후속 단계가 자기 시간 척도에 맞는 채널을 선택 [Slide L8 p.61–62, 67–69].

*Jang et al. (Science Advances 2020)* [Slide L8 p.66–69]: 쥐의 S1 barrel cortex 에 whisker stimulation. L4 ↔ L5/6 의 spike train 동시 기록.

*결과*:
- **Rate code**: instantaneous firing rate (iFR) 가 자극 강도와 비례.
- **Temporal code**: spike timing 이 stimulus onset 에 잠금.
- **Synchrony code**: L4 와 L5/6 사이 spike-time coherence 가 넓은 frequency 범위에서 일정.

세 부호가 *동시에* 동일 spike train 에 존재. 후속 영역은 자기 시간 척도에 따라 *어느 채널을 들을지* 선택 가능.

**이론적 의미**. 정보 채널 용량이 *다중화* 로 증가 — rate + timing + sync 가 독립 채널이면 단일 spike train 이 여러 비트 운반.

---

## §11. "어떻게 측정하는가?" — 실험 디자인

식별성 대신 *실험 설계* 의 관점:

| 부호 | 결정하는 실험 | *결정 못 하는* 실험 (왜?) |
|---|---|---|
| **Rate code** | 자극 강도 × firing rate fitting (tuning curve) | 단일 spike train, 짧은 윈도 — 평균 추정에 데이터 부족 |
| **Temporal code (TTFS)** | 자극 onset 정렬 → first-spike latency 분포 | 자극 시점 모름 → 정렬 기준 없음 |
| **Phase code** | LFP recording (theta 추출) + spike-LFP 위상 분석 | spike 만 — 외부 reference 없음, phase 정의 불가 |
| **Synchrony code** | Multi-electrode recording + cross-correlogram | 단일 unit 만 — pairwise 정보 *완전 손실* |
| **Multiplexed (모두 동시)** | iFR + iSR profile + cross-frequency coupling | 단일 모달 분석 — 한 채널 잡으면 다른 채널이 *공변량* 으로 보일 수 있음 (가짜 ID) |

**식별성 함정**. Rate 와 TTFS 는 *부분적으로 동일*: 강한 자극 → 빠른 첫 spike + 높은 rate. 단일 trial 만 보면 둘을 *식별 불가*. 분리하려면 *변동* 자극 + 다중 trial 필요 (Mainen-Sejnowski 디자인).

---

## §12. 흔한 오해와 시험 함정

1. **"Rate vs temporal — 둘 중 하나가 진짜"** — 아니다. 둘은 *동시에 진실* 가능 (multiplexed). 어느 부호가 dominant 인가는 *질문* 에 따라 다름.
2. **"Phase precession 도 결국 rate code"** — 아니다. Place field 의 대칭점에서 rate 는 동일하나 phase 는 반대. *원리적으로* rate 만으로는 구별 불가.
3. **"뉴런이 noisy 하니 정밀 부호 불가능"** — 아니다 (Mainen-Sejnowski). 입력에 정보가 있으면 뉴런은 정밀하게 발화할 수 있다. Noise 는 자극이 *평탄할 때만* 두드러짐.
4. **"Synchrony = 같은 정보"** — 아니다. 두 뉴런의 synchrony 자체가 *추가* 정보 (binding). Firing rate 와 *독립*적인 채널.
5. **"Population rate 가 가장 robust"** — 부분적. 큰 N 일수록 robust 하지만 *시간 분해능 손실* (시행 평균 또는 뉴런 평균이 평탄화). Single-trial 디코딩에는 부적합한 경우 있음.
6. **"부호가 정해져 있음"** — 아니다. *영역별, 시기별, 행동 상태별* 로 dominant 부호가 변함. 신경 부호 연구는 *항상 맥락-의존적*.

---

## §13. 자기 점검 — 백지에서 재현 가능?

- [ ] 4 가지 신경 부호 (rate, temporal, phase, synchrony) 를 각각 *한 가지 결정적 실험* 으로 정의한다.
- [ ] 3 가지 rate 정의 (spike count, density, population) 를 *언제 쓰는지* 와 함께 답한다.
- [ ] Thorpe (1996) 의 빠른 시각 인식 결과가 *rate code 의 한계* 를 어떻게 시사하는지 한 문단으로 설명한다.
- [ ] Phase precession 을 30초 안에 그림으로 그리고 *왜 rate code 로 설명 불가* 인지 답한다.
- [ ] Mainen-Sejnowski (1995) 의 변동 noise vs DC 결과를 한 문장으로 설명한다.
- [ ] Multiplexed code 의 *실험적 증거* (Jang 2020 또는 유사) 를 한 문장으로 답한다.
- [ ] Synchrony code 가 firing rate 와 *독립* 채널인 이유를 한 문장으로 설명한다.
- [ ] PSTH (peri-stimulus time histogram) 가 *single-trial 디코딩에 사용 불가* 한 이유를 답한다 (개구리-파리 예).
- [ ] Rate 와 TTFS 가 *식별 불가능* 한 실험 조건을 답한다.
""".strip()

L8_SUMMARY = (L8_SUMMARY
              .replace("__F1__", F1)
              .replace("__F2__", F2)
              .replace("__F3__", F3))


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
    upsert_summary("L8", "Neural Codes: Rate, Temporal, Phase, Synchrony", L8_SUMMARY)
    chars = len(L8_SUMMARY)
    print(f"L8 v3 cached: {chars} chars; figures: 3; toggles: 3; sections: 13")
