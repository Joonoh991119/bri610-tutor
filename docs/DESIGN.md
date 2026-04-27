# BRI610 AI Tutor — 설계도 v1
2026-04-27 KST · 12h 자율 라운드 시작 시점

---

## 1. 학습자 프로필 (구속 조건)

**대상**: SNU BCS (Brain & Cognitive Sciences) 박사과정생.
**전제 지식**:
- 신경과학 일반 (학부 수준 ✓)
- 미적분: 단순 미분 / 적분은 가능, **분리변수 ODE / 1차 선형 ODE / 지수 함수 직관 ✗**
- 전자기학: **0** — 전하 / 전류 / 전압 / capacitor / resistor / Kirchhoff 법칙 *모름*
- 한국어 모국어 / 영어 reading comprehension OK / 영어 writing 약함

**결론**: 컴퓨터신경과학 표준 교재(Dayan & Abbott)는 학생을 *전기공학·미분방정식 사전이수* 했다고 가정하지만, 본 학생은 그렇지 않다. 시스템이 그 갭을 *명시적으로* 메워야 한다.

## 2. 12-시간 학습 목표 (success criteria)

12시간 후 학생은 *백지에서*:
1. 막 방정식 $\tau_m \, dV/dt = -(V - V_{rest}) + R_m I_{inj}$ 를 KCL+옴+capacitor 정의로부터 유도할 수 있다.
2. Step current 응답 $V(t) = V_\infty + (V_0 - V_\infty)e^{-t/\tau_m}$ 를 분리변수 + 변수변환으로 푼다.
3. Nernst 식을 Boltzmann 평형으로부터 유도한다.
4. HH 모델의 4-ODE 시스템을 표기 그대로 적고, 각 변수 (m, n, h, V) 의 물리적 의미를 1줄로 설명한다.
5. Cable 방정식 정상상태 해 $V(x) = V_0 e^{-x/\lambda}$ 를 구하고 $\lambda$ 의 정의를 적는다.
6. 4가지 neural code (rate / temporal / phase / synchrony) 를 구분하고 각각의 한계를 1줄로 설명한다.
7. 각 개념을 *댐+수문* / *4-locking 보안문* / *급수파이프 압력 감쇠* 등의 직관 비유로 설명할 수 있다.

## 3. 학습 범위 = **강의 슬라이드 7종만** (교재 인용 금지)

| 강의 | 페이지 | 핵심 토픽 | 가중 (학습 시간 비율) |
|---|---|---|---|
| L2 Introduction | 68 | 컴퓨터신경과학 개요, 막 RC 도입 | 5% (gateway) |
| **L3 Membrane Biophysics I** | 34 | $V_m$, $C_m$, $R_m$, $\tau_m$, Nernst, GHK | **20%** (모든 후속의 토대) |
| L4 Membrane Biophysics II | 31 | 이온 채널 종류, synaptic transmission | 10% |
| **L5 Action Potential & HH** | 34 | HH 4-ODE, gating, voltage clamp | **25%** (정점) |
| **L6 Cable Theory** | 32 | Cable PDE, $\lambda$, AP propagation | 15% |
| L7 Different Models | 45 | LIF, adaptive IF, Izhikevich, HH 비교 | 15% |
| L8 Neural Codes | 74 | rate/temporal/phase/synchrony, multiplexed | 10% |

**Dayan & Abbott / Fundamental Neuroscience 인용 금지** — 슬라이드 안에서 학습자가 24시간 내 마스터 가능해야 함.

## 4. 강조 파트 (학습 비중 최대)

### 4.1 Tier 1 (최고 비중)
- **막 방정식 유도** ($t=0$ / $t=\infty$ 한계 + 폐형 해) — Foundation 5 카드 + walkthrough 6 단계 + L3 exemplar summary
- **HH 4-ODE 시스템** + 게이팅 변수 $m, n, h$ 의 의미
- **Nernst 식 Boltzmann 유도** — 슬라이드 L3 p.27-29 그라운딩
- **Cable equation 정상상태** — $V(x) = V_0 e^{-x/\lambda}$ + $\lambda$ 의 의미

### 4.2 Tier 2 (중요)
- GHK 식의 *log-domain 가중평균* 의미 (Nernst 와의 차이)
- Action potential 생성의 양의/음의 피드백 사이클
- Cable 분기점 + AP propagation 속도

### 4.3 Tier 3 (확장)
- Neural codes 4종의 정량 비교
- LIF 모델의 한계와 Izhikevich 모델
- Spike-rate adaptation 메커니즘

## 5. 시스템 디자인 원칙

### 5.1 시각 디자인 — Light Scientific Journal
- **bg**: `#fbfaf6` off-white paper
- **accent**: `#1a5c8e` Neuron/eLife journal blue
- **type ink colors**: blue / forest green / sienna / maroon (purple 제거)
- **body font**: Source Serif 4 (학술 article 톤)
- **UI font**: Inter / Pretendard (한글)
- **이모지 0** — 모든 시각 신호는 Lucide 벡터 아이콘 또는 텍스트 배지
- **도판**: 모두 publication-grade SVG (Inter sans 라벨 + Source Serif italic 변수)

### 5.2 페다고지 디자인
- **Bottom-up 접근**: $Q = CV$ → $I_C = C dV/dt$ → KCL → 막 방정식 → HH → cable
- **Triple presentation**: 모든 핵심 개념을 (1) 수식, (2) 비유 (댐/수문/회로), (3) 뉴런 분자 구조 — 셋 다로 보여줌
- **Step input 우대**: 단일 컴파트먼트 step current 응답이 모든 dynamics 의 *공통 기본형* 임을 강조 (HH gating, cable spatial, EPSP 모두 같은 ODE 패턴의 변형)

### 5.3 콘텐츠 디자인
- **카드**: 4가지 타입 (recall / concept / application / proof) × 7가지 토픽 × 3-5 difficulty levels
- **카드 본문 구조**: Setup (그림 + 1-2 줄 컨텍스트) → 질문 (a/b/c 다중 부분) → 정답 (단계별 유도) → Rationale (흔한 오해 + cross-link)
- **인용**: `[Slide L# p.#]` 만 사용 — 1차 문헌은 슬라이드에 명시된 경우에만
- **시각 자료**: 학술 톤 SVG, 인라인 변수 italic, 캡션 sans-serif italic
- **Walkthrough**: 6 단계 정도, structured input gate (3 필드: "내가 이해한 바" / "내가 시도한 것" / "막힌 부분")

### 5.4 라우팅 (현재)
- **DeepSeek v4 pro** PRIMARY: tutor, summary, consultant, lens_factual, lens_difficulty
- **Kimi K 2.6** PRIMARY: quiz_generator, explain_my_answer, persona_narrator, lens_pedagogical, priority_scorer
- **DeepSeek R1-0528**: derive (chain-of-thought)
- **Sonnet 4.6**: lens_factual fallback (paid quality gate)
- **Free Qwen**: router, diagnostic only
- **Ollama qwen2.5:14b-instruct**: local fallback when OR fails

### 5.5 검증 사이클
1. **단일 카드 작성** (Opus 4.7 자체)
2. **무료/Kimi 1차 리뷰**: 4-lens (factual/pedagogical/korean/difficulty), max_rounds=1
3. **Opus review team 2차 리뷰**: 3 병렬 Opus 에이전트가 각자 (i) 슬라이드 그라운딩 (ii) 페다고지 효과 (iii) 한국어 자연성 + 비유 명료성 — 냉정 평가
4. **불일치 카드** → 수정 → 재리뷰
5. **수렴** = 4-lens 모두 pass + Opus review team 3개 모두 score≥8/10

## 6. 12시간 라운드 작업 계획

### Phase 1 (~1h): 설계 + 0제로 파운데이션 카드 (15+)
- DESIGN.md, HISTORY.md ✓
- DE/EM 0제로 카드 12-15: 미분의 의미 (slope, dV/dt) / 적분 (면적 / 누적 charge) / 분리변수법 직관 / 지수함수 자연성 / 전하 / 전류 / 전압 / 전기장 / 도체-절연체 / Kirchhoff 전류·전압 법칙 / 옴 법칙 / RC 회로 직관 / 시간상수 의미

### Phase 2 (~3h): 병렬 콘텐츠 저작
- Subagent A (Opus): L4 + L6 exemplar summary (각 6000+ chars)
- Subagent B (Opus): L5 + L7 + L8 exemplar summary (각 6000+ chars)
- Subagent C (Sonnet): 12+ 추가 SVG 도판
- Subagent D (Sonnet): 11 hallucinated 시드 카드 재작성

### Phase 3 (~3h): Bank 확장 44 → 80+
- 토픽별 카드 개수 균형
- foundations 15 / membrane_eq 8 / Nernst 6 / HH 8 / cable 6 / model_types 6 / neural_codes 6 / 통합 5 = 60 신규 + 잔존 = 80+

### Phase 4 (~2h): 리뷰 파이프라인
- 무료 + Kimi 1차 리뷰 (전체 80+ 카드, 병렬 batch)
- Opus review team 3 병렬 에이전트
- 불일치 → 재작성 → 재리뷰

### Phase 5 (~2h): 통합 + 폴리시
- 최종 백엔드 재시작
- E2E smoke test
- Final HISTORY 업데이트

### Phase 6 (~1h): 최종 보고
- 사용자에게 결과 + 다음 라운드 후보 제시

## 7. KPI (12h 후 측정)

- Bank 카드 수: ≥ 80
- 슬라이드-only 인용 률: 100%
- DA reference 잔존: 0
- Publication-grade SVG 수: ≥ 16
- Exemplar summary 수: ≥ 5 (L3 ✓ + L4 + L5 + L6 + L7 또는 L8)
- Walkthrough: ≥ 4 (현재) — 라운드에서 1-2 추가 가능
- 4-lens 통과률: ≥ 95%
- Opus review team score 평균: ≥ 8.0/10
- 학생이 백지에서 24h-mastery 체크리스트 7항목 중 ≥ 5 답변 가능 (자기 보고 또는 quiz 정답률)

## 8. 위험 + 완화

| 위험 | 가능성 | 영향 | 완화 |
|---|---|---|---|
| OR 토큰 소진 ($20 budget) | 중 | 중 | Kimi K 2.6 (저가) 와 Free Qwen 우선 사용; DeepSeek v4 pro는 quality gate에만 |
| Multi-Lens 컨버전스 실패 | 중 | 중 | max_rounds=1 default + manual queue; 5% 이하 escalation 예상 |
| 백엔드 다운타임 | 낮음 | 중 | uvicorn 자동 재시작; tunnel은 2시간 라이프타임 — 만료 시 재발급 |
| Opus 컨텍스트 한도 | 중 | 낮음 | 작업을 작은 chunk 로; 서브에이전트로 격리 |
| 슬라이드 그라운딩 검증 실패 | 낮음 | 높음 | 슬라이드 텍스트 추출본을 직접 저작자에게 제공 (in-context); regex 인용 검증 |
