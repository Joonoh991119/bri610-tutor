# BRI610 AI Tutor — 작업 히스토리 (2026-04-26 → 2026-04-27)

작성: 2026-04-27 KST. 사용자(BCS 박사과정) ↔ Opus 4.7(orchestrator) + 다중 Sonnet/Opus 서브에이전트 협업 기록.

## 라운드 0: 출발점 (v0.4 기존 자산)

```
backend/
  main.py        FastAPI v0.4
  agents.py      Router + Tutor/Derive/Quiz/Exam/Summary
  retriever.py   pgvector + tsvector + RRF
  db.py          PostgreSQL access
pipeline/
  pipeline_harness.py  Parse→QC→Embed→Verify
  schema.sql     v0.4 DB DDL
frontend/src/
  6 탭 (Tutor/Search/Quiz/Exam/Summary/Slides) — 다크 saffron 테마
data/
  L2..L6 슬라이드 199장, Dayan&Abbott + Fundamental Neuroscience textbook 1304페이지 임베딩 완료
```
v0.4 Korean+analogy 프롬프트 + DB dashboard + cached summaries + web deploy까지 완료된 상태.

## 라운드 1: 심층 벤치마킹 + 통합 리뷰

- **5개 병렬 에이전트** Sonnet 백그라운드로 발사 (per-app structured 보고서)
  - AI 튜터 8개: Khanmigo / LearnLM / OpenAI Study Mode / NotebookLM / KELE / SocratiAI / Synthesis / Duolingo Max
  - PDF 파서 8개: Marker / MinerU / olmOCR / Docling / Nougat / Mathpix / LlamaParse / PyMuPDF+pix2tex
  - 임베딩 10개: Nemotron VL (baseline) / Qwen3-Embed 8B & 4B / Voyage-3 / Cohere v4 / Jina v4 / BGE-M3 / NV-Embed v2 / OpenAI 3-large / e5
  - 수학 추론 10개: SymPy / WolframAlpha / Lean4 / DeepSeek-Prover / Mathematica + Qwen3-30B-A3B / Qwen2.5-Math-72B / DeepSeek-R1-0528 / Llemma / phi-4-reasoning
  - SRS+UX 14개: FSRS-6/py-fsrs/ts-fsrs/Anki/SM-18/RemNote/Mochi/KaTeX/MathJax/MathLive/MyScript/Seshat/Detexify/MathQuill/CodeCogs
- 결과 → `docs/benchmarks/v0.5/0[1-5]_*.md` (총 30k+ 단어 보고서)
- **통합 리뷰 (Opus)**: Plan B+ 선정 (Foundational Quality + Pedagogy with C concession) → `00_integrated_synthesis_and_plan.md`

## 라운드 2: R1–R5 + harness + Multi-Lens 통합 플랜 리비전

사용자 5대 요구 추가:
- R1 수식·이미지 완벽 (Mermaid/ASCII 금지, 실제 도판)
- R2 hallucination·non-informative 문항 zero (curated bank + team review)
- R3 interactive·addictive UI + persona
- R4 4가지 학습 모드 (recall/concept/application/proof)
- R5 ODE/PDE/뉴런 구조 기초 prerequisite

→ `00b_revised_plan_with_R1-R5.md` (P0~P10, 24.2 dev-days, 7,005 LOC)

## 라운드 3: Phase 0 + Group A — 인프라 정비

- 7 v0.4 버그픽스: lecture_summaries DDL / SearchPanel source filter / LECTURE_PAGES hardcoded / 연결풀 / vector lecture filter / search_lectures.py legacy / CORS env-driven
- v0.5 schema migration `002_v05_schema.sql`: users + sessions + mastery + figures + question_bank + srs_cards + srs_reviews + question_review_log + lens_disagreement_log + foundation_content + analytics_events (10개 신규 테이블)
- ThreadedConnectionPool 도입 (`backend/db_pool.py`)
- L7 (45p) + L8 (74p) PDF 인제스천 → 강의 7종 318 슬라이드

## 라운드 4: Group C — 검증·하네스

- SymPy verifier cascade (`backend/verify/`): preprocess HH/cable 심볼 매핑 + ThreadPoolExecutor timeout. **10/10 acceptance test 통과**
- Harness LLM client (`backend/harness/llm_client.py`): 15-route, OR→Ollama 캐스케이드, telemetry → analytics_events
- Hooks registry (`backend/harness/hooks.py`): 4 hook types (pre_question_display / post_answer / pre_derivation / post_walkthrough_step)
- Telemetry writer

## 라운드 5: Group D — Multi-Lens Review

- `multi_lens_review()` 오케스트레이터 + 4 reviewer (Factual / Pedagogical / Korean / Difficulty)
- KO+EN bilingual prompts, 컨버전스 ≤3 라운드
- Factual veto + Difficulty advisory relax
- `question_review_log` + `lens_disagreement_log` 기록

## 라운드 6: 페다고지 + 시드 뱅크 + UI

- 18 PhD-level seed cards 손저작 (HH/cable/Nernst × 4 + model_types × 3 + neural_codes × 3) — **뒤에 11/18이 hallucination으로 식별됨**
- Persona Narrator (뉴런쌤) — Kimi 기반 한국어 자연성
- FSRS-6 SRS scheduler (`backend/srs/scheduler.py`) + `/api/srs/queue` `/api/srs/review`
- 12개 hand-curated demo seed (slide-grounded)

## 라운드 7: 외부 접속 + 백엔드 정상화

- Vite `--host 0.0.0.0` + `allowedHosts` (Cloudflare Quick Tunnel 허용)
- Backend `--host 0.0.0.0` + `CORS_ORIGINS=*`
- LAN: `http://147.47.66.137:3000` (SNU 캠퍼스 네트워크)
- Public: `https://deviation-celebrities-mainstream-continuing.trycloudflare.com`

## 라운드 8: 한국어 + 슬라이드-only 강제

- Quiz/Summary 본문 영어 누락 → QUIZ_PROMPT 절대 규칙 6개 (한국어 의무 / 슬라이드 only / Bloom Apply 이상 / distractor=오개념 / 4-항목 해설 / self-check)
- LLM citation hallucination 방지: retrieval whitelist injection
- FTS sanitize OR-fallback (English query 짧은 토큰만 매칭 실패 → AND 0 hit 시 OR 자동 시도)
- Quiz/Summary 검색 쿼리 영어 키워드 보강 (`_LECTURE_TITLE_KW` 매핑)
- L7/L8 검색 0-hit 문제 해결 (한국어 쿼리 → 영어 stemmer 매치 실패)

## 라운드 9: 병렬 콘텐츠 작업 (Subagent A/B/C)

- **Agent A (Sonnet)**: Walkthrough 모드 → 4개 (HH gating ODE / cable λ / Nernst / membrane equation t=0→t=∞) + KELE consultant-teacher + structured input gate
- **Agent B (Sonnet)**: QuestionGenerator 에이전트 + bank 18→30 카드 (L4 synapses / L2 intro / L7 models / L8 codes / extras 추가)
- **Agent C (Sonnet)**: PersonaHeader + Toast + gamification rules + /api/me + streak/XP/level/badges

## 라운드 10: 박사급 강도 + 사용자 강조 카드

- PhD-rigor mandate 메모리 저장 (recall: 가정/식별성, concept: 두 관점 대조, application: 절차+식별성, proof: 비자명 단계)
- 6 membrane_eq 카드 직접 저작 (사용자 emphasize: t=0 / t=∞ derivation 가중)
- 메타-코멘트 ("사용자 강조" 등) SQL strip
- DeepSeek v4 pro + Kimi K 2.6 lens 라우트 추가

## 라운드 11: Hallucination 감사

전체 슬라이드 추출 → 18 시드 카드와 대조:
- **11/18 카드 hallucination 식별** (Rall 3/2-law / Wilson-Cowan / Mensi GIF MLE / Fisher-info CRLB / Mutual-info bits / 잘못된 슬라이드 페이지 인용 등 슬라이드에 없는 내용)
- 잔존 7 카드만 정확
- 6 신규 membrane_eq 카드는 검증된 슬라이드 그라운딩

## 라운드 12: Light scientific-journal 디자인

- 다크 saffron → off-white paper #fbfaf6
- accent #e8a958 → journal blue #1a5c8e (Neuron / eLife / Nature Neuro)
- type ink colors: blue / forest green / sienna / maroon (purple 제거)
- font: Source Serif 4 body + Inter UI
- 이모지 13곳 → Lucide 벡터 (Flame, Award, Lightbulb, FunctionSquare, Sunrise, Moon, CheckCircle, XCircle)

## 라운드 13: 모델 라우트 업그레이드 + DA 정리

- OPENROUTER_API_KEY를 `~/.zshrc`에서 발견·주입
- 라우트 재정렬: tutor/summary/consultant/lens_factual/lens_difficulty → **DeepSeek v4 pro**, quiz/explain/persona/lens_pedagogical → **Kimi K 2.6**, derive → DeepSeek-R1-0528. 무료 qwen은 router/diagnostic만
- Dayan & Abbott 인용 전면 제거: cards rationale +44 / source_citation secondary_textbook +9 / lecture_summaries 캐시 4건
- Multi-Lens default max_rounds 3 → 1 (속도)

## 라운드 14: Foundation 카드 + 학술 도판

- Foundation 8 카드 직접 저작 (Q=CV / I=CdV/dt / Ohm's law / RC parallel / 1차 ODE 동질·비동질 / RC charging / 뉴런↔회로 매핑)
- Publication-grade SVG 4개: bilayer_capacitor / membrane_rc_circuit / rc_charging_curve / ohmic_iv (Source Serif italic 변수 + Inter sans 라벨 + journal palette)
- Markdown.jsx에 `rehype-raw` 플러그인 추가 (인라인 SVG/HTML pass-through)

## 라운드 15: L3 Exemplar Summary 직접 저작

- Opus 4.7 직접 저작 6,975자
- 8 섹션: 정의 / bilayer=capacitor / I_C 유도 / R_m / τ_m / 막방정식 KCL 유도 / Expert intuitive mapping (댐+수문 비유) / Nernst Boltzmann 유도 / GHK / 식별성 / 흔한 오해 / 24h-mastery 체크리스트
- 슬라이드 only, DA 0건
- `lecture_summaries` 테이블에 캐시 — Summary 탭에서 즉시 표시

## 현재 상태 (2026-04-27 KST)

- Bank: **44 카드** (foundations 8 + membrane_eq 6 + HH 4 + Nernst 4 + cable 4 + L4 3 + neural_codes 3 + model_types 3 + L2 2 + L7 2 + L8 2 + extras 3)
- Walkthroughs: **4개** (HH / cable λ / Nernst / membrane equation)
- Publication SVG figures: **4개** + Markdown rehype-raw
- Exemplar summaries: **L3** (6,975자, Opus 4.7 저작)
- 라우트: DeepSeek v4 pro (5 routes) + Kimi K 2.6 (5 routes) + 무료 qwen (3 routes)
- 디자인: light scientific-journal, 이모지 0
- 공개 URL: 활성

## 알려진 잔존 작업 (12h 라운드 시작 시점)

- 11 hallucinated 시드 카드 재작성 (Opus 4.7 직접)
- L4/L5/L6/L7/L8 exemplar summary 저작
- DE/EM 무지 학습자용 0제로 카드 (미분 의미·전하·전류·전기장 직관 등)
- Bank 44 → 80+ 확장
- Publication SVG 4 → 16+ 확장 (HH 게이팅, voltage clamp protocol, AP propagation, ion channel structure, Nernst diffusion balance, GHK 가중평균 등)
- Free + Kimi 1차 리뷰 패스
- Opus review team 냉정 평가 + 반복 개선
