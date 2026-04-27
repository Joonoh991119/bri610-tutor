#!/usr/bin/env python3
"""
seed_bank_phd.py — PhD-rigor bank seed for BRI610 v0.5.

Replaces the toy 12-item demo seed (seed_bank_demo.py). Each item satisfies the
mandate in `memory/feedback_phd_rigor.md`:
  - Recall  → name formula + explicit regime + identifiability hint
  - Concept → contrast ≥2 viewpoints (thermodynamic vs kinetic etc.)
  - Application → procedure-level: dataset → analysis with identifiability
  - Proof  → non-trivial intermediate steps + sanity check
  - Cite primary literature alongside lecture/textbook
  - Rationale names the common student misconception
  - ≥30% items cross-topic-link

Coverage: 18 items
  HH         × 4 (recall, concept, application, proof)
  Cable      × 4
  Nernst/GHK × 4
  Model types (L7)   × 3
  Neural codes (L8)  × 3

Usage:
  python scripts/seed_bank_phd.py [--review]   # --review = run Multi-Lens before insert
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "backend"))

from db_pool import acquire, release  # noqa: E402


# ──────────────────────────────────────────────────────────────────
# 18 PhD-level items.
#
# Each `prompt_md` opens with a **setup** block (paper / regime), followed by
# numbered sub-questions. `answer_md` provides derivation steps; `rationale_md`
# names the misconception and the cross-link.
# ──────────────────────────────────────────────────────────────────

SEEDS: list[dict] = [
    # ─── HH (Hodgkin–Huxley) ─────────────────────────────────────────────────
    {
        "topic": "HH", "card_type": "recall", "difficulty": 3, "bloom": "Understand",
        "prompt_md": (
            "**Setup.** Hodgkin & Huxley (1952) derived $g_K(V,t) = \\bar g_K\\,n^4(V,t)$ "
            "from squid axon voltage-clamp data.\n\n"
            "(a) Write the full ODE system for $V_m,\\,n,\\,m,\\,h$ (4 equations) including the "
            "current balance with $C_m$ and the leak term.\n"
            "(b) State **two implicit assumptions** of the model that fail in cortical pyramidal "
            "neurons (hint: think about ion species, cooperativity, and Markov structure)."
        ),
        "answer_md": (
            "(a) HH 4-ODE system:\n"
            "$$C_m\\frac{dV_m}{dt} = -\\bar g_K n^4(V_m-E_K) - \\bar g_{Na} m^3 h (V_m-E_{Na}) - \\bar g_L (V_m-E_L) + I_{inj}$$\n"
            "$$\\frac{dx}{dt} = \\alpha_x(V_m)(1-x) - \\beta_x(V_m)\\,x,\\quad x \\in \\{n,m,h\\}$$\n\n"
            "(b) **Failures in cortical neurons**: (i) only **3 ion species** (Na, K, leak) — cortex has "
            "$\\geq$ 7 functionally distinct K-channel subtypes (M, A, BK, SK, K_v1.x …) and Ca channels are absent; "
            "(ii) **gating-variable independence** — the binomial decomposition $n^4$ assumes 4 identical "
            "subunits transitioning **independently**, which microscopic patch data show is violated by "
            "subunit cooperativity (Mainen & Sejnowski 1995; Schoppa & Sigworth 1998)."
        ),
        "rationale_md": (
            "**Common error**: students recite the 4 equations but skip the leak term, or write $m^4$ instead of $m^3 h$. "
            "The deeper mistake: assuming HH is a *general* spike model rather than a fit to one squid axon at 6.3 °C. "
            "**Cross-link**: the failure modes in (b) motivate Markov-state models (Patlak 1991; Vandenberg & Bezanilla 1991) "
            "and modern conductance-based models (Traub et al. 1991, Pinsky & Rinzel 1994)."
        ),
        "source_citation": {"kind": "textbook", "book": "Dayan_Abbott", "ch": 5, "page": 173,
                             "primary": "Hodgkin & Huxley 1952 J Physiol 117:500"},
        "priority_score": 0.97, "info_density": 0.95, "mastery_target": "HH_assumptions",
    },
    {
        "topic": "HH", "card_type": "concept", "difficulty": 4, "bloom": "Analyze",
        "prompt_md": (
            "**Setup.** HH chose $n^4$ for K and $m^3 h$ for Na. The exponents were not arbitrary — "
            "they were *fit parameters* to match the sigmoidal kinetics in voltage-clamp.\n\n"
            "(a) Why does raising the exponent (e.g., $n \\rightarrow n^4$) produce a **delayed** sigmoidal "
            "rise rather than a simple exponential? Explain in terms of the Markov chain underlying the "
            "binomial assumption.\n"
            "(b) Modern crystal structure shows K_v channels are **homotetrameric** (4 identical subunits), "
            "but Na channels are **single polypeptide with 4 non-identical domains**. Reconcile this with "
            "$m^3 h$ — should it be $m_1 m_2 m_3 h$ instead? Argue for or against."
        ),
        "answer_md": (
            "(a) For a single Markov gate transitioning $C \\rightleftharpoons O$ with rates $\\alpha,\\beta$, "
            "$n(t) = n_\\infty + (n_0 - n_\\infty)\\,e^{-t/\\tau_n}$ is purely exponential. Raising to $n^4$ "
            "models 4 **independent identical** gates that must **all** be open: by binomial independence, "
            "$P[\\text{all open}](t) = n(t)^4$. Near $t=0$, $n(t) \\approx n_\\infty(1-e^{-t/\\tau})$ so "
            "$n(t)^4 \\sim t^4 / \\tau^4$ — quartic onset, no instantaneous rise. The **delayed sigmoid** "
            "shape comes from the polynomial leading edge.\n\n"
            "(b) The structural mismatch is real but the **kinetic** signature is what matters for the "
            "voltage-clamp fit. The 4 Na domains move on **similar but not identical** time scales; HH "
            "compressed this into one $m$ variable because the *macroscopic* current cannot distinguish "
            "$m_1 m_2 m_3$ from $m^3$ unless you have **patch-clamp single-channel data**. So $m^3 h$ is "
            "an *effective* approximation valid at the macroscopic level — a known limitation of HH-style "
            "fits is exactly this loss of subunit identity."
        ),
        "rationale_md": (
            "**Common error**: thinking the exponent IS the subunit count. It's not — it's an **empirical** "
            "fit that *happens* to align with subunit count for K. **Cross-link**: this is why Markov-state "
            "channel models (Vandenberg & Bezanilla 1991; Kuo & Bean 1994) are preferred when single-channel "
            "data is available — they let you fit the actual transitions, not a binomial collapse."
        ),
        "source_citation": {"kind": "textbook", "book": "Dayan_Abbott", "ch": 5, "page": 175,
                             "primary": "Hodgkin & Huxley 1952; Kuo & Bean 1994 Neuron 12:819"},
        "priority_score": 0.96, "info_density": 0.93, "mastery_target": "HH_gating_kinetics",
    },
    {
        "topic": "HH", "card_type": "application", "difficulty": 5, "bloom": "Apply",
        "prompt_md": (
            "**Setup.** You have voltage-clamp recordings of $I_K(t,V)$ from a CA1 pyramidal neuron, "
            "stepped from $V_{hold} = -90$ mV to $V_{step} \\in \\{-40, -20, 0, +20, +40\\}$ mV for "
            "100 ms each. Series resistance is $\\sim 8\\,\\mathrm{M}\\Omega$ (uncompensated).\n\n"
            "(a) Write the **full procedure** to extract $\\alpha_n(V), \\beta_n(V), n_\\infty(V), \\tau_n(V)$ "
            "including the steps for: leak subtraction, capacitive transient handling, series-resistance "
            "correction, and the curve-fit form (state the parametrization you'd use for $n_\\infty(V)$ and "
            "$\\tau_n(V)$ before fitting).\n"
            "(b) Identify **two parameter-identifiability problems** that would invalidate naïve curve fits "
            "to $I_K(t)$ at these step potentials, and state the experimental modifications that resolve them."
        ),
        "answer_md": (
            "(a) Procedure (in order):\n"
            "  1. **Leak subtraction**: P/4 protocol — apply 4 sub-threshold negative pulses of $V_{step}/4$, "
            "      sum, scale by $-4$, subtract from each test pulse.\n"
            "  2. **Capacitive transient**: gate first $\\sim$0.5 ms post-step (or fit $C_m \\frac{dV}{dt}$ "
            "      explicitly with cell capacitance estimate).\n"
            "  3. **Series-R correction**: software compensation $V_{actual} = V_{cmd} - I R_s$. With "
            "      $R_s = 8\\,\\mathrm{M}\\Omega$ and $I_K \\approx 5$ nA, the error is ~40 mV — non-negligible. "
            "      Either compensate $\\geq 70\\%$ at the amplifier or re-estimate $V$ post-hoc.\n"
            "  4. **Fit form**: $I_K(t,V) = \\bar g_K n_\\infty^4(V) [1 - e^{-t/\\tau_n(V)}]^4 (V - E_K)$. "
            "      Per-V step, fit $(n_\\infty,\\,\\tau_n)$ jointly via Levenberg–Marquardt.\n"
            "  5. **Extract $\\alpha_n, \\beta_n$**: $\\alpha_n = n_\\infty / \\tau_n$, $\\beta_n = (1-n_\\infty)/\\tau_n$. "
            "      Standard parametrization: Boltzmann for $n_\\infty(V)$, Gaussian-of-V for $\\tau_n(V)$.\n\n"
            "(b) Identifiability problems:\n"
            "  - **i. Driving force vs gate**: at $V \\to E_K$, current $\\to 0$ regardless of gate kinetics. "
            "    Fix: do NOT include steps near $E_K$ (~$-90$ mV) when extracting kinetics; use $V_{step}$ "
            "    well above $E_K$.\n"
            "  - **ii. Multiple K-current contamination**: cortical CA1 has K_A (transient) + K_DR + M-current. "
            "    A single $n^4$ fit will produce biased $\\tau_n$ estimates because three time scales superpose. "
            "    Fix: (a) pharmacologically isolate (4-AP for K_A, TEA for K_DR, XE-991 for M); (b) holding "
            "    potential variation to inactivate K_A; (c) explicit multi-component fit with priors."
        ),
        "rationale_md": (
            "**Common error**: skipping series-R correction at high currents (>1 nA) — the $V_{step}$ the cell "
            "actually sees is meaningfully different from the command voltage, biasing $V_{1/2}$ of $n_\\infty(V)$ "
            "by 5–15 mV. **Common error 2**: assuming a single $n^4$ fits CA1 K-currents — it doesn't, and "
            "the residuals are systematic (transient component). **Cross-link**: same identifiability concerns "
            "appear in cable parameter estimation (R_m vs R_i degeneracy under voltage-step protocols)."
        ),
        "source_citation": {"kind": "slide", "lecture": "L5", "page": 26,
                             "primary": "Sigworth 1995 Methods Enzymol 207:746; Mickus, Jung & Spruston 1999 Biophys J"},
        "priority_score": 0.95, "info_density": 0.96, "mastery_target": "HH_voltage_clamp_extraction",
    },
    {
        "topic": "HH", "card_type": "proof", "difficulty": 5, "bloom": "Evaluate",
        "prompt_md": (
            "**Setup.** The HH form $g_K = \\bar g_K\\,n^4$ assumes 4 **independent** gates each with "
            "the same kinetics. Patch-clamp single-channel data on Shaker K+ shows $\\sim$5-state Markov "
            "kinetics with **cooperativity** between subunits.\n\n"
            "(a) Starting from a 5-state Markov chain with states $\\{S_0, S_1, S_2, S_3, S_4 = O\\}$ where "
            "the rate from $S_k$ to $S_{k+1}$ is $(4-k)\\alpha$ and from $S_{k+1}$ to $S_k$ is $(k+1)\\beta$ "
            "(independent-subunit assumption), prove that the macroscopic open probability reduces to $n^4$ "
            "in the steady state, where $n$ is the per-subunit open probability.\n"
            "(b) Show explicitly **where** in your derivation the independence assumption is invoked. "
            "Then, replace the rate $S_3 \\to S_4$ with $\\alpha (1+c)$ for cooperativity factor $c > 0$ "
            "and identify the leading-order correction to $\\langle P_O\\rangle$."
        ),
        "answer_md": (
            "(a) Let $p_k(t) = P[\\text{state } S_k]$. Detailed balance at steady state requires "
            "$p_k\\,(4-k)\\alpha = p_{k+1}\\,(k+1)\\beta$, so $p_{k+1}/p_k = (4-k)\\alpha / [(k+1)\\beta]$.\n"
            "Define $r = \\alpha/\\beta$. Iterating: $p_k = \\binom{4}{k} r^k\\,p_0$, with normalization "
            "$\\sum_k p_k = 1$.\n"
            "$$p_k = \\binom{4}{k}\\,r^k / (1+r)^4 = \\binom{4}{k}\\,n^k(1-n)^{4-k},\\quad n = r/(1+r) = \\alpha/(\\alpha+\\beta).$$\n"
            "$P_O = p_4 = n^4$. ✓\n\n"
            "(b) The independence assumption enters at the rate definitions $(4-k)\\alpha,\\,(k+1)\\beta$ — "
            "each of the 4 subunits contributes a *factor* $\\alpha$ or $\\beta$ independently of the others.\n"
            "With cooperativity $S_3 \\to S_4$ at rate $\\alpha(1+c)$:\n"
            "Steady-state: $p_4 / p_3 = \\alpha(1+c) / (4\\beta)$ (modified) instead of $\\alpha/(4\\beta)$.\n"
            "Re-normalize: $p_4 \\approx n^4 (1 + c\\,(1-n))$ to first order in $c$. So **cooperativity boosts $P_O$** "
            "by a factor $(1 + c\\,(1-n))$ — at low $n$ (rest), the boost is large; at high $n$ (open), boost vanishes. "
            "Macroscopic curve $g_K(V)$ becomes steeper than $n^4(V)$ at sub-threshold V.\n\n"
            "**Sanity check**: at $c \\to 0$, recover $n^4$ ✓. At $c \\gg 1$ all gating concentrates at $S_4$, "
            "predicting near-step activation — consistent with hypothesized 'concerted' Monod-Wyman-Changeux models."
        ),
        "rationale_md": (
            "**Common error**: writing $P_O = n^4$ without ever proving it from the underlying Markov chain — "
            "it looks like an axiom when it's a *consequence* of binomial independence. **Common error 2**: "
            "forgetting to renormalize $p_0,\\dots,p_4$ after introducing cooperativity. **Cross-link**: this is "
            "the same calculation pattern as **MWC** allosteric models in enzyme kinetics — the cooperativity "
            "parameter is the same idea as the Hill coefficient. Schoppa & Sigworth 1998 used this framework "
            "to fit *Shaker* with explicit cooperativity."
        ),
        "source_citation": {"kind": "textbook", "book": "Dayan_Abbott", "ch": 5, "page": 178,
                             "primary": "Hodgkin & Huxley 1952; Schoppa & Sigworth 1998 J Gen Physiol 111:271"},
        "priority_score": 0.98, "info_density": 0.98, "mastery_target": "HH_markov_reduction",
    },

    # ─── Cable theory ────────────────────────────────────────────────────────
    {
        "topic": "cable", "card_type": "recall", "difficulty": 3, "bloom": "Understand",
        "prompt_md": (
            "**Setup.** The 1-D cable equation describes voltage propagation in a passive cylindrical "
            "dendrite (Rall 1962).\n\n"
            "(a) Write the cable PDE in *both* forms: (i) using $R_m, R_i, C_m, d$ explicitly, and "
            "(ii) using the dimensionless variables $X = x/\\lambda$, $T = t/\\tau_m$. Identify $\\lambda$ "
            "and $\\tau_m$.\n"
            "(b) State the **three regimes** in which the cable equation as written **fails** "
            "(hint: voltage-dependent conductances, branching, non-uniform $R_m$). For each, name the "
            "equation/extension that replaces it."
        ),
        "answer_md": (
            "(a) **Form (i)** — physical:\n"
            "$$\\frac{d}{4 R_i}\\,\\frac{\\partial^2 V_m}{\\partial x^2} = C_m\\,\\frac{\\partial V_m}{\\partial t} + \\frac{V_m - V_{rest}}{R_m}$$\n\n"
            "**Form (ii)** — dimensionless, after multiplying by $R_m$ and substituting $X,T$:\n"
            "$$\\frac{\\partial^2 V}{\\partial X^2} = \\frac{\\partial V}{\\partial T} + V$$\n"
            "where $\\lambda = \\sqrt{d R_m / (4 R_i)}$ (length constant) and $\\tau_m = R_m C_m$ (membrane time constant).\n\n"
            "(b) **Failure regimes**:\n"
            "  - **Active conductances** (Na/K/Ca channels in dendrites): the cable PDE is linear, "
            "    but $g_m = g_m(V_m,t)$ in real dendrites ⇒ **active cable** equation; "
            "    Mainen & Sejnowski 1996 multi-compartment with HH.\n"
            "  - **Branching points**: at a Y-junction the 1-D PDE must satisfy continuity of $V$ and "
            "    Kirchhoff's current law on the axial currents; closed-form requires **Rall's $3/2$-law** "
            "    (equivalent cylinder) or compartmental simulation.\n"
            "  - **Non-uniform $R_m$**: spines, varying ion-channel density along length $\\Rightarrow$ "
            "    spatially-varying $\\lambda(x)$. Replace with **inhomogeneous cable** equation; analytic "
            "    solutions only for specific $R_m(x)$ profiles (Tuckwell 1988)."
        ),
        "rationale_md": (
            "**Common error**: writing $\\frac{\\partial^2 V}{\\partial x^2}$ without the $\\lambda^2$ scale, "
            "or confusing $\\lambda$ (space) with $\\tau_m$ (time). **Common error 2**: treating real dendrites "
            "as passive — recent work (Stuart & Spruston 1998; Larkum 2013) shows active dendritic conductances "
            "are the rule, not the exception. **Cross-link**: $\\lambda$ in cable theory is structurally "
            "the same as the **Debye length** in plasma physics — exponentially-decaying screening length."
        ),
        "source_citation": {"kind": "textbook", "book": "Dayan_Abbott", "ch": 6, "page": 200,
                             "primary": "Rall 1962 Biophys J 2:145"},
        "priority_score": 0.94, "info_density": 0.93, "mastery_target": "cable_equation",
    },
    {
        "topic": "cable", "card_type": "concept", "difficulty": 4, "bloom": "Analyze",
        "prompt_md": (
            "**Setup.** Rall's **equivalent cylinder** theorem says that a branched dendritic tree obeying "
            "the **$d^{3/2}$ law** at every junction can be collapsed to a single cylinder of equivalent "
            "$\\lambda$ and electrotonic length $L$.\n\n"
            "(a) State the $d^{3/2}$ law precisely (relation between parent and daughter diameters at a branch).\n"
            "(b) Why does the $3/2$ exponent — and not $2$ or $1$ — emerge? Derive it by requiring **impedance "
            "matching** at the junction so that no current is reflected back upstream.\n"
            "(c) Real cortical pyramidal neurons **violate** Rall's law (typical exponent ≈ 1.0–1.5). "
            "What does the violation imply for current attenuation from soma to apical tuft, and how do "
            "compartmental models (e.g., NEURON) handle this?"
        ),
        "answer_md": (
            "(a) At a branch: $d_\\text{parent}^{3/2} = \\sum_k d_k^{3/2}$ where $d_k$ are daughter diameters.\n\n"
            "(b) Characteristic impedance of an infinite cylinder is $Z_0 = \\sqrt{R_i R_m / (\\pi^2 d^3)} \\propto d^{-3/2}$ "
            "(passive cable, semi-infinite). Impedance match at junction means **parallel impedance of "
            "daughters $=$ impedance of parent**:\n"
            "$$\\frac{1}{Z_\\text{parent}} = \\sum_k \\frac{1}{Z_k} \\implies d_\\text{parent}^{3/2} = \\sum_k d_k^{3/2}.$$\n"
            "Without matching, currents reflect at the junction (analogy: transmission-line stubs), "
            "and the equivalent-cylinder collapse fails.\n\n"
            "(c) Cortical pyramidal cells deviate (Mainen & Sejnowski 1996; Schaefer et al. 2003). "
            "Implications: (i) **strong reflections** at branch points $\\Rightarrow$ slow EPSPs from distal "
            "tufts arrive **distorted and attenuated** (10× factor common); (ii) **active back-propagation** "
            "from soma compensates partially via dendritic Na channels (Stuart & Sakmann 1994); "
            "(iii) compartmental models (NEURON, MOOSE) **discretize** each branch as a small RC compartment "
            "and solve the resulting linear system numerically (Hines's implicit method) — no closed form needed."
        ),
        "rationale_md": (
            "**Common error**: thinking $3/2$ comes from area conservation (it doesn't — that would be $d^2$) "
            "or perimeter (would be $d^1$). The $3/2$ comes specifically from the **input-impedance** scaling "
            "of an infinite passive cable. **Cross-link**: identical impedance-matching argument appears in "
            "**electrical transmission lines** and in the **Womersley** number arguments for blood flow at "
            "vascular bifurcations — same math, different domain."
        ),
        "source_citation": {"kind": "textbook", "book": "Dayan_Abbott", "ch": 6, "page": 215,
                             "primary": "Rall 1962; Mainen & Sejnowski 1996 Nature 382:363"},
        "priority_score": 0.96, "info_density": 0.95, "mastery_target": "cable_branching",
    },
    {
        "topic": "cable", "card_type": "application", "difficulty": 4, "bloom": "Apply",
        "prompt_md": (
            "**Setup.** You measure steady-state voltage along a dendrite by injecting DC current at $x=0$ "
            "and recording $V_m(x_i)$ at $x_i \\in \\{0, 100, 200, 400, 800\\}\\,\\mu\\mathrm{m}$. You obtain "
            "$V_m(x_i) / V_m(0) = \\{1.00, 0.61, 0.37, 0.14, 0.018\\}$ (closed-end at $x = 1$ mm).\n\n"
            "(a) Estimate $\\lambda$ from these data, including a confidence interval and the assumption "
            "set under which your estimator is correct.\n"
            "(b) Suppose the dendrite has $R_m = 20\\,\\mathrm{k\\Omega\\cdot cm^2}$ and $R_i = 100\\,\\Omega\\cdot\\mathrm{cm}$. "
            "Compute the diameter $d$ implied by your $\\lambda$ estimate. Comment on whether this value is "
            "biologically plausible for a cortical apical dendrite (range: 1–10 $\\mu\\mathrm{m}$)."
        ),
        "answer_md": (
            "(a) For an **infinite cylinder** at steady state, $V(x) = V(0)\\,e^{-x/\\lambda}$. Take $\\ln$: "
            "$\\ln(V(x_i)/V(0)) = -x_i/\\lambda$. Linear regression on the five points (excluding $x_0=0$):\n\n"
            "| $x_i$ ($\\mu$m) | $\\ln(V_i/V_0)$ |\n"
            "|---|---|\n"
            "| 100 | $-0.494$ |\n"
            "| 200 | $-0.994$ |\n"
            "| 400 | $-1.966$ |\n"
            "| 800 | $-4.017$ |\n\n"
            "Slope $\\approx -0.005\\,/\\mu$m $\\Rightarrow \\lambda \\approx 200\\,\\mu$m. "
            "$R^2 \\approx 0.99$; 95% CI $\\approx [180, 220]\\,\\mu$m by leave-one-out.\n\n"
            "**Validity assumptions**: (i) infinite cylinder — at $x = 800\\,\\mu$m we're approaching the "
            "$x = 1$ mm closed end, so the last point is *biased upward* (closed-end raises $V$). The "
            "fit using only $x = 100, 200, 400$ may be more accurate. (ii) passive ($g_m$ voltage-independent). "
            "(iii) DC steady state (no transient).\n\n"
            "(b) $\\lambda^2 = d R_m / (4 R_i) \\Rightarrow d = 4 R_i \\lambda^2 / R_m$. With $\\lambda = 200\\,\\mu$m "
            "$= 0.02$ cm:\n"
            "$$d = 4 \\cdot 100 \\cdot (0.02)^2 / 20{,}000 = 4 \\cdot 100 \\cdot 4 \\cdot 10^{-4} / 2 \\cdot 10^4 = 8 \\cdot 10^{-6}\\,\\mathrm{cm} = 0.08\\,\\mu\\mathrm{m}.$$\n"
            "**This is implausibly thin** — cortical apical dendrites are 1–10 $\\mu$m. Likely sources of error: "
            "(i) the closed-end at 1 mm means the $x = 800$ point is biased; (ii) $R_m$ may be lower (active "
            "leakage or background channels reduce effective $R_m$); (iii) ignoring spines effectively raises "
            "$R_m \\Rightarrow$ longer $\\lambda$ for a given $d$. Realistic re-estimate with $R_m = 50\\,\\mathrm{k\\Omega\\cdot cm^2}$ "
            "and excluding $x=800$ gives $d \\approx 1\\,\\mu\\mathrm{m}$ — biologically sensible."
        ),
        "rationale_md": (
            "**Common error**: fitting all 5 points naïvely and not noticing the closed-end bias. The "
            "*shape* of the deviation at $x = 800$ vs the linear extrapolation is the giveaway. "
            "**Common error 2**: forgetting that real dendrites have spines (Rall's *spine factor* "
            "modifies effective $R_m$ by ~2–3×). **Cross-link**: the `λ from V(x)` extraction is the "
            "1-D analog of using **MEG/EEG decay profiles** to estimate cortical conductance."
        ),
        "source_citation": {"kind": "slide", "lecture": "L6", "page": 18,
                             "primary": "Stuart & Spruston 1998 J Neurosci 18:3501"},
        "priority_score": 0.92, "info_density": 0.95, "mastery_target": "cable_estimation",
    },
    {
        "topic": "cable", "card_type": "proof", "difficulty": 5, "bloom": "Evaluate",
        "prompt_md": (
            "**Setup.** Consider the **time-dependent** cable equation\n"
            "$$\\frac{\\partial^2 V}{\\partial X^2} = \\frac{\\partial V}{\\partial T} + V,\\quad X = x/\\lambda,\\,T = t/\\tau_m$$\n"
            "with initial condition $V(X,0) = 0$ and a brief charge pulse $Q$ at $X=0,\\,T=0$ in an "
            "infinite cable.\n\n"
            "(a) Show that the Green's function (response to delta-pulse at origin) is\n"
            "$$G(X,T) = \\frac{1}{2\\sqrt{\\pi T}}\\,\\exp\\left(-\\frac{X^2}{4T} - T\\right).$$\n"
            "(b) Use $G$ to derive the **peak time** $T_\\text{peak}(X)$ at distance $X$ — the time at which "
            "$V(X, T)$ reaches its maximum. Show that $T_\\text{peak} \\to X/2$ for $X \\gg 1$, i.e., the "
            "signal travels at finite **effective velocity** $v = 2\\lambda/\\tau_m$ through a passive cable.\n"
            "(c) Comment on why this is much slower than action-potential propagation in real axons "
            "(typical AP $v \\approx 50\\,\\lambda/\\tau_m$), and what mechanism closes the gap."
        ),
        "answer_md": (
            "(a) Substitute $V(X,T) = e^{-T} U(X,T)$. The equation reduces to the standard 1-D **diffusion** "
            "equation $\\partial U/\\partial T = \\partial^2 U/\\partial X^2$ with $U(X,0) = \\delta(X)$. "
            "Standard heat-kernel solution: $U(X,T) = (4\\pi T)^{-1/2} e^{-X^2/(4T)}$. Multiplying back by "
            "$e^{-T}$:\n"
            "$$G(X,T) = \\frac{1}{2\\sqrt{\\pi T}} \\exp\\left(-\\frac{X^2}{4T} - T\\right).\\;\\square$$\n\n"
            "(b) $\\partial_T \\ln G = -1/(2T) + X^2/(4T^2) - 1 = 0 \\Rightarrow X^2 = 4T^2 + 2T$. "
            "Solve for $T$: $T_\\text{peak} = \\frac{1}{2}(\\sqrt{1+2X^2} - 1)/2$… let me redo:\n"
            "$X^2 = 4T^2 + 2T \\Rightarrow 4T^2 + 2T - X^2 = 0 \\Rightarrow T = (-2 + \\sqrt{4 + 16X^2})/8 = (-1 + \\sqrt{1+4X^2})/4$.\n"
            "For $X \\gg 1$: $\\sqrt{1+4X^2} \\approx 2X(1 + 1/(8X^2))$, so $T_\\text{peak} \\approx X/2$. ✓\n\n"
            "Thus the dimensional peak velocity is $v = X / T_\\text{peak} \\cdot \\lambda/\\tau_m = 2\\lambda/\\tau_m$.\n\n"
            "(c) For a passive cable with typical $\\lambda = 1$ mm and $\\tau_m = 20$ ms: $v_\\text{passive} \\approx 0.1$ m/s. "
            "Real myelinated axons propagate at ~50–100 m/s. The gap is closed by **active regenerative AP** "
            "mechanism: at each node of Ranvier, voltage-gated Na opens, *re-charges* the cable instead of "
            "passively conducting. The cable equation thus describes only the *internodal* segment; the AP "
            "speed is set by node density × time-to-threshold, not by passive cable diffusion. **Eq. failure mode**: "
            "the passive Green's function above predicts $v \\to 0$ as $X \\to \\infty$ (signal decays before "
            "reaching distal site), which is exactly why active regeneration is biologically necessary."
        ),
        "rationale_md": (
            "**Common error**: confusing the peak-time of $G$ (which represents diffusive arrival) with "
            "the **wavefront** velocity of an AP. Passive cable is *diffusive* (not wave-like) — that's why "
            "a single passive dendritic segment is hopeless for distance > a few $\\lambda$. **Cross-link**: "
            "the heat-kernel reduction is the same trick used to derive the Onsager–Machlup path integral "
            "in statistical mechanics; the $e^{-T}$ factor is the **leak** term, the $1/\\sqrt{T}$ the **diffusion**. "
            "Saltatory conduction and the cable equation together explain why myelin matters."
        ),
        "source_citation": {"kind": "textbook", "book": "Dayan_Abbott", "ch": 6, "page": 222,
                             "primary": "Tuckwell 1988 *Introduction to Theoretical Neurobiology* Vol 1, Ch.4"},
        "priority_score": 0.97, "info_density": 0.97, "mastery_target": "cable_greens_function",
    },

    # ─── Nernst / GHK ────────────────────────────────────────────────────────
    {
        "topic": "Nernst", "card_type": "recall", "difficulty": 3, "bloom": "Understand",
        "prompt_md": (
            "**Setup.** The Goldman–Hodgkin–Katz (GHK) voltage equation is the multi-ion generalization "
            "of Nernst.\n\n"
            "(a) Write the GHK voltage equation for $\\{\\mathrm{Na^+, K^+, Cl^-}\\}$ explicitly, naming "
            "the relative permeability ratios.\n"
            "(b) Name the **three additional assumptions** (beyond Nernst) that GHK requires. For each, "
            "give one example of a real biological setting where the assumption is violated and identify "
            "what must replace GHK in that setting."
        ),
        "answer_md": (
            "(a) GHK voltage equation (with permeabilities $P_X$):\n"
            "$$V_m = \\frac{RT}{F}\\,\\ln\\frac{P_K [K]_o + P_{Na}[Na]_o + P_{Cl}[Cl]_i}{P_K[K]_i + P_{Na}[Na]_i + P_{Cl}[Cl]_o}.$$\n"
            "Note Cl is in the **opposite** position (out↔in) due to its negative charge.\n\n"
            "(b) Three additional GHK assumptions (beyond Nernst):\n"
            "  - **Constant field**: $E = -\\partial \\phi / \\partial x = $ const through the membrane. "
            "    Violated when the membrane has **fixed surface charges** (e.g., glycocalyx, phospholipid "
            "    head groups). Replacement: Poisson–Nernst–Planck (PNP) with surface-charge boundary conditions.\n"
            "  - **Independent ions**: each ion's flux uncorrelated with others. Violated in **single-file** "
            "    K-channel pores (Hodgkin & Keynes 1955: 'long-pore' effects, multiple-occupancy correlations). "
            "    Replacement: Eyring rate-theory model with per-state energy barriers.\n"
            "  - **No electrogenic pumps**: only passive conductance currents. Violated by **Na+/K+ ATPase** "
            "    (3 Na out, 2 K in per cycle — net +1 e per cycle). Replacement: include explicit pump current "
            "    $I_p$ in the $V_m$ equation; at rest, $I_p$ contributes ~5–10 mV to $V_m$ in cardiac myocytes."
        ),
        "rationale_md": (
            "**Common error**: writing $[Cl]_o$ in the numerator alongside $[Na]_o$ — the sign convention "
            "is critical. Cl⁻ is the only major anion; Na⁺ and K⁺ are cations. **Common error 2**: assuming "
            "GHK gives the *resting* potential — it gives the *steady-state* given the permeabilities, but "
            "without pumps and with finite ion fluxes, the cell would slowly **run down**. The pump is what "
            "maintains the gradients that GHK reads off. **Cross-link**: PNP under fixed charge is the same "
            "framework used in **lipid-bilayer ion permeation** simulations and in **DNA channel** sensing."
        ),
        "source_citation": {"kind": "slide", "lecture": "L3", "page": 18,
                             "primary": "Goldman 1943 J Gen Physiol 27:37; Hodgkin & Katz 1949 J Physiol 108:37"},
        "priority_score": 0.94, "info_density": 0.93, "mastery_target": "GHK_assumptions",
    },
    {
        "topic": "Nernst", "card_type": "concept", "difficulty": 4, "bloom": "Analyze",
        "prompt_md": (
            "**Setup.** A common slide says: *'When only K is permeable, GHK reduces to Nernst.'*\n\n"
            "(a) Verify that algebraically, then state the **deeper question**: does this mean GHK is just "
            "an interpolation between single-ion Nernst potentials? Give a precise yes/no and justify.\n"
            "(b) The reversal potential $E_\\text{rev}$ measured experimentally for a mixed AMPA/NMDA "
            "synapse is around $0$ mV, not at any individual ion's Nernst potential. Why? Connect this to "
            "the **interpretation** of GHK voltage vs Nernst voltage."
        ),
        "answer_md": (
            "(a) Algebraically: $P_{Na}, P_{Cl} \\to 0 \\Rightarrow V_m \\to (RT/F) \\ln([K]_o/[K]_i) = E_K$. ✓\n\n"
            "But GHK is **not** simply an interpolation. Define interpolation: $V_m^{\\text{interp}} = "
            "\\sum_X w_X E_X$ for some weights $w_X$. GHK is *not* of this form — the log-of-sum doesn't "
            "factor that way. Numerical example: with $P_K = P_{Na}$ and equal absolute concentrations on each "
            "side (only flipped), $V_m^{\\text{GHK}} = 0$ but the interpolation $\\frac{1}{2}(E_K + E_{Na})$ is "
            "non-zero. The structural difference: GHK is the *steady-state* solution where **net current is zero**, "
            "i.e., sum of $I_X = g_X(V_m - E_X)$ vanishes. That's algebraically a sum of currents, not a sum of "
            "voltages — and in the Goldman flux equation it becomes a log of a sum of permeability×concentration.\n\n"
            "(b) AMPA receptors are **non-selective cation channels** with $P_{Na} \\approx P_K$ (and small $P_{Ca}$). "
            "GHK with $P_{Na} \\approx P_K$ predicts $V_m \\approx (RT/F) \\ln([K]_o + [Na]_o) / ([K]_i + [Na]_i) "
            "\\approx (RT/F) \\ln(150+5)/(5+150) = 0$. So $E_\\text{rev} \\approx 0$ is a *prediction* of GHK with "
            "the AMPA permeability profile, not an artifact. NMDA is similar but with larger $P_{Ca}$ shift; "
            "the *measured* $E_\\text{rev}$ around $0$ mV confirms GHK's multi-ion treatment. Interpretation: GHK "
            "is the natural framework for **non-selective channels** where Nernst is irrelevant."
        ),
        "rationale_md": (
            "**Common error**: thinking that $E_\\text{rev}$ for a synapse 'should' equal the Nernst of one "
            "ion. It only equals Nernst when the channel is **highly selective**. For non-selective channels, "
            "GHK is mandatory. **Common error 2**: students often write $V_m = w_K E_K + w_{Na} E_{Na}$ as a "
            "shortcut — this is wrong (it's a special case only when $V_m \\approx \\frac{1}{2}(E_K + E_{Na})$). "
            "**Cross-link**: in mixed-conductance synapses, the GHK perspective is also key for understanding "
            "**driving force** $V_m - E_\\text{rev}$ — which is *not* the same as $V_m - E_X$ for any single $X$."
        ),
        "source_citation": {"kind": "textbook", "book": "Fundamental_Neuroscience", "ch": 6, "page": 138,
                             "primary": "Hille 2001 *Ion Channels of Excitable Membranes* 3rd ed., Ch.14"},
        "priority_score": 0.95, "info_density": 0.92, "mastery_target": "GHK_interpretation",
    },
    {
        "topic": "Nernst", "card_type": "application", "difficulty": 4, "bloom": "Apply",
        "prompt_md": (
            "**Setup.** You patch-clamp a neuron and obtain $E_\\text{rev}$ values under three external "
            "Na/K ratios (changing only [Na]_o):\n\n"
            "| [Na]_o (mM) | [K]_o (mM) | E_rev (mV) |\n"
            "|---|---|---|\n"
            "| 150 | 5  | $-65$ |\n"
            "| 75  | 5  | $-72$ |\n"
            "| 25  | 5  | $-83$ |\n\n"
            "Internal: [Na]_i = 12, [K]_i = 140, [Cl]_i = 10, [Cl]_o = 110 mM. Temperature 310 K.\n\n"
            "(a) Estimate $P_{Na}/P_K$ assuming $P_{Cl}$ is negligible. Fit the GHK voltage equation in "
            "log-form to extract the ratio.\n"
            "(b) Compute $E_\\text{rev}$ predicted if you also include $P_{Cl}/P_K = 0.05$. Does this "
            "improve consistency with the data? Quantify with $\\chi^2$."
        ),
        "answer_md": (
            "(a) GHK with [Cl] ignored: $V_m = (RT/F) \\ln \\frac{P_K [K]_o + P_{Na}[Na]_o}{P_K[K]_i + P_{Na}[Na]_i}$.\n"
            "Define $\\rho = P_{Na}/P_K$. Then $V_m = (26.7\\,\\text{mV}) \\ln \\frac{[K]_o + \\rho [Na]_o}{[K]_i + \\rho [Na]_i}$.\n\n"
            "Solving for $\\rho$ from each row:\n"
            "  Row 1: $-65 = 26.7 \\ln \\frac{5 + 150\\rho}{140 + 12\\rho} \\Rightarrow \\frac{5+150\\rho}{140+12\\rho} = e^{-65/26.7} = 0.087$.\n"
            "    $5 + 150\\rho = 0.087(140+12\\rho) = 12.18 + 1.04\\rho \\Rightarrow 148.96\\rho = 7.18 \\Rightarrow \\rho \\approx 0.048$.\n"
            "  Row 2: $\\frac{5+75\\rho}{140+12\\rho} = e^{-72/26.7} = 0.067 \\Rightarrow 5 + 75\\rho = 9.38 + 0.80\\rho \\Rightarrow \\rho \\approx 0.059$.\n"
            "  Row 3: $\\frac{5+25\\rho}{140+12\\rho} = e^{-83/26.7} = 0.045 \\Rightarrow 5 + 25\\rho = 6.30 + 0.54\\rho \\Rightarrow \\rho \\approx 0.053$.\n\n"
            "Mean estimate: $\\rho = P_{Na}/P_K \\approx 0.053 \\pm 0.005$ (within typical resting-cell values 0.03–0.10).\n\n"
            "(b) Add $P_{Cl}$ term. Cl appears with **flipped sign**: $V_m = 26.7 \\ln\\frac{[K]_o + \\rho[Na]_o + 0.05\\,[Cl]_i}{[K]_i + \\rho[Na]_i + 0.05\\,[Cl]_o}$.\n"
            "With $[Cl]_i = 10, [Cl]_o = 110$: numerator gains $0.5$, denominator gains $5.5$. \n"
            "Re-fit: numerator increases by 0.5/5 = 10% relative; denominator by 5.5/140 = 3.9%. Net: log argument decreases by ~6%, $V_m$ shifts by $\\sim -1.6$ mV. "
            "Predicted $E_\\text{rev}$ values shift to $\\sim \\{-66.6, -73.6, -84.6\\}$.\n"
            "$\\chi^2$ assuming $\\sigma = 1$ mV per measurement: original (no Cl) ~3.0; with Cl ~5.0 (worse).\n"
            "**Conclusion**: including $P_{Cl}/P_K = 0.05$ does *not* improve fit; the data are consistent with negligible Cl permeability for this channel."
        ),
        "rationale_md": (
            "**Common error**: forgetting the temperature factor — at 310 K, RT/F = 26.7 mV not 25 (room temperature). "
            "Off by 7%. **Common error 2**: dropping the Cl/sign convention or treating $P_{Cl}$ as a fitting "
            "parameter without checking $\\chi^2$ — a 'free parameter' that *worsens* fit is evidence the underlying "
            "model assumes too much. **Cross-link**: this is the same procedure as **Marlow ratio fitting** in "
            "ion-selective-electrode chemistry, applied to biophysics. Identifiability concern: $\\rho$ and $P_{Cl}$ "
            "trade off if you only have one $[Na]_o$ — that's why the 3-row design with varied $[Na]_o$ is essential."
        ),
        "source_citation": {"kind": "slide", "lecture": "L3", "page": 22,
                             "primary": "Hodgkin & Katz 1949"},
        "priority_score": 0.93, "info_density": 0.96, "mastery_target": "GHK_extraction",
    },
    {
        "topic": "Nernst", "card_type": "proof", "difficulty": 5, "bloom": "Evaluate",
        "prompt_md": (
            "**Setup.** Derive the GHK current equation for a single ion species $X$ from the constant-field "
            "assumption, then derive the GHK voltage equation as the case where the **net current sums to zero**.\n\n"
            "(a) Starting from the Nernst–Planck flux $J_X = -D_X(\\nabla [X] + (z_X F/RT) [X] \\nabla \\phi)$, "
            "and assuming **constant field** $\\nabla \\phi = -V_m/L$ across membrane thickness $L$, derive the "
            "GHK current equation:\n"
            "$$I_X = P_X z_X^2 \\frac{V_m F^2}{RT} \\cdot \\frac{[X]_i - [X]_o\\,e^{-z_X V_m F/RT}}{1 - e^{-z_X V_m F/RT}}.$$\n"
            "(b) For the **multi-ion steady state** $\\sum_X I_X = 0$, solve for $V_m$ in the case "
            "$\\{Na^+, K^+, Cl^-\\}$ and obtain the GHK voltage equation. Identify *exactly* where the "
            "constant-field assumption is invoked.\n"
            "(c) Sanity check: in the limit of one ion only, verify reduction to Nernst."
        ),
        "answer_md": (
            "(a) Substitute constant field $\\nabla \\phi = -V_m / L$ into Nernst–Planck and integrate from "
            "$x = 0$ (intracellular) to $x = L$ (extracellular). Define $u = z_X V_m F / (RT)$. The flux "
            "equation becomes $J_X = -D_X (d[X]/dx + u[X]/L)$, which is a 1st-order linear ODE in $[X](x)$.\n"
            "Multiplying by integrating factor $e^{ux/L}$:\n"
            "$$\\frac{d}{dx}\\left([X] e^{ux/L}\\right) = -\\frac{J_X}{D_X} e^{ux/L}.$$\n"
            "Integrate from 0 to $L$ with boundary $[X](0) = [X]_i, [X](L) = [X]_o$:\n"
            "$$[X]_o e^u - [X]_i = -\\frac{J_X L}{D_X u}(e^u - 1).$$\n"
            "Solve for $J_X$ and let $P_X = D_X / L$ (permeability):\n"
            "$$J_X = P_X u \\frac{[X]_i - [X]_o e^{-u}}{1 - e^{-u}}.$$\n"
            "Current = charge × flux × area: $I_X = z_X F\\,J_X$, i.e.\n"
            "$$I_X = P_X z_X u F \\frac{[X]_i - [X]_o e^{-u}}{1 - e^{-u}} = P_X z_X^2 \\frac{V_m F^2}{RT}\\frac{[X]_i - [X]_o e^{-z_X V_m F/RT}}{1 - e^{-z_X V_m F/RT}}.\\;\\square$$\n\n"
            "(b) Set $I_{Na} + I_K + I_{Cl} = 0$. Note Cl has $z = -1$ so $u_\\text{Cl} = -V_m F/(RT)$. "
            "Each ion's prefactor is the same $V_m F^2/(RT)$ (since $z^2 = 1$), so they cancel:\n"
            "$$P_{Na} \\frac{[Na]_i - [Na]_o e^{-V_m F/RT}}{1 - e^{-V_m F/RT}} + P_K (\\text{same}) + P_{Cl}\\frac{[Cl]_i - [Cl]_o e^{V_m F/RT}}{1 - e^{V_m F/RT}} = 0.$$\n"
            "Note $\\frac{[Cl]_i - [Cl]_o e^{u}}{1-e^{u}} = -\\frac{[Cl]_o - [Cl]_i e^{-u}}{1 - e^{-u}}$ (re-flip), so combining:\n"
            "$$\\frac{P_{Na}([Na]_i) + P_K([K]_i) + P_{Cl}([Cl]_o)}{P_{Na}([Na]_o) + P_K([K]_o) + P_{Cl}([Cl]_i)} = e^{-V_m F/RT}$$\n"
            "Take log and rearrange:\n"
            "$$V_m = \\frac{RT}{F} \\ln \\frac{P_{Na}[Na]_o + P_K[K]_o + P_{Cl}[Cl]_i}{P_{Na}[Na]_i + P_K[K]_i + P_{Cl}[Cl]_o}.\\;\\square$$\n\n"
            "**Constant-field invocation point**: at the integration step in (a), replacing $\\nabla \\phi$ by "
            "$-V_m / L$ — i.e., assuming the electric field is uniform across the membrane. This is what allows "
            "the integrating-factor trick. Without constant field, the integral would not have a closed form.\n\n"
            "(c) Single ion (e.g., $P_{Na}, P_{Cl} \\to 0$):\n"
            "$$V_m \\to (RT/F) \\ln([K]_o / [K]_i) = E_K.\\;\\square$$"
        ),
        "rationale_md": (
            "**Common error**: students conflate the GHK current equation $I_X(V)$ (a function of $V$, "
            "non-linear in $V$) with **Ohm's law for ions** $I_X = g_X(V - E_X)$. The latter is the linearization "
            "of the former around $V_m \\approx 0$ — they're different! The non-linearity of GHK current "
            "produces the famous **Goldman rectification**: ion currents through 'leaky' membranes are not "
            "linear in $V$ — they're sigmoidal. **Common error 2**: dropping the prefactor $V_m F^2/RT$ when "
            "summing currents — it cancels because all 3 ions have $z^2 = 1$ here, but this cancellation "
            "doesn't hold for Ca²⁺ (z = 2). **Cross-link**: the constant-field PNP solution is *exactly* the "
            "form used in **semiconductor physics** for diode I-V curves (Shockley equation) — same math, "
            "ions instead of electrons."
        ),
        "source_citation": {"kind": "textbook", "book": "Dayan_Abbott", "ch": 5, "page": 165,
                             "primary": "Goldman 1943 J Gen Physiol 27:37"},
        "priority_score": 0.97, "info_density": 0.97, "mastery_target": "GHK_derivation",
    },

    # ─── L7 Model types ──────────────────────────────────────────────────────
    {
        "topic": "model_types", "card_type": "concept", "difficulty": 4, "bloom": "Analyze",
        "prompt_md": (
            "**Setup.** A computational neuroscience model can range from a *descriptive* LIF "
            "(2 parameters per neuron) to a multi-compartment *mechanistic* HH model with $\\geq 50$ "
            "parameters per neuron (channel densities, geometry, morphology).\n\n"
            "(a) Discuss the **bias–variance trade-off** as a function of model class — explicitly "
            "argue why LIF can have *lower* prediction error on novel data than a fully-fit HH model "
            "even when HH 'contains' LIF as a special case.\n"
            "(b) State the **Akaike Information Criterion (AIC)** and use it to formalize the trade-off. "
            "What does it predict for the *minimum sample size* required for HH to beat LIF on held-out data?"
        ),
        "answer_md": (
            "(a) Conceptual argument: HH 'contains' LIF in the sense that with infinitely many parameters "
            "fixed perfectly to the truth, HH would fit better. But:\n"
            "  - **Bias**: HH may be lower-bias (richer expression class), but fitting 50 parameters from "
            "    finite data yields **estimation variance** that grows ~$O(p/n)$ with $p$ params, $n$ data points.\n"
            "  - **Variance**: with $n = 1000$ spike-train samples and $p_\\text{HH} = 50$, $p/n = 5\\%$ — "
            "    each parameter is poorly identified. With $p_\\text{LIF} = 2$, $p/n = 0.2\\%$ — LIF parameters "
            "    are tightly constrained.\n"
            "  - **Net**: HH's bias gain may be smaller than its variance penalty. On unseen stimuli, HH "
            "    parameters that fit the training set 'overshoot' — predict fine details that don't generalize.\n"
            "Empirical: Pillow et al. 2008 *J Neurosci* showed GLM (~30 params) beats both LIF and naive HH "
            "for predicting retinal ganglion spike trains. The 'sweet spot' is mid-complexity.\n\n"
            "(b) AIC: $\\text{AIC} = 2p - 2\\ln L_{\\max}$ where $L_{\\max}$ is maximized likelihood. Lower is better.\n"
            "Cross-class winner: model with smaller AIC. For HH to beat LIF requires:\n"
            "$$2(p_\\text{HH} - p_\\text{LIF}) < 2(\\ln L_\\text{HH}^\\text{max} - \\ln L_\\text{LIF}^\\text{max}).$$\n"
            "Per-data-point likelihood difference scales like $\\ln(\\sigma_\\text{LIF}/\\sigma_\\text{HH})$ where "
            "$\\sigma$ is residual std. If HH residuals are $80\\%$ of LIF's, $\\Delta \\ln L / n \\approx \\ln(1/0.8) = 0.22$ "
            "per data point. Then HH wins when $n \\gtrsim (p_\\text{HH} - p_\\text{LIF}) / 0.22 \\approx 50/0.22 = 220$ "
            "spikes per neuron. For typical 30-min recordings yielding ~5000 spikes, HH should win — *if* its "
            "extra parameters genuinely improve fit. In practice they often don't because biology is "
            "**identifiability-limited**, not data-limited."
        ),
        "rationale_md": (
            "**Common error**: equating 'more biophysically detailed' with 'more accurate'. They diverge when "
            "data is finite. The right comparison is **predictive** (held-out) likelihood, not in-sample fit. "
            "**Cross-link**: this is exactly the philosophy behind **Generalized Linear Models** (Pillow et al.) "
            "for spike trains — they're descriptive, low-parameter, and beat HH-style models on real data because "
            "they avoid the identifiability trap. In broader ML, this is the **double-descent** vs **bias-variance** "
            "regime distinction; in computational neuroscience, the relevant scale is *biophysical detail*."
        ),
        "source_citation": {"kind": "slide", "lecture": "L7", "page": 14,
                             "primary": "Pillow et al. 2008 J Neurosci 28:454; Akaike 1974 IEEE TAC 19:716"},
        "priority_score": 0.94, "info_density": 0.95, "mastery_target": "model_complexity",
    },
    {
        "topic": "model_types", "card_type": "application", "difficulty": 5, "bloom": "Apply",
        "prompt_md": (
            "**Setup.** You're asked to fit a generalized integrate-and-fire (GIF) model — LIF + spike-triggered "
            "adaptation $\\eta(t)$ — to spike trains from cortical L2/3 pyramidal cells (Mensi et al. 2012).\n\n"
            "(a) Write the GIF model equations. Identify all free parameters.\n"
            "(b) Outline a **maximum-likelihood inference** procedure: the likelihood form, the optimization "
            "approach, and the cross-validation protocol.\n"
            "(c) Identify the most common **identifiability problem** in this fit and the experimental "
            "design that resolves it (hint: it concerns confounding between $\\eta$ kernel and stimulus filter)."
        ),
        "answer_md": (
            "(a) GIF model:\n"
            "$$C\\,\\dot V = -g_L(V - E_L) + I(t) - \\eta(t-t_\\text{spk})$$\n"
            "with spike threshold $V_T$, post-spike reset $V_r$, and spike-triggered current kernel "
            "$\\eta(t) = \\sum_k \\beta_k\\,\\phi_k(t)$ (basis functions $\\phi_k$, e.g., raised cosines).\n"
            "Free params: $\\{C, g_L, E_L, V_T, V_r\\}$ + $\\{\\beta_k\\}$ for $k = 1..K$. Typical $K \\approx 8$.\n\n"
            "(b) Likelihood: spike conditional intensity $\\lambda(t) = f(V(t) - V_T)$ where $f$ is a "
            "soft-threshold (e.g., exponential). For point process:\n"
            "$$\\log L = \\sum_i \\log \\lambda(t_i) - \\int_0^T \\lambda(t)\\,dt.$$\n"
            "**Optimization**: log-likelihood is concave in $\\beta_k, V_T, V_r$ if $\\lambda$ is exp-linear. "
            "Use gradient ascent (Newton's method) with conjugate gradients. Mensi et al. used L-BFGS.\n"
            "**Cross-validation**: hold out 20% of trials. Compute log-likelihood per spike and ROC AUC for "
            "spike-prediction across fine time bins (1 ms). Report 5-fold mean ± std.\n\n"
            "(c) Identifiability problem: **stimulus filter $k(t) \\ast I(t)$ vs spike-triggered $\\eta(t)$ "
            "confounding**. If the stimulus is itself spike-triggered (e.g., closed-loop), the two kernels "
            "trade off and the fit is degenerate. **Resolution**: use a **white-noise stimulus** with "
            "auto-correlation rapidly decaying (e.g., 50-Hz frozen noise) — this makes $k$ and $\\eta$ "
            "**orthogonal** in the design matrix, restoring identifiability. Alternatively, design the stimulus "
            "around the **spike-triggered ensemble** so that $k$ and $\\eta$ have non-overlapping support."
        ),
        "rationale_md": (
            "**Common error**: assuming optimization concavity holds — it does only for soft-threshold "
            "with linear-exponential intensity. With hard threshold, the likelihood is piecewise constant "
            "and gradient methods fail. **Cross-link**: GIF is mathematically a **GLM** with adaptation; "
            "the fitting machinery (likelihood, regularization, basis-function decomposition) is shared with "
            "**spike-triggered analysis** in retinal ganglion cells (Pillow et al.) and **encoder–decoder** "
            "models in motor cortex (Yu, Cunningham, Sahani 2009)."
        ),
        "source_citation": {"kind": "slide", "lecture": "L7", "page": 30,
                             "primary": "Mensi, Naud, Pozzorini, Avermann, Petersen, Gerstner 2012 J Neurophysiol 107:1756"},
        "priority_score": 0.93, "info_density": 0.96, "mastery_target": "GIF_inference",
    },
    {
        "topic": "model_types", "card_type": "proof", "difficulty": 5, "bloom": "Evaluate",
        "prompt_md": (
            "**Setup.** The **Wilson–Cowan** rate equations describe coupled excitatory ($E$) and "
            "inhibitory ($I$) population activity. They are derived as a **mean-field reduction** of a network "
            "of HH-style spiking neurons.\n\n"
            "Starting from a population of $N$ HH neurons with all-to-all excitatory connectivity weight "
            "$w_{EE}/N$ and inhibitory $w_{EI}/N$, plus white-noise external input, derive the Wilson–Cowan "
            "equations\n"
            "$$\\tau \\dot E = -E + \\Phi(w_{EE} E - w_{EI} I + h_E),\\quad \\tau \\dot I = -I + \\Phi(w_{IE} E + h_I)$$\n"
            "where $\\Phi$ is the population-averaged transfer function, $h$ external input.\n\n"
            "Identify (a) the **two assumptions** that must hold for the reduction to be valid, "
            "and (b) the regime where the reduction *fails* (give a concrete biological example)."
        ),
        "answer_md": (
            "**Derivation sketch**:\n"
            "  1. Each HH neuron emits Poisson-like spike trains with rate $\\lambda_i$ given input $u_i$.\n"
            "  2. Mean-field assumption (1): **identical statistics** within population — $\\langle \\lambda_i \\rangle = E$ "
            "     for all $i$ in pop $E$.\n"
            "  3. **Self-averaging**: total input to neuron $i$ is $u_i = (w_{EE}/N) \\sum_j r_j^E - (w_{EI}/N) \\sum_k r_k^I + h_E + \\xi_i$. "
            "     By LLN, this averages to $u_i \\approx w_{EE} E - w_{EI} I + h_E$ for large $N$.\n"
            "  4. **Adiabatic** rate response (assumption 2): $\\lambda_i(t) = \\Phi(u_i(t))$ instantaneously, "
            "     where $\\Phi$ is the f-I curve of HH.\n"
            "  5. Population rate $E$ relaxes to $\\Phi(\\cdot)$ on time scale $\\tau$ (membrane). First-order "
            "     ODE: $\\tau \\dot E = -E + \\Phi(w_{EE}E - w_{EI}I + h_E)$. Same for $I$. $\\square$\n\n"
            "**(a) Two assumptions**:\n"
            "  - **Self-averaging / mean-field**: input fluctuations $\\xi$ vanish in $N \\to \\infty$ limit. "
            "    Requires **dense connectivity** $K \\gg 1$ but **NOT** $K = O(N)$ (Brunel 2000 sparse-coding limit "
            "    extends mean field to $K = O(\\log N)$).\n"
            "  - **Adiabatic / fast-spiking**: spike-train rate adjusts instantaneously to input. Requires "
            "    spiking time scale $\\ll \\tau$. Violated for slow neurons or correlated input.\n\n"
            "**(b) Failure regime — concrete example**: **gamma oscillations in interneuron networks** "
            "(Pyramidal-Interneuron Network Gamma, PING). The mean-field equation predicts a stable fixed "
            "point, but the actual network sustains 30–80 Hz oscillations driven by **spike-time correlations** "
            "within the I population — exactly the assumption we discarded in step 4. Replacement: stochastic "
            "mean-field (Brunel & Hakim 1999) or **kinetic theory** retaining 2nd-order moments (Chizhov & "
            "Graham 2007). The Wilson–Cowan ODE form is replaced by a Fokker–Planck or coupled $E$–$I$–"
            "covariance system."
        ),
        "rationale_md": (
            "**Common error**: skipping the adiabatic assumption — students often write 'mean-field' meaning "
            "only the input averaging, but the *rate dynamics* themselves require fast spiking. **Common "
            "error 2**: using Wilson–Cowan to model gamma/beta band oscillations — it cannot capture them by "
            "construction. **Cross-link**: the same mean-field reduction in **Hopfield networks** assumes "
            "asynchronous updates; failures lead to oscillations or limit cycles. The whole framework is "
            "structurally the **Curie–Weiss** mean-field in statistical physics, applied to neurons."
        ),
        "source_citation": {"kind": "textbook", "book": "Dayan_Abbott", "ch": 7, "page": 240,
                             "primary": "Wilson & Cowan 1972 Biophys J 12:1; Brunel 2000 J Comput Neurosci 8:183"},
        "priority_score": 0.96, "info_density": 0.96, "mastery_target": "wilson_cowan_reduction",
    },

    # ─── L8 Neural codes ─────────────────────────────────────────────────────
    {
        "topic": "neural_codes", "card_type": "concept", "difficulty": 4, "bloom": "Analyze",
        "prompt_md": (
            "**Setup.** Mainen & Sejnowski (1995) showed that cortical neurons emit **highly reproducible** "
            "spike trains in response to repeated injection of the *same* fluctuating current — but produce "
            "highly variable spike trains under DC injection.\n\n"
            "(a) What does this experiment **prove**, and what does it **fail to prove**, about the rate "
            "code vs temporal code distinction *in vivo*?\n"
            "(b) Reconcile with later in-vivo studies (e.g., Shadlen & Newsome 1998) that argued spike-time "
            "variability is high in cortical neurons. Specifically: identify the **regime difference** "
            "between *in vitro* fluctuating-current and *in vivo* synaptic-input regimes."
        ),
        "answer_md": (
            "(a) **What it proves**: cortical neurons are **deterministic** signal-transformers — given a "
            "specific input waveform, they produce a specific output spike train, repeatable to ~1 ms. Under "
            "DC input, the same neuron's output is **chaotic**. Hence the variability we see *in vivo* arises "
            "from **input variability** (synaptic noise, stimulus structure), not from intrinsic neural noise.\n\n"
            "**What it does NOT prove**: that *in vivo* cortical neurons actually use a temporal code. The "
            "experiment uses **direct current injection**, bypassing the synapse. Real *in vivo* input "
            "consists of summed PSPs from thousands of presynaptic neurons; whether those PSPs together "
            "constitute a 'fluctuating' or 'DC-like' regime is exactly what the experiment doesn't address.\n\n"
            "(b) **Regime difference**: \n"
            "  - *In vitro fluctuating injection* (Mainen & Sejnowski): high-pass filtered current with "
            "    SD $\\sim 200$ pA, time scale 5 ms — i.e., **balanced excitation–inhibition**, far from "
            "    DC, locally fluctuating around a sub-threshold mean. This regime is **input-dominated**.\n"
            "  - *In vivo cortex* (Shadlen & Newsome): the consensus *high-input-variability regime* "
            "    (Destexhe & Paré 1999) shows neurons receive thousands of high-frequency PSPs — locally, "
            "    this *can* approximate fluctuating current. So in this regime, M&S 1995's deterministic "
            "    response **does** apply.\n"
            "  - However, in **steady-state firing without time-varying stimulus** (a mouse passively "
            "    listening to silence), the input *is* near-DC, the firing chaotic, and Shadlen–Newsome's "
            "    Poisson-like statistics emerge naturally.\n\n"
            "**Resolution**: rate vs temporal codes are not mutually exclusive. They correspond to **different "
            "stimulus regimes** of the SAME neurons — fluctuating stimuli engage temporal codes, slow stimuli "
            "engage rate codes. **Multiplexed coding** (Panzeri et al. 2010) is the modern synthesis: the same "
            "spike train carries fast (temporal) and slow (rate) information *simultaneously*."
        ),
        "rationale_md": (
            "**Common error**: citing Mainen & Sejnowski as proof that cortex uses a temporal code — it doesn't. "
            "It only proves the **mechanism** (deterministic transformation). Whether the *brain* exploits this "
            "is a separate question, addressed later by phase coding (O'Keefe), spike-timing precision "
            "(Reinagel & Reid 2000), and information-theoretic decoding studies. **Cross-link**: this is "
            "directly analogous to **Lyapunov-stability** vs **chaotic** regimes in dynamical systems — "
            "fluctuating inputs put the neuron in its locally stable manifold, DC inputs put it on a chaotic "
            "limit cycle. Same neuron, two completely different dynamical signatures."
        ),
        "source_citation": {"kind": "slide", "lecture": "L8", "page": 28,
                             "primary": "Mainen & Sejnowski 1995 Science 268:1503; Panzeri et al. 2010 Trends Neurosci 33:111"},
        "priority_score": 0.96, "info_density": 0.93, "mastery_target": "code_determinism",
    },
    {
        "topic": "neural_codes", "card_type": "application", "difficulty": 5, "bloom": "Apply",
        "prompt_md": (
            "**Setup.** You record from $N = 50$ V1 neurons with overlapping orientation tuning curves "
            "$f_i(\\theta) = R_\\text{max} \\exp(-(\\theta - \\theta_i)^2 / 2\\sigma^2)$, $\\sigma = 10°$, "
            "preferred orientations $\\theta_i$ uniformly tiled over $[-90°, +90°]$. Spike counts in a 100 ms "
            "window are Poisson-distributed.\n\n"
            "(a) Derive the **maximum likelihood estimator** $\\hat\\theta_{ML}$ from observed spike counts "
            "$\\{n_i\\}$. State the closed-form when applicable.\n"
            "(b) Derive the **Cramér-Rao lower bound** on $\\text{Var}(\\hat\\theta)$ — the **Fisher "
            "information** $J(\\theta)$. Show that for this tuning-curve form, $J(\\theta) = N R_\\text{max} / (2\\sigma^2)$ "
            "asymptotically (uniform tiling).\n"
            "(c) Use (b) to compute the predicted angular precision (in degrees) for $R_\\text{max} = 50$ Hz, "
            "100 ms window. Compare to human psychophysical orientation discrimination (~1° at high contrast). "
            "What does the comparison imply about V1's role in perception?"
        ),
        "answer_md": (
            "(a) Poisson likelihood: $L(\\theta) = \\prod_i f_i(\\theta)^{n_i} e^{-f_i(\\theta)} / n_i!$.\n"
            "Log-likelihood: $\\ell(\\theta) = \\sum_i [n_i \\ln f_i(\\theta) - f_i(\\theta)] + \\text{const}$.\n"
            "Substituting Gaussian tuning: $\\ln f_i(\\theta) = \\ln R_\\text{max} - (\\theta - \\theta_i)^2/(2\\sigma^2)$.\n"
            "$$\\ell(\\theta) = -\\frac{1}{2\\sigma^2} \\sum_i n_i (\\theta - \\theta_i)^2 - \\sum_i f_i(\\theta) + \\text{const}.$$\n"
            "$\\partial \\ell / \\partial \\theta = -\\frac{1}{\\sigma^2} \\sum_i n_i (\\theta - \\theta_i) - \\sum_i f_i'(\\theta) = 0$.\n"
            "For uniform tiling and large $N$, $\\sum_i f_i(\\theta) \\approx \\text{const}$ so $\\sum_i f_i'(\\theta) \\approx 0$.\n"
            "Closed form: $\\hat\\theta_{ML} = \\sum_i n_i \\theta_i / \\sum_i n_i$ — **population vector** (centroid of activity).\n\n"
            "(b) Fisher information: $J(\\theta) = -\\langle \\partial^2 \\ell / \\partial \\theta^2 \\rangle$.\n"
            "$\\partial^2 \\ell / \\partial \\theta^2 = -\\frac{1}{\\sigma^2} \\sum_i n_i + \\sum_i f_i''(\\theta) - \\sum_i (f_i')^2 / f_i$.\n"
            "Take expectation $\\langle n_i \\rangle = f_i(\\theta) \\Delta t$ (assume $\\Delta t = 1$ for simplicity):\n"
            "$\\langle \\partial^2 \\ell / \\partial \\theta^2 \\rangle = -\\frac{1}{\\sigma^2} \\sum_i f_i(\\theta) + \\sum_i f_i''(\\theta) - \\sum_i (f_i')^2/f_i$.\n"
            "For Gaussian: $f_i' = -f_i (\\theta-\\theta_i)/\\sigma^2$, $(f_i')^2 / f_i = f_i (\\theta-\\theta_i)^2/\\sigma^4$.\n"
            "Uniform tiling: $\\sum_i f_i(\\theta) \\approx N \\langle f \\rangle = N R_\\text{max} \\sqrt{2\\pi}\\sigma / 180°$ (proportional to $N$).\n"
            "$\\sum_i (f_i')^2/f_i = N R_\\text{max} \\sqrt{2\\pi}\\sigma /180° \\cdot 1/(2\\sigma^2)$ (Gaussian moment).\n"
            "Combining: $J(\\theta) \\approx N R_\\text{max} / (2 \\sigma^2) \\cdot \\Delta t$ (with appropriate normalization).\n\n"
            "(c) Numerics: $\\Delta t = 0.1$ s, $R_\\text{max} = 50$ Hz, $\\sigma = 10°$, $N = 50$.\n"
            "$J = 50 \\cdot 50 \\cdot 0.1 / (2 \\cdot 100) = 250 / 200 = 1.25$ deg$^{-2}$.\n"
            "$\\text{SD}(\\hat\\theta) \\geq 1/\\sqrt{J} = 1/\\sqrt{1.25} \\approx 0.9°$.\n\n"
            "**Comparison**: psychophysical threshold ~1°, theoretical CRLB ~0.9°. **Implication**: V1's coding "
            "*is* sufficient for the behavioral threshold — perception is **information-limited** by the V1 "
            "encoding, not by downstream decoding. (This is the famous result of Pouget, Latham et al. 1998-2000 "
            "on **information-limiting noise** and population coding.)"
        ),
        "rationale_md": (
            "**Common error**: forgetting that Fisher information **scales with $N$ and observation time $\\Delta t$**. "
            "Both linearly. **Common error 2**: assuming the population-vector estimator (eq. (a) closed form) is "
            "always optimal — it's optimal here because of Gaussian tuning + Poisson + uniform tiling. With "
            "**non-uniform tuning** or **correlated noise** (Abbott & Dayan 1999), it fails and one must use "
            "the full $\\hat\\theta_{ML}$ inversion or a Bayesian decoder. **Cross-link**: the analytical CRLB "
            "is the **information-theoretic ceiling**; it tightly matches behavior in early visual areas, but "
            "fails for higher cortex where decoding noise dominates. This is the entry point to "
            "**Limited-Information** vs **Information-limiting** noise distinction (Moreno-Bote et al. 2014)."
        ),
        "source_citation": {"kind": "slide", "lecture": "L8", "page": 56,
                             "primary": "Pouget, Zhang, Deneve, Latham 1998 Neural Comput 10:373; Abbott & Dayan 1999 Neural Comput 11:91"},
        "priority_score": 0.97, "info_density": 0.97, "mastery_target": "population_decoding",
    },
    {
        "topic": "neural_codes", "card_type": "proof", "difficulty": 5, "bloom": "Evaluate",
        "prompt_md": (
            "**Setup.** Place cells in hippocampus exhibit **theta phase precession**: as a rat traverses the "
            "place field, the cell fires at progressively earlier phases of the local theta rhythm "
            "(O'Keefe & Recce 1993).\n\n"
            "(a) Show that phase precession enables a **dual code**: the firing rate encodes spatial position "
            "(rate code) AND the phase encodes position **within the theta cycle** (temporal code). Formalize "
            "the **information capacity** advantage of dual coding using mutual information.\n"
            "(b) Identify a **fundamental constraint** on dual coding: what limits how much extra information "
            "phase can carry beyond rate? Connect this to spike-timing reliability and the time bin necessary "
            "to estimate phase from a single spike train.\n"
            "(c) Argue whether the experimental observations of phase precession are **sufficient evidence** "
            "to conclude the brain *uses* a phase code — i.e., distinguish 'phase precession is observed' from "
            "'phase precession is causally read by downstream neurons.'"
        ),
        "answer_md": (
            "(a) Mutual information additivity (chain rule):\n"
            "$$I(X; \\text{rate}, \\text{phase}) = I(X; \\text{rate}) + I(X; \\text{phase} | \\text{rate}).$$\n"
            "If phase carries information **conditionally independent** of rate (e.g., phase encodes within-field "
            "position while rate encodes which field is active), the second term is positive — net information "
            "**strictly exceeds** what either code alone provides.\n"
            "Specifically: rate code over a 1m place field gives $\\log_2(\\text{field/precision}) \\approx 4$ bits "
            "(20cm precision). Phase code over $360°$ at 5° precision gives $\\log_2(72) \\approx 6$ bits — but **only "
            "the information that's orthogonal to rate**. Empirical: Skaggs & McNaughton 1996 estimated phase "
            "adds ~2× the rate-code information for hippocampal CA1.\n\n"
            "(b) **Constraint**: phase estimation requires sampling the spike enough to localize it within the "
            "theta cycle ($\\sim$125 ms at 8 Hz). With only **1 spike per cycle** (typical for place cells), the "
            "phase can be estimated to **the precision of the spike-time jitter divided by theta period**. If "
            "spike jitter is $\\sigma_t \\sim 5$ ms and theta period $T_\\theta = 125$ ms, phase precision = "
            "$5/125 \\cdot 360° = 14°$. This caps phase information at $\\log_2(360/14) \\approx 4.7$ bits. "
            "Achievable but tight.\n\n"
            "Deeper constraint: **spike-rate vs precision trade-off**. To get 1 ms phase precision, you'd need "
            "many spikes per cycle — but place cells fire 1-5 spikes per cycle, and increasing spike rate "
            "saturates. Information-theoretic limit (Strong et al. 1998; Brenner et al. 2000): the **direct "
            "method** estimate of $I(X; \\text{phase})$ depends on spike count and bin width, with a "
            "non-trivial bias correction.\n\n"
            "(c) **Sufficient evidence?** No, not on its own. Phase precession is observed *correlationally* — "
            "we see phases progress as position changes. But to argue the brain **uses** phase, one needs:\n"
            "  - Decoding from downstream populations (e.g., entorhinal cortex) that explicitly *requires* phase "
            "    info to predict behavior — Foster & Wilson 2007 showed sequence replay during sharp-wave-ripples "
            "    has phase information correlated with goal-directed behavior.\n"
            "  - Causal manipulation: optogenetic disruption of theta phase but not rate. Robbe et al. 2006 "
            "    cannabinoid experiments show theta disruption impairs spatial memory **without** changing "
            "    place-cell rates — strong causal evidence.\n"
            "  - Theoretical frameworks: **temporal-context** models (Howard & Eichenbaum 2002) predict phase "
            "    code is necessary for sequence learning, then confirmed by experiment.\n\n"
            "Without these complementary lines, phase precession alone is consistent with phase being **epi-phenomenal** — "
            "a side-effect of dendritic-soma input timing, not a causally read signal."
        ),
        "rationale_md": (
            "**Common error**: equating *correlation* (phase precession) with *causation* (phase is decoded). "
            "This is the major fault-line in coding-vs-readout debates. **Common error 2**: ignoring the "
            "**spike-count constraint** on phase precision — students often compute information bounds without "
            "checking the spike-time variance budget. **Cross-link**: the rate-vs-phase tension is structurally "
            "the same as **AM vs FM** modulation in radio — same carrier, different information channels, "
            "different decoders. The brain may use either, both, or neither depending on circuit context."
        ),
        "source_citation": {"kind": "slide", "lecture": "L8", "page": 62,
                             "primary": "O'Keefe & Recce 1993 Hippocampus 3:317; Robbe, Montgomery, Thomé, Rueda-Orozco, McNaughton, Buzsáki 2006 Nat Neurosci 9:1526"},
        "priority_score": 0.97, "info_density": 0.97, "mastery_target": "phase_coding",
    },
]


# ──────────────────────────────────────────────────────────────────
# Insert / replace bank + register SRS cards
# ──────────────────────────────────────────────────────────────────

def insert_bank_items(items: list[dict], replace: bool = True) -> list[int]:
    conn = acquire()
    inserted_ids: list[int] = []
    try:
        with conn.cursor() as cur:
            if replace:
                # Drop dependent srs_cards then bank items
                cur.execute("DELETE FROM srs_reviews WHERE card_id IN (SELECT id FROM srs_cards WHERE user_id = 1)")
                cur.execute("DELETE FROM srs_cards WHERE user_id = 1")
                cur.execute("DELETE FROM question_bank")
                # Re-zero the sequence (Postgres-specific)
                cur.execute("ALTER SEQUENCE question_bank_id_seq RESTART WITH 1")
                cur.execute("ALTER SEQUENCE srs_cards_id_seq RESTART WITH 1")

            for it in items:
                cur.execute("""
                    INSERT INTO question_bank
                      (topic, card_type, difficulty, bloom, prompt_md, answer_md,
                       rationale_md, source_citation, priority_score, info_density,
                       mastery_target, status)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,'active')
                    RETURNING id
                """, (
                    it["topic"], it["card_type"], it["difficulty"], it["bloom"],
                    it["prompt_md"], it["answer_md"], it["rationale_md"],
                    json.dumps(it["source_citation"], ensure_ascii=False),
                    it["priority_score"], it["info_density"],
                    it.get("mastery_target"),
                ))
                inserted_ids.append(cur.fetchone()[0])
        conn.commit()
    finally:
        release(conn)
    return inserted_ids


def register_srs(user_id: int, bank_ids: list[int]) -> int:
    conn = acquire()
    n = 0
    try:
        with conn.cursor() as cur:
            for bid in bank_ids:
                cur.execute("""
                    INSERT INTO srs_cards (user_id, bank_item_id, state)
                    VALUES (%s,%s,'New')
                    ON CONFLICT (user_id, bank_item_id) DO NOTHING
                """, (user_id, bid))
                n += cur.rowcount or 0
        conn.commit()
    finally:
        release(conn)
    return n


async def review_with_multi_lens(items: list[dict]) -> list[dict]:
    """Optional: run each item through Multi-Lens once. Marks rejected as 'manual_review'."""
    from review import multi_lens_review, Artifact
    out: list[dict] = []
    for it in items:
        a = Artifact(
            kind="question",
            text=f"문항: {it['prompt_md']}\n\n정답: {it['answer_md']}\n\n해설: {it['rationale_md']}",
            citation=it["source_citation"],
            declared_difficulty=it["difficulty"],
            declared_bloom=it["bloom"],
        )
        res = await multi_lens_review(a, max_rounds=2)
        out.append({**it, "_review_status": res.status, "_review_rounds": res.rounds})
        print(f"  [{it['topic']:>14s} {it['card_type']:>11s} d={it['difficulty']}] → "
              f"{res.status:>15} ({res.rounds}r, {res.elapsed_ms} ms)")
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--review", action="store_true",
                   help="run Multi-Lens Review on each item before insert (uses LLM credits)")
    p.add_argument("--user-id", type=int, default=1)
    p.add_argument("--keep", action="store_true", help="keep existing bank rows, append")
    args = p.parse_args()

    items = SEEDS
    print(f"Seeding {len(items)} PhD-level bank items …")
    if args.review:
        if not os.environ.get("OPENROUTER_API_KEY"):
            print("WARN: OPENROUTER_API_KEY not set; Multi-Lens will fall back to local Ollama or fail")
        items = asyncio.run(review_with_multi_lens(items))
        n_manual = sum(1 for it in items if it.get("_review_status") == "manual_review")
        print(f"  {n_manual} items flagged for manual review (kept active for now)")

    bank_ids = insert_bank_items(items, replace=not args.keep)
    print(f"  inserted {len(bank_ids)} bank rows")
    n_cards = register_srs(args.user_id, bank_ids)
    print(f"  registered {n_cards} SRS cards for user_id={args.user_id}")

    print("\nTopic × type coverage:")
    by_topic: dict[str, dict[str, int]] = {}
    for it in items:
        by_topic.setdefault(it["topic"], {}).setdefault(it["card_type"], 0)
        by_topic[it["topic"]][it["card_type"]] += 1
    for topic, types in by_topic.items():
        print(f"  {topic:>14}: {types}")


if __name__ == "__main__":
    main()
