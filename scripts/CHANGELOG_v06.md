# v0.6 — Rendering & Content Quality

## v0.6.4 (figure-redesign + KaTeX skip-tags)
- Markdown.jsx: drop em/strong from SKIP_TAGS so KaTeX runs inside markdown emphasis
- Figure redesign: 5 hand-crafted SVGs (driving_force, f_i_curve_rheobase, conductance_weighted_avg, mainen_sejnowski_trial_reliability, psth_construction)
- L3 그림 5 (ghk_weighted_log) Na bar: #4477aa → #ee6677 to match caption "빨강"

## v0.6.5 (DB content cleanup via Chrome MCP audit)
- 120 parenthetical math expressions wrapped, 78 unwrapped on prose-mix refinement
- 35 inner $-pairs stripped from $$..$$ display blocks
- 14 lost math captures restored from $($1)$ literal-backref bug
- 62 <strong>/</strong> tags nuked after regex collateral damage

## v0.6.6 (table CSS)
- overflow-wrap anywhere → break-word in table cells (was breaking digits mid-number)
- table { display:block; max-width:100%; overflow-x:auto } for narrow viewports

## v0.6.7 (final cleanup)
- Last 2 $($1)$ corruptions in L3 V(t) formulas restored via context heuristic
- L8 [Slide L# phase-code] placeholder → [Slide L8 p.66–69]
- L7 (V_reset) wrapped in $V_\text{reset}$
