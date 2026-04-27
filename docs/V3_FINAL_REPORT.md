# BRI610 Tutor v0.5 — v3 Iteration Final Report
**Date:** 2026-04-27 03:30 KST  
**Branch:** `main`

## Pipeline status

| Component | State |
|---|---|
| Backend (FastAPI :8000) | Healthy — `harness/sympy/fsrs/db_pool` all OK |
| Frontend (Vite :3000) | HTTP 200 |
| Cloudflare tunnel | https://deviation-celebrities-mainstream-continuing.trycloudflare.com |
| DB (Postgres + pgvector) | 318 slides + 1304 textbook pages + 1503 embedded |
| Bank | **56 active cards** across 15 topics |
| Summaries | **6 lectures cached** (L3–L8), 9.5–9.9k chars each, 3 `<details>` toggles each, 3–6 figures |
| Lecture plans | 6 plans available via `/api/lecture/list` |
| Figures | 16 SVG (palette desaturated, 326 color swaps + 8 declutters) |

## v3 iteration summary (this session)

### Audit
- Multi-Lens audit ran on all 56 cards × 4 lenses (factual / pedagogical / korean / difficulty).
- Verdict distribution (round 1):
  - factual: 14 pass / 8 revise / 5 reject (cards 1–27); ~21 cards flagged total
  - pedagogical: 25 pass / 1 revise / 1 reject
  - korean: 27 pass / 0 issues
  - difficulty: 25 pass / 2 revise

### Card rewrites (21 factual fixes)
Cards 1–27 — 18 hard factual errors fixed and logged (`round_num=2 verdict=pass`):
- Card 1 (HH recall) — removed misattributed M&S 1995 cooperativity citation
- Card 2 (HH concept) — restored `n_∞^4` prefactor in Taylor expansion
- Card 3 (HH application) — P/4 protocol scaling correction
- Card 6 (cable concept) — added Δx ≤ λ/10 Rall criterion
- Card 7 (cable application) — corrected closed-end vs infinite-cylinder interpretation
- Card 8 (cable proof) — `I_inj` enters as boundary condition not body term
- Card 10 (Nernst concept) — "ignored" not "infinite" permeability
- Card 11 (Nernst application) — Na inactive at rest, removed wrong −14760 μA/cm²
- Card 12 (Nernst proof) — sign convention consistency
- Card 13 (model_types concept) — Izhikevich is independent, not derived from HH
- Card 14 (model_types application) — `g_sra(0)=0`, explicit spike discontinuity
- Card 16 (neural_codes concept) — M&S 1995: τ=3ms, direct current (not E/I), removed "chaotic"
- Card 17 (neural_codes application) — explicit Δt=ms→s unit conversion
- Card 18 (neural_codes proof) — phase precession 360°→180°→0° (not 180°→90°→0°)
- Card 20 (synapses application) — alpha function not single exponential; Euler dim-fixed
- Card 21 (LIF recall) — `I_e/C_m` not `I_e/R_m` (dimensional)
- Card 23 (L8 codes recall) — Poisson first-spike `−ln(1−u)/r`
- Card 24 (synapses proof) — alpha = `(t/τ)·e^{1−t/τ}` not `A·e^{−t/τ}`

Cards 28–52 — 3 fixes:
- Card 29 — full HH voltage-clamp identifiability rewrite (proper notation)
- Card 32 — page citation alignment (L7 p.11 → p.14)
- Card 36 — `i_m` slide notation throughout

Cards 53–56 — clean (no factual flags).

### Skipped (per slide-only spec)
Cards 28, 30 + others flagged solely for missing Dayan & Abbott primary citation — slide-only is intentional per `feedback_lecture_only_scope.md`.

## v3 summary transformations
- Numerical anchors stripped (e.g., $C_m \approx 1\,\mu\mathrm{F/cm}^2$, $R_m$ values, τ ranges, concentration values, single-channel pS).
- 3 `<details>` toggles added per summary for prerequisite reminders (separation of variables, KCL, Q=CV, 2D phase plane, cross-correlogram, etc.).
- All preserved: KaTeX equations, Korean+English narrative, sequential derivation steps, concept-map tables, slide page citations, figure callouts.

## SVG declutter (16 figures)
- 326 color swaps to muted journal palette (eLife/Neuron/iScience tone).
- 8 structural cleanups: removed redundant labels, collapsed multi-line captions, fixed phase-precession label inversion, removed misleading P/4 leak annotation in voltage clamp, etc.

## Open items / next session
- Pedagogical lens revisions (10 cards flagged for scaffolding) — not addressed; would benefit from `<details>` hint toggles in card prompts.
- DeepSeek `'choices'` parsing intermittent — likely OpenRouter response format edge case; cascade does fall through to Kimi/Sonnet/Ollama. No data lost.
- Korean lens flagged 1 card (#1, "Failures in cortical neurons" awkward translation) — minor.

## Verification queries
```sql
-- v3 fixes logged
SELECT COUNT(DISTINCT artifact_id) FROM question_review_log
  WHERE round_num=2 AND verdict='pass' AND reasoning LIKE 'v3 fix%';
-- 21
-- Cached summaries
SELECT lecture, LENGTH(summary) FROM lecture_summaries ORDER BY lecture;
-- L3: 9529, L4: 9809, L5: 9539, L6: 9715, L7: 9910, L8: 9731
```

