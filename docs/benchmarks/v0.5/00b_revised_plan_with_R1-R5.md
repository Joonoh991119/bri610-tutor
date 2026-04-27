# v0.5 Revised Plan — R1–R5 + Agent Harness + Multi-Lens Review

**Author**: Opus architect revision
**Date**: 2026-04-26
**Supersedes**: `00_integrated_synthesis_and_plan.md` (Plan B+ with C concession)
**Inputs added since 00**: `feedback_v05_user_requirements.md` (R1–R5 + harness + Multi-Lens Review)

This document is a delta on top of `00_integrated_synthesis_and_plan.md`. Everything in the original plan that is not modified here remains in force. Where this document changes scope, it cites the original atomic step ID (e.g., `P4.9`) so the prior decomposition stays traceable.

---

## 1. R1–R5 + Harness + Multi-Lens Review impact analysis

### R1 — Math/image perfection (figures-as-first-class)

**Modifies**: P1 (parser dispatcher) — MinerU output now must surface bounding boxes and figure crops, not only LaTeX text. P4.3 (Tutor refactor) — Tutor system prompt extended with `<figure src=…>` rule. P5.6 (SRS UI) — card render must support figure rendering.
**Adds NEW**: **P7-figures** sub-phase: `extract_figures.py` block-level pipeline → cropping → `figures` table → embedding (Nemotron VL on the crop, Qwen3 on caption). New frontend `<FigureRenderer>` component with click-to-zoom + page-back-link. Fallback chain for "diagram requested but none in DB": Chrome MCP web image search → manual approval queue → ASCII-with-disclaimer (last resort, never silent).
**Est'd added LOC**: ~520 (300 pipeline + 90 backend + 130 frontend).
**Est'd added dev-days**: **+2.0**.

### R2 — Curated, team-reviewed question bank, no hallucination

**Modifies**: P4.9 (Bloom's-forced quiz) — the on-the-fly Quiz prompt is **deleted**, replaced by a static-bank delivery layer. The `Quiz` agent becomes a `BankSelector` agent (chooses items from `question_bank` by FSRS state + mastery + topic gap). Adaptive difficulty stays adaptive at delivery time; generation is offline.
**Adds NEW**: **P7 — Question bank pipeline** (Generator → Fact Checker → Pedagogy Critic → Priority Scorer → Multi-Lens Review → bank). `question_bank` table, `question_review_log` table, batch CLI `scripts/generate_bank.py` per topic, nightly daemon to re-review existing items.
**Est'd added LOC**: ~880 (420 generator/critics/scorer + 200 multi-lens loop + 130 CLI + 130 backend selector).
**Est'd added dev-days**: **+3.5** (bank pre-generation is offline-batch-heavy and review-iteration-heavy).

### R3 — Interactive, addictive UI + persona

**Modifies**: P5.6 (SRS panel) — wraps card flips in Framer Motion; level-up celebration on streak threshold; persona narrator wraps every Tutor response. P0 schema — `users` table extended.
**Adds NEW**: **P8 — Persona + gamification + dashboard**. `frontend/src/persona/` module with character (`뉴런쌤`, default; J can rename), encouragement-line library, mascot SVG, voice-tone style guide for the Tutor system prompt. Backend persona narrator agent (post-processor: takes Tutor JSON output and injects persona voice in Korean). Streak/XP/level state machine, achievement-badge rules engine, mastery-heatmap dashboard component.
**Est'd added LOC**: ~620 (160 persona module + 180 gamification state + 280 dashboard/heatmap).
**Est'd added dev-days**: **+2.5**.

### R4 — 4 diverse study modes per concept

**Modifies**: P5.4 (card seeder, was 3 types) — card type enum **expands from 3 to 4**: `recall | concept | application | proof` (the v0 plan had `recall|derive|equation_fill`; `derive` and `equation_fill` collapse into `proof`, and `concept` + `application` are new). P5.1 schema migration adds CHECK constraint for the 4 enum values. P7 bank generator must produce all 4 types per topic with declared coverage targets (e.g., HH: 8 recall + 6 concept + 8 application + 6 proof = 28 items, similar for cable).
**Adds NEW**: Daily-mix algorithm in `backend/srs/daily_mix.py` weighted by per-type mastery (`mastery` table). Cable theory & Membrane Equation explicitly listed as named seed topics in `scripts/generate_bank.py` config.
**Est'd added LOC**: ~240 (40 schema + 110 daily_mix + 90 generator type-coverage logic).
**Est'd added dev-days**: **+1.0** (mostly absorbed inside P7).

### R5 — Foundation prereq education (ODE / PDE / neuron structure)

**Modifies**: None directly — purely additive.
**Adds NEW**: **P9 — Foundation prereq ingestion + diagnostic routing**. New `foundation_content` table; ingestion CLI pulls from 3 named sources via Chrome MCP (3Blue1Brown DiffEq YouTube transcripts via the `scilingo-youtube-transcript` skill, Strogatz textbook excerpts where openly licensed, Kandel principle summaries via published OCW). Diagnostic agent (mastery-gap detector) runs after every walkthrough turn and on session start; if a prereq concept is detected as weak (< threshold mastery), router surfaces a foundation card before the next main-track card. `is_prereq=true` flag on bank items.
**Est'd added LOC**: ~510 (200 ingestion + 130 diagnostic + 100 router + 80 frontend cue).
**Est'd added dev-days**: **+2.5** (Chrome MCP + transcript path + content-licensing care).

### Harness + hooks

**Modifies**: All agent call sites in `backend/agents.py` — wrapped behind hook registry calls.
**Adds NEW**: **P10 — Hook system + nightly daemon**. `backend/harness/` package with `_llm_client.py` (SciLingo-style, with retries, fallbacks, telemetry), `hooks.py` (registry + dispatch), `daemon.py` (nightly Multi-Lens Review re-audit of bank, decay surfacing, telemetry rollups). 4 hook types: `pre_question_display`, `post_answer`, `pre_derivation`, `post_walkthrough_step`.
**Est'd added LOC**: ~480 (180 LLM client + 120 hooks + 180 daemon).
**Est'd added dev-days**: **+2.0**.

### Multi-Lens Review loop

**Modifies**: P7 generator pipeline integrates the loop in-line. Existing P4 walkthrough-step generation calls the loop on each step before display.
**Adds NEW**: `backend/review/multi_lens.py` orchestrator + 4 lens-reviewer agents (Factual / Pedagogical / Korean Naturalness / Difficulty Calibration). `lens_disagreement_log` table for telemetry. Convergence: max 3 revision rounds, else escalate to manual review queue (`question_review_log.status='manual_review'`).
**Est'd added LOC**: ~420 (80 orchestrator + 4×60 lens reviewers + 100 schema/log/manual queue UI).
**Est'd added dev-days**: **+2.0** (architecture-heavy; Opus-reserved work).

**Total added**: ~3,670 LOC, ~+15.5 dev-days on top of original Plan B+ (~14 days, ~2,400 LOC). Net revised target: **~6,070 LOC, ~29.5 dev-days**. See §4 for compression options.

---

## 2. Revised stack (delta from current plan)

### New tables (DDL deltas, all in `pipeline/schema.sql`)

```sql
-- R1
CREATE TABLE figures (
  id            SERIAL PRIMARY KEY,
  source        TEXT CHECK (source IN ('slide','textbook','web','foundation')),
  lecture       TEXT,                 -- e.g. 'L5'
  book          TEXT,                 -- e.g. 'DA' or 'FN'
  page          INT,
  bbox          FLOAT8[],             -- [x0,y0,x1,y1] in PDF points
  caption       TEXT,
  caption_ko    TEXT,
  img_path      TEXT NOT NULL,        -- relative to data/figures/
  img_embedding vector(2048),         -- Nemotron VL on the crop
  caption_embedding vector(1024),     -- Qwen3 on the caption
  created_at    TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX figures_caption_hnsw ON figures USING hnsw (caption_embedding vector_cosine_ops);

-- R2 / R4
CREATE TABLE question_bank (
  id              SERIAL PRIMARY KEY,
  topic           TEXT NOT NULL,             -- 'HH','cable','Nernst','membrane_eq',...
  card_type       TEXT NOT NULL CHECK (card_type IN ('recall','concept','application','proof')),
  difficulty      INT  NOT NULL CHECK (difficulty BETWEEN 1 AND 5),
  bloom           TEXT CHECK (bloom IN ('Remember','Understand','Apply','Analyze','Evaluate','Create')),
  prompt_md       TEXT NOT NULL,             -- KaTeX-ready markdown
  answer_md       TEXT NOT NULL,
  rationale_md    TEXT NOT NULL,             -- post-hoc explanation
  source_citation JSONB NOT NULL,            -- {kind:'textbook',book:'DA',ch:5,page:119}
  priority_score  FLOAT NOT NULL,            -- 0..1, set by Priority Scorer
  info_density    FLOAT NOT NULL,            -- 0..1
  is_prereq       BOOLEAN DEFAULT false,
  mastery_target  TEXT,                      -- which concept-id this contributes mastery to
  status          TEXT DEFAULT 'active' CHECK (status IN ('active','retired','manual_review','draft')),
  figure_id       INT REFERENCES figures(id),
  created_at      TIMESTAMPTZ DEFAULT now()
);

-- R3
ALTER TABLE users
  ADD COLUMN streak_days       INT     DEFAULT 0,
  ADD COLUMN streak_last_date  DATE,
  ADD COLUMN xp                INT     DEFAULT 0,
  ADD COLUMN level              INT     DEFAULT 1,
  ADD COLUMN badges            JSONB   DEFAULT '[]'::jsonb,
  ADD COLUMN persona_voice     TEXT    DEFAULT '뉴런쌤',
  ADD COLUMN daily_goal_min    INT     DEFAULT 20;

-- R3 (mastery surface)
CREATE TABLE mastery (
  user_id    INT REFERENCES users(id),
  topic      TEXT,
  card_type  TEXT,                     -- per-type mastery (recall vs proof differs)
  score      FLOAT  NOT NULL,          -- 0..1, EMA over recent reviews
  updated_at TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (user_id, topic, card_type)
);

-- R5
CREATE TABLE foundation_content (
  id             SERIAL PRIMARY KEY,
  source_kind    TEXT CHECK (source_kind IN ('3b1b_diffeq','strogatz','kandel','web_other')),
  source_url     TEXT,
  topic          TEXT NOT NULL,        -- 'ODE_basic','PDE_basic','neuron_anatomy',...
  title          TEXT,
  body_md        TEXT NOT NULL,
  body_ko        TEXT,                 -- LLM-translated, reviewed
  text_embedding vector(1024),
  license        TEXT,                 -- track for legal compliance
  ingested_at    TIMESTAMPTZ DEFAULT now()
);

-- Multi-Lens Review
CREATE TABLE question_review_log (
  id             SERIAL PRIMARY KEY,
  artifact_kind  TEXT NOT NULL,        -- 'question'|'walkthrough_step'|'summary'
  artifact_id    INT  NOT NULL,        -- FK depending on kind
  round_num      INT  NOT NULL,        -- 1..3
  lens           TEXT NOT NULL CHECK (lens IN ('factual','pedagogical','korean','difficulty')),
  verdict        TEXT NOT NULL CHECK (verdict IN ('pass','revise','reject')),
  reasoning      TEXT,
  revised_text   TEXT,
  reviewed_at    TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE lens_disagreement_log (
  id            SERIAL PRIMARY KEY,
  artifact_id   INT,
  artifact_kind TEXT,
  round_num     INT,
  lenses_passing TEXT[],   -- e.g., ARRAY['factual','korean']
  lenses_failing TEXT[],
  resolution     TEXT,     -- 'converged'|'manual'|'rejected'
  logged_at      TIMESTAMPTZ DEFAULT now()
);
```

### New agents (in `backend/agents/`)

| Agent | Replaces / new | Role |
|---|---|---|
| `BankSelector` | replaces on-the-fly `Quiz` | Picks N items from `question_bank` per FSRS due + mastery gap + topic mix |
| `QuestionGenerator` | new, batch-only | Generates candidate items of a declared `(topic, card_type, difficulty)` from RAG-grounded chunks |
| `FactCheckerLens` | new (Lens 1) | RAG-grounded factual check vs source citation |
| `PedagogyCriticLens` | new (Lens 2) | Bloom's level + scaffolding adequacy |
| `KoreanNaturalnessLens` | new (Lens 3) | Native-speaker-grade Korean |
| `DifficultyCalibrationLens` | new (Lens 4) | Matches declared difficulty tag |
| `PriorityScorer` | new | Scores `priority_score` and `info_density` for bank items |
| `PersonaNarrator` | new (post-process) | Wraps Tutor JSON in `뉴런쌤` voice |
| `DiagnosticAgent` | new | Detects mastery gaps, flags prereq need |
| `WebSearchAgent` | new | Chrome MCP for foundation content + figure web-search |

### New frontend modules

```
frontend/src/persona/        # 뉴런쌤 mascot, encouragement copy, voice config
frontend/src/gamification/   # streak, XP, level, badges, level-up animation
frontend/src/dashboard/      # mastery heatmap, daily goal, progress
frontend/src/components/MathSafety.tsx   # KaTeX wrapper that NEVER throws on malformed LaTeX (R1)
frontend/src/components/FigureRenderer.tsx
frontend/src/components/ManualReviewQueue.tsx   # admin view of escalated items
```

---

## 3. Final atomic decomposition — REVISED (P0–P10)

Phases P0–P6 retain the original IDs from `00_integrated_synthesis_and_plan.md`. Modifications inline. New phases P7–P10 are appended.

### Phase P0 — Pre-flight bug fixes (1 day, unchanged)

P0.1–P0.7 unchanged. **Add** P0.8 below.

| ID | Task | Files | LOC | Verify | Deps |
|---|---|---|---|---|---|
| **P0.8** | Add `users` extension columns + `mastery` table DDL | `pipeline/schema.sql` | +35 | `\d users` shows streak/XP; `\d mastery` exists | — |

### Phase P1 — Parser dispatcher (2 days; modify P1.2)

P1.1, P1.3, P1.4, P1.5, P1.6 unchanged. **Modify P1.2**: MinerU output extraction must include figure bounding boxes alongside LaTeX. Adds ~30 LOC.

### Phase P2 — Embedding dual-column + L8 ingest (1.5 days, unchanged)

Steps unchanged.

### Phase P3 — SymPy verifier cascade (1.5 days, unchanged)

Steps unchanged.

### Phase P4 — Pedagogy: KELE split + structured gate + Explain-My-Answer (3 days; **modify P4.9, add P4.10**)

P4.1–P4.8 unchanged. **P4.9 changes scope**: instead of "Bloom's-forced Quiz prompt", P4.9 becomes "delete on-the-fly Quiz prompt; add `BankSelector` shim that calls `/api/bank/next`". Quiz quality moves to P7. **P4.10 NEW**: Wrap every walkthrough-step generation through Multi-Lens Review.

| ID | Task | Files | LOC | Verify | Deps |
|---|---|---|---|---|---|
| **P4.9 (revised)** | Delete on-the-fly Quiz; add `BankSelector` calling `/api/bank/next` | `backend/agents.py`, `backend/agents/bank_selector.py` (new) | +90/-60 | Quiz route returns items only from `question_bank` | P7.5 |
| **P4.10 (new)** | Wrap walkthrough-step output through `multi_lens_review()` | `backend/agents.py` (Tutor section) | +35 | Each step displayed only after `verdict='pass'` from all 4 lenses or escalation | P10.2 |

### Phase P5 — SRS + UI (2.5 days; **modify P5.1, P5.4, P5.6, P5.7**)

P5.2, P5.3, P5.5, P5.8 unchanged.

| ID | Task | Files | LOC | Verify | Deps |
|---|---|---|---|---|---|
| **P5.1 (revised)** | `srs_cards` DDL **with 4-type enum**: `recall|concept|application|proof` | `pipeline/schema.sql` | +35 | `\d srs_cards` shows CHECK on 4 values | P0.1, P0.8 |
| **P5.4 (revised)** | Card seeder pulls **from question_bank** instead of generating; mirrors bank items into `srs_cards` for FSRS scheduling | `scripts/seed_srs_cards.py` (rewrite) | ~150 | After P7.6 ships, ≥80 SRS cards across all 4 types from L5/L6/L3 | P7.6 |
| **P5.6 (revised)** | `<SRSPanel>` with persona narrator + Framer Motion card flip + figure render + level-up animation | `frontend/src/components/SRSPanel.jsx` | ~310 | Cards flip smoothly; persona greeting on session start; figure crops display | P5.5, P5.7, P8.2 |
| **P5.7 (revised)** | `<MathInput>` lazy-loaded MathLive **wrapped in MathSafety** (never throws on malformed LaTeX) | `frontend/src/components/MathInput.tsx`, `frontend/src/components/MathSafety.tsx` (new) | ~140 | Pasting `\\frac{` (incomplete) renders fallback `[수식 표시 오류]` instead of crashing | — |

### Phase P6 — Offline LLM fallback + smoke test (1 day, unchanged)

Steps unchanged.

### Phase P7 — **NEW** Question bank pipeline (Multi-Lens Review + 4 card types) (3.5 days)

| ID | Task | Files | LOC | Verify | Deps |
|---|---|---|---|---|---|
| **P7.1** | `question_bank` + `question_review_log` + `lens_disagreement_log` DDL | `pipeline/schema.sql` | +80 | `\d question_bank` shows 4-type enum, JSONB citation | P0 |
| **P7.2** | `QuestionGenerator` agent — RAG-grounded, 4-type aware, takes `(topic, card_type, difficulty)` config | `backend/agents/question_generator.py` (new) | ~180 | Given `(topic='HH', card_type='proof', difficulty=4)` returns 1 candidate JSON with prompt+answer+rationale+citation | P2.4 |
| **P7.3** | `PriorityScorer` — calls scorer LLM with rubric, sets `priority_score`+`info_density` | `backend/agents/priority_scorer.py` (new) | ~110 | Scores fall in [0,1]; HH-gating items score >0.8 | P7.1 |
| **P7.4** | Multi-Lens Review orchestrator (uses P10.2 module) | `backend/review/bank_review.py` (new) | ~140 | Calls all 4 lenses, iterates up to 3, returns final verdict; logs every round | P10.2 |
| **P7.5** | `BankSelector` agent + `/api/bank/next` endpoint — adaptive selection by FSRS+mastery+topic gap | `backend/agents/bank_selector.py`, `backend/main.py` | ~200 | Returns 10 items balanced across 4 types; reorders by mastery gap | P7.1, P5.2 |
| **P7.6** | Batch CLI: `scripts/generate_bank.py --topics HH,cable,Nernst,membrane_eq` | `scripts/generate_bank.py` (new) | ~170 | Run produces ≥80 reviewed bank items with all 4 types coverage; review log populated | P7.2, P7.3, P7.4 |
| **P7.7** | Daily-mix algorithm: weighted sample by per-type mastery | `backend/srs/daily_mix.py` (new) | ~110 | Lower-mastery type gets ≥1.5× weight; never 100% one type | P7.5 |

### Phase P8 — **NEW** Persona + gamification + dashboard (2.5 days)

| ID | Task | Files | LOC | Verify | Deps |
|---|---|---|---|---|---|
| **P8.1** | Persona module: 뉴런쌤 mascot SVG + encouragement-line library + Tutor system-prompt voice config | `frontend/src/persona/` (new dir, 4 files) | ~160 | Tutor responses contain persona-voice lead-in; mascot renders | — |
| **P8.2** | Backend `PersonaNarrator` post-processor wrapping Tutor JSON | `backend/agents/persona_narrator.py` (new) | ~80 | Tutor output starts with persona greeting in Korean | — |
| **P8.3** | Gamification state machine: streak/XP/level/badges, with rules engine | `backend/gamification/` (new dir) + `frontend/src/gamification/` | ~220 | Daily streak increments on first session; level-up at XP thresholds; 3 starter badges fire | P0.8 |
| **P8.4** | Mastery heatmap dashboard component (per topic × card_type) | `frontend/src/dashboard/MasteryHeatmap.tsx` (new) | ~180 | Renders 4×N grid with color-graded mastery cells; clicking a cell deep-links to bank | P5.4 |
| **P8.5** | Daily-goal nudge component | `frontend/src/dashboard/DailyGoal.tsx` (new) | ~80 | Renders progress ring; nudge banner if user hasn't hit goal by 8pm | P8.3 |

### Phase P9 — **NEW** Foundation prereq ingestion + diagnostic routing (2.5 days)

| ID | Task | Files | LOC | Verify | Deps |
|---|---|---|---|---|---|
| **P9.1** | `foundation_content` DDL | `pipeline/schema.sql` | +30 | `\d foundation_content` exists | P0 |
| **P9.2** | Web-Search agent using Chrome MCP for transcript/content fetch | `backend/agents/web_search.py` (new) | ~120 | Given a 3B1B DiffEq URL, returns transcript text via Chrome MCP / `scilingo-youtube-transcript` skill | — |
| **P9.3** | Foundation ingestion CLI: pull ODE/PDE/neuron-anatomy from 3 sources, embed, store | `scripts/ingest_foundation.py` (new) | ~180 | After run, `foundation_content` count ≥30; license tracked per row | P9.1, P9.2 |
| **P9.4** | `DiagnosticAgent` — detects mastery gap on prereq concepts | `backend/agents/diagnostic.py` (new) | ~130 | Given `mastery` row with score<0.3 on `ODE_basic`, returns `prereq_needed=['ODE_basic']` | P0.8 |
| **P9.5** | Router hook: insert prereq card if diagnostic flags before next main-track card | `backend/srs/router.py` (new) | ~90 | Walkthrough on cable PDE detects PDE-weak student, routes to `PDE_basic` foundation card first | P9.4, P7.5 |
| **P9.6** | Frontend cue: "기초 보강이 필요해요" banner with foundation-card UI | `frontend/src/components/FoundationCue.jsx` (new) | ~80 | Banner appears when router returns prereq; dismissable | P9.5 |

### Phase P10 — **NEW** Hook system + nightly daemon + Multi-Lens Review (2.0 days)

| ID | Task | Files | LOC | Verify | Deps |
|---|---|---|---|---|---|
| **P10.1** | `backend/harness/_llm_client.py` — SciLingo-style with retries, OpenRouter→Ollama fallback (replaces inline `_llm()` in agents.py) | `backend/harness/_llm_client.py` (new) | ~180 | All agents call via `harness_llm()`; identical I/O to v0.4 `_llm()` | P6.2 |
| **P10.2** | `multi_lens_review()` orchestrator + 4 lens reviewers | `backend/review/multi_lens.py`, `backend/review/lenses/{factual,pedagogical,korean,difficulty}.py` | ~340 | Synthetic test artifact: all 4 lenses called; convergence within 3 rounds; non-converging escalates to manual queue | — |
| **P10.3** | Hook registry + 4 hook types | `backend/harness/hooks.py` (new) | ~120 | Registering a `pre_question_display` hook fires before BankSelector returns; logged | P10.1 |
| **P10.4** | Nightly daemon: re-runs Multi-Lens Review on aged bank items, writes decay surfaces | `backend/harness/daemon.py` (new) | ~180 | `python -m backend.harness.daemon` reviews 100 oldest items, flags ≥5 for revision based on lens disagreements | P10.2 |
| **P10.5** | Telemetry event schema + persist to `analytics_events` table | `backend/harness/telemetry.py` (new), `pipeline/schema.sql` | ~110 | Every agent call emits an event; queryable via SQL | P10.3 |
| **P10.6** | Manual-review queue admin UI | `frontend/src/components/ManualReviewQueue.tsx` (new) | ~140 | Items with `status='manual_review'` listed; J can approve/reject/edit | P7.1 |

---

## 4. Total revised dev-day + LOC estimate

| Phase | LOC | Dev-days |
|---|---|---|
| P0 (was) | 285 | 1.0 |
| P0 added (P0.8) | +35 | +0.1 |
| P1 (was) | 400 | 2.0 |
| P1 modified (P1.2 +bbox) | +30 | +0.2 |
| P2 (was) | 320 | 1.5 |
| P3 (was) | 400 | 1.5 |
| P4 (was) | 695 | 3.0 |
| P4 modified (P4.9 + P4.10 new) | +60 | +0.3 |
| P5 (was) | 1040 | 2.5 |
| P5 modified (P5.6/P5.7/P5.4) | +180 | +0.6 |
| P6 (was) | 150 | 1.0 |
| **P7 NEW** | 990 | 3.5 |
| **P8 NEW** | 720 | 2.5 |
| **P9 NEW** | 630 | 2.5 |
| **P10 NEW** | 1070 | 2.0 |
| **TOTAL** | **~7,005 LOC** | **~24.2 dev-days** |

Versus original Plan B+ (14 days, 2,400 LOC): **+10.2 dev-days, +4,605 LOC**. The increase is overwhelmingly P7 (bank pipeline) + P8 (gamification UI) + P9 (foundation track) + P10 (harness/multi-lens) — all explicit user requirements.

**Compression options**:

1. **Defer P9 to v0.5.1** — saves 2.5 days. Foundation track is highest-value but lowest-urgency (active BRI610 students likely have ODE basics; gap-detection-then-route is a refinement). Recommended if exam season is <3 weeks away. Total then: ~21.7 days.
2. **Defer P8.4 + P8.5 (heatmap + daily-goal)** to v0.5.1 — saves 0.8 days. Persona + streak/XP ship; dashboard waits.
3. **Reduce bank seed coverage** — generate 60 items instead of 80+, saves ~0.5 day in P7.6 batch time.

Recommendation: ship full P0–P7 + P10 first (the no-hallucination bank + harness is the highest-leverage requirement), then P8 (engagement) the same week, defer P9 to v0.5.1 — gates the release at ~21.7 days.

---

## 5. Multi-Lens Review architecture (~600 words)

The Multi-Lens Review loop is the load-bearing quality mechanism for everything user-facing: questions in the bank, walkthrough steps as they stream, summaries before persistence. It is a small orchestrator that fans out to 4 specialized reviewer agents in parallel, collects verdicts, and either passes the artifact, asks for a single revision (with all failing-lens feedback merged), or — after 3 rounds without convergence — escalates to a human-review queue.

### Pseudocode

```python
# backend/review/multi_lens.py
async def multi_lens_review(
    artifact: Artifact,                # {kind, text, citation, declared_difficulty, declared_bloom}
    max_rounds: int = 3,
) -> ReviewResult:
    current_text = artifact.text
    for round_num in range(1, max_rounds + 1):
        # parallel fan-out
        verdicts = await asyncio.gather(
            factual_lens(current_text, artifact.citation),
            pedagogical_lens(current_text, artifact.declared_bloom),
            korean_lens(current_text),
            difficulty_lens(current_text, artifact.declared_difficulty),
        )
        passing = [v for v in verdicts if v.verdict == 'pass']
        failing = [v for v in verdicts if v.verdict != 'pass']

        log_review_round(artifact.id, round_num, verdicts)

        if len(passing) == 4:
            return ReviewResult(status='approved', text=current_text, rounds=round_num)

        # any reject → escalate immediately
        if any(v.verdict == 'reject' for v in failing):
            return ReviewResult(status='manual_review',
                                text=current_text, rounds=round_num,
                                reasons=[v.reasoning for v in failing])

        # all failing are 'revise' → merge feedback, regenerate once
        merged_feedback = merge_feedback(failing)
        current_text = await reviser_agent(current_text, merged_feedback,
                                            artifact.citation,
                                            artifact.declared_difficulty,
                                            artifact.declared_bloom)
    # max rounds reached without convergence
    log_disagreement(artifact.id, lenses_failing=[v.lens for v in failing])
    return ReviewResult(status='manual_review', text=current_text, rounds=max_rounds)
```

### Lens prompt templates (bilingual KO/EN, condensed)

**Lens 1 — Factual (`factual_lens`)**:
> 당신은 BRI610 신경과학 사실 검증자입니다. 다음 항목이 인용 출처(Dayan&Abbott Ch.5 p.119 등)와 정확히 일치하는지 검토하세요. 수치, 부호, 변수 정의, 단위가 모두 일치해야 합니다.
> *You are a BRI610 neuroscience fact-checker. Verify the artifact matches the cited source exactly — numerics, signs, variable definitions, units must all match.* Output: `{verdict: pass|revise|reject, reasoning_ko, reasoning_en, suggested_fix}`.

**Lens 2 — Pedagogical**:
> 선언된 Bloom's 단계(`{bloom}`)와 비계(scaffolding) 적절성. 학생이 이 항목으로 무엇을 학습하는가? Bloom's 레벨 매칭 + 비계 충분성을 평가하세요.

**Lens 3 — Korean Naturalness**:
> 한국어 표현이 어색하지 않은지, 직역체가 아닌지 평가하세요. STEM 용어는 표준 용례를 사용해야 함 (예: "막전위" not "멤브레인 포텐셜"). 단, 정착된 영문 용어는 그대로 둘 수 있음.

**Lens 4 — Difficulty Calibration**:
> 선언된 난이도(`{difficulty}`)와 실제 인지부하 일치 여부. recall은 1–2, concept 2–3, application 3–4, proof 4–5 범위. 외삽이 필요하면 +1, 직접 인용은 -1.

Each lens runs at temperature 0.0 with `max_tokens=300`. Cost: 4 calls × ~300 tokens output each per round, average 1.4 rounds (heuristic from KELE-style pipelines) ⇒ ~1,680 output tokens/artifact. With 80 bank items × ~1.4 rounds × 4 lenses ≈ 450 LLM calls one-time for initial bank build. On Ollama (qwen3:30b-a3b): ~30–45 minutes wall-clock; on OpenRouter free: under quota. Acceptable.

### Convergence criteria

- **Approved**: all 4 lenses return `pass` in same round.
- **Iterate**: any lens returns `revise` → merge feedback, send to reviser agent (the original generator with feedback context), re-review.
- **Reject (immediate escalation)**: any lens returns `reject` (factual contradiction, unsalvageable). Item enters `question_review_log.status='manual_review'`.
- **Non-convergent**: 3 rounds elapsed without all-pass → escalate.

### Failure escalation — manual review queue

Items with `status='manual_review'` surface in `frontend/src/components/ManualReviewQueue.tsx` (P10.6) — admin view only, J can approve/reject/edit/regenerate. Telemetry: `lens_disagreement_log` records which lenses keep disagreeing (e.g., factual vs difficulty often conflict on edge cases) — informs lens-prompt v2 tuning.

### Storage — `question_review_log` schema (already in §2)

Every round writes one row per lens (4 rows × 3 rounds max = 12 rows per worst-case artifact). Telemetry-friendly: `SELECT artifact_id, COUNT(*), MAX(round_num)` reveals slow-converging items.

---

## 6. Agent team harness blueprint (~400 words)

The harness is a thin coordination layer that wraps all LLM calls, registers domain hooks, runs nightly maintenance, and emits telemetry. Modeled on SciLingo's `_llm_client.py` + `enrichment_daemon.py` pattern.

### Module structure

```
backend/harness/
├── __init__.py
├── _llm_client.py     # All LLM calls go through here. Owns retries, OpenRouter→Ollama
│                      # fallback, response logging, prompt-cache key derivation.
├── hooks.py           # Hook registry. Decorator + dispatcher.
├── daemon.py          # Nightly batch: re-review aged bank, refresh decay surfaces,
│                      # rollup telemetry. Invoked via cron or manual: `python -m backend.harness.daemon`.
├── telemetry.py       # Event schema, async writer to `analytics_events`.
└── tests/
    ├── test_hooks.py
    └── test_daemon.py
```

### Hook registry

```python
# backend/harness/hooks.py
HOOKS = {
    'pre_question_display':   [],   # (item) -> item | reject
    'post_answer':            [],   # (review_event) -> None  # FSRS update + telemetry
    'pre_derivation':         [],   # (latex_attempt) -> verified_attempt
    'post_walkthrough_step':  [],   # (step_output, session_state) -> next_action
}

def register(hook_name):
    def decorator(fn):
        HOOKS[hook_name].append(fn)
        return fn
    return decorator

async def fire(hook_name, payload):
    for fn in HOOKS[hook_name]:
        payload = await fn(payload)  # chain
        if payload is None:  # reject signal
            return None
    return payload
```

Default registrations (in respective modules):

- `pre_question_display` → quality_gate (rejects items with `priority_score<0.4`)
- `post_answer` → FSRS scheduler update + mastery EMA update + XP grant + streak check
- `pre_derivation` → SymPy verifier cascade (P3)
- `post_walkthrough_step` → Multi-Lens Review (P10.2) on the just-emitted step + mode-lock state machine (P4.8)

### Daemon invocation

`python -m backend.harness.daemon` — runs three jobs:

1. **Bank decay audit**: pulls oldest 100 `question_bank` items not reviewed in 30 days, runs `multi_lens_review()`, flags `revise` candidates.
2. **Disagreement rollup**: aggregates `lens_disagreement_log` last 7 days, identifies systematic lens-vs-lens conflicts (e.g., factual vs difficulty disagreeing 12% of the time on `proof` items) — informs lens prompt tuning.
3. **Telemetry rollup**: aggregates `analytics_events` into per-user mastery deltas, streak status, daily goal completion. Writes daily report row.

Cron (user adds manually):
```
0 3 * * * cd /Users/joonoh/Projects/bri610-tutor && /usr/bin/env python -m backend.harness.daemon >> logs/daemon.log 2>&1
```

For v0.5 we ship the daemon as a manual-invoke CLI; cron-installation is documented in the README but not auto-installed.

### Telemetry event schema

```sql
CREATE TABLE analytics_events (
  id          BIGSERIAL PRIMARY KEY,
  event_kind  TEXT NOT NULL,    -- 'agent_call','review_round','answer_submitted',
                                -- 'streak_increment','levelup','prereq_routed', ...
  user_id     INT,
  session_id  TEXT,
  agent       TEXT,
  ms          INT,              -- latency
  tokens_in   INT,
  tokens_out  INT,
  llm_route   TEXT,             -- 'openrouter:gpt-4o','ollama:qwen3-30b-a3b'
  payload     JSONB,            -- event-specific
  created_at  TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX analytics_events_kind_time ON analytics_events (event_kind, created_at DESC);
```

Every agent call writes one event. Multi-Lens rounds write 4 events per round. SRS reviews write 1 event. Cheap to query for the daemon's daily rollup.

---

## 7. Updated kickoff sequence (immediate next 6–8 steps)

Reordering rationale: P7 (bank generation) is the new bottleneck because P5.4 (SRS card seeder) now reads from the bank instead of generating, and P4.9 (Quiz) is replaced by `BankSelector`. So P7 must land before P4.9 ships and before P5.4 ships. Figure extraction (R1) moves up to overlap with P1 since both touch the parser.

Execute in this order; parallelize within each numbered group.

1. **Group A — P0 bug-fix sweep + schema deltas (Day 1, parallel)**:
   - P0.1–P0.7 (original 7 bugs).
   - **P0.8** (users + mastery DDL).
   - P7.1 + P9.1 + figure DDL (`figures` table) + analytics_events DDL — ship all schema changes in one migration to avoid migration churn.

2. **Group B — Parser + figures (Day 2–3, parallel where independent)**:
   - P1.1 + P1.2 (MinerU dispatcher) **with figure-bbox extraction added**.
   - P1.3 (Marker for slides).
   - **P7-figures**: `extract_figures.py` block-level pipeline + caption embedder + `<FigureRenderer>` frontend stub (uses placeholder data while P1.4 re-parse runs).
   - P1.4 + P1.5 (re-parse DA Ch.5–7 + slides) — run during evening so embedders aren't loaded.

3. **Group C — Verifier cascade + harness skeleton (Day 4, parallel)**:
   - P3.1, P3.2, P3.5 (SymPy preprocessor + verifier + 5 test cases).
   - **P10.1** (`harness/_llm_client.py`) — establish call site for all subsequent agents.
   - **P10.2 stub** (multi_lens_review skeleton with 4 lens stubs returning `pass`; real prompts in Day 5).

4. **Group D — Multi-Lens Review wiring (Day 5)**:
   - P10.2 full implementation (4 lens prompts, convergence loop).
   - P10.3 (hook registry).
   - P10.5 (telemetry).

5. **Group E — Question bank pipeline (Day 6–8)**:
   - P7.2 (QuestionGenerator).
   - P7.3 (PriorityScorer).
   - P7.4 (bank-review wiring through multi_lens).
   - P7.6 (batch CLI; run for HH, cable, Nernst, membrane_eq — generates ~80 items overnight).
   - P7.5 + P7.7 (BankSelector + daily-mix).

6. **Group F — Pedagogy + SRS plumbing (Day 9–11)**:
   - P4.1–P4.8 (KELE Consultant + SocraticAI gate + Explain-My-Answer + mode lock).
   - P4.9 + P4.10 (delete on-the-fly Quiz, wrap walkthrough in Multi-Lens).
   - P5.1–P5.3 + P5.5 + P5.7 + P5.8 (SRS schema, scheduler, queue, hooks, MathInput, tab).
   - P5.4 (rewritten — pulls from bank).

7. **Group G — Persona + gamification + dashboard (Day 12–14)**:
   - P8.1 + P8.2 (persona + narrator).
   - P8.3 (gamification state).
   - P5.6 (SRS panel with persona + Framer Motion).
   - P8.4 + P8.5 (dashboard + daily-goal).

8. **Group H — Foundation prereq + nightly daemon + smoke (Day 15–17 if not deferred)**:
   - P9.2–P9.6 (web-search agent, ingestion, diagnostic, router, frontend cue).
   - P10.4 (nightly daemon).
   - P10.6 (manual-review queue admin UI).
   - P6.1–P6.5 (offline LLM fallback + smoke test + memory updates).

If Group H deferred to v0.5.1 (per §4 compression), the kickoff stops after Group G at ~Day 14 wall-clock (allowing for 5h Claude rate limits, real elapsed is ~21 days).

---

## 8. New risks (top 3) introduced by R1–R5

### Risk N1 — Bank generation time + cost (multi-agent review is N× slower)

**Description**: Each bank item requires (1 generator call) + (4 lens calls × avg 1.4 rounds) + (1 reviser call when failing) ≈ 7 LLM calls per generated item. For an 80-item seed bank: ~560 LLM calls. On OpenRouter free tier (current quota observed ~200 calls/hr before 429), the bank build takes ~3 hours wall-clock minimum, possibly 5 with backoffs. Hitting 429 mid-batch resumes via Ollama qwen3:30b-a3b but slows wall-clock further (~20 tok/s on M-series).

**Probability**: High. **Impact**: Medium — delays P7.6 finish, blocks P5.4 + P4.9.

**Mitigation**:
- Batch the generation in **3 chunks of ~25 items overnight** (Day 6, 7, 8 evenings) to spread quota burn.
- Use Ollama qwen3:30b-a3b for the FactCheckerLens specifically — it's the most quota-heavy lens (citation lookup repeats) and the most local-LLM-amenable (deterministic comparison vs source text).
- Cache per-(topic, card_type, difficulty, source_chunk_hash) — re-runs of regen on minor lens disagreements re-use generator output where possible.
- Failure mode: if 12 hours in we have <40 items, accept the smaller seed bank and ship with reduced coverage; note in v0.5.0 release.

### Risk N2 — Multi-Lens Review oscillation / non-convergence

**Description**: 4 independent lenses with non-aligned objectives can disagree persistently — e.g., Lens 2 (Pedagogy) wants more scaffolding, Lens 4 (Difficulty) reads added scaffolding as lowering difficulty below the declared tag. The reviser then bounces between two equilibria without converging in 3 rounds. KELE-style pipelines report ~5–10% non-convergence in multi-critic settings; for our 4-lens bank we should expect similar.

**Probability**: Medium-High. **Impact**: Medium — ~5–10% of items end up in the manual review queue, requiring J's attention at unpredictable times.

**Mitigation**:
- **Lens priority ordering**: Factual is veto-power (immediate reject if fails). The other 3 are advisory — if Pedagogy + Korean pass and Difficulty fails alone, accept the item and adjust the declared difficulty tag downward by 1 instead of regenerating.
- **Reviser receives ALL failing-lens feedback merged**, not one at a time — this avoids ping-pong between lens 2 and lens 4.
- **Manual queue with batch-approve**: J reviews 5–10 items at once weekly, not per-item. Keeps interruption load low.
- **Telemetry-driven lens-prompt v2**: after 1 week, identify which lens-pair systematically disagrees, soften one lens's threshold.

### Risk N3 — Chrome MCP rate limits + content scraping legality (3Blue1Brown is YouTube; need transcript path)

**Description**: R5 names 3Blue1Brown DiffEq, Strogatz Nonlinear Dynamics, Kandel Principles of Neural Science as foundation sources. (a) **3B1B**: video-only on YouTube — must use the `scilingo-youtube-transcript` skill (Chrome MCP transcript route) since youtube-transcript-api is rate-limited and often returns no captions for 3B1B. (b) **Strogatz**: book under copyright; openly-licensed excerpts only (e.g., MIT OCW notes that paraphrase concepts). Cannot mass-ingest the full text. (c) **Kandel**: same — restrict to OCW summaries / openly-published author lectures. Chrome MCP itself has session-level rate limits (per browser tab; bursts >30 nav/min get throttled).

**Probability**: Certain (legal constraint) + Medium (rate limits). **Impact**: Medium — limits P9 ingestion volume; if mishandled, copyright exposure (low-risk for personal-use academic tutor but still real).

**Mitigation**:
- **3B1B**: route exclusively through `scilingo-youtube-transcript` skill (J's real Chrome via claude-in-chrome MCP), one video at a time, with 30s sleep between.
- **Strogatz/Kandel**: restrict ingestion to (i) MIT OCW course notes, (ii) author-public-lecture transcripts on YouTube, (iii) freely-distributed problem sets. Track `license` column per row and refuse ingest of unlabeled items.
- **Chrome MCP rate limit**: run `ingest_foundation.py` as a slow batch (1 page per 20s), invoked overnight; never block interactive sessions on it.
- **Fallback ladder**: if licensed content too thin, add `wolfram_education_api` or `khan_academy_open_content` as substitute foundation sources for ODE/PDE basics. Both are openly licensed.
- **Document the source list and license of every `foundation_content` row** so a future review can audit compliance. The `license` column is mandatory (NOT NULL after v0.5.1).

---

*References (deltas only)*: User feedback memory `feedback_v05_user_requirements.md`; SciLingo harness pattern (`_llm_client.py`, `enrichment_daemon.py`); KELE consultant-teacher (`01_ai_tutors.md` §5); SocratiQ Bloom's-forced eval (`01_ai_tutors.md` §5); Multi-critic pipelines (KELE 9-dim eval). Original plan citations (`02..05_*.md`) carry over from `00_integrated_synthesis_and_plan.md`.
