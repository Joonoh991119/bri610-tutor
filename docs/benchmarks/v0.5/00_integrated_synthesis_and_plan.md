# v0.5 통합 리뷰 & 최종 구현 플랜

**Author**: Opus architect synthesis
**Date**: 2026-04-26
**Inputs**: 5 deep benchmark reports (`01_ai_tutors.md` … `05_srs_and_ux.md`) + v0.4 codebase audit + memory files (`project_core`, `architecture_v05`, `bugs_v04_known`, `pedagogy_invariants`, `lecture_priorities`).
**Reading rule**: every recommendation here is grounded in a benchmark number or audit finding. Where a memory file conflicts with a benchmark, the conflict is named and resolved.

---

## Part 1: 통합 설계 제약 (Integrated Design Constraints)

### 1.1 데이터 파이프라인 (parsing + embedding)

**Parser routing — content-type dispatcher.** The v0.4 pipeline routes everything through PyMuPDF, which has confirmed garbage on equation pages ("CmdVdt=−Iion" output) and ranks 6.67/10 on the formula benchmark (`02_pdf_parsers.md`, arXiv:2512.09874) — second-lowest of 21 tools. Three benchmarks converge:

- **MinerU2.5 Formula CDM 97.45 vs Marker 85.24 vs Mathpix 86.6** (OmniDocBench v1.6).
- **olmOCR-Bench: olmOCR-2 82.4 vs Marker 76.1 vs MinerU 75.8** (text linearization).
- **Formula-extraction LLM-as-judge: MinerU2.5 9.17, Mathpix 9.64, olmOCR-2 8.94, LlamaParse 8.14, PyMuPDF 6.67**.

The right answer is a **content-type-routed dispatcher**, not a single parser:

| Page type | Primary | Fallback | Rationale |
|---|---|---|---|
| Equation/mixed (DA Ch.5–7, FN HH/cable) | **MinerU pipeline-MLX backend** | Marker + Ollama | CDM 97.45 leads; MLX 3× CPU speed on M-series |
| Prose/reference | **PyMuPDF (keep)** | Docling | 100 p/s; lossless; already integrated |
| Lecture slides (PPTX) | **Marker `--use_llm` (Ollama)** | LlamaParse Fast (free 10k credits) | PPTX-native; Texify equation regions; $0 |
| Korean text | All three handle KR fine | — | Nougat rejected (Chinese edit-dist 0.998 ⇒ KR fails too) |

**This conflicts with `architecture_v05.md` which selected Marker as the single primary parser.** Resolution: the memory file was based on April 2026 SOTA-at-publication; the deeper benchmark in `02_pdf_parsers.md` shows MinerU's 12-point CDM lead is decisive for HH/cable equation fidelity. **Keep Marker for slides** (PPTX native, Texify is strong on the slide layout) but **use MinerU for textbook equation pages**. The memory should be updated.

**Embedding — keep multimodal, add Korean-strong text.** `03_embeddings.md` is unambiguous:

- **Qwen3-Embedding-8B is the only model with MMTEB #1 (70.58) + Apache 2.0 + Ollama-native.** MTEB-EN 75.22 vs OpenAI 3-large 64.6 vs BGE-M3 ~64.2 — a 10-point lead.
- **Nemotron VL** has no published MTEB or Korean breakdown but is free on OpenRouter and already embedded 1503 pages — re-embed cost is real.

**Decision: dual-column pgvector schema** — keep Nemotron VL `image_embedding` (2048-dim) for slide-image retrieval; **add `text_embedding_v2 vector(1024)` (Qwen3-8B MRL @ 1024)** for prose retrieval. This matches the SQL pattern proposed in `03_embeddings.md`. Cost of re-embed: $0 (Qwen3 local Ollama, ~15–45 min on M-series at Q4_K_M).

**Re-parse cost estimate (one-time, free)**:
- DA Ch.5–7 (HH, cable, ~120 p) via MinerU: ~3 min on MLX.
- DA Ch.1–4 (~100 p): ~3 min.
- FN equation pages (~200 p): ~6 min.
- L8 lecture slides (74 p) via Marker+Ollama: ~5 min.
- **Total: ~17–20 min compute, $0 cost.**

If MinerU pipeline backend formula CDM falls below the 97.45 hosted-Pro figure (the local-pipeline number is not separately published), the fallback ladder is: **Marker+Ollama → Mathpix API @ $0.002/page** for the ~50 worst pages = budget ceiling **<$0.50 total**.

### 1.2 추론 & 검증 (reasoning + verification)

**Three-tier verifier cascade** (ground-truth from `04_math_reasoning.md`):

```
LLM derivation step  →  SymPy.simplify(student - reference)
                            ↓ on parse_latex error or dsolve timeout
                        Wolfram Engine (free dev license, wolframclient)
                            ↓ if WL also fails / partial
                        WolframAlpha Show-Steps API (cap @ 2k/month, cache by hash)
```

- **SymPy** verdict: ADOPT-AS-PRIMARY-VERIFIER. BSD-3, zero latency, runs in-process. Known gap: `parse_latex` fails on `\partial` (issue #4438, open since 2014). Fix: 50-line LaTeX preprocessor mapping HH/cable Greek-subscript symbols + partial→Derivative substitution.
- **Wolfram Engine** verdict: ADOPT-AS-FALLBACK. Free non-commercial dev license. `ToExpression[..., TeXForm]` handles `\partial` natively. wolframclient SDK is clean. Cold-start 3–5s; keep kernel warm via process pool.
- **WolframAlpha API** verdict: ADOPT-AS-FALLBACK only for problems both above fail on (full nonlinear HH 4-ODE with V-clamp BC). Cache aggressively.

**Lean4 / DeepSeek-Prover-V2** explicitly **REJECTED for v0.5** by `04_math_reasoning.md`: "40–80 hours minimum to formalize HH ODEs in Lean4… not recommended for current sprint." Memory file `architecture_v05.md` already rejected Lean4. Concur.

**Offline LLM backup (when OpenRouter free quota hits 429)**:

- **Primary: `qwen3:30b-a3b` (Q4_K_M, ~6 GB)** — AIME 2025: 81.5%, native Korean fluency, MoE 3B-active so fast on M-series (20–40 tok/s). Already in `architecture_v05.md`.
- **Secondary: `deepseek-r1:8b-0528-qwen3-q4_K_M`** (~6 GB) — AIME 2025: 87.5% (highest per-GB), but always-on `<think>` blocks ⇒ strip in API response. Use specifically when SymPy says "wrong" and we need a step-by-step diagnosis.

`Qwen2.5-Math-72B` rejected (42 GB VRAM impractical), `Llemma-34B` rejected (2023 numbers obsolete), `phi-4-reasoning` rejected (Korean weak; only relevant if 8 GB Mac, which J doesn't have).

**HH gating ODE & Cable PDE specific verifier preprocessor** (mandatory):

```python
HH_SYMBOLS = {
  r'\alpha_n': 'alpha_n', r'\beta_n': 'beta_n',
  r'\alpha_m': 'alpha_m', r'\beta_m': 'beta_m',
  r'\alpha_h': 'alpha_h', r'\beta_h': 'beta_h',
  r'\bar{g}_{Na}': 'gNa_bar', r'\bar{g}_K': 'gK_bar',
  r'\lambda': 'lam', r'\tau': 'tau',
  r'V_m': 'Vm', r'V_{rest}': 'Vrest', r'V_{th}': 'Vth',
  r'C_m': 'Cm', r'I_{ion}': 'Iion',
}
# + regex \frac{\partial X}{\partial Y} → Derivative(X, Y)
```

Test cases from `04_math_reasoning.md` §"5 Test Cases" (HH gating sign flip, Nernst rearrangement, cable PDE escalation) become `tests/test_verify.py` on day one.

### 1.3 페다고지 패턴 (pedagogy patterns)

`01_ai_tutors.md` produced three "must-copy" patterns and two "anti-patterns." All five must be encoded.

**P1 — KELE consultant–teacher split.** Before generating any student-facing turn, run a Consultant agent that picks a Socratic move from a BRI610 taxonomy and emits a structured tag, e.g.

```json
{ "move": "prerequisite_check", "target": "Nernst equation",
  "reason": "student attempted GHK without Nernst basis" }
```

The Teacher agent then generates output constrained to that move. This is the missing piece in v0.4's single-prompt design and is the only non-trivial architectural change required for the pedagogy upgrade. Reduce KELE's 34 SocRules to a BRI610-specific set of **8 moves**: `analogy`, `prerequisite_check`, `derivation_prompt`, `counterexample`, `dimensional_analysis`, `limiting_case`, `direct_explanation_with_followup`, `socratic_exit`. (The last is the dignified-exit ramp that handles the NotebookLM/Khanmigo failure mode.)

**P2 — SocraticAI structured input gate.** For walkthrough mode and derivation mode, the student form **requires** three fields before the Tutor responds: `(a) what I currently understand`, `(b) what I tried`, `(c) where I am stuck`. Ashoka result: 75% substantive reflections in 3 weeks. This is implemented as a frontend form overlay + backend validation (reject empty fields before LLM call).

**P3 — Duolingo "Explain My Answer" post-hoc error explanation.** When SymPy returns `status: "wrong"`, do NOT generate a generic hint. Instead generate: (i) the specific algebraic error, (ii) the underlying misconception named in BRI610 vocabulary (e.g., "막전위 의존성 무시"), (iii) one targeted Socratic question. This is a two-step pipeline: `verify_equation()` → if wrong, `explain_my_answer()` agent with the SymPy residual + reference chunk as context.

**P4 — SocratiQ Bloom's-Taxonomy quiz generation, bounded RAG.** `01_ai_tutors.md` flags that SocratiQ's question distribution skewed low (42% Remembering, 5% Evaluating). Override that for a graduate STEM tutor: **explicit Bloom's-level forcing in the Quiz prompt** (Apply ≥30%, Analyze ≥30%, Evaluate ≥20%, Create ≥10%, Remember/Understand ≤10%). Bound retrieval to course materials only — already true via existing pgvector index; the new constraint is a system-prompt requirement that every claim must cite a `[Slide L# p#]` or `[Dayan&Abbott Ch.X §Y]` token.

**P5 — Mode lock (anti-anti-pattern from ChatGPT Study Mode failure).** Add a per-session `strict_mode` flag set per-route. In `walkthrough` mode the Socratic gate cannot be bypassed within a session, with audit-log of attempts. **However**, after N=3 failed hints, the `socratic_exit` move triggers automatically: the Tutor shows the full derivation and then asks the student to re-explain it in their own words. This is the dignified exit ramp that NotebookLM lacked.

**Pedagogy invariants from `pedagogy_invariants.md` (Korean primary, 3-step intuition→formalization→connection, citations) remain non-negotiable** and now propagate to all walkthrough and SRS code paths.

### 1.4 SRS & 학습 사이클

`05_srs_and_ux.md` is decisive: **FSRS-6 beats SM-2 for 99.6% of users** by log loss. SM-2's "ease hell" is especially bad for STEM where students press Hard repeatedly on derivation cards.

**Stack:**
- **Backend: `py-fsrs` 6.3.1** (MIT, Apache-style optimizer included). Wraps the 21-parameter DSR scheduler.
- **Frontend: `ts-fsrs` 5.3.2** (MIT) — runs scheduling in-browser during a session, no round-trip per card. Sync review logs to backend after session for optimizer.
- **Schema:** add `srs_cards` table per `05_srs_and_ux.md` §Synthesis 1.

**Card extraction strategy — graduate STEM specific (3 card types, NOT flashcards-from-text):**

| Card type | Trigger | Question | Answer |
|---|---|---|---|
| `recall` | Concept name (e.g., "막전위") | Define + write key equation from memory | LaTeX equation |
| `derive` | Step N of derivation | Equation at step N | Step N+1 |
| `equation_fill` | Display equation with one term blanked | LaTeX with `\boxed{?}` | The blanked term |

Granularity rationale: a concept-level "explain HH" card lets students pattern-match the final result and pass without remembering the gating-variable kinetics. Step-level cards force genuine retrieval.

**Initial card population: auto-extract from L5 HH lecture (8 ODEs ⇒ ~24 cards), L6 cable (4 derivation steps ⇒ ~12 cards), L3 Nernst+GHK (~10 cards). Total ~50 cards from the 4 highest-priority lectures (`lecture_priorities.md`).** Cold-start FSRS-6 default parameters until the user accumulates 200+ reviews.

### 1.5 UI/UX

`05_srs_and_ux.md` Synthesis 2 is decisive:

- **Display: keep KaTeX 0.16.45.** Synchronous render (~30 kB gzipped) is essential for SRS card-flip animations — MathJax's async model would flash. v0.4 already uses KaTeX; no change.
- **Input: MathLive 0.109.1** (`<math-field>` web component). MIT, 800+ commands, autocomplete. Bundle is 728 kB — load **only via `React.lazy()`** on the SRS review screen and the derive-attempt input. Initial page load stays <400 kB.
- **Korean IME guard (critical):** macOS 한글 IME's compositionstart/end events conflict with MathLive's shadow-DOM keyboard capture. Solution from `05_srs_and_ux.md` §Synthesis 2:
  1. `compositionstart` → set `el.mathVirtualKeyboardPolicy = "off"`
  2. `compositionend` → restore `"manual"`
  3. Korean annotations go in a **separate** `<textarea>` above the math-field, never typed into the math-field directly.
- **Detexify symbol palette** (PARTIAL-ADOPT): embed the browser-side classifier as a "?" button next to the math-field for symbol lookup. ~150 kB extra, ~50 LOC.
- **Reject MathQuill** (abandoned), **MyScript** (no tablet hardware), **Seshat** (abandoned), **CodeCogs** (image-based, breaks React model).

---

## Part 2: Refined Candidate Plans

Three plans, each grounded in the benchmark data above.

### Plan A: "Pragmatic + 핵심 검증" (~8–10 dev-days)

**Thesis (200 words).** v0.4 ships and works; the highest-leverage missing capability is **derivation correctness**, not parser overhaul or pedagogy framework. Plan A spends one day fixing the 7 known bugs, then invests the remainder into the SymPy verifier cascade and FSRS SRS, leaving parser and embedding as v0.4. L8 ingestion uses existing PyMuPDF (acceptable: L8 is concept-heavy, only 3 equation hits per `lecture_priorities.md`). The pedagogy upgrade is limited to the **single-highest-leverage** pattern from `01_ai_tutors.md`: SocraticAI's structured input gate. KELE consultant-teacher split is deferred to v0.6. This plan is the smallest viable v0.5 that meaningfully advances exam prep utility (FSRS + SymPy diagnostic on derivations + L8 in DB). Risk profile is lowest because it touches the fewest subsystems, but its ceiling is correspondingly limited: equation-page retrieval quality stays at v0.4 baseline (PyMuPDF garbage on HH pages will continue to confuse retrieval), and pedagogy depth doesn't materially improve.

**Stack.**
- Parser: PyMuPDF (keep). MinerU only invoked manually via CLI on demand.
- Embedding: Nemotron VL only (keep).
- Verification: SymPy + Wolfram Engine fallback. No WolframAlpha (skip 3rd tier).
- Pedagogy: SocraticAI structured input gate only. No KELE split.
- SRS: py-fsrs 6.3.1 server-side; ts-fsrs frontend. ~50 hand-curated cards.
- UI: KaTeX (keep) + MathLive (lazy-loaded for SRS only). No Detexify.
- Offline LLM: qwen3:30b-a3b only (no DeepSeek-R1 secondary).

**Atomic steps & LOC.**
1. Fix 7 v0.4 bugs (`pipeline/schema.sql`, `frontend/src/api.js`, `SearchPanel`, `SlideViewer`, `retriever.py` ×2, `search_lectures.py`, CORS) — ~150 LOC. (1 day)
2. L8 ingest via existing `pipeline_harness.py parse` — 0 LOC pipeline change, 1 SQL row insert config. (0.5 day)
3. SymPy preprocessor + `verify_equation()` + 5 test cases in `tests/test_verify.py` — ~120 LOC. (1 day)
4. Wolfram Engine integration in `backend/wolfram_client.py` with kernel pool — ~80 LOC. (1 day)
5. Wire verifier into Derive agent: extract `$$...$$` blocks, annotate in API response — ~60 LOC in `backend/agents.py`. (0.5 day)
6. Structured input gate frontend form (3 fields) — ~80 LOC in new `DeriveAttempt.jsx` + 30 LOC backend validation. (0.5 day)
7. py-fsrs scheduler + `srs_cards` schema + `/api/srs/*` endpoints — ~200 LOC. (1.5 days)
8. ts-fsrs frontend hook + `SRSPanel.jsx` review UI — ~250 LOC. (1.5 days)
9. MathLive lazy-loaded `<MathInput>` component with Korean IME guard — ~80 LOC. (0.5 day)
10. Card seeder script: extract 50 cards from L5/L6/L3 lecture content via Ollama — ~100 LOC. (1 day)
11. Ollama qwen3:30b-a3b fallback in `agents._llm()` (catch 429, route to local) — ~40 LOC. (0.5 day)
12. End-to-end smoke test + memory updates — (0.5 day)

**Total: ~9 dev-days, ~1190 LOC.**

**Risks.** (i) PyMuPDF garbage on HH pages keeps confusing retrieval ⇒ Tutor may quote corrupted text; (ii) Korean IME guard is fragile (macOS Sonoma 한글 vs Sequoia behavior differs); (iii) FSRS cold-start may schedule poorly for first 50–100 reviews.

### Plan B: "Foundational Quality + Pedagogy" (~12–15 dev-days)

**Thesis (200 words).** Treat v0.5 as the cleanup-and-foundation release. Re-parse all equation pages with MinerU (CDM 97.45 vs PyMuPDF garbage), add Qwen3-Embedding-8B as a second text-embedding column (MMTEB 70.58 #1 ⇒ Korean+English STEM retrieval lift), implement SymPy cascade verifier, AND adopt KELE consultant-teacher split for the Tutor + Derive agents (the two most pedagogically-loaded), AND SocratiQ Bloom's-forced quiz generation. Add FSRS-6 SRS with full 50-card seed. Ceiling is highest of the three plans: every subsystem moves to 2026 SOTA. Cost is real: dual-column pgvector reindex, ~17 min one-time re-parse, two new agents (Consultant + Explain-My-Answer), and integration testing across all of them. Under the 5h Claude rate limit + auto mode this is achievable in two weeks if Sonnet executes the pattern work (parser dispatcher, embedding pipeline, SRS schema) and Opus reserves itself for the architectural pieces (consultant-teacher split, structured input gate, mode lock state machine).

**Stack.**
- Parser: MinerU (textbook equation) + Marker+Ollama (slides) + PyMuPDF (prose). Dispatcher in `pipeline_harness.py`.
- Embedding: dual-column. Nemotron VL `image_embedding` (keep) + Qwen3-Embedding-8B `text_embedding_v2` (add, 1024-dim MRL). A/B at retrieval.
- Verification: SymPy → Wolfram Engine → WolframAlpha (full 3-tier).
- Pedagogy: KELE consultant-teacher split (Tutor + Derive agents) + SocraticAI gate + Duolingo Explain-My-Answer + SocratiQ Bloom's quiz + mode lock.
- SRS: py-fsrs + ts-fsrs full stack, 50-card seed.
- UI: KaTeX + MathLive (lazy) + Detexify palette + Korean IME guard.
- Offline LLM: qwen3:30b-a3b primary + deepseek-r1:8b-0528 secondary.

**Atomic steps & LOC.** Phases P0–P5. Detailed in Part 5 below if selected. Top-line: ~14 dev-days, ~2400 LOC.

**Risks.** (i) MinerU local pipeline backend formula CDM is not separately published; if it underperforms hosted-Pro 97.45 by >10 pts on our HH pages, Mathpix fallback budget grows; (ii) Qwen3-8B Q4_K_M on 16 GB Mac is tight (~4.5 GB + 8 GB OS); may need Q4_K_M ⇒ Q5_K_M for accuracy or Qwen3-4B downgrade; (iii) consultant-teacher split doubles LLM calls per turn ⇒ OpenRouter free quota burns ~2× faster.

### Plan C: "Pedagogy-First Multi-Agent" (~10–13 dev-days)

**Thesis (200 words).** The benchmarks reveal that the single biggest user-impact lever for an LLM-tutor is the **pedagogical interaction model**, not parser fidelity or SRS sophistication. Khanmigo, Study Mode, NotebookLM all converge to the same anti-pattern (Socratic withholding without exit) and KELE's 9-dimension eval consistently shows multi-agent planning beats single-prompt by large margins. Plan C invests heavily in the consultant-teacher split for ALL five existing agents (Router stays single, but Tutor / Derive / Quiz / Exam / Summary each get a Consultant pre-pass), the structured input gate, the mode lock with dignified exit, and the post-hoc Explain-My-Answer pattern. Parser/embedding stay v0.4 except: re-parse only L5 HH (the highest-priority equation lecture, `lecture_priorities.md`) with MinerU as a quality-of-evidence proof-of-concept. SRS is shipped with FSRS-6 + SymPy verifier as in Plan A. The pedagogy infrastructure built here is reusable for v0.6 when parser overhaul lands. Risk: the consultant-teacher split is the most architecturally invasive change of any plan and is the area with the least production reference (KELE has not released code).

**Stack.**
- Parser: PyMuPDF (keep) + MinerU on L5 only (~3 min compute, $0).
- Embedding: Nemotron VL only (defer Qwen3 to v0.6).
- Verification: SymPy + Wolfram Engine.
- Pedagogy: **KELE split for ALL 5 agents** + SocraticAI gate + Duolingo Explain-My-Answer + SocratiQ Bloom's + mode lock + dignified exit ramp.
- SRS: py-fsrs + ts-fsrs.
- UI: KaTeX + MathLive (lazy) + Korean IME guard. No Detexify.
- Offline LLM: qwen3:30b-a3b.

**Atomic steps & LOC.** ~12 dev-days, ~2100 LOC.

**Risks.** (i) Reverse-engineering KELE's SocRules without released code may produce a strategy taxonomy that doesn't match research claims; (ii) 2× LLM calls per turn (consultant + teacher) for all 5 agents = ~5× v0.4 quota burn; (iii) without parser fix, retrieval still surfaces garbled HH equations to the Consultant, who may select an irrelevant move.

---

## Part 3: Cross-Critique

**A vs B.** Plan A under-invests in the parser. PyMuPDF's "CmdVdt=−Iion" garbage on HH pages is the single most-cited concrete failure in `02_pdf_parsers.md` §8 and the v0.4 audit. With the Tutor citing `[Dayan&Abbott Ch.5]` chunks that are corrupted, no amount of SymPy verification downstream rescues retrieval quality — the LLM is hallucinating from garbage. Plan B's 17-minute MinerU re-parse fixes this at $0 cost. Conversely, Plan B's Qwen3 dual-column adds risk (RAM pressure on 16 GB Mac, dimension migration) for retrieval quality gains we can't yet quantify on our specific Korean+EN STEM corpus. A's pragmatism understates the parser fix; B's foundational scope adds embedding work that arguably belongs in v0.6 after a measured A/B test on real student queries.

**B vs C.** B and C agree on SymPy + FSRS + SocraticAI gate but diverge on parser and pedagogy depth. B fixes the parser broadly (all equation pages); C fixes only L5. C bets that pedagogy is higher-leverage than retrieval cleanliness. The benchmark evidence is mixed: KELE's 9-dim eval beat GPT-4o on Socratic dimensions but not on factual grounding, while NotebookLM's source-grounded approach scored highest on student-reported usefulness. For BRI610's exam-prep target, factual grounding (correct HH equations from textbook) probably matters more than dialogue strategy depth — favoring B. Also, applying KELE split to all 5 agents (C) versus just Tutor+Derive (B) is over-engineered: Quiz and Exam agents emit JSON/structured output where Socratic strategy selection has no obvious effect.

**A vs C.** Both keep parser at v0.4 baseline. A invests dev-days in SRS + verifier cleanly; C invests them in consultant-teacher infrastructure. A is shippable in week 1; C requires the architecturally most invasive change in any plan and has no reference implementation (KELE code unreleased). A's ceiling is strictly lower than C's on the pedagogy axis, but A's floor is higher (less can break). For a graduate user who needs the tutor working before exams, A's predictability is valuable. For a multi-month research project, C's foundation is more durable. The user is closer to the former scenario (BRI610 final exam season approaches per `lecture_priorities.md`).

---

## Part 4: SELECTION

### Selected: **Plan B "Foundational Quality + Pedagogy"**, with one tactical concession from C.

**Concession**: KELE consultant-teacher split is applied to **Tutor + Derive only** (B's scope), not all 5 agents (C's scope). Quiz/Exam/Summary keep v0.4 single-prompt design — they emit structured output where strategy-selection has no leverage.

### Reasoning (300 words)

Weighting the criteria explicitly:

- **(1) User impact for graduate exam prep — 40%.** B wins decisively. The MinerU re-parse fixes the single most-cited concrete defect (PyMuPDF garbage on HH equations) which directly degrades every Tutor and Derive response on the highest-priority lectures (L5/L3/L4/L6). The Qwen3-8B text-embedding column adds Korean+English STEM retrieval lift on top — measurable via the A/B harness in `03_embeddings.md` §A/B Test Design. Pedagogy improvements (consultant-teacher, structured gate, Explain-My-Answer) compound on a clean retrieval base.

- **(2) Completion probability in <2–3 weeks under 5h Claude rate + auto mode — 25%.** B is 14 dev-days, A is 9, C is 12. All three are nominally feasible in 3 weeks. B's risk surface is largest but the riskiest piece (parser dispatcher) is pattern work delegable to Sonnet (per `feedback_opus_delegation.md`), preserving Opus budget for the architectural pieces (consultant-teacher split, mode lock state machine).

- **(3) Foundation for future iteration — 15%.** B builds Qwen3 embedding + parser dispatcher + KELE-pattern infrastructure. v0.6 features (Lean4 verifier, full multi-agent, voice input) all sit cleanly on this base. A defers all of these. C builds pedagogy infra but leaves the data-quality foundation cracked.

- **(4) Cost — 10%.** B parser re-parse: $0 (local). B embedding: $0 (Ollama local). 2× LLM calls for consultant-teacher in Tutor/Derive: doubles quota burn for those routes only — manageable with Ollama qwen3:30b-a3b fallback. Mathpix budget ceiling: <$0.50 if MinerU local underperforms.

- **(5) Risk of regressing v0.4 — 10%.** Dual-column embedding is ADDITIVE (keep Nemotron VL). Parser re-parse is incremental (per page-type). KELE split is OPT-IN per agent (Tutor/Derive only). All changes are gated behind feature flags and the 7 v0.4 bugs are fixed first.

**Decisive tiebreaker.** Plan A's choice to leave PyMuPDF garbage in place is a false economy: it means the SRS cards we extract in Plan A are extracted from corrupted textbook chunks. We'd be embedding wrong equations into the FSRS state. Plan B fixes the data foundation first.

---

## Part 5: 최종 Atomic Decomposition (Plan B + C concession)

### Phase P0 — Pre-flight bug fixes (1 day, parallelizable)

| ID | Task | Files | LOC | Verify | Deps |
|---|---|---|---|---|---|
| **P0.1** | Add `lecture_summaries` DDL | `pipeline/schema.sql` | +25 | `psql -f schema.sql` clean; `/api/summaries/L3/generate` returns 200 | — |
| **P0.2** | Fix `SearchPanel` source filter | `frontend/src/api.js` (sig), `frontend/src/components/SearchPanel.jsx` | ±15 | Search "HH" with source=textbook returns only DA/FN | — |
| **P0.3** | Derive `LECTURE_PAGES` from `/api/lectures` | `frontend/src/components/SlideViewer.jsx` | ±30 | L8 (74 p) appears after ingestion without code edit | P5.1 |
| **P0.4** | Add psycopg2 ThreadedConnectionPool | `backend/db.py`, `backend/retriever.py` | +50 | Concurrent `/api/chat` ×10 doesn't exhaust max_connections | — |
| **P0.5** | Add `WHERE lecture=%s` in `_vector_search_slides` | `backend/retriever.py:82-96` | +5 | Slide search with `lecture=L5` returns only L5 rows | — |
| **P0.6** | Unhardcode path in `search_lectures.py` | `pipeline/search_lectures.py:11` | ±5 | Runs without `/home/claude` symlink | — |
| **P0.7** | Tighten CORS to localhost + deploy origin | `backend/main.py:26` | ±5 | Curl from foreign origin gets blocked | — |

### Phase P1 — Parser dispatcher (2 days)

| ID | Task | Files | LOC | Verify | Deps |
|---|---|---|---|---|---|
| **P1.1** | Add `parser` arg to `parse_textbook()`; dispatcher branch | `pipeline/pipeline_harness.py:228-326` | +60 | `--parser pymupdf` (default) preserves v0.4 behavior; CI green | P0 |
| **P1.2** | Implement `_parse_mineru()` (subprocess + JSON ingest) | `pipeline/parsers/mineru.py` (new) | ~180 | DA Ch.5 page 119 (HH gating) outputs `\frac{dn}{dt}=\alpha_n(V)(1-n)-\beta_n n` not "CmdVdt=−Iion" | P1.1 |
| **P1.3** | Implement `_parse_marker()` w/ Ollama LLM mode | `pipeline/parsers/marker.py` (new) | ~140 | L5 slide page 18 outputs LaTeX equation block | P1.1 |
| **P1.4** | Re-parse DA Ch.5–7 with MinerU; FN equation pages | CLI invocation, no code | 0 | DB `textbook_pages.content` for ~320 equation pages contains `$$` blocks; `has_eq_garbage()` <5% | P1.2 |
| **P1.5** | Re-parse all lecture slides L2–L6 with Marker | CLI invocation | 0 | Slide content has LaTeX, not Unicode garbage | P1.3 |
| **P1.6** | Add `equation_has_latex` QC check | `pipeline/pipeline_harness.py` QC dict | +15 | Failed pages flagged `manual_eq` for fallback | P1.4 |

### Phase P2 — Embedding dual-column + L8 ingest (1.5 days)

| ID | Task | Files | LOC | Verify | Deps |
|---|---|---|---|---|---|
| **P2.1** | ALTER TABLE add `text_embedding_v2 vector(1024)` + HNSW index | `pipeline/schema.sql` (ALTER) | +12 | `\d textbook_pages` shows new column | P0 |
| **P2.2** | Pull `qwen3-embedding:8b` via Ollama; smoke test | shell only | 0 | `ollama run qwen3-embedding:8b "test"` returns 4096-dim | — |
| **P2.3** | Add `embed_qwen3()` w/ MRL @ 1024-dim | `pipeline/embedders/qwen3.py` (new) | ~110 | 1024-dim float32 numpy array per page | P2.1, P2.2 |
| **P2.4** | Re-embed all `textbook_pages` into `text_embedding_v2` (Ollama, batched 50) | CLI | 0 | `SELECT count(*) WHERE text_embedding_v2 IS NOT NULL` = 1304 | P2.3, P1.4 |
| **P2.5** | Ingest L8 (74 p) lecture: parse w/ Marker → embed Nemotron (image) + Qwen3 (text) | CLI | 0 | `slides WHERE lecture='L8'` count = 74; both embeddings populated | P1.3 |
| **P2.6** | Add `text_v2` retrieval branch to HybridRetriever; expose `embedding_version` flag | `backend/retriever.py` | +50 | `/api/chat?embed=v2` returns different top-k than v1; logged | P2.4 |
| **P2.7** | Build A/B harness: 80 manually-annotated queries, nDCG@5 paired Wilcoxon | `scripts/embed_ab.py` (new) | ~150 | Output JSON with v1 vs v2 nDCG@5 per query | P2.6 |

### Phase P3 — SymPy verifier cascade (1.5 days)

| ID | Task | Files | LOC | Verify | Deps |
|---|---|---|---|---|---|
| **P3.1** | LaTeX preprocessor (HH/cable symbol map + partial→Derivative) | `backend/verify/preprocess.py` (new) | ~80 | All 5 test cases from `04_math_reasoning.md` §"5 Test Cases" pass | — |
| **P3.2** | `sympy_verify()` w/ ThreadPoolExecutor 5s timeout | `backend/verify/sympy_check.py` (new) | ~70 | TC-1..TC-4 return verified/wrong; TC-5 returns timeout/unverified | P3.1 |
| **P3.3** | Wolfram Engine kernel pool + `wolfram_verify()` | `backend/verify/wolfram_check.py` (new) | ~120 | TC-5 (cable PDE `\partial`) returns verified via WL fallback | P3.1 |
| **P3.4** | Cascade dispatcher: SymPy → Wolfram → mark unverified | `backend/verify/__init__.py` | ~40 | Each layer logged with timing | P3.2, P3.3 |
| **P3.5** | `tests/test_verify.py` with 5 TCs + HH 4-ODE system + cable PDE | `tests/test_verify.py` (new) | ~90 | `pytest tests/test_verify.py` 100% pass | P3.4 |

### Phase P4 — Pedagogy: KELE split + structured gate + Explain-My-Answer (3 days)

| ID | Task | Files | LOC | Verify | Deps |
|---|---|---|---|---|---|
| **P4.1** | Define BRI610 SocRule taxonomy (8 moves) | `backend/agents/socrules.py` (new) | ~60 | Imported by Consultant; 8 move IDs validated | — |
| **P4.2** | Implement Consultant agent (strategy selector, low-temperature 0.0) | `backend/agents/consultant.py` (new) | ~120 | Given a fake student turn, emits `{move, target, reason}` JSON | P4.1 |
| **P4.3** | Refactor Tutor agent to consume `move` tag; constrain output | `backend/agents.py` (Tutor section) | +80 / -30 | Tutor with `move=analogy` does not produce derivation | P4.2 |
| **P4.4** | Refactor Derive agent for consultant pass | `backend/agents.py` (Derive section) | +60 / -20 | Derive with `move=dimensional_analysis` runs unit-check | P4.2 |
| **P4.5** | Structured input gate: 3-field form `<DeriveAttempt>` | `frontend/src/components/DeriveAttempt.jsx` (new) | ~120 | Empty fields ⇒ submit button disabled; backend rejects on bypass | — |
| **P4.6** | Backend validation: reject derive POST if any of 3 fields empty | `backend/main.py` | +30 | Curl with empty `tried` returns 422 | P4.5 |
| **P4.7** | Explain-My-Answer agent: SymPy `wrong` ⇒ contextualized error explanation | `backend/agents/explain.py` (new) | ~110 | When student sends sign-flipped HH gating ODE, response names the misconception in Korean | P3.4, P4.2 |
| **P4.8** | Mode lock state machine: per-session strict_mode + dignified exit at N=3 | `backend/session/mode.py` (new) + `agents.py` | ~90 | After 3 hint cycles, `move=socratic_exit` triggers full derivation + re-explain prompt | P4.2 |
| **P4.9** | Bloom's-forced quiz prompt update | `backend/agents.py` (Quiz section) | +25 / -10 | 10-question batch on L5 has ≥3 Apply, ≥3 Analyze, ≥2 Evaluate | — |

### Phase P5 — SRS + UI (2.5 days)

| ID | Task | Files | LOC | Verify | Deps |
|---|---|---|---|---|---|
| **P5.1** | `srs_cards` table DDL (per `05_srs_and_ux.md` §Synthesis 1) | `pipeline/schema.sql` | +35 | `\d srs_cards` shows DSR columns | P0.1 |
| **P5.2** | py-fsrs `Scheduler` wrapper + `/api/srs/review` POST | `backend/srs/scheduler.py` (new), `backend/main.py` | ~140 | POST `{card_id, rating: 3}` returns updated due/stability/state | P5.1 |
| **P5.3** | `/api/srs/queue` GET (due cards for user) | `backend/main.py` | +40 | Returns due cards in due-date order | P5.2 |
| **P5.4** | Card seeder: extract 50 cards from L5/L6/L3 via Ollama qwen3:30b-a3b | `scripts/seed_srs_cards.py` (new) | ~180 | DB has ≥50 rows w/ types `recall|derive|equation_fill` | P1.4, P2.5 |
| **P5.5** | ts-fsrs frontend hook + `useReviewSession` | `frontend/src/hooks/useReviewSession.ts` (new) | ~100 | Local scheduler matches backend on identical input | P5.2 |
| **P5.6** | `<SRSPanel>` review UI w/ MathLive answer input | `frontend/src/components/SRSPanel.jsx` (new) | ~250 | Card flip animation; submit ⇒ FSRS update + next card | P5.5, P5.7 |
| **P5.7** | `<MathInput>` lazy-loaded MathLive w/ Korean IME guard | `frontend/src/components/MathInput.tsx` (new) | ~80 | `compositionstart` ⇒ keyboard policy off; Korean typing in adjacent textarea works | — |
| **P5.8** | Tab #7 "복습 (SRS)" added to `App.jsx` | `frontend/src/App.jsx` | +15 | Tab loads `<SRSPanel>` lazily | P5.6 |

### Phase P6 — Offline LLM fallback + smoke test (1 day)

| ID | Task | Files | LOC | Verify | Deps |
|---|---|---|---|---|---|
| **P6.1** | Ollama client w/ qwen3:30b-a3b + deepseek-r1:8b-0528 | `backend/llm/ollama_client.py` (new) | ~90 | `await client.generate("test")` returns text | — |
| **P6.2** | Catch 429 from OpenRouter ⇒ route to Ollama | `backend/agents.py` `_llm()` | +40 | Inject 429; next call uses Ollama; log fallback event | P6.1 |
| **P6.3** | Strip `<think>` blocks from DeepSeek-R1 output | `backend/llm/ollama_client.py` | +20 | Output never contains `<think>` | P6.1 |
| **P6.4** | E2E smoke: walkthrough L5 HH, derive Nernst, quiz L3, SRS review | manual via curl + frontend | 0 | All routes return 200 with verified equations | all |
| **P6.5** | Update memory files: `architecture_v05.md` (parser change), `bugs_v04_known.md` (mark fixed) | memory/*.md | ±50 | `MEMORY.md` index intact | P6.4 |

**Total Plan B+ scope: ~32 atomic steps, ~14 dev-days, ~2400 LOC.**

---

## Part 6: 데이터 기반 risks & mitigations

### Risk 1: MinerU local pipeline backend formula CDM lower than hosted-Pro 97.45

- **Description**: Per `02_pdf_parsers.md` §2 Weakness 1, the 97.45 CDM is for MinerU2.5-Pro hosted; the local `pipeline` backend is "more modestly ~85 overall" without separate formula CDM. Our HH/cable pages may show degraded LaTeX vs the benchmark suggests.
- **Probability**: Medium.
- **Impact**: Medium — degrades the parser-fix value of Plan B but doesn't invalidate it (85 is still >> PyMuPDF 6.67).
- **Mitigation**: After P1.4, run `equation_has_latex` QC (P1.6) and any failed page falls back via Mathpix at $0.002/page. Budget ceiling ~$0.50 for ~250 fallback pages (well within free-tier credits implied by user constraint).

### Risk 2: Qwen3-Embedding-8B Q4_K_M (~4.5 GB) tight on 16 GB Mac with Ollama LLM also loaded

- **Description**: `03_embeddings.md` §2 Weakness 1: "Memory-heavy locally: 8B parameters require ~16GB RAM (Q8 quant ~8.5GB) — tight on 16GB M-series." Running qwen3:30b-a3b (~6 GB) + Qwen3-Embedding-8B Q4_K_M (~4.5 GB) + OS + browser ≈ 14–15 GB used.
- **Probability**: High.
- **Impact**: Low if managed (swap), Medium if it causes Ollama OOM during a long re-embed batch.
- **Mitigation**: Run re-embed (P2.4) as a discrete batch step with no other Ollama model loaded; use `ollama stop` between embed and LLM phases. If still tight, downgrade to **Qwen3-Embedding-4B** (MMTEB 69.45, ~2.2 GB) per `03_embeddings.md` §3 — accuracy gap is only 1.13 points.

### Risk 3: Consultant-teacher split doubles LLM calls for Tutor/Derive routes ⇒ OpenRouter free quota burns ~2× faster

- **Description**: `01_ai_tutors.md` §5 KELE notes the framework requires two LLM calls per user turn. v0.4 currently makes ~1 call per turn for Tutor/Derive. Quiz/Exam/Summary still 1 call (per Plan B+ concession). Net: ~1.5× quota burn for typical session.
- **Probability**: Certain (by design).
- **Impact**: Medium — risks 429 errors during exam-prep sessions.
- **Mitigation**: P6.2 routes 429 to Ollama qwen3:30b-a3b automatically. Consultant call uses temperature 0.0 + max_tokens 200 (small response) which is cheap. Cache strategy decisions for identical (recent_history, student_input) keys for 30 min — ~50% reuse expected on derivation walkthroughs.

### Risk 4: KELE SocRule taxonomy reverse-engineered without released code

- **Description**: `01_ai_tutors.md` §6 KELE Verdict: "no code release… reconstruct from paper." 8-move BRI610 taxonomy (P4.1) is our interpretation; no external benchmark to validate.
- **Probability**: Medium.
- **Impact**: Medium — could produce strategy selections that feel arbitrary to the user.
- **Mitigation**: Treat the 8-move taxonomy as v0.5.0 and explicitly version it; collect telemetry on which moves correlate with positive student responses (`/api/srs/review` rating after a tutor turn). Iterate the move set in v0.5.1 based on data. SocratiQ's 9-dim eval framework (`01_ai_tutors.md` §5 KELE Strengths 5) provides reusable evaluation methodology.

### Risk 5: Korean IME guard works on macOS Sonoma but breaks on Sequoia

- **Description**: `05_srs_and_ux.md` §3 MathLive Weakness 2: composition events conflict with shadow DOM is a documented but solved-per-version issue. macOS 한글 IME behavior changed between OS versions.
- **Probability**: Low–Medium.
- **Impact**: Medium — Korean students cannot type bilingual annotations alongside equations.
- **Mitigation**: Architectural solution from `05_srs_and_ux.md` §Synthesis 2 — separate `<textarea>` for Korean, `<math-field>` for LaTeX. This bypasses the composition conflict entirely (no Korean is typed into the math-field). Plus `compositionstart`/`end` listeners as belt-and-suspenders. Test on both macOS versions before merging P5.7.

---

## Part 7: Kickoff checklist (immediate next 5 steps)

When implementation starts, do these in order, parallelizing where indicated:

1. **P0 bug-fix sweep** (parallel, all 7 in one commit) — fixes `lecture_summaries`, `SearchPanel`, `LECTURE_PAGES`, conn pool, vector lecture filter, hardcoded path, CORS. Sonnet via `Agent` tool can execute these in parallel since they touch independent files. Estimated: 2–3 hours wall clock. **Commit message**: `fix: pre-v0.5 critical regressions (7 bugs)`.

2. **P1.1 + P1.2 + P1.4 — MinerU re-parse of DA Ch.5–7** — install `mineru` (`pip install mineru`), implement dispatcher branch + `_parse_mineru()`, run on 120 pages. This validates the parser pipeline on the highest-priority content (HH gating). **Verification**: spot-check DA Ch.5 page 119 in DB — content must contain `\frac{dn}{dt}=\alpha_n(V)(1-n)-\beta_n n` not "CmdVdt=−Iion". If MinerU local backend formula CDM fails QC, escalate to Risk 1 mitigation.

3. **P3.1 + P3.2 + P3.5 — SymPy preprocessor + verifier + 5 test cases**. The 5 test cases from `04_math_reasoning.md` are concrete; this is the smallest, most independently-testable unit in the entire plan. Ship before any agent integration. **Verification**: `pytest tests/test_verify.py` 100% green.

4. **P2.1 + P2.2 + P2.3 — Schema migration + Qwen3 pull + embedder wrapper**, but **DO NOT yet run P2.4 re-embed**. Land the schema + code; re-embed batch happens in step 5 below after verifying RAM headroom. **Verification**: `\d textbook_pages` shows `text_embedding_v2 vector(1024)`; `embed_qwen3("test")` returns 1024-dim numpy.

5. **P5.1 + P5.2 — `srs_cards` table + py-fsrs `/api/srs/review`**. SRS backend is independent of all other phases and unblocks frontend (P5.5–P5.8) work in parallel by Sonnet. **Verification**: POST a synthetic card review, observe DSR state update + `due` advancement consistent with FSRS-6 default parameters.

After these 5, the parallel decomposition opens up: P1.3+P1.5 (slides re-parse), P2.4+P2.7 (embedding re-batch + A/B), P3.3+P3.4 (Wolfram fallback + cascade), and P4 series (pedagogy) can all proceed in parallel via Sonnet subagents while Opus reserves itself for P4.2 (Consultant agent design — judgment-heavy), P4.8 (mode lock state machine — irreversible architecture), and P5.6 (SRS review UX — design-heavy).

---

*References: `01_ai_tutors.md` (KELE consultant-teacher, SocraticAI structured gate, SocratiQ Bloom's, Duolingo Explain-My-Answer, Khanmigo/NotebookLM Socratic anti-pattern); `02_pdf_parsers.md` (MinerU CDM 97.45, Marker 85.24, PyMuPDF 6.67); `03_embeddings.md` (Qwen3-8B MMTEB 70.58 #1, dual-column schema); `04_math_reasoning.md` (SymPy + Wolfram + WolframAlpha cascade, qwen3:30b-a3b AIME 81.5%, deepseek-r1:8b 87.5%); `05_srs_and_ux.md` (FSRS-6 99.6% superiority, KaTeX synchronous + MathLive lazy + Korean IME guard); memory: `architecture_v05.md`, `bugs_v04_known.md`, `lecture_priorities.md`, `pedagogy_invariants.md`.*
