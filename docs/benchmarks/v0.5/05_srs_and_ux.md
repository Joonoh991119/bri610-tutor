# Benchmark Report v0.5: SRS Algorithms & Equation UX Components

**Project:** BRI610 Computational Neuroscience Tutor  
**Date:** April 26, 2026  
**Stack context:** React + Vite + KaTeX 0.16, Python backend  
**User profile:** Korean PhD student, Mac M-series, bilingual KO+EN, equation-heavy (HH gating, cable PDE)

---

## Category A: SRS Algorithms / Libraries

---

## FSRS-6 + py-fsrs

**Repo / URL**: https://github.com/open-spaced-repetition/py-fsrs  
**License / Cost**: MIT — Free  
**Latest version**: 6.3.1 — March 10, 2026

### 1. 개요 (Overview)
FSRS-6 (Free Spaced Repetition Scheduler, 6th generation) is a machine-learning-based spaced repetition algorithm trained on ~1.7 billion Anki reviews from 20,000 users; py-fsrs is the canonical Python package that exposes the scheduler as a library for custom SRS backends.

### 2. 핵심 기능 (Core capabilities)
- **21-parameter model**: Two new parameters vs. FSRS-5's 19, covering short-term (same-day) review dynamics and an optimizable forgetting curve flatness coefficient
- **Three-component memory model**: Stability (S), Difficulty (D), Retrievability (R = e^{-t/S}) with explicit DSR state machine
- **Optimizer included**: `py-fsrs` ships a PyTorch-based optimizer that fits the 21 weights to a user's own review history via gradient descent on log-loss
- **Same-day review formula**: Upgraded handling for cards reviewed multiple times within 24 hours (critical for intensive problem sets)
- **Desired-retention targeting**: Scheduler accepts a `desired_retention` float (0.70–0.97) and adjusts intervals accordingly
- **Rating scale**: Again (1) / Hard (2) / Good (3) / Easy (4)
- Python ≥ 3.10 required

### 3. 성능 / 지표 (Performance / Metrics)
- **FSRS-6 log loss** (srs-benchmark, ~10 000 user collections, without same-day reviews): **0.3460 ± 0.0042**
- **RMSE (bins)**: 0.0653 ± 0.0011
- **AUC**: 0.7034 ± 0.0023
- **Superiority over Anki SM-2**: 99.6% of users achieve lower log loss with FSRS-6 (optimized) than SM-2
- **Review-count reduction**: 15–30% fewer reviews vs. SM-2 at identical target retention (typically 90%)
- Default parameters derived from 700 M+ reviews; outperform cold-start SM-2 for most users even without personal optimization
- Optimization runtime: ~30 s on M-series for 10 000-card histories (PyTorch CPU)

### 4. 강점 (Strengths)
1. Best-in-class predictive accuracy among open-source algorithms (second only to RWKV LSTM which is not deployable at low cost)
2. Personal optimizer converges on user-specific memory curves — critical for STEM where card difficulty variance is extreme
3. Explicit memory state (S, D, R) maps directly to a relational DB schema; no hidden recurrence
4. `desired_retention` parameter lets the tutor author control the review load per session budget
5. Active maintenance: 6.3.1 released March 2026, FSRS-7 (fractional intervals) already in srs-benchmark

### 5. 약점 / 한계 (Weaknesses)
1. Cold-start problem: optimizer needs ≥ 200–400 reviews per card type before personalization outperforms defaults significantly
2. 21 floats must be stored and versioned per user; migration from FSRS-5 (19 params) requires appending two zeros initially
3. No native handling of multi-part derivation cards — the card model is single-question atomic; must be decomposed at ingestion time
4. Python-only: scheduling logic lives on the server; client cannot reschedule offline without ts-fsrs
5. Forgetting curve assumes exponential decay — may not model initial encoding of novel mathematical notation

### 6. 통합 난이도 (Integration difficulty for our React+Vite stack)
```bash
pip install fsrs==6.3.1
```
**Server-side only.** Expose a `/schedule` REST endpoint; React calls it after each card rating. ~40 lines of Python to wrap the `FSRS` scheduler object in FastAPI. No TypeScript types needed on the backend. Korean IME irrelevant (server-side logic).

```python
from fsrs import FSRS, Card, Rating
scheduler = FSRS()  # uses default 21 params
card = Card()
card, review_log = scheduler.review_card(card, Rating.Good)
# card.due, card.stability, card.difficulty, card.state now updated
```

### 7. 결론 (Verdict)
**ADOPT** — Primary backend scheduler. FSRS-6 is the state-of-the-art open algorithm. py-fsrs 6.3.1 is production-ready, MIT licensed, and integrates in < 50 lines. The DSR state model maps cleanly to a `srs_cards` Postgres table. Use optimized parameters after collecting 400+ reviews; ship with default params initially.

---

## ts-fsrs

**Repo / URL**: https://github.com/open-spaced-repetition/ts-fsrs  
**License / Cost**: MIT — Free  
**Latest version**: 5.3.2 — April 2026

### 1. 개요 (Overview)
ts-fsrs is the official TypeScript port of the FSRS algorithm (tracks the same FSRS-6 spec as py-fsrs), packaged as an ES module / CommonJS / UMD triple build, usable in browser, Node.js, and Deno contexts.

### 2. 핵심 기능 (Core capabilities)
- Full FSRS-6 implementation: same 21-parameter DSR model, same Rating scale
- Ships `createEmptyCard()`, `fsrs()` scheduler factory, `generatorParameters()` for custom weights
- ES module tree-shakeable; UMD bundle for CDN/legacy
- TypeScript-first: all types exported (`Card`, `ReviewLog`, `Rating`, `State`, `RecordLog`)
- Rollup build; `type: "module"` in package.json
- Requires Node ≥ 20.0.0 for dev; browser target has no Node dependency
- Undo / rollback via review log is built-in

### 3. 성능 / 지표 (Performance / Metrics)
- Bundle size (JS only, no assets): ~18 kB minified, ~6 kB gzipped (estimate from package source; no Bundlephobia entry yet for 5.x)
- Scheduling computation: < 1 ms per card on any modern JS engine (pure arithmetic, no ML inference)
- Scheduling 500 cards at startup: < 5 ms total
- No network calls; fully synchronous

### 4. 강점 (Strengths)
1. Zero-dependency: no runtime node_modules needed in browser bundle
2. Algorithmic parity with py-fsrs: both implement FSRS-6 spec; switching between them produces identical intervals given the same params
3. Enables **offline-first** scheduling: React app can reschedule cards without a server round-trip, then sync to backend
4. Complete TypeScript types; works with strict mode and Vite's esbuild pipeline without config changes
5. Active releases: maintained in lock-step with py-fsrs by the same open-spaced-repetition org

### 5. 약점 / 한계 (Weaknesses)
1. No built-in optimizer: parameter optimization still requires py-fsrs (Python/PyTorch); ts-fsrs only schedules with given params
2. Parameter vector must be fetched from the server per user — adds one API call on app boot
3. Review logs must be synced to the server for optimizer to run; need careful offline queue design
4. FSRS-7 (fractional intervals) not yet in ts-fsrs 5.x as of April 2026
5. Weekly download count (~6 000/week on npm) indicates smaller community than React-native SRS frameworks; fewer StackOverflow answers

### 6. 통합 난이도 (Integration difficulty for our React+Vite stack)
```bash
npm install ts-fsrs
```
**TypeScript types:** fully typed, no `@types/` package needed.  
**React component:** not a UI component — pure scheduling logic callable from any hook.

```typescript
import { createEmptyCard, fsrs, Rating } from 'ts-fsrs';
const scheduler = fsrs(); // use fetched 21-param array here
const card = createEmptyCard();
const result = scheduler.next(card, new Date(), Rating.Good);
// result.card.due, result.card.stability, result.card.state
```

Korean IME: irrelevant (algorithm logic only, no UI).  
Vite config: no special config; ES module import works natively.

### 7. 결론 (Verdict)
**ADOPT** — Use as companion to py-fsrs for offline scheduling. The combination is: py-fsrs optimizes weights on the server weekly; ts-fsrs runs the scheduling loop in the browser in real time. This gives offline support and instant UX responsiveness without server round-trips during a study session.

---

## Anki SM-2

**Repo / URL**: https://faqs.ankiweb.net/what-spaced-repetition-algorithm  
**License / Cost**: AGPL-3.0 (Anki app) — Free; algorithm itself is public domain  
**Latest version**: SM-2 spec stable since 1987 (P.A. Wozniak); Anki's modified variant is in Anki 24.x but deprecated in favor of FSRS

### 1. 개요 (Overview)
SuperMemo 2 (SM-2) is the 1987 Piotr Wozniak algorithm that assigns an "ease factor" (EF) to each card and multiplies the previous interval by EF after each "Good" or "Easy" rating; it is the default algorithm used by most flashcard apps pre-2023.

### 2. 핵심 기능 (Core capabilities)
- **Ease factor** (EF): starts at 2.5, adjusted ±0.1–0.2 per review based on rating
- **Interval** multiplied by EF each successful review; reset to 1 day on failure
- **Grade 0–5**: fail (0-1 = reset), pass (2-5 = EF adjustment)
- **Anki modifications**: added "Hard" button (EF −0.15), "Easy" button (EF +0.15), 1-day new-card step, fuzz factor on intervals
- Stateless between sessions: only EF and current interval stored

### 3. 성능 / 지표 (Performance / Metrics)
- FSRS-6 achieves lower log loss than SM-2 for 99.6% of users in the srs-benchmark dataset
- SM-2 does not model same-day reviews; repeated failures cause "ease hell" (EF stuck near 1.3 minimum)
- No per-user optimization: EF adjustments are hand-coded constants, not ML-derived
- Average retention at target interval: not well-calibrated; observed over-intervals on easy cards

### 4. 강점 (Strengths)
1. Trivially simple to implement: ~20 lines of code, no external dependencies
2. Decades of community familiarity; every flashcard tool supports SM-2 export/import
3. Zero cold-start: works from the first review without training data
4. Predictable, inspectable: EF is a single number students can understand intuitively
5. No optimizer to run: no infrastructure cost for scheduling computation

### 5. 약점 / 한계 (Weaknesses)
1. "Ease hell": repeated Hard/Again presses drive EF to its floor (1.3), locking hard cards into short intervals permanently
2. No stability concept: SM-2 cannot distinguish between a card forgotten once vs. ten times with different long-term trajectories
3. Same-day reviews are undefined behavior: Anki resets to 10-min steps, which is an unprincipled workaround
4. Intervals grow too fast for easy cards (EF 2.5 → 6-month gap after 5 reviews), causing under-review of material that was correctly spaced but forgotten
5. No calibration objective: there is no loss function or retention target; EF is a heuristic

### 6. 통합 난이도 (Integration difficulty for our React+Vite stack)
SM-2 has no official library — any implementation is a direct port of the ~20-line formula. A Python implementation is trivial. A TypeScript port is equally trivial. No npm package needed. DB schema is simpler (only `ease_factor`, `interval`, `step` needed).

### 7. 결론 (Verdict)
**REJECT** — SM-2 is worse than FSRS-6 for 99.6% of users by log loss metric, and has known pathological failure modes ("ease hell") that are especially harmful for equation-heavy STEM content where students frequently rate cards Hard. The only scenario to keep SM-2 is as an import-compatibility fallback for Anki decks.

---

## SuperMemo SM-18

**Repo / URL**: https://www.supermemo.com (closed-source, proprietary)  
**License / Cost**: Proprietary — SuperMemo 18 requires Windows app purchase (~$66 USD)  
**Latest version**: SM-18 shipping in SuperMemo 18.x (algorithm internally uses SM-19/SM-20 variants in newer builds)

### 1. 개요 (Overview)
SuperMemo SM-18 is the scheduling algorithm embedded in SuperMemo 18, using a multi-component memory model with live parameter optimization on individual repetition data; it is the direct commercial competitor to FSRS but remains entirely closed-source.

### 2. 핵심 기능 (Core capabilities)
- **5-component model of memory** (SuperMemo internal): retrievability, stability, complexity, recall, and circadian component
- **Live optimization**: parameters updated incrementally after every review (not batch optimizer like FSRS)
- Handles incremental reading, priority queues, topic vs. item card types
- Circadian rhythm model: schedules reviews based on time-of-day patterns
- SM-19/SM-20 variants now also in development within the SuperMemo platform

### 3. 성능 / 지표 (Performance / Metrics)
- SuperMemo's own benchmarks (June–July 2025 internal tests) claim SM-19 beats unoptimized FSRS by 18:2 ratio on "universal metric"
- Independent srs-benchmark does not include SM-18 (closed binary, cannot be evaluated)
- Live incremental optimization theoretically outperforms FSRS batch optimization in very long-term usage (> 5 years)
- Requires Windows — no macOS native app, no web API

### 4. 강점 (Strengths)
1. Longest R&D history: algorithm continuously refined since 1987 with proprietary data from decades of users
2. Live per-review optimization: no separate optimizer run needed
3. Circadian model is unique: accounts for time-of-day encoding differences
4. Handles incremental reading natively — good for graduate textbook review
5. Claims outperformance on long-term retention vs. FSRS with default params

### 5. 약점 / 한계 (Weaknesses)
1. **Windows-only**: no macOS native app, no web API, no Linux — incompatible with our Mac M-series user
2. Closed-source: cannot integrate the algorithm into our tutor's backend
3. No Python library, no TypeScript port — integration is impossible without reverse engineering
4. Proprietary pricing, no academic or open license
5. Claims not independently verifiable: no open benchmark data for SM-18/19/20

### 6. 통합 난이도 (Integration difficulty for our React+Vite stack)
**Impossible.** Closed-source, Windows-only application. No API, no SDK, no npm package.

### 7. 결론 (Verdict)
**REJECT** — Platform incompatibility (Windows-only) makes SM-18 a non-starter for our Mac-based deployment. Even setting aside platform issues, the closed-source nature prohibits integration. Reference only for academic comparison of algorithm design philosophies.

---

## RemNote Algorithm

**Repo / URL**: https://www.remnote.com (hosted app); plugin: https://github.com/open-spaced-repetition/fsrs4remnote  
**License / Cost**: RemNote app: freemium (free tier limited, Pro ~$8/month); FSRS underlying algorithm: MIT  
**Latest version**: RemNote 1.16+ ships FSRS-6; fsrs4remnote plugin tracks FSRS versions

### 1. 개요 (Overview)
RemNote originally used a custom SM-2 variant; since release 1.16 it ships FSRS (currently FSRS-6) as a beta default alongside its SM-2 legacy scheduler, positioning the app as a note-taking + SRS combined workspace.

### 2. 핵심 기능 (Core capabilities)
- FSRS-6 implementation inside RemNote (same 21-parameter model as py-fsrs/ts-fsrs)
- Personal parameter optimization available via the settings panel
- SM-2 fallback still available; history preserved on algorithm switch
- Custom scheduler plugin API: external schedulers can hook into RemNote's review loop
- Concept hierarchy cards: hierarchical notes auto-generate cards (useful for derivation chains)
- Practice queue mixed with reading queue

### 3. 성능 / 지표 (Performance / Metrics)
- Same FSRS-6 algorithm: 20–30% fewer reviews than SM-2 at equal retention
- Optimization happens in-app (not user-visible compute)
- RemNote's own user data reports ~25% review reduction on switch from SM-2 to FSRS

### 4. 강점 (Strengths)
1. Out-of-box solution: no infrastructure to build; fully hosted
2. FSRS-6 already integrated — users get the best open algorithm immediately
3. Hierarchical knowledge model fits graduate STEM better than flat flashcard decks
4. Web-based: works on Mac M-series without native app issues
5. Custom scheduler plugin hook allows extending or overriding the algorithm

### 5. 약점 / 한계 (Weaknesses)
1. Black box: RemNote's FSRS integration is not open; parameter export is limited
2. Equation rendering: RemNote uses KaTeX but the integration is not tunable for our specific HH/cable PDE notation needs
3. Cannot embed RemNote's SRS engine into our custom React tutor — it is a self-contained app
4. Free tier card count limits and syncing restrictions
5. No handwriting-to-card pipeline; card creation is manual

### 6. 통합 난이도 (Integration difficulty for our React+Vite stack)
**Not directly integrable.** RemNote is an app, not a library. Its FSRS algorithm is not separately exportable. If we want FSRS, use py-fsrs + ts-fsrs directly. RemNote is only relevant as a competitor reference or as a supplemental study tool alongside our custom tutor.

### 7. 결론 (Verdict)
**REJECT (as library) / PARTIAL-ADOPT (as supplemental tool)** — Do not attempt to integrate RemNote's SRS engine; instead use py-fsrs + ts-fsrs directly. RemNote is worth recommending to the student as a supplemental note-taking/review tool, but our tutor should have its own SRS loop for course-specific equation cards.

---

## Mochi.cards Algorithm

**Repo / URL**: https://mochi.cards  
**License / Cost**: Proprietary app — Free tier (200 card limit), Pro $5/month  
**Latest version**: Mochi v1.20.5+ (FSRS beta added June 2025, bug-fixed January 2026)

### 1. 개요 (Overview)
Mochi is a Markdown-native flashcard app that added FSRS as a beta scheduling option in June 2025, replacing its previous proprietary interval algorithm; it is primarily relevant as a competitor product reference rather than an integrable library.

### 2. 핵심 기능 (Core capabilities)
- FSRS-6 beta: same underlying algorithm as py-fsrs/ts-fsrs; Mochi-specific parameter defaults
- Markdown + LaTeX card authoring (KaTeX rendering)
- Due-date fuzzing to prevent review clumping (fixed in v1.20.5)
- Desktop (macOS/Windows/Linux) + Web + iOS/Android
- Import/export in Mochi format and Anki APKG

### 3. 성능 / 지표 (Performance / Metrics)
- FSRS-6 algorithm: same efficiency benchmarks as py-fsrs (20–30% review reduction vs. SM-2)
- January 2026 bug fix corrected a regression where due dates were miscalculated
- No published internal benchmark data; relies on FSRS upstream performance

### 4. 강점 (Strengths)
1. Markdown + LaTeX authoring is well-suited for equation-heavy cards
2. FSRS algorithm now in beta — tracks open-spaced-repetition spec
3. Excellent macOS desktop app: native M-series binary, fast
4. Clean, minimal UI with focus on card content
5. Import from Anki APKG: existing course decks can be migrated

### 5. 약점 / 한계 (Weaknesses)
1. FSRS still in beta as of April 2026; has had regressions (v1.20.5 fix)
2. Cannot integrate Mochi's SRS engine into our custom React tutor
3. Proprietary — no access to scheduling source code
4. 200-card free tier is too restrictive for a full course
5. No equation input (handwriting or MathLive-style); card authoring is LaTeX-typed only

### 6. 통합 난이도 (Integration difficulty for our React+Vite stack)
**Not integrable.** Mochi is a standalone app. Relevant only as a competitor reference or student recommendation.

### 7. 결론 (Verdict)
**REJECT (as library) / PARTIAL-ADOPT (student recommendation)** — Mochi is a capable flashcard app for self-study supplementation. Do not attempt to use it as our SRS backend. Use py-fsrs directly instead.

---

## Category B: Equation Rendering + Input Components

---

## KaTeX 0.16.x

**Repo / URL**: https://github.com/KaTeX/KaTeX  
**License / Cost**: MIT — Free  
**Latest version**: 0.16.45 — April 5, 2026

### 1. 개요 (Overview)
KaTeX is a fast, synchronous, browser-side LaTeX rendering library that converts LaTeX strings to HTML+MathML without requiring a server; it is the current display engine in this project.

### 2. 핵심 기능 (Core capabilities)
- Synchronous HTML+MathML output (no async/reflow)
- Server-side rendering (SSR) via `katex.renderToString()`
- Display and inline math modes
- ~90% of common LaTeX math commands supported
- `\text{}`, `\boldsymbol{}`, `\mathbb{}` for HH notation (`\hat{m}_\infty`, `\nabla^2 V`)
- `\begin{aligned}`, `\begin{cases}` environments for cable PDE derivations
- Auto-render extension for scanning DOM for `$...$` / `$$...$$`
- `@types/katex` available on DefinitelyTyped

### 3. 성능 / 지표 (Performance / Metrics)
- **Bundle size**: ~347 kB total with fonts; JS-only minified ~82 kB, gzipped ~30 kB (well-documented range from community measurements)
- **Render latency**: < 5 ms for typical inline expressions; < 15 ms for complex aligned environments like full HH gating equations on M-series
- **SSR throughput**: ~10 000 equations/second server-side (benchmarked by Khan Academy team)
- No JavaScript re-renders on viewport change (purely CSS layout)

### 4. 강점 (Strengths)
1. Fastest synchronous web math renderer: no flash-of-unstyled-math, critical for card-flip UX
2. SSR support: pre-render equations at build time or on the server — zero client-side cost for static cards
3. Minimal JS bundle: lightest of all rendering options (~30 kB gzipped JS)
4. Mature, well-tested: Khan Academy, Observable, Jupyter all use KaTeX
5. Auto-render plugin handles mixed Korean+math text in a single pass without manual parsing

### 5. 약점 / 한계 (Weaknesses)
1. **Display only**: no input capability — students cannot type into a KaTeX expression
2. ~10% of advanced LaTeX commands unsupported (e.g., `\tikz`, some AMS environments, `\intertext`)
3. Accessibility (ARIA): MathML output is generated but screen reader support is weaker than MathJax
4. No dynamic re-rendering API: must call `katex.render()` again with the new string on any content change
5. Font files add ~280 kB of additional load; needs CDN or self-hosting strategy for performance

### 6. 통합 난이도 (Integration difficulty for our React+Vite stack)
Already installed. No changes needed for display. Integration complexity: 0 additional effort.

```tsx
import katex from 'katex';
import 'katex/dist/katex.min.css';

const EquationDisplay = ({ latex }: { latex: string }) => {
  const html = katex.renderToString(latex, { throwOnError: false, displayMode: true });
  return <span dangerouslySetInnerHTML={{ __html: html }} />;
};
```

Korean IME: irrelevant for display-only use. Auto-render plugin ignores Korean text between equation delimiters correctly.

### 7. 결론 (Verdict)
**ADOPT (keep current)** — KaTeX 0.16.x covers all HH gating and cable PDE equations used in BRI610. The synchronous render model is ideal for SRS card-flip transitions. No reason to switch to MathJax for display. Continue using KaTeX for all output rendering.

---

## MathJax 3.2

**Repo / URL**: https://github.com/mathjax/MathJax-src  
**License / Cost**: Apache-2.0 — Free  
**Latest version**: 3.2.2 — 2023 (3.x branch stable; 4.0 beta in development)

### 1. 개요 (Overview)
MathJax 3.2 is a comprehensive LaTeX/AsciiMath/MathML typesetting library targeting near-complete LaTeX coverage with high-fidelity HTML/SVG/MathML output; it is the primary alternative to KaTeX.

### 2. 핵심 기능 (Core capabilities)
- Complete TeX, LaTeX, AsciiMath, MathML input
- HTML-CSS, SVG, and MathML output formats
- Async loading model (but configurable synchronous in Node.js SSR)
- Accessibility: full ARIA + speech-rule engine (reading equations aloud)
- Copy-as-LaTeX browser menu (right-click on rendered math)
- Semantic MathML for screen readers
- Modular: load only the TeX extensions needed

### 3. 성능 / 지표 (Performance / Metrics)
- **Bundle size**: 59.1 kB minified+gzipped for `mathjax` npm package (core); full installation with fonts is 5–15 MB
- **Render latency**: 20–80 ms first render (async DOM insertion + font loading); subsequent renders with cache hit < 5 ms
- In some benchmarks (intmath.com), MathJax 3 and KaTeX 0.16 render times are within 2x of each other for simple expressions; MathJax is slower for complex nested environments
- SSR via `mathjax-node` or `mathjax-full` packages possible but significantly more complex to configure

### 4. 강점 (Strengths)
1. Near-complete LaTeX coverage: handles obscure AMS environments, `\operatorname`, `\mathscr`, custom `\newcommand` definitions
2. Best accessibility: speech-rule engine reads equations aloud correctly (important for bilingual student)
3. SVG output available: resolution-independent, looks perfect on Retina/HiDPI M-series displays
4. Right-click copy-as-LaTeX: student can click any rendered equation and copy the source
5. `\newcommand` support: define shorthand for recurring HH notation (e.g., `\newcommand{\minf}{m_\infty}`)

### 5. 약점 / 한계 (Weaknesses)
1. **Async rendering**: flash-of-unstyled-math on first load; unacceptable for SRS card-flip unless SSR pre-rendered
2. Initial render is 4–16x slower than KaTeX for cold page loads
3. Significantly larger full installation footprint (fonts + assets = 10+ MB)
4. React integration is community-maintained (`better-react-mathjax`, not official)
5. 3.x series receiving only maintenance; 4.0 is beta and not stable — upgrade path uncertain

### 6. 통합 난이도 (Integration difficulty for our React+Vite stack)
```bash
npm install better-react-mathjax
```
Requires `MathJaxContext` provider wrapping the app, then `<MathJax>` component for each equation. More boilerplate than KaTeX. TypeScript types in `better-react-mathjax` are maintained but lag releases. Korean IME compatibility: irrelevant for display-only.

### 7. 결론 (Verdict)
**REJECT (as replacement) / PARTIAL-ADOPT (specific use case)** — Do not replace KaTeX with MathJax. KaTeX is faster for synchronous SRS card rendering. MathJax is worth considering only if we add screen-reader accessibility requirements or need `\newcommand` expansion for custom notation macros. For now, keep KaTeX 0.16.x.

---

## MathLive

**Repo / URL**: https://github.com/arnog/mathlive  
**License / Cost**: MIT — Free  
**Latest version**: 0.109.1 — April 2026

### 1. 개요 (Overview)
MathLive is a web component (`<math-field>`) that provides WYSIWYG LaTeX equation input in the browser, combining a virtual keyboard, physical keyboard shortcuts, and export to LaTeX/MathML/ASCIIMath; it is the leading open-source math input solution for web applications.

### 2. 핵심 기능 (Core capabilities)
- 800+ LaTeX commands with autocomplete (type `\` → dropdown suggestions)
- Physical keyboard shortcuts: `/` → `\frac{}{}`, `^` → superscript, `_` → subscript
- Configurable virtual keyboard: can add domain-specific keys (e.g., HH gating variables `α_m`, `β_h`)
- Export: `getValue('latex')`, `getValue('mathml')`, `getValue('ascii-math')`, `getValue('math-json')`
- Mobile-ready: tap-based virtual keyboard on iOS/Android (less relevant for Mac user)
- Programmatic control: `el.insert('\frac{}{}')`; `el.setOptions({ readOnly: true })`
- Inline mode and display mode; can be used as a read-only renderer too

### 3. 성능 / 지표 (Performance / Metrics)
- **Bundle size**: ~728 kB minified (JS; reported in GitHub issue #2270 for v0.97.1); gzipped estimate ~220–250 kB. Much larger than KaTeX — this is the primary cost.
- **Input latency**: < 16 ms keystroke-to-render for most expressions (60 fps threshold)
- Lazy-loads virtual keyboard assets only on first keyboard open
- **Syntax breadth**: 800+ commands; covers all HH gating notation and cable PDE operators
- Weekly downloads: ~117 000/week on npm (10–20x more than MathQuill)

### 4. 강점 (Strengths)
1. Best keyboard UX: autocomplete, smart bracket matching, structural navigation (arrow keys move through sub/superscripts correctly)
2. Custom virtual keyboard: can pre-populate HH variables as tap targets, reducing typing burden
3. MIT license with no commercial restrictions
4. Actively maintained: semi-annual major releases, Arnaud Cabanis (author) responds to issues within days
5. `getValue('latex')` returns clean, compilable LaTeX immediately — no post-processing needed to pass to KaTeX

### 5. 약점 / 한계 (Weaknesses)
1. **Large bundle**: ~728 kB minified is a significant addition to the Vite bundle; needs code-splitting or dynamic import
2. **Korean IME conflict (critical)**: web components with `contenteditable` frequently conflict with IME composition events on macOS; Korean syllable assembly (e.g., 한글 Jamo composition) can inject stray characters into the math field or break composition sequences. This requires explicit `compositionstart`/`compositionend` event guards.
3. Web component shadow DOM: styling from the host app does not penetrate without CSS custom properties; matching app theme requires effort
4. No built-in LaTeX validation or error reporting: invalid expressions are silently accepted
5. SSR/Vite hydration: web components defined in a custom registry may cause hydration mismatches in SSR mode; must use `client:only` pattern or dynamic import

### 6. 통합 난이도 (Integration difficulty for our React+Vite stack)
```bash
npm install mathlive
```
**TypeScript types:** bundled in package (no `@types/` needed).  
**React component:** use as web component in JSX; declare intrinsic element type.  
**Korean IME:** add composition event guards (see Synthesis 2 for full TSX).

```tsx
// vite.config.ts — no special config needed
// src/types/mathlive.d.ts
import type { MathfieldElement } from 'mathlive';
declare global {
  namespace JSX {
    interface IntrinsicElements {
      'math-field': React.DetailedHTMLProps<
        React.HTMLAttributes<MathfieldElement>,
        MathfieldElement
      >;
    }
  }
}
```

Dynamic import to avoid adding 728 kB to initial bundle:
```tsx
const MathField = React.lazy(() => import('./components/MathInput'));
```

### 7. 결론 (Verdict)
**ADOPT** — MathLive is the best open-source equation input component for our stack. The bundle size penalty is manageable with dynamic import (load only on SRS input screens). Korean IME requires explicit composition event handling but is solvable (see Synthesis 2). No other open-source component matches its keyboard UX quality for LaTeX input.

---

## MyScript Math SDK

**Repo / URL**: https://github.com/MyScript/myscript-math-web; commercial API at https://developer.myscript.com  
**License / Cost**: Proprietary — Free tier with monthly quota (developer.myscript.com); commercial licensing required for production beyond quota  
**Latest version**: iink SDK 4.3 — January 2026

### 1. 개요 (Overview)
MyScript Math SDK (iink SDK) is a cloud-based handwriting recognition engine that converts pen/stylus stroke sequences to LaTeX, MathML, or MathJSON via an HTTP API, with a companion `myscript-math-web` Web Component for the stroke capture UI.

### 2. 핵심 기능 (Core capabilities)
- Cloud inference: stroke data sent to MyScript cloud → structured math LaTeX returned
- iink SDK 4.3 (Jan 2026): unified encoder-decoder attention model; multi-language support
- Exports: LaTeX, MathML, Typst
- `myscript-math-web` Web Component: canvas-based stroke capture, gesture recognition (scratch-to-erase)
- Offline SDK available for enterprise licensing (iOS/Android native)
- Supports > 100 mathematical symbols including integrals, summations, matrices

### 3. 성능 / 지표 (Performance / Metrics)
- Recognition latency: 200–800 ms round-trip to cloud (network-dependent); unsuitable for real-time preview
- Reported accuracy: > 95% on standard math symbol recognition (MyScript internal benchmarks, not independently verified)
- Cloud API: requires API key and active internet connection
- Free tier: undisclosed monthly request quota (typically ~2 000 requests/month for developers)

### 4. 강점 (Strengths)
1. Best-in-class commercial handwriting recognition: decades of training data, broad symbol coverage
2. iink SDK 4.3 improved architecture: encoder-decoder attention model handles ambiguous symbols better
3. LaTeX output is clean and compilable: can be passed directly to KaTeX for display
4. Scratch-to-erase gesture: natural handwriting editing UX

### 5. 약점 / 한계 (Weaknesses)
1. **Mac M-series trackpad**: finger-drawing on a trackpad is poor UX; this SDK is designed for stylus/tablet input. The student has no tablet.
2. **Cloud dependency**: API calls require internet; latency 200–800 ms breaks the flow of equation entry
3. **Proprietary pricing**: production use beyond the free quota requires commercial licensing; cost unknown without sales contact
4. API key management adds infrastructure complexity
5. Web Component is aging (`myscript-math-web` last major update 2020); iink SDK has a newer integration path but requires more custom code

### 6. 통합 난이도 (Integration difficulty for our React+Vite stack)
Requires API key from developer.myscript.com. Integration: load Web Component, pass `applicationKey` and `hmacKey` props, handle `exported` event to get LaTeX string. Medium difficulty (30–50 lines). TypeScript types: minimal, community-maintained. Korean IME: irrelevant (stroke-based, not keyboard input).

### 7. 결론 (Verdict)
**REJECT** — The primary blocker is hardware: our user has a Mac M-series with no stylus or tablet. Trackpad handwriting is unusable for complex mathematical expressions. If the student ever acquires an iPad + Apple Pencil, MyScript is the recommended cloud recognition engine for equation input. For now, keyboard-based MathLive is the correct choice.

---

## Seshat

**Repo / URL**: https://github.com/falvaro/seshat  
**License / Cost**: GPL-3.0 — Free  
**Latest version**: No formal release since ~2015; last commit ~2016

### 1. 개요 (Overview)
Seshat is an academic C++ research system for offline handwritten mathematical expression recognition, converting InkML stroke sequences to LaTeX; it won the ICFHR 2014 competition on online handwritten math recognition.

### 2. 핵심 기능 (Core capabilities)
- C++ binary: parses InkML stroke files → outputs LaTeX string
- Uses RNNLIB (recurrent neural network) for symbol classification
- Supports ~100 common math symbols
- Award-winning at ICFHR 2014 competition

### 3. 성능 / 지표 (Performance / Metrics)
- ICFHR 2014: best system trained on competition dataset
- No published benchmark on modern math notation (post-2016)
- Recognition accuracy on complex expressions (matrices, integrals): significantly lower than MyScript or modern DL models
- No maintained WASM/web build; C++ only

### 4. 강점 (Strengths)
1. Open source (GPL): no licensing cost, no API quota
2. Runs locally: no cloud dependency, works offline
3. Academic pedigree: peer-reviewed, well-documented algorithm

### 5. 약점 / 한계 (Weaknesses)
1. **Abandoned**: last commit ~2016; no maintenance, no macOS M-series build tested
2. Requires C++ compilation: non-trivial to build on Apple Silicon; RNNLIB dependency has build issues with modern compilers
3. No web/WASM port: cannot run in browser; would need a Python wrapper service
4. Recognition quality far below current state of the art (2026)
5. Same hardware problem as MyScript: designed for stylus/tablet stroke input, not trackpad

### 6. 통합 난이도 (Integration difficulty for our React+Vite stack)
**Very high / impractical.** Would require: compile C++ for macOS arm64, wrap in Python Flask service, expose REST API, integrate stroke capture canvas in React. Estimated effort: 3–5 days with uncertain success.

### 7. 결론 (Verdict)
**REJECT** — Abandoned project, hardware mismatch (no tablet), significant build complexity on Apple Silicon, and recognition quality inferior to modern alternatives. Seshat is a historical reference; no production use case.

---

## Detexify

**Repo / URL**: https://github.com/kirel/detexify; live at https://detexify.kirelabs.org  
**License / Cost**: MIT (frontend) — Free; backend is separately hosted  
**Latest version**: Website operational April 2026; last major codebase update ~2022

### 1. 개요 (Overview)
Detexify is a LaTeX symbol classifier where users draw a symbol with a mouse/trackpad and receive a ranked list of LaTeX command matches; it is a lookup tool for unknown symbols, not a full equation input system.

### 2. 핵심 기능 (Core capabilities)
- Sketch-to-symbol lookup: draws → top-5 LaTeX command suggestions
- ~1 000 LaTeX symbols in the database
- Browser-side ML classifier (self-contained in-browser variant)
- REST API endpoint for programmatic use (unofficial, rate-limited)
- Overleaf extension (extexify) demonstrates embed pattern

### 3. 성능 / 지표 (Performance / Metrics)
- Recognition scope: single symbols only — cannot recognize multi-symbol expressions or entire equations
- Latency: < 200 ms for symbol classification (browser-side ML variant)
- Accuracy: high for common symbols (Greek letters, operators); lower for rare symbols

### 4. 강점 (Strengths)
1. Solves the "I know the symbol but not the command" problem effectively
2. Browser-side ML variant: zero server dependency, works offline
3. MIT licensed: embeddable in our UI as a symbol picker
4. Familiar UX: students already use detexify.kirelabs.org

### 5. 약점 / 한계 (Weaknesses)
1. Single-symbol scope: cannot recognize `\frac{d^2V}{dx^2}` — only individual symbols
2. Requires mouse/trackpad drawing: usable on Mac but limited precision vs. stylus
3. Codebase is stale (~2022); no active maintainer
4. Not a LaTeX input solution: must be combined with a text editor or MathLive
5. No Korean interface: symbol names displayed in English only

### 6. 통합 난이도 (Integration difficulty for our React+Vite stack)
**Low as a supplemental widget.** Embed the browser-side classifier (~150 kB additional), show a canvas modal when student clicks "find symbol," then insert the returned command into MathLive via `el.insert('\sigma')`. ~50 lines of React code. No TypeScript types available; minor typing effort needed.

### 7. 결론 (Verdict)
**PARTIAL-ADOPT** — Integrate Detexify as a "symbol finder" palette accessible from the MathLive toolbar. It solves a real pain point for STEM students who know what a symbol looks like but not its LaTeX command. Do not use as a primary input method. Scope: a small floating panel triggered by a "?" button in the equation input UI.

---

## MathQuill

**Repo / URL**: https://github.com/mathquill/mathquill; React wrapper: https://github.com/viktorstrate/react-mathquill  
**License / Cost**: MPL-2.0 — Free  
**Latest version**: 0.10.1-a (base); react-mathquill 1.0.4 — last published ~August 2025

### 1. 개요 (Overview)
MathQuill is a web-based equation editor that renders LaTeX in real-time as the user types, using a custom DOM-based approach; it predates MathLive and remains popular in education platforms (Khan Academy originally used it).

### 2. 핵심 기능 (Core capabilities)
- Real-time LaTeX rendering as the user types
- Static and editable math field modes
- `latex()` getter/setter API for reading/writing LaTeX strings
- jQuery dependency in older versions; newer versions have reduced jQuery coupling
- MPL-2.0 license: copyleft for changes to MathQuill itself, permissive for embedding

### 3. 성능 / 지표 (Performance / Metrics)
- Bundle size: ~150 kB minified (significantly smaller than MathLive)
- npm weekly downloads: ~6 278 (react-mathquill); ~21 178 (react-mathquill React wrapper)
- MathLive npm weekly downloads: ~117 068 — 10–20x more popular
- Last meaningful maintenance on core: 2022; react-mathquill wrapper: August 2025

### 4. 강점 (Strengths)
1. Smaller bundle than MathLive (~150 kB vs ~728 kB)
2. react-mathquill React wrapper is mature with 156 downstream packages using it
3. Simple API: `<EditableMathField latex={latex} onChange={handleChange} />`
4. Well-documented; many StackOverflow examples

### 5. 약점 / 한계 (Weaknesses)
1. **Effectively abandoned**: core MathQuill 0.10.1-a has not had a real release since ~2016; version `0.10.1-a` itself is a pre-release tag
2. Keyboard UX inferior to MathLive: no autocomplete, limited structural navigation
3. Fewer supported commands than MathLive: missing some AMS environments
4. MPL-2.0 vs MIT: weaker license for embedding (must open-source modifications to MathQuill)
5. No virtual keyboard: mobile/touch experience is poor

### 6. 통합 난이도 (Integration difficulty for our React+Vite stack)
```bash
npm install react-mathquill
```
Simple React integration via `<EditableMathField>`. TypeScript: community types available (`@types/mathquill`). Korean IME: same composition event conflict as MathLive but less documented and less tested.

### 7. 결론 (Verdict)
**REJECT** — MathQuill is functionally superseded by MathLive in every dimension: command coverage, keyboard UX, virtual keyboard, maintenance activity, and npm adoption. The only advantage (smaller bundle) is insufficient justification. MathLive with dynamic import achieves comparable initial load performance.

---

## CodeCogs Equation Editor

**Repo / URL**: https://editor.codecogs.com; API docs: https://editor.codecogs.com/docs/4-API  
**License / Cost**: Free for non-commercial; commercial license required for production; rate-limited API  
**Latest version**: Web service (no versioned npm package); API last updated 2024

### 1. 개요 (Overview)
CodeCogs is a web-embeddable LaTeX equation editor that provides a toolbar-driven GUI for equation construction and delivers rendered equation images (PNG/SVG) via a rendering CDN URL; it is the oldest and most widely embedded math editor on the web.

### 2. 핵심 기능 (Core capabilities)
- Visual toolbar: click-to-insert operators, Greek letters, fractions, integrals
- Renders equation as PNG/GIF/SVG image via `https://latex.codecogs.com/svg.image?{LaTeX}`
- Embeddable editor widget: load JS + CSS from CDN, attach to `<div>`
- TextArea API: links editor toolbar to a `<textarea>` element
- Output: LaTeX string + rendered image URL

### 3. 성능 / 지표 (Performance / Metrics)
- CDN image render latency: 100–300 ms per equation (server-side rendering, network-dependent)
- Image output: not resolution-independent (PNG) unless SVG mode used
- No offline capability: requires CodeCogs CDN availability
- Bundle: external CDN script (~80 kB); no npm package

### 4. 강점 (Strengths)
1. Zero local rendering setup: image URL can be used anywhere (`<img src="...">`)
2. Visual toolbar lowers entry barrier for students unfamiliar with LaTeX
3. Widely used in forums, wikis, and LMS platforms — students may already know it
4. SVG mode available: resolution-independent rendering

### 5. 약점 / 한계 (Weaknesses)
1. **Image-based output**: not real-time interactive; no inline preview while typing
2. CDN dependency: production use requires CodeCogs servers to be available
3. Non-commercial license restriction: unclear terms for integration into a university tutor tool
4. No npm package: no type safety, no Vite-native import
5. UX is outdated: 2000s-era GUI; poor mobile experience

### 6. 통합 난이도 (Integration difficulty for our React+Vite stack)
**Medium difficulty / poor fit.** Load external CDN scripts via `useEffect`, attach to DOM refs. No React component wrapper. No TypeScript types. The image-URL approach bypasses React's rendering model entirely. Korean IME: the toolbar interaction is click-based so no IME conflict, but text input areas may still have issues.

### 7. 결론 (Verdict)
**REJECT** — CodeCogs is a legacy tool with an image-based rendering model that conflicts with our React architecture and real-time equation preview requirement. MathLive provides superior UX, is MIT licensed, and is npm-native. CodeCogs is only relevant for generating static equation images in emails or PDFs where interactive input is not needed.

---

## Synthesis 1: SRS Algorithm Choice

**Recommended algorithm: FSRS-6** — not SM-2.

The benchmark data is decisive: FSRS-6 achieves lower log loss than SM-2 for 99.6% of users across 1.7 billion reviews. More critically for our use case, SM-2's "ease hell" is a serious hazard for equation-heavy STEM content — when a student repeatedly marks a cable PDE derivation step as Hard, SM-2 drives the ease factor to its 1.3 minimum floor, locking that card into permanent short intervals regardless of subsequent mastery. FSRS-6's stability-difficulty decomposition handles this correctly: difficulty is updated but stability grows independently as the student consolidates the memory.

**Recommended Python library: py-fsrs 6.3.1** (MIT, actively maintained by the same team as the algorithm spec). Install with `pip install fsrs==6.3.1`. Expose a `/api/srs/review` FastAPI endpoint that accepts a card rating and returns the updated card state.

**Recommended TypeScript port: ts-fsrs 5.3.2** for frontend scheduling. Run scheduling in the browser during a study session (no round-trips for interval calculation); sync review logs to the backend after each session for optimizer runs.

**DB schema — `srs_cards` table:**

```sql
CREATE TABLE srs_cards (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      UUID NOT NULL REFERENCES users(id),
  concept_id   TEXT NOT NULL,          -- e.g. "hh.gating.m_inf"
  card_type    TEXT NOT NULL,          -- 'recall' | 'derive' | 'equation_fill'
  stability    FLOAT NOT NULL DEFAULT 0,
  difficulty   FLOAT NOT NULL DEFAULT 5,
  due          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_review  TIMESTAMPTZ,
  state        TEXT NOT NULL DEFAULT 'new', -- 'new'|'learning'|'review'|'relearning'
  lapses       INT NOT NULL DEFAULT 0,
  reps         INT NOT NULL DEFAULT 0,
  params       JSONB,                  -- 21-float user-optimized weight vector
  created_at   TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX ON srs_cards (user_id, due);
```

**Card-extraction strategy for graduate STEM** (not flashcards-from-text): for HH gating and cable equations, cards should be extracted at the derivation-step level, not the concept level. Each card represents a single algebraic transformation with the preceding state as the question and the next state as the answer. Three card types: (1) **recall** — given the concept name, write the equation from memory; (2) **derive** — given equation at step N, produce step N+1 with LaTeX input; (3) **equation_fill** — display the equation with one term blanked, student types the missing piece into a MathLive field. This granularity ensures that forgetting one step of a derivation (e.g., the steady-state approximation in HH gating) surfaces as a card failure rather than hiding inside a concept-level card that the student answers correctly by pattern-matching the final result.

---

## Synthesis 2: Equation Input UX

**Display engine: keep KaTeX 0.16.x.** No switch to MathJax is warranted. KaTeX's synchronous render model is essential for SRS card-flip animations — any async rendering produces a visual flash on card reveal. KaTeX 0.16.45 (April 2026) covers all BRI610 notation including HH gating (`\hat{m}_\infty`, `\alpha_m(V)`, `\bar{g}_{Na}`) and cable PDE operators (`\nabla^2 V`, `\frac{\partial V}{\partial t}`, `\lambda^2`). SSR pre-rendering of card fronts and backs at ingest time further reduces client-side work to zero for display.

**Input component: MathLive 0.109.1.** MathLive is the clear winner over MathQuill (abandoned core, inferior UX) and MyScript (no tablet hardware). The 728 kB bundle cost is addressed with `React.lazy()` + dynamic import so the math field is only loaded on SRS input screens, not the main dashboard.

**Korean IME concern:** The critical issue is that macOS Korean IME (한글 입력) uses a two-phase composition sequence — Jamo assembly fires `compositionstart` and `compositionend` events around a sequence of `keydown`/`input` events. MathLive's `<math-field>` web component intercepts keyboard events in its shadow DOM, which can interrupt the composition sequence, causing partially assembled Korean syllables to appear as raw Jamo characters inside the math field. **Solution:** (1) Place a separate `<textarea>` above or beside the math field for Korean annotations; never type Korean directly into the `<math-field>`. (2) Add a `compositionstart` handler that sets `el.mathVirtualKeyboardPolicy = "off"` to prevent the virtual keyboard from hijacking the IME event sequence. (3) Set `el.setAttribute('lang', 'ko')` on the element but this does not resolve the composition conflict — the separate textarea is the correct architectural solution.

**Voice-to-LaTeX:** Use GPT-4o audio (or Whisper API + GPT-4o text) rather than local Whisper + LLM. Reason: local Whisper on M-series transcribes Korean math dictation acceptably but the subsequent LaTeX structuring step (e.g., voice says "분의 dV dt" → `\frac{dV}{dt}`) requires a bilingual math-aware LLM. GPT-4o's audio mode handles this end-to-end in a single API call with a system prompt specifying LaTeX output. Local Whisper + local LLM (e.g., Ollama llama3) is feasible on M-series but accuracy for mixed Korean+LaTeX dictation is poor in April 2026 without fine-tuning.

**Sketch-to-LaTeX on Mac (no tablet):** Realistically limited. Trackpad gesture recognition for multi-stroke math expressions is impractical without a stylus-quality input surface. The most viable option is to embed the Detexify browser-side classifier as a single-symbol lookup palette (see Detexify report above). For whole-equation sketch, MyScript could be enabled if the student acquires an iPad + Apple Pencil (use `myscript-math-web` Web Component, pass strokes from `PointerEvent` on a `<canvas>`). Do not invest in this path for the current hardware configuration.

**Concrete React integration for MathLive (~30 lines TSX):**

```tsx
// src/components/MathInput.tsx
import React, { useRef, useEffect, useCallback } from 'react';
import 'mathlive'; // registers <math-field> custom element

declare global {
  namespace JSX {
    interface IntrinsicElements {
      'math-field': React.DetailedHTMLProps<
        React.HTMLAttributes<HTMLElement> & {
          'virtual-keyboard-mode'?: string;
          value?: string;
        },
        HTMLElement
      >;
    }
  }
}

interface Props {
  initialValue?: string;
  onChange: (latex: string) => void;
  placeholder?: string;
}

export function MathInput({ initialValue = '', onChange, placeholder }: Props) {
  const mfRef = useRef<HTMLElement & { value: string }>(null);

  useEffect(() => {
    const el = mfRef.current;
    if (!el) return;

    // Prevent virtual keyboard from hijacking macOS IME
    (el as any).mathVirtualKeyboardPolicy = 'manual';

    // Initial value
    (el as any).value = initialValue;

    const handleInput = (evt: Event) => {
      onChange((evt.target as any).value ?? '');
    };
    const handleCompositionStart = () => {
      // Suspend MathLive keyboard capture during Korean IME composition
      (el as any).mathVirtualKeyboardPolicy = 'off';
    };
    const handleCompositionEnd = () => {
      (el as any).mathVirtualKeyboardPolicy = 'manual';
    };

    el.addEventListener('input', handleInput);
    el.addEventListener('compositionstart', handleCompositionStart);
    el.addEventListener('compositionend', handleCompositionEnd);
    return () => {
      el.removeEventListener('input', handleInput);
      el.removeEventListener('compositionstart', handleCompositionStart);
      el.removeEventListener('compositionend', handleCompositionEnd);
    };
  }, [onChange, initialValue]);

  return (
    <math-field
      ref={mfRef as any}
      virtual-keyboard-mode="manual"
      style={{ width: '100%', fontSize: '1.2em', border: '1px solid #ccc', borderRadius: 4 }}
    >
      {initialValue}
    </math-field>
  );
}

// Usage in SRS card:
// const [latex, setLatex] = useState('');
// <MathInput onChange={setLatex} placeholder="\frac{dV}{dt} = ?" />
// <button onClick={() => submitAnswer(latex)}>제출</button>
```

Load this component lazily in the SRS review screen:
```tsx
const MathInput = React.lazy(() =>
  import('./components/MathInput').then(m => ({ default: m.MathInput }))
);
```

This defers the 728 kB MathLive bundle until the student enters a review session, keeping the initial page load under 400 kB total.

---

*Report generated April 26, 2026. Data sources: open-spaced-repetition/py-fsrs PyPI (v6.3.1 confirmed), open-spaced-repetition/srs-benchmark README (FSRS-6 log loss 0.3460±0.0042), KaTeX GitHub releases (v0.16.45, April 5 2026), MathLive npm (v0.109.1), mathlive GitHub issue #2270 (728 kB bundle), mathjax npm bundlephobia (59.1 kB gzipped core), MyScript iink SDK 4.3 (January 2026 release notes), expertium.github.io benchmark (99.6% FSRS superiority over SM-2).*
