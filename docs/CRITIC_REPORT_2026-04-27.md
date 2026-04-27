# Critic Report — L3 v2 summary + 16 figures

Reviewer: Opus 4.7 (1M ctx), simulating a graduate computational-neuroscience reader with prior journal-design experience.
Date: 2026-04-27. Material reviewed: `/api/summaries/L3` (cached, 173 lines), 16 SVGs in `frontend/public/figures/`, `docs/DESIGN.md`, `scripts/seed_exemplar_L3_v2.py`.

## Overall verdict: NEEDS REVISION

Strong bones (clear structure, consistent palette, real derivations), but four classes of defects keep this below the journal bar:
1. **Numerical inconsistency between summary and figures** (E_K is −83 in §7 but −90 on the GHK column and Nernst caption; V_rest ≈ −80 in §7 but −70 in the GHK output and AP figure). Fix once, in one source of truth.
2. **One genuine sign/ordering error** in §3 (R_m typical-values range printed in the wrong direction) and an **arithmetic slip** in §4 (τ_m = 10–100 ms is fine but does not square with `R_m C_m` of typical specific values quoted; needs a worked one-liner).
3. **Several figures that look fine in isolation but contain quiet correctness defects**: cable_decay_spatial.svg has a tangle of two curves on a normalized x-axis that is fundamentally ambiguous; hippocampal_phase_precession.svg has a duplicated-typo y-axis label; ohmic_iv.svg places the slope label *below* the line where slope-text overlaps the V−E_X driving-force annotation; ap_propagation_unmyelinated.svg buries t₁/t₂ time-slice indices in a way that is unparseable without the caption.
4. **Pedagogical hole**: §9 (identifiability) introduces *cable r_m / r_i* without ever defining them or distinguishing them from the section-1 R_m. Student rusty on EM cannot survive this jump.

The summary is genuinely well-organized and the analogy table (§6) is one of the best things I have seen in this codebase — it earns its space. But the inconsistencies above will be the *first* thing a careful student notices, and trust collapses on that point.

---

## L3 v2 summary

### Pedagogical clarity: 7/10
The bottom-up pacing (§1 capacitor → §2 I_C = C dV/dt → §5 KCL → §7 Nernst → §8 GHK) is correct and the "한 줄 요약" device at each section anchor is excellent for revision. Good plain-language metaphors ("capacitor 가 전류를 먹는다", L26).

But:
- **§3 line 38** prints `R_m ≈ 1 MΩ·cm² ~ 1 GΩ·cm²` with the ascii tilde rendering as a range. This is the wrong direction for typical *specific* membrane resistance — usually quoted **kΩ·cm² to ~100 kΩ·cm²** (Hille, Dayan & Abbott, Koch). 1 MΩ·cm² is plausible for very high-R neurons; 1 GΩ·cm² is essentially impossible for a real membrane (would imply leak conductance of 1 nS/cm² — a million-fold lower than measured). A student who memorizes this will fail every problem set.
- **§4 line 51** says "C_m and R_m … *specific* form … cancels". True, but the prose collapses two distinct objects (specific R_m in Ω·cm² vs. whole-cell R_input in MΩ) without naming them. This is the same conflation that kills students at L6 (cable theory).
- **§9 line 144** introduces "dendrite의 multi-time-constant" as a complication without prior buildup. A student who is rusty on ODE theory will read this as magic.

### Scientific accuracy: 6/10
Real defects:
1. **§3 line 38** range inversion (above): `1 MΩ·cm² ~ 1 GΩ·cm²` should be roughly `1 kΩ·cm² – 100 kΩ·cm²` for *specific* membrane resistance (R_m in classical Hodgkin–Huxley units), or alternatively `10 MΩ – 1 GΩ` for *whole-cell* input resistance (R_input). Pick one convention and keep units consistent. As written, the numbers don't match either standard.
2. **§7 line 114**: "체온 310 K", uses `[K]_o = 5.5, [K]_i = 150` → log(5.5/150) × 26.7 mV ≈ **−87.9 mV**, not −83. The −83 figure comes from `[K]_o = 4.5` or T = 295 K. Reconcile: state T explicitly *or* state the concentration ratio that gives −83. Currently inconsistent with the bilayer_capacitor.svg figure that says −65 mV resting and the Nernst figure that says −90.
3. **§7 line 115**: `[Na]_o = 150 / [Na]_i = 15` → 26.7 × ln(10) = **+61.5 mV**, not +58. Either round to +60 (matches GHK figure) or change concentrations to typical mammalian (`140 / 18` → +57). Currently a 4-mV discrepancy with the GHK figure.
4. **§7 line 117**: `V_rest ≈ E_K ≈ −80 mV` — but the `ghk_weighted_log.svg` figure shows V_m ≈ −70 mV and E_K = −90. Pick a single convention. Real cortical V_rest is closer to −65 to −70 (because P_Na/P_K ≈ 0.04, *not* zero), so the "V_rest ≈ E_K" approximation is pedagogically misleading. A more honest statement: "휴지 막은 K leak이 dominant이지만 P_Na 의 작은 leak 때문에 V_rest 는 E_K 보다 ~10 mV depolarized."
5. **§8 GHK formula**: the Cl⁻ subscripts are correct (i in numerator, o in denominator) due to the negative charge — good. But the prose in §10.4 ("Nernst 들의 *log-domain* 가중평균") is technically wrong: GHK is **not** a log-mean of E_K, E_Na, E_Cl. It is `(RT/F) ln (weighted-numerator/weighted-denominator)`. These differ except in the limit where one permeability dominates. The summary actually states this correctly in §8 itself ("산술 평균이 아니라"), but §10 mis-summarizes it. Make §10 consistent.
6. **§2 line 28**: `C_m = 1 nF` neuron. State this is *whole-cell* (typical small neuron of ~100 µm × 100 µm patch ≈ 1×10⁻⁴ cm² × 1 µF/cm² = 1 nF). As written, a student may confuse this with specific C_m.
7. **§6 table row 4**: "ATP 차단 시 막은 댐이 *터지듯이* 무너진다 (ischemic depolarization)" — depolarization is roughly exponential to 0 over minutes-to-hours, not "터지듯이" (explosive). This is the right physiology but rhetorically overdramatic.

The Boltzmann derivation (§7, lines 104–111) is clean and correct. The membrane-equation derivation (§5) is clean and correct. The 30-second derivation goal is achievable from this text.

### Layout/readability: 8/10
- Block sizes are well-paced; no section is overlong.
- Five embedded figures (§1, §4, §5, §7, §8) are placed exactly where the eye needs them.
- Tables in §6 and §9 are excellent — best parts of the document.
- The boxed equations (`\boxed{...}`) in §5 and §7 give clean visual anchors.

But:
- **§9 table row "C_m" cell** is dense ("$I/(\dot V)$ … *변화* 신호에서만") — a student will need a second pass.
- **§11 self-check** is 8 items long for a 12-section document; consider consolidating to 5 (one per Tier-1 concept) and putting the rest in a "stretch" sub-list.
- The `> **24-시간 마스터리 목표**` blockquote at line 3 is a single 130-char run-on. Break it into three lines or three numbered items for scannability.

### Citation discipline: 9/10
All citations use `[Slide L3 p.##]`. No DA references. Pages cited (13, 18, 20, 22, 23, 27–29, 30) are within the L3 range (slides 13–33 per DESIGN). Given that DESIGN.md (line 33) says L3 spans p.13–p.33 and "membrane biophysics I" key concepts are V_m/C_m/R_m/τ_m/Nernst/GHK, the page assignments look plausibly grounded:
- p.13 = bilayer/capacitor intro ✓
- p.18 = C_m ≈ 1 µF/cm² universal claim ✓
- p.20 = the dV/dt = 1 mV/ms numerical anchor ✓
- p.27–29 = Nernst Boltzmann derivation ✓
- p.30 = GHK ✓

One minor critique: p.22 (R_m variability) and p.23 (τ_m area cancellation) are claims a slide deck *might* have but are usually expressed as side notes; verify these against the actual slide text. -1 pt because un-spot-checked, not because demonstrably wrong.

### Coverage of slide content: 6/10
**Missing** (relative to a typical L3 "membrane biophysics I" deck spanning 21 slides on these topics):
1. **Driving force / I-V relation**: there is an `ohmic_iv.svg` figure in the figure pool, but it is **not embedded in this summary**. The relation `I_X = g_X(V − E_X)` is the bridge from §7 (Nernst) to §5 (membrane equation, where leak is written as `(V − V_rest)/R_m`). Without this link, a student does not see why "V_rest" replaces "Σ ion equilibria weighted by g".
2. **Why is V_rest not exactly E_K?** The summary states V_rest ≈ E_K but never closes the loop with GHK — i.e., it does not point out that the ~10 mV gap is *exactly* what a non-zero P_Na/P_K ratio gives via GHK. This is the single most important conceptual link in the lecture.
3. **Driving force concept across reversal**: the inward/outward rectification logic that explains why Na⁺ depolarizes and K⁺ repolarizes — barely hinted at in §8 line 132 ("V_m 이 E_Na 쪽으로 끌려간다") but never made explicit.
4. **Equivalent circuit per ion (g_Na, g_K, g_L in parallel)**: the canonical "battery + variable resistor in parallel" diagram for each ion species is not shown. The membrane_rc_circuit.svg figure shows only one EMF (V_rest), collapsing the chemistry. For a student transitioning to L5 (HH), the parallel-conductance picture must be shown here.
5. **Resting Na/K ATPase pump as charge contributor**: §10.2 mentions it, but the summary never explains that the pump is **electrogenic** (3 Na out / 2 K in) and therefore contributes a small (~−5 mV) hyperpolarizing component to V_rest beyond the GHK prediction. This is an L3-level fact in most courses.
6. **Quantitative "1 nA → 1 mV/ms" derivation**: §2 line 28 states the result but does not show the unit-cancellation. For an EM-rusty student, this is exactly the kind of micro-derivation that should be in a foundation card or here.

### Memorability / intuition: 8/10
The §6 댐+수문 table is *the* highlight: the "수학은 같지만 생물은 다르다" framing distinguishes literal vs. metaphorical mapping in a way I rarely see done well. The "댐 응답은 분 단위, τ_m 은 밀리초 단위 (속도 차이 10⁵)" line is exactly the kind of factor-of-10 anchor that survives a year of forgetting.

§9's "식별성 깨진다 = 다른 매개변수 조합이 같은 데이터를 설명" is a real insight, well-localized.

But:
- §6 "댐 자체 (수위 = 전압)" — the dam analogy is strained because in a dam, water height *is* the stored quantity (analog of charge), not the analog of voltage. The pedagogically tighter mapping is: water-height-difference = voltage, water-volume-stored = charge, valve-aperture = conductance. Tighten this.
- The "ischemic depolarization 터지듯이" image (§6 last line) is wrong as physics (it's slow, ~minutes) and right as drama. Either fix or commit to the dramatization.
- §10.5 "휴지 막이 음수인 이유는 K가 양성이라서" — the correction explanation is actually murkier than the original misconception. Tighten to one sentence: "K⁺ 이 농도 기울기로 *밖으로 나가면서* 양전하를 가져가, cytoplasm 이 음전하 과잉이 된다."

### Concrete fixes for L3 v2

1. **§3 line 38**: replace `$R_m \approx 1\,\mathrm{M}\Omega \cdot \mathrm{cm}^2 \sim 1\,\mathrm{G}\Omega \cdot \mathrm{cm}^2$` with `$R_m \approx 1\text{–}100\,\mathrm{k}\Omega \cdot \mathrm{cm}^2$ (specific) — equivalent to whole-cell input resistance $R_\text{in} \approx 10\,\mathrm{M}\Omega\text{–}1\,\mathrm{G}\Omega$ depending on cell size.` Reason: current values are off by 3–6 orders of magnitude.

2. **§7 line 114**: change `$E_K \approx -83$ mV` to `$E_K \approx -88$ mV` (matches T=310 K, 5.5/150) **or** change concentrations to `[K]_o = 4, [K]_i = 140` and keep −90. Pick one and propagate to all five figures.

3. **§7 line 115**: same — Na⁺ at 150/15 → +61, not +58. Round to +60 globally.

4. **§7 line 117**: replace `$V_{rest} \approx E_K \approx -80$ mV` with: `$V_{rest} \approx -65$ mV (typical pyramidal) — about 25 mV depolarized from $E_K$ because $P_\text{Na}/P_K \approx 0.04$ (see §8 GHK).` This *closes the loop* with §8.

5. **§5 line 66**: between the KCL line and the boxed equation, insert one half-line: `(KCL: 한 노드로 들어가는 전류 = 나가는 전류; 그림 3 의 위쪽 노드에 적용.)` Reason: students rusty on EM forget which node KCL is applied to.

6. **§9 line 150**: define `r_m` and `r_i` (per-unit-length quantities) before using them, *or* replace with prose: "L6 cable theory 에서 specific 막 저항과 axoplasm 저항의 비율만 결정 가능 — 이유는 정상상태 V(x) 가 두 양의 비율 함수이기 때문." Reason: as written, undefined symbols.

7. **§10.4 misconception correction**: replace `*log-도메인* 가중평균. 산술평균 결과와 일반적으로 *다르다*` with `Nernst 들의 어떤 평균도 *아니다*. GHK 는 (RT/F) ln (이온별 농도-투과도 곱의 비). 정확한 Nernst-들의-평균이라는 표현은 misnomer.` Reason: the §8 prose itself says it's not arithmetic, but §10's "log-도메인 가중평균" overshoots into a claim that's also imprecise.

8. **Embed `ohmic_iv.svg` as new §3.5 figure** between R_m and τ_m: "Driving force = V − E_X · single-channel I-V." This is currently a wasted asset. Caption: "한 채널의 전류는 전압이 아니라 *driving force* (V − E_X) 에 비례. 이것이 §5 의 leak 항이 (V − V_rest)/R_m 인 이유."

9. **Add §3.6 "전체 회로의 합성"** showing the parallel-conductance picture: g_K · (V − E_K) + g_Na · (V − E_Na) + g_L · (V − E_L) = 0 at rest. This is the single missing concept that bridges §7 → §5.

10. **§11 self-check**: trim from 8 items to 5 (Tier 1 only): KCL+옴+capacitor → 막 방정식; Boltzmann → Nernst; τ_m 면적 무관; GHK ≠ Nernst-mean; step current 폐형 해. Move the rest to a "stretch" sub-list.

11. **§2 line 28**: insert one parenthetical: `(단위 확인: $1\,\mathrm{nA} / 1\,\mathrm{nF} = 10^{-9}\,\mathrm{C/s} / 10^{-9}\,\mathrm{F} = 1\,\mathrm{V/s} = 1\,\mathrm{mV/ms}$.)` Reason: EM-rusty student must see the cancellation once.

12. **§6 table row 1**: replace "댐 자체 (수위 = 전압)" with "댐 (수위 차이 = 전압, 저장된 물 = 전하)". Reason: tighten the mapping.

---

## SVG figures — detailed table

| Figure | Journal | InfoClarity | Annot | Color | Correct | Notes |
|---|---|---|---|---|---|---|
| `bilayer_capacitor.svg` | 8 | 8 | 7 | 9 | 9 | 13 head-groups per leaflet is too dense — drop to 7. Tail wavy lines are too short to read as fatty acids; consider 2× length. `d ≈ 3–4 nm` callout is well-placed. |
| `rc_charging_curve.svg` | 9 | 9 | 9 | 9 | **10** | Tangent line slope is geometrically *correct* (initial tangent passes through V_∞ at t=τ — this is the property students should learn). 63% callout is the right point. Best figure in the set. |
| `membrane_rc_circuit.svg` | 8 | 8 | 9 | 9 | 7 | Single EMF only — collapses ion chemistry. Should add E_K, E_Na, E_L parallel branches at least conceptually, or label the EMF as "V_rest = aggregate". `R_m` shown as IEC rectangle (good) not zigzag — consistent EU style. |
| `nernst_diffusion_balance.svg` | 8 | 7 | 6 | 9 | 6 | Two upward/downward arrows (sienna outward force, blue inward force) overlap in the middle of the membrane — visually muddled. Caption says "≈ −90 mV for K⁺" but the summary §7 says −83. Diffusional-force label `RT ln([K⁺]_i/[K⁺]_o)` is the correct *direction* (positive when [K]_i > [K]_o → drives outward) but should be clearly labeled as a *magnitude*; an unsuspecting reader will see this label and the equation `E_K = (RT/zF) ln([K]_o/[K]_i)` and wonder which sign convention is right. |
| `ghk_weighted_log.svg` | 8 | 9 | 8 | 9 | 7 | Bar-chart metaphor for permeabilities is excellent. **But** E_K = −90 mV in the K column and V_m ≈ −70 mV in the output — both inconsistent with summary text (E_K = −83, V_rest ≈ −80). Cl reversal `E_Cl ≈ −65` is plausible. P_Cl ≈ 0.45 is high; typical values are 0.45 (squid) or 0.10 (mammal); cite the source. |
| `ohmic_iv.svg` | 8 | 8 | 6 | 9 | 9 | "slope = g_X = 1/R_X" label sits *on top of* the I-V line, partially overlapping the line and the V−E_X driving-force annotation. Move slope label to upper-right quadrant. Good x-intercept marker. **Not embedded in summary** — wasted asset. |
| `hh_gating_variables.svg` | 9 | 9 | 9 | 9 | 9 | Half-activations shown correctly: m at −40, h at −55 (crossing at 0.5), n at −50. Sigmoid steepness for m looks too sharp — V_half-to-saturation in ~10 mV which matches Hodgkin-Huxley original (slope k ≈ 9). Good. |
| `voltage_clamp_protocol.svg` | 8 | 8 | 8 | 9 | 8 | Two-panel V_cmd / I_K layout is canonical. But: `n⁴ sigmoid (4 subunits)` annotation is at x=236 on the rising phase — slightly inside the capacitive transient region; move right by 30 px. `P/4 leak subtraction` annotation is good but is referenced to the *plateau*, not the rise where leak subtraction matters most. |
| `ion_channel_subunit.svg` | 9 | 9 | 9 | 9 | 9 | Excellent. K (4 α) vs Na (4 domains, IV with inactivation ball) — pedagogically perfect. `n⁴ ⟺ 4 subunits` and `m³h ⟺ 3 activation × 1 inactivation` annotations directly bridge structure to HH. Top-down view is the right choice. Best of the structural figures. |
| `cable_decay_spatial.svg` | 7 | 5 | 6 | 9 | 5 | **Critical defect**: x-axis labeled `x/λ` but two curves with different λ are superimposed. If x is normalized to *long* λ, the "short λ" curve compresses by 2× — but the figure shows the short-λ curve hitting 37% at x/λ = 0.5, which is only sensible if x is in physical units (mm), not in λ-units. **Fix**: relabel x-axis as "x (mm)" and label the long-λ tick at x = 1 mm, short-λ tick at x = 0.5 mm (or whatever). Currently the figure is *internally inconsistent*. Also: λ formula `λ = √(r_m/r_i)` — these are per-unit-length quantities, but no figure ever defines them; need an inset. |
| `ap_propagation_unmyelinated.svg` | 7 | 6 | 6 | 8 | 8 | t₁/t₂ time-slice labels at x=14 are far from their corresponding mini-plots; needs leader lines or boxed grouping. Local-circuit-current arrows above the axon (at y≈224) are very small relative to the figure — bump stroke-width to 1.8. Refractory annotation at x=138, y=216 collides with the t₂ trace. |
| `ap_propagation_myelinated.svg` | 8 | 7 | 8 | 9 | 8 | Saltatory jump arrows (sienna dashed) are visually nice. **But**: Node 1 *and* Node 2 both shown as actively firing at the same time — this is wrong; in saltatory conduction, only one node is at AP peak at a time, with the next about to depolarize. Show Node 1 = peak (filled), Node 2 = depolarizing (half-fill), Node 3 = subthreshold (pale), Node 4 = rest. Currently Node 1 = AP and Node 2 = AP both filled — a student will infer simultaneous firing. |
| `synapse_chemical.svg` | 8 | 8 | 8 | 9 | 8 | AMPA fast / NMDA slow + Mg block at rest — correct. Cleft drawn at 28 px tall labeled "~20 nm" but receptor heights are similar — scale is impressionistic, OK for schematic. `slow decay ~10–20 ms` annotation overlaps the falling-phase trace. EPSP rise of ~2 ms is tight but defensible for AMPA. |
| `rate_vs_temporal_codes.svg` | 8 | 9 | 8 | 9 | 9 | Best raster pair I have seen for this concept. ~9 spikes (rate) vs 3 precise spikes (temporal) is a clean contrast. Jitter brackets `< 1 ms` are on-target. `bits ∝ log₂(rate)` annotation is good shorthand but technically `bits ∝ log₂(1+SNR)` or rate-distortion; OK as gloss. |
| `hippocampal_phase_precession.svg` | 7 | 6 | 5 | 9 | 7 | **Defect**: lines 128 and 129 both say "early in θ cycle" with different phase ranges — duplicated typo. Top label should be "**late** in θ cycle (high phase °)". Precession slope label `~−360°/field` overshoots — typical mean precession is 180–300°/field; ~360° is high but seen in some cells. The top panel "position vs t" diagonal is good. Phase-precession scatter dots align reasonably with the regression line. |
| `action_potential_phases.svg` | 9 | 9 | 8 | 9 | 8 | Phase annotations (rising / peak / falling / AHP) are well-placed and color-coded by ion (sienna = Na, forest = K). Threshold dashed line at −50 is correct. **But**: gating-variable annotations at top (`m↑ h↓ n↑ n↓`) are at y=50 above the trace, disconnected from the time points; add fine vertical lines down to the curve. Refractory bracket at y=281 below E_K dashed line — hard to read; bump 4 px up. |

### Concrete figure fixes (for any score < 7)

**`cable_decay_spatial.svg` (correctness 5):**
- Either (a) keep `x/λ` x-axis and *remove* the second curve entirely (one universal curve in λ-units conveys the message), or
- (b) relabel x-axis to "x (mm)", annotate long-λ = 1 mm and short-λ = 0.5 mm ticks, and let the two curves diverge naturally. Option (b) is more pedagogical because it shows that λ is a *property of the cable*, not just a normalization unit.
- Inset definition box: "r_m = 막 저항 × 단위 길이 (Ω·cm), r_i = axoplasm 저항 / 단위 길이 (Ω/cm)".

**`hippocampal_phase_precession.svg` (annotations 5):**
- Line 128: change `early in θ cycle (late phase °)` → `late phase: ~270° (entry)`.
- Line 129: change `early in θ cycle (early phase °)` → `early phase: ~90° (exit)`.
- Move precession-slope label `~−360°/field` to read `−180° to −360°/field (cell-dependent)` — more honest.

**`ap_propagation_unmyelinated.svg` (info-clarity 6, annotations 6):**
- Move t₁/t₂ labels from x=14 (off-panel) to inside each mini-plot at x=70, y=top-of-plot.
- Add a leader bracket on the right edge linking each y-band to its time-slice.
- Bump local-circuit arrow stroke from 1.4 → 2.0.

**`ohmic_iv.svg` (annotations 6):**
- Move "slope = g_X = 1/R_X" label from y=240 to y=110 (above the line, in the upper-right quadrant where the line has positive slope). Currently overlaps the V−E_X driving-force callout.
- Embed in summary §3.5 (currently unused).

**`nernst_diffusion_balance.svg` (annotations 6, correctness 6):**
- Reconcile −90 mV caption with summary E_K = −83/−87 (after fix #2 above).
- Annotate the diffusional-force expression as `|F_diff| = RT ln([K]_i/[K]_o)` with explicit absolute-value bars to avoid sign confusion.
- Move the two parallel arrows (outward sienna, inward blue) from the same x-region (x=265 and x=290, near-overlapping) to opposite halves: outward on left, inward on right, both pointing *toward each other*, with a "balance" label between them.

**`membrane_rc_circuit.svg` (correctness 7):**
- Add label on the EMF: "V_rest (≡ GHK aggregate of E_K, E_Na, E_Cl)" — currently reads as a fundamental constant, which mistrains the mental model that L5 will need.

**`ap_propagation_myelinated.svg` (correctness 8):**
- Change Node 2 fill from `#b16413 opacity=0.9` to `opacity=0.5` — depolarizing not yet at peak.
- Or, better: redraw as 4 frozen frames (t1: only Node 1 active; t2: only Node 2 active; t3: Node 3 active) like the unmyelinated propagation figure. Currently it shows simultaneous firing, which is incorrect.

---

## Top 5 priorities for next iteration

1. **Reconcile numerical canon across summary + all 5 embedded L3 figures.** Pick one set: T = 310 K, [K]_o = 4 mM, [K]_i = 140 mM → E_K = −90 mV; [Na]_o = 145, [Na]_i = 12 → E_Na = +60 mV; V_rest = −65 mV (typical cortical, *not* equal to E_K). Update every occurrence in `seed_exemplar_L3_v2.py` *and* the SVG captions/labels. (Affects: bilayer_capacitor.svg caption, nernst_diffusion_balance.svg, ghk_weighted_log.svg, action_potential_phases.svg.) Single source of truth lives in a new `scripts/_constants_L3.py`.

2. **Fix R_m order-of-magnitude error in §3 line 38** and add explicit specific-vs-whole-cell distinction in a new mini-table inside §3. This is a 2-paragraph change but eliminates the most damaging numerical mistake in the document.

3. **Repair `cable_decay_spatial.svg` axis ambiguity** and **`ap_propagation_myelinated.svg` simultaneous-firing error**. These are the two figures most likely to mistrain a student on a tested concept.

4. **Embed the unused `ohmic_iv.svg`** as new §3.5 and **add §3.6 parallel-conductance circuit** as the bridge from §7 (Nernst per ion) back to §5 (single-EMF KCL). This is the single missing pedagogical link in the document.

5. **Tighten §6 dam analogy** (water-height-difference = voltage, not water-height = voltage) and **fix duplicated typo in `hippocampal_phase_precession.svg`** y-axis labels. Small but visible.

---

### Closing note for the reviewer-author dialogue

If the next iteration accepts fixes 1, 2, 8 (`ohmic_iv` embed), 9 (parallel-conductance), and the cable + myelin figure repairs, this summary clears the bar for "internal teaching handout, graduate level". To reach "publication-style worked example" (Neuron / eLife methods supplement), it additionally needs:
- explicit unit lines (kg·m·s·A SI, repeated for every novel quantity introduced)
- one numerical worked example per Tier-1 concept (currently only §2 has one)
- a "what does breaking each assumption do?" section (linearity, single compartment, instantaneous channel kinetics) — these are the hooks L4–L6 will pull on.

The §6 analogy table and §9 identifiability table are publication-quality insights and should be preserved verbatim through revisions. Don't lose them in refactoring.
