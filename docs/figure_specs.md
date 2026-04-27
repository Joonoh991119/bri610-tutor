# BRI610 Figure Specifications — Element-Level Meaning Reference

For each figure: **(P)urpose** = the single message the figure must teach.
**(E)lements** = each visible component and what it represents.
**(C)onstraints** = scientific, pedagogical, and aesthetic rules.

The matplotlib output (`scripts/render_figures_mpl.py`) provides the data layout;
this spec hands the *meaning* to the renewal pass. Both are inputs to the
final design-renewal agent.

---

## 1. `bilayer_capacitor.svg` (slide L2 p.21 / L3 p.22)
- **P**: Lipid bilayer behaves as a parallel-plate capacitor. $C_m \approx \varepsilon \varepsilon_0 / d$.
- **E**:
  - Two horizontal plates = inner / outer leaflets of phospholipids.
  - Hatching = polar headgroup region.
  - Gap between plates = hydrophobic acyl-chain core (dielectric medium).
  - Capacitor symbol on side = circuit equivalent.
  - Equation = relationship between membrane thickness $d$ and specific capacitance.
- **C**: Symbolic, not to scale. Single ochre callout marks the dielectric gap. No numerics in body.

## 2. `membrane_rc_circuit.svg` (slide L2 p.21 / L3 p.22–24)
- **P**: Single-compartment passive membrane = R, C, EMF in parallel; KCL gives $C_m\,dV/dt = I_{inj} - (V-E_L)/R_m$.
- **E**:
  - Top rail = extracellular space; bottom rail = cytoplasm.
  - Capacitor branch ($C_m$) = membrane lipid bilayer storing charge.
  - Resistor branch ($R_m$) + battery ($E_L$) = passive ion-channel leak with reversal potential.
  - Current source ($I_{inj}$) = experimentally injected current. **Single ochre callout**.
  - Voltmeter ($V_m$) = transmembrane potential measurement.
  - Equation panel = KCL (Kirchhoff current law).
- **C**: Schematic, vertical orientation. No grid. KCL panel below the circuit, not on it.

## 3. `rc_charging_curve.svg` (slide L3 p.24)
- **P**: Charging dynamics: $V(t) = V_\infty(1 - e^{-t/\tau})$; reaches 63% of $V_\infty$ at $t=\tau$.
- **E**:
  - x-axis: time in units of $\tau$.
  - y-axis: $V/V_\infty$, range [0, 1.05].
  - Curve = exponential approach (accent blue).
  - Tangent at origin = initial slope reaches $V_\infty$ at $t=\tau$ (single ochre dashed line).
  - Marker dot at $(t=\tau, V/V_\infty = 0.63)$ with annotation `1 − 1/e ≈ 63%`.
- **C**: Pure plot, no diagram. Annotation positioned outside the curve.

## 4. `ohmic_iv.svg` (slide L3 p.18)
- **P**: Open ion channel obeys Ohm's law: $I = g(V − E_X)$; reverses at $V = E_X$.
- **E**:
  - Linear I-V line (accent).
  - Slope = single-channel conductance $g_X$ (label inline along the line).
  - x-intercept = reversal potential $E_X$ (ochre tick + label).
  - Quadrants labeled: outward current ($I>0$) above x-axis, inward ($I<0$) below.
- **C**: Single straight line. No grid lines except subtle x=0 and y=0.

## 5. `action_potential_phases.svg` (slide L5 p.6, 14)
- **P**: AP voltage trace bounded above by $E_{Na}$ and below by $E_K$; four phases: rest → rising (Na influx) → peak → repolarisation (K efflux) → AHP → return.
- **E**:
  - V_m(t) curve (accent).
  - $E_{Na} = +58$ mV horizontal dashed line (top).
  - $E_K = −83$ mV horizontal dashed line (bottom).
  - Phase labels above the curve: `rising` `peak` `falling` `AHP`.
  - Threshold `−55 mV` dashed (lighter).
  - Resting `V_rest = −65 mV` dashed.
- **C**: Single ochre = the threshold crossing dot at the rising phase. All phase labels read horizontally.

## 6. `hh_gating_variables.svg` (slide L5 p.24)
- **P**: Three steady-state gating variables: $m_\infty$ (Na activation), $h_\infty$ (Na inactivation), $n_\infty$ (K activation) plotted vs. $V$. Half-activation between −40 and −55 mV.
- **E**:
  - Three sigmoids (accent / teal / ochre).
  - x-axis: V in mV from −100 to +50.
  - y-axis: probability [0, 1].
  - Legend: top-right inside plot frame, no overlap with curves at high V.
  - $m_\infty$ rises with V; $h_\infty$ falls with V; $n_\infty$ rises with V (gentler than $m_\infty$).
- **C**: Three lines must be visually distinguishable in grayscale (use linestyle as redundant encoding). Half-activation marker dots optional.

## 7. `voltage_clamp_protocol.svg` (slide L5 p.20–22)
- **P**: Voltage clamp imposes $V_m$, measures the current required → reveals time-dependent ionic conductances.
- **E**:
  - Top panel: $V_{cmd}(t)$ step from holding to test (e.g. −80 → +20 mV).
  - Bottom panel: $I(t)$ response with **inward Na transient** (early dip) then **outward K plateau**.
  - Vertical ochre line at step onset, both panels.
  - Labels: `holding`, `step`, `Na peak`, `K plateau`.
- **C**: Two panels, vertically stacked, shared time axis. Subtle horizontal zero line on current panel.

## 8. `ap_propagation_unmyelinated.svg` (slide L6 p.5–7)
- **P**: Unmyelinated AP spreads continuously; refractory zone behind the active patch enforces unidirectional propagation.
- **E**:
  - Long horizontal axon cylinder.
  - 5 sequential AP "humps" along the axon at successive moments.
  - Brick-shaded segment behind the active patch = refractory zone.
  - Single ochre arrow forward = direction of propagation.
- **C**: Time snapshot, NOT all firing simultaneously. Active patch in accent; refractory in brick (faded).

## 9. `ap_propagation_myelinated.svg` (slide L6 p.13–15)
- **P**: Saltatory conduction: AP "jumps" between nodes of Ranvier; large velocity gain.
- **E**:
  - Axon with 4 myelin sheath segments separating 5 nodes.
  - Active node = solid accent dot.
  - Adjacent node approaching threshold = lighter dot.
  - Single ochre jump arrow between active and next.
  - Other potential jumps faded.
  - Velocity comparison label: `up to 100 m/s` (cite slide).
- **C**: Single moment in time. Ochre callout limited to the active jump only.

## 10. `cable_decay_spatial.svg` (slide L6 p.11)
- **P**: Steady-state cable: $V(x) = V_0 e^{-x/\lambda}$; signal drops to 37% at one length constant, 14% at two.
- **E**:
  - Plot of $V/V_0$ vs $x/\lambda$.
  - x-axis 0 to 5 (in λ units), y-axis 0 to 1.
  - Single curve (accent).
  - Marker dots at $(1, 0.37)$ and $(2, 0.14)$ with ochre annotations `1/e ≈ 37%` and `1/e² ≈ 14%`.
  - Inset table or callout: λ ∝ √d → diameter dependence.
- **C**: Universal curve on $x/\lambda$ axis (no specific λ value baked in).

## 11. `nernst_diffusion_balance.svg` (slide L3 p.27–29)
- **P**: At Nernst potential, diffusion force (concentration gradient) and electrical force (membrane potential) balance for a permeant ion.
- **E**:
  - Two compartments: extracellular (low [K⁺]) and intracellular (high [K⁺]).
  - Selective channel symbol in the membrane.
  - Diffusion arrow: outward (K⁺ flows down concentration gradient).
  - Electrical force arrow: inward (negative interior pulls K⁺ back).
  - Two arrows opposing → equilibrium at $E_K = (RT/zF) \ln([K]_o/[K]_i)$.
- **C**: Symmetric layout. Single ochre = the channel symbol.

## 12. `ghk_weighted_log.svg` (slide L3 p.32)
- **P**: Resting $V_m$ is the **permeability-weighted log** of all permeant ions: $V_m = (RT/F) \ln \frac{P_K[K]_o + P_{Na}[Na]_o + P_{Cl}[Cl]_i}{P_K[K]_i + P_{Na}[Na]_i + P_{Cl}[Cl]_o}$. $P_K$ dominates at rest, so $V_m \approx E_K$.
- **E**:
  - 3 horizontal bars showing relative permeability ratios at rest: $P_K$ (long), $P_{Na}$ (short), $P_{Cl}$ (medium).
  - Each bar labeled with the ion species.
  - Equation inset above the bars.
  - Single ochre highlight on $P_K$ bar (the dominant term).
- **C**: Bar chart, not pie chart. Bars same color (accent) except ochre highlight.

## 13. `ion_channel_subunit.svg` (slide L4 p.10–18)
- **P**: K⁺ channel = 4 identical α-subunits → $n^4$ kinetics. Na⁺ channel = 1 α with 4 pseudo-domains + ball-and-chain (h gate) → $m^3 h$ kinetics.
- **E**:
  - Left panel: Kv channel — 4 subunits arranged radially, each labeled `α`. $n^4$ formula caption.
  - Right panel: Nav channel — 1 long α with 4 domains, plus inactivation ball tethered to inner mouth. $m^3 h$ formula caption.
- **C**: Top-down view. Schematic, not photorealistic. No saturated colors — solid INK outlines on PAPER fill.

## 14. `synapse_chemical.svg` (slide L7 p.10–14)
- **P**: Action potential → Ca²⁺ entry → vesicle fusion → NT release → postsynaptic receptor activation → EPSP.
- **E**:
  - Presynaptic terminal with reserve vesicles (3–4 small circles).
  - Active-zone vesicle fusing at the membrane (single ochre callout).
  - Synaptic cleft with NT molecules (small dots).
  - Postsynaptic membrane with AMPA + NMDA receptors (rectangles).
  - Inward Na⁺ flux through AMPA → EPSP trace on the right (small inset).
  - EPSP trace: rapid rise from $V_{rest}$, slow decay back.
- **C**: Two-panel: left = anatomy, right = trace. Single ochre = fusion event + Na⁺ flux arrow only.

## 15. `rate_vs_temporal_codes.svg` (slide L8 p.18–22)
- **P**: Same total spike count can encode information either by rate (mean) or by precise temporal pattern (timing).
- **E**:
  - Top raster: regular spikes at constant rate $\bar{r}$ — "rate code".
  - Bottom raster: same number of spikes but irregular precise inter-spike intervals — "temporal code".
  - Both rasters show the same $\bar{r} = 5$ Hz mean.
  - Annotation arrows: `count = signal` (top) vs `precise timing = signal` (bottom).
- **C**: Two horizontally-aligned rasters. Spike ticks in INK. Annotations in ochre.

## 16. `hippocampal_phase_precession.svg` (slide L8 p.36–39)
- **P**: As animal traverses a place field, spike phase relative to theta rhythm advances from late θ-phase (entry) → 0° (exit). Encodes position within the field.
- **E**:
  - Top: scatter of spike events plotted as (position, theta phase) — diagonal trajectory from late phase → early phase.
  - Bottom: theta-cycle reference oscillation (continuous wave).
  - Labels: "field entry (late θ)", "field exit (early θ)".
  - Direction arrow showing precession.
- **C**: Two panels stacked, shared x-axis (position). Single ochre = direction-of-precession arrow.

---

## Universal constraints (apply to all figures)

| Constraint | Rule |
|---|---|
| Palette | INK `#1a1a20`, INK-DIM `#4f4f57`, INK-FAINT `#7a7a82`, PAPER `#fbfaf6`, RULE `#ccc7b8`, RULE-SOFT `#ddd9cd`, ACCENT `#2c4f78`, TEAL `#3a6a5a`, OCHRE `#a96a35`, BRICK `#7a3645`, MOSS `#4a6f5b`. **No others.** |
| Ochre callouts | Maximum 1 per figure |
| Text overlap | Programmatically verified zero overlap |
| Typography | Sans-serif for UI labels; serif italic for variables ($V_m$, $\tau$, $\lambda$ ...) |
| Minus sign | U+2212 (−) not hyphen |
| Slide citation | Footer line `Slide L# p.N` in INK-FAINT 10px |
| viewBox | 600 × 360 (or 600 × 320 compact) |
| Background | Always paper fill `#fbfaf6` |
| Grid | None unless plotting genuinely needs it; remove top + right spines |
| Animation | None (static SVG) |
| Aesthetic | eLife / Neuron / iScience / Nature Neuroscience print tone — desaturated, single accent, generous margins |
