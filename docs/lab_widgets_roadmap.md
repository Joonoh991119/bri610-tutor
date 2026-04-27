# Lab Widgets Roadmap — L3-L8 Full Coverage

User mandate (2026-04-28): *"핵심적인 수식이나 개념들은 모두 실험실에서 시각적으로 깊이, 직관적 이해할 수 있도록 구현"* — every core equation/concept gets a visual, deeply-interactive widget.

This document maps every must-cover concept per lecture to a widget, sized into 3 tiers. Tier 1 = ship in this push, Tier 2/3 = follow-up batches.

## Tier 0 — In flight (Sonnet B, v0.7.9)

| # | Lecture | Widget | Concept |
|---|---|---|---|
| 1 | L3 | **Membrane RC** | $\tau_m\,dV/dt = -(V - V_\infty)$ — sliders for $\tau_m$, $V_\infty$, $V_0$; mark 63% point at $t = \tau_m$ |
| 2 | L4 | **Alpha function** | $g(t) = A\,t\,e^{-t/t_{peak}}$ — peak at $t_{peak}$, $g_{max} = A t_{peak}/e$ |
| 3 | L4 | **Fusion / Shunting** | $C_m dV/dt = -g_L(V-E_L) - g_{syn}(t)(V-E_{syn}) + I_{inj}$; twin Y-axis with $\tau_m^{eff}$ dipping during synaptic activation |
| 4 | L5 | **Hodgkin–Huxley simplified** | Full 4-ODE; AP train under DC step; live $m, h, n$ readout |

## Tier 1 — Next push (must-have for lab completeness)

| # | Lecture | Widget | Concept |
|---|---|---|---|
| 5 | L3 | **Nernst equilibrium** | Bidirectional arrow animation: diffusion (concentration gradient ↔ outward flux) vs electric drift (electrostatic force ↔ inward flux); slider for $[X]_o/[X]_i$ ratio + valence $z$; live $E_X$ readout |
| 6 | L3 | **GHK weighted log calculator** | 3-bar chart for $p_K, p_{Na}, p_{Cl}$ permeability sliders; plot resulting $V_m$ on left axis; show transition from rest ($p_K \gg$) to AP peak ($p_{Na} \gg$) by dragging permeabilities |
| 7 | L4 | **Driving force visualizer** | Number line of $V$ vs $E_X$; arrow direction + magnitude flip at $E_X$; toggle ion species (K, Na, Cl, AMPA) to see how same $V$ gives different forces |
| 8 | L5 | **HH gating curves** | Plot $m_\infty(V), h_\infty(V), n_\infty(V)$ + their $\tau$ functions; vertical V cursor swept by slider; live $P_{open}^{Na} = m^3 h$ + $P_{open}^K = n^4$ readout |
| 9 | L6 | **Cable spatial decay** | $V(x) = V_0 e^{-x/\lambda}$ with $\lambda = \sqrt{d R_m / 4 R_i}$ derived from sliders; mark $\lambda$, $2\lambda$, $3\lambda$ at 37%, 14%, 5% |
| 10 | L7 | **LIF f-I curve** | Closed-form $r(I) = 1 / [\tau_{ref} + \tau_m \ln(...)]$; plot rate vs current; mark rheobase + saturation $1/\tau_{ref}$ |
| 11 | L8 | **Phase precession** | Animated rat traversing place field; spike raster on theta cycles; observed phase decreases as rat moves through field; toggle "rate vs phase" decoder |

## Tier 2 — Extended (depth + comparative insight)

| # | Lecture | Widget | Concept |
|---|---|---|---|
| 12 | L4 | **NMDA Mg block** | Voltage-dependent $\text{Mg}^{2+}$ block curve; visualize "AND-gate" by flipping AMPA current ON/OFF and watching NMDA threshold |
| 13 | L5 | **Voltage clamp protocol** | Step protocol; toggle TTX (Na block) / TEA (K block); separated $g_K(t), g_{Na}(t)$ traces |
| 14 | L5 | **AP phase plane** | $V$ vs $n$ phase plane; trajectory traces limit cycle; bifurcation marker as $I_{ext}$ slider crosses rheobase |
| 15 | L6 | **Saltatory vs continuous propagation** | Side-by-side raster: unmyelinated axon (continuous AP regeneration along x) vs myelinated (jumps between nodes of Ranvier); velocity readout |
| 16 | L7 | **Izhikevich (a, b, c, d) explorer** | Sliders for 4 parameters; live spike pattern (RS, IB, FS, LTS, ...) with category label |
| 17 | L7 | **Spike-frequency adaptation** | LIF vs aLIF side-by-side; same DC step shows constant rate (LIF) vs decaying rate (aLIF + slow $g_{sra}$) |
| 18 | L8 | **PSTH builder** | Multi-trial raster → bin → smooth pipeline; slider for bin width (1-100 ms); live PSTH curve |
| 19 | L8 | **Mainen-Sejnowski reliability** | Two panels: DC stim (jittery spike timing across trials) vs frozen noise (sub-ms repeatable timing); reliability index live |

## Tier 3 — Optional (advanced / research-grade)

| # | Lecture | Widget | Concept |
|---|---|---|---|
| 20 | L6 | **Cable spatiotemporal heatmap** | $V(x, t)$ 2D heatmap with current injection at $x=0$ |
| 21 | L7 | **Multi-compartment HH** | Soma + dendrite branches; AP propagation visualization |
| 22 | L8 | **Multiplexed code analyzer** | Single spike train decoded as rate / temporal / phase / synchrony channels; information-theoretic decomposition |

## Implementation conventions

- **No new heavy deps**. All plots inline SVG. Optional one tiny chart lib if absolutely needed (justify in PR).
- **Tol BRIGHT palette only**: `#4477AA` `#66CCEE` `#EE6677` `#228833` `#CCBB44` + neutrals from CSS vars.
- **KaTeX for all equations** via `<Markdown>` component (already in `frontend/src/components/Markdown.jsx`).
- **Korean+English bilingual labels**: math notation in English, descriptions in Korean.
- **Direct manipulation**: every widget responds to slider drag in real-time; no "Submit" buttons.
- **Pedagogical anchors**: each widget has a 1-line "직관 한 줄" that updates with parameter changes for non-obvious limits (e.g., "shunting only — V doesn't move but τ_eff dips").
- **localStorage**: persist active tab + last slider values per widget so users return to where they left off.
- **Numerical methods**: forward Euler with dt = 0.01-0.1 ms suffices; precompute traces in `useMemo` keyed on slider state.

## Pedagogical priority ordering

For users who finish reading L3 → L8 sequentially, the lab should let them *test the concept they just read* without leaving the page. Order matters:

1. **Read L3 §1 (capacitance)** → run *Membrane RC* widget
2. **Read L3 §3 (Nernst)** → run *Nernst equilibrium* widget
3. **Read L3 §4 (GHK)** → run *GHK calculator* widget
4. **Read L4 §1 (driving force)** → run *Driving force visualizer*
5. **Read L4 §10 (alpha)** → run *Alpha function*
6. **Read L4 §10 (shunting)** → run *Fusion / Shunting*
7. **Read L4 §11 (NMDA)** → run *NMDA Mg block*
8. **Read L5 §1 (HH)** → run *HH simplified*
9. **Read L5 §1 (gating)** → run *HH gating curves*
10. **Read L5 §3 (voltage clamp)** → run *Voltage clamp protocol*
11. **Read L5 §11 (phase plane)** → run *AP phase plane*
12. **Read L6 §3 (cable)** → run *Cable spatial decay*
13. **Read L6 §7 (saltatory)** → run *Saltatory propagation*
14. **Read L7 §3 (LIF)** → run *LIF f-I curve*
15. **Read L7 §6 (Izhikevich)** → run *Izhikevich explorer*
16. **Read L7 §7 (SFA)** → run *SFA comparison*
17. **Read L8 §B (phase code)** → run *Phase precession*
18. **Read L8 §2 (PSTH)** → run *PSTH builder*
19. **Read L8 §11 (M-S paradox)** → run *Reliability comparison*

This pedagogical ordering should drive the **side-tab** organization in `InteractivePanel.jsx` — tabs grouped by lecture, then by section.

## Cross-summary hyperlinks

Each widget should link back to the relevant lecture summary (`#summary?lecture=L3`) for theory context. Conversely, each lecture summary's relevant section should link forward to the widget (`#interactive?widget=membrane-rc`). This requires:
- Frontend route handler to read URL hash + select tab/widget.
- Markdown.jsx already handles `#summary?lecture=L#` — extend to `#interactive?widget=X`.
