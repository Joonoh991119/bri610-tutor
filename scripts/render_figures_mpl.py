#!/usr/bin/env python3
"""
BRI610 lecture figures — publication-grade SVG renderer (Tol BRIGHT palette).

Generates 16 SVGs in frontend/public/figures/ using a strict Tol-BRIGHT
colorblind-safe palette, semantic per-figure color assignment, redundant
line-style encoding (solid/dashed/dotted), and zero-rotation horizontal
text labels (y-axis labels become ax.text() above the y-axis column).

Run: python3 scripts/render_figures_mpl.py
"""
from __future__ import annotations

import math
import os
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import (
    FancyArrowPatch, FancyBboxPatch, Rectangle, Circle, Polygon,
    Ellipse, Wedge, ConnectionPatch,
)
from matplotlib.lines import Line2D
import numpy as np

# ---------------------------------------------------------------------------
# Palette — Tol BRIGHT (Nature Neurosci / iScience standard, colorblind-safe)
# Plus GitHub-style neutrals.  Total: 10 hex codes, no others permitted.
# ---------------------------------------------------------------------------
BRI610 = {
    # Tol BRIGHT semantic colors
    'blue':      '#4477AA',  # voltage / Na+ / depolarization
    'cyan':      '#66CCEE',  # K+ / repolarization / equilibrium
    'red':       '#EE6677',  # inactivation / refractory / warning
    'green':     '#228833',  # passive / extracellular / gradient
    'yellow':    '#CCBB44',  # SINGLE answer-point callout per figure
    # Neutrals (GitHub-style)
    'ink':       '#1f2328',
    'ink_dim':   '#57606a',
    'ink_faint': '#8c959f',
    'paper':     '#fafbfc',
    'rule_soft': '#d0d7de',
}

# Convenience alias for rule (visual ticks/baselines)
BRI610['rule'] = BRI610['rule_soft']

OUT_DIR = Path('/Users/joonoh/Projects/bri610-tutor/frontend/public/figures')
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Deterministic font-cache and rendering for idempotency
os.environ.setdefault('SOURCE_DATE_EPOCH', '1700000000')


def apply_bri610_style() -> None:
    mpl.rcdefaults()
    mpl.rcParams.update({
        'figure.dpi': 100,
        'figure.facecolor': BRI610['paper'],
        'figure.autolayout': False,
        'savefig.facecolor': BRI610['paper'],
        'savefig.edgecolor': 'none',
        'savefig.format': 'svg',
        'svg.fonttype': 'path',
        'svg.hashsalt': 'bri610-figures-v2',
        'font.family': 'DejaVu Sans',
        'font.size': 8.5,
        'axes.facecolor': BRI610['paper'],
        'axes.edgecolor': BRI610['ink_dim'],
        'axes.labelcolor': BRI610['ink'],
        'axes.titlecolor': BRI610['ink'],
        'axes.linewidth': 0.7,
        'axes.labelsize': 9,
        'axes.titlesize': 9.5,
        'axes.titlepad': 14,  # extra room for the horizontal y-label
        'axes.labelpad': 4,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.titleweight': 'normal',
        'axes.labelweight': 'normal',
        'xtick.color': BRI610['ink_dim'],
        'ytick.color': BRI610['ink_dim'],
        'xtick.labelcolor': BRI610['ink'],
        'ytick.labelcolor': BRI610['ink'],
        'xtick.labelsize': 7.5,
        'ytick.labelsize': 7.5,
        'xtick.direction': 'out',
        'ytick.direction': 'out',
        'xtick.major.size': 3,
        'ytick.major.size': 3,
        'xtick.major.width': 0.6,
        'ytick.major.width': 0.6,
        'lines.linewidth': 1.6,
        'legend.fontsize': 7.5,
        'legend.frameon': False,
        'legend.borderaxespad': 0.4,
        'legend.handlelength': 2.2,
        'legend.handletextpad': 0.6,
        'mathtext.fontset': 'dejavusans',
        'mathtext.default': 'it',
    })


# ---------------------------------------------------------------------------
# Horizontal y-label helper — replaces ax.set_ylabel()
# Places `text` ABOVE the top of the y-axis, horizontal (no rotation),
# left-aligned with the y-axis spine.
# ---------------------------------------------------------------------------
def hlabel_y(ax, text: str, *, dy: float = 0.012, fontsize: float = 9,
             color: str | None = None, ha: str = 'left'):
    """Horizontal y-axis label — drawn above the top tick, in axes-fraction."""
    if color is None:
        color = BRI610['ink_dim']
    # x just left of the data column (slightly outside the spine, near tick label width)
    ax.text(0.0, 1.0 + dy, text, transform=ax.transAxes,
            ha=ha, va='bottom', fontsize=fontsize, color=color, rotation=0)


# ---------------------------------------------------------------------------
# Overlap checking & save helper
# ---------------------------------------------------------------------------
def _tick_label_ids(fig) -> set:
    ids = set()
    for ax in fig.get_axes():
        for axis in (ax.xaxis, ax.yaxis):
            for tick in axis.get_major_ticks() + axis.get_minor_ticks():
                ids.add(id(tick.label1))
                ids.add(id(tick.label2))
    return ids


def collect_text_bboxes(fig, include_ticks=False):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    tick_ids = set() if include_ticks else _tick_label_ids(fig)
    items = []
    seen = set()
    for t in fig.findobj(mpl.text.Text):
        s = (t.get_text() or '').strip()
        if not s:
            continue
        if not t.get_visible():
            continue
        if id(t) in tick_ids:
            continue
        if id(t) in seen:
            continue
        seen.add(id(t))
        try:
            bb = t.get_window_extent(renderer)
        except Exception:
            continue
        if bb.width <= 0 or bb.height <= 0:
            continue
        items.append((t, bb, s))
    return items


def check_overlaps(fig, ignore_substrings=(), allow_duplicates=()):
    items = collect_text_bboxes(fig)
    pairs = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            ti, bi, si = items[i]
            tj, bj, sj = items[j]
            if any(ig in si or ig in sj for ig in ignore_substrings):
                continue
            if si == sj and si in allow_duplicates:
                continue
            if bi.overlaps(bj):
                pairs.append((si, sj))
    return pairs


def count_yellow(fig) -> int:
    count = 0
    target = BRI610['yellow'].lower()
    for art in fig.findobj(mpl.text.Text):
        try:
            hex_c = mpl.colors.to_hex(art.get_color()).lower()
        except Exception:
            continue
        if hex_c == target and (art.get_text() or '').strip():
            count += 1
    return count


def save(fig, name: str):
    path = OUT_DIR / name
    fig.savefig(path, format='svg', bbox_inches='tight', pad_inches=0.1)
    return path


# ---------------------------------------------------------------------------
# Helper: schematic axes
# ---------------------------------------------------------------------------
def schematic_ax(fig, xlim=(0, 100), ylim=(0, 60)):
    ax = fig.add_subplot(111)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect('auto')
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_facecolor(BRI610['paper'])
    return ax


# ===========================================================================
# GROUP A — DATA PLOTS
# ===========================================================================

def fig_rc_charging():
    fig, ax = plt.subplots(figsize=(6, 3.6))
    tau = 1.0
    t = np.linspace(0, 5 * tau, 400)
    V = 1 - np.exp(-t / tau)
    # BLUE solid V curve
    ax.plot(t, V, color=BRI610['blue'], linewidth=1.8, linestyle='-',
            label=r'$V(t)=V_\infty(1-e^{-t/\tau})$')

    # tangent at origin — INK_FAINT dashed
    tt = np.linspace(0, 1.05 * tau, 50)
    ax.plot(tt, tt, color=BRI610['ink_faint'], linewidth=0.9,
            linestyle=(0, (4, 3)),
            label=r'tangent at $t=0$')

    # Slope label with leader, horizontal
    ax.annotate('initial slope = 1/τ', xy=(0.55, 0.55),
                xytext=(1.4, 0.20), ha='left', va='center',
                color=BRI610['ink_dim'], fontsize=8,
                arrowprops=dict(arrowstyle='-', color=BRI610['ink_faint'], lw=0.6))

    # tau marker — guide lines
    ax.axvline(tau, ymin=0, ymax=(0.63 / 1.05), color=BRI610['ink_faint'],
               linewidth=0.7, linestyle=(0, (2, 2)))
    ax.axhline(0.63, xmin=0, xmax=tau / (5 * tau), color=BRI610['ink_faint'],
               linewidth=0.7, linestyle=(0, (2, 2)))
    # YELLOW marker at (τ, 0.63)
    ax.plot([tau], [0.63], marker='o', markersize=5.5, color=BRI610['yellow'],
            markeredgecolor=BRI610['ink'], markeredgewidth=0.6, zorder=5)

    ax.text(tau, -0.04, r'$\tau$', ha='center', va='top', color=BRI610['ink'])
    ax.text(-0.06, 0.63, '0.63', ha='right', va='center', color=BRI610['ink'])
    ax.text(5 * tau, 1.0, r'$V_\infty$', ha='right', va='bottom',
            color=BRI610['ink_dim'])
    ax.axhline(1.0, color=BRI610['rule_soft'], linewidth=0.5, linestyle=(0, (1, 3)))

    ax.set_xlim(0, 5 * tau)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel('time')
    hlabel_y(ax, r'$V(t)\,/\,V_\infty$')
    ax.set_title('RC membrane charging')
    ax.set_xticks([0, tau, 2 * tau, 3 * tau, 4 * tau, 5 * tau])
    ax.set_xticklabels(['0', r'$\tau$', r'$2\tau$', r'$3\tau$', r'$4\tau$', r'$5\tau$'])
    ax.legend(loc='lower right', frameon=False)
    fig.tight_layout(pad=0.6)
    return fig


def fig_ohmic_iv():
    fig, ax = plt.subplots(figsize=(6, 3.6))
    g = 0.05
    Ex = -75.0
    V = np.linspace(-100, 50, 200)
    I = g * (V - Ex)
    ax.plot(V, I, color=BRI610['blue'], linewidth=1.8, linestyle='-',
            label=r'$I_X = g_X(V - E_X)$')

    ax.axhline(0, color=BRI610['rule_soft'], linewidth=0.6)
    ax.axvline(0, color=BRI610['rule_soft'], linewidth=0.6)

    # YELLOW marker at E_X intercept
    ax.plot([Ex], [0], marker='o', markersize=5.5, color=BRI610['yellow'],
            markeredgecolor=BRI610['ink'], markeredgewidth=0.6, zorder=5)
    ax.annotate(r'$E_X = -75\,\mathrm{mV}$', xy=(Ex, 0),
                xytext=(Ex + 12, -1.6),
                ha='left', va='top', color=BRI610['ink'],
                arrowprops=dict(arrowstyle='-', color=BRI610['ink_faint'], lw=0.6))

    # slope label, horizontal, with leader
    ax.annotate(r'slope $= g_X$', xy=(20, g * (20 - Ex)),
                xytext=(-90, 3.3), ha='left', va='center',
                color=BRI610['ink_dim'], fontsize=8,
                arrowprops=dict(arrowstyle='-', color=BRI610['ink_faint'], lw=0.6))

    ax.set_xlim(-100, 50)
    ax.set_ylim(-5, 5)
    ax.set_xlabel(r'$V$  (mV)')
    hlabel_y(ax, r'$I$  (a.u.)')
    ax.set_title('Ohmic ionic current')
    ax.legend(loc='lower right', frameon=False)
    fig.tight_layout(pad=0.6)
    return fig


def fig_action_potential_phases():
    fig, ax = plt.subplots(figsize=(6, 3.6))
    t = np.linspace(0, 6, 1200)
    V_rest = -65.0
    rise = np.exp(-((t - 1.6) ** 2) / (2 * 0.18 ** 2)) * 95
    ahp = -np.exp(-((t - 2.6) ** 2) / (2 * 0.45 ** 2)) * 18
    V = V_rest + rise + ahp
    # BLUE solid V_m
    ax.plot(t, V, color=BRI610['blue'], linewidth=1.8, linestyle='-')

    # E_Na — BLUE-faded dashed (top)
    ax.axhline(58, color=BRI610['blue'], linewidth=0.8,
               linestyle=(0, (4, 3)), alpha=0.45)
    # E_K — CYAN-faded dashed (bottom)
    ax.axhline(-83, color=BRI610['cyan'], linewidth=0.8,
               linestyle=(0, (4, 3)), alpha=0.65)
    ax.text(5.95, 58, r'$E_{Na}\,=\,+58$', ha='right', va='bottom',
            color=BRI610['ink_dim'])
    ax.text(5.95, -83, r'$E_K\,=\,-83$', ha='right', va='top',
            color=BRI610['ink_dim'])

    # Threshold-cross detection (V crosses ~ -55 going up)
    threshold = -55.0
    cross_idx = None
    for i in range(1, len(V)):
        if V[i - 1] < threshold <= V[i]:
            cross_idx = i
            break
    if cross_idx is not None:
        # YELLOW dot at threshold cross — the answer-point
        ax.plot([t[cross_idx]], [V[cross_idx]], marker='o', markersize=6,
                color=BRI610['yellow'],
                markeredgecolor=BRI610['ink'], markeredgewidth=0.6, zorder=6)
        ax.annotate('threshold', xy=(t[cross_idx], V[cross_idx]),
                    xytext=(0.25, -90),
                    ha='left', va='center', color=BRI610['ink'], fontsize=8,
                    arrowprops=dict(arrowstyle='-', color=BRI610['ink_faint'], lw=0.6))

    # Phase labels — staggered (avoid threshold annotation column at t≈1.45)
    phase_labels = [
        (0.6, -30, 'rest'),
        (1.6, 8, 'rise'),
        (1.95, 40, 'peak'),
        (3.1, -55, 'AHP'),
        (4.7, -45, 'return'),
    ]
    for xv, yv, lbl in phase_labels:
        ax.text(xv, yv, lbl, ha='center', va='center', color=BRI610['ink'],
                fontsize=8, bbox=dict(boxstyle='round,pad=0.18',
                                      facecolor=BRI610['paper'],
                                      edgecolor=BRI610['rule_soft'], linewidth=0.5))

    ax.set_xlim(0, 6)
    ax.set_ylim(-100, 60)
    ax.set_xlabel('time (ms)')
    hlabel_y(ax, r'$V_m$  (mV)')
    ax.set_title('Action potential phases')
    fig.tight_layout(pad=0.6)
    return fig


def boltz(V, V12, k):
    return 1.0 / (1.0 + np.exp(-(V - V12) / k))


def fig_hh_gating():
    fig, ax = plt.subplots(figsize=(6, 3.6))
    V = np.linspace(-100, 50, 400)
    m_inf = boltz(V, -40, 7.0)
    h_inf = 1 - boltz(V, -62, 6.0)
    n_inf = boltz(V, -53, 12.0)

    # Redundant encoding: solid / dashed / dotted
    ax.plot(V, m_inf, color=BRI610['blue'], linewidth=1.8, linestyle='-',
            label=r'$m_\infty(V)$  (Na$^+$ activation)')
    ax.plot(V, h_inf, color=BRI610['red'], linewidth=1.8, linestyle=(0, (5, 3)),
            label=r'$h_\infty(V)$  (Na$^+$ inactivation)')
    ax.plot(V, n_inf, color=BRI610['cyan'], linewidth=1.8, linestyle=(0, (1.4, 2.2)),
            label=r'$n_\infty(V)$  (K$^+$ activation)')

    ax.set_xlim(-100, 50)
    ax.set_ylim(-0.02, 1.05)
    ax.set_xlabel(r'$V$  (mV)')
    hlabel_y(ax, 'steady-state activation')
    ax.set_title('Hodgkin–Huxley gating variables')
    ax.legend(loc='center right', frameon=False)
    fig.tight_layout(pad=0.6)
    return fig


def fig_voltage_clamp():
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 3.6),
                                    gridspec_kw={'height_ratios': [1, 1.3], 'hspace': 0.55})
    t = np.linspace(0, 10, 1000)
    Vcmd = np.where(t < 2, -80, 20)
    Vcmd = np.where(t > 8, -80, Vcmd)
    # BLUE V_clamp
    ax1.plot(t, Vcmd, color=BRI610['blue'], linewidth=1.6, linestyle='-')
    ax1.set_ylim(-100, 40)
    hlabel_y(ax1, r'$V_{clamp}$  (mV)')
    ax1.set_title('Voltage-clamp protocol & response')
    ax1.set_xticklabels([])
    ax1.set_xlim(0, 10)
    ax1.text(0.4, -80, '−80 mV hold', va='bottom', ha='left',
             color=BRI610['ink_dim'], fontsize=7.5)
    ax1.text(5, 20, '+20 mV step', va='bottom', ha='center',
             color=BRI610['ink_dim'], fontsize=7.5)

    # YELLOW vertical step-onset lines in BOTH panels
    ax1.axvline(2, color=BRI610['yellow'], linewidth=1.2)
    ax2.axvline(2, color=BRI610['yellow'], linewidth=1.2)

    # Decompose response into Na transient (RED) and K plateau (CYAN), plotted separately
    mask = t >= 2
    tau_na = 0.25
    tau_k = 1.4
    I_na = np.zeros_like(t)
    I_k = np.zeros_like(t)
    I_na[mask] = (-3.5) * np.exp(-(t[mask] - 2) / tau_na) * (t[mask] - 2) / tau_na * np.exp(1)
    I_k[mask] = 2.4 * (1 - np.exp(-(t[mask] - 2) / tau_k))
    end_mask = t >= 8
    last_idx = np.argmax(t >= 8) - 1
    I_na[end_mask] = I_na[last_idx] * np.exp(-(t[end_mask] - 8) / 0.4)
    I_k[end_mask] = I_k[last_idx] * np.exp(-(t[end_mask] - 8) / 0.4)
    ax2.plot(t, I_na, color=BRI610['red'], linewidth=1.6, linestyle=(0, (5, 3)),
             label=r'$I_{Na}$  transient')
    ax2.plot(t, I_k, color=BRI610['cyan'], linewidth=1.6, linestyle=(0, (1.4, 2.2)),
             label=r'$I_K$  plateau')
    ax2.axhline(0, color=BRI610['rule_soft'], linewidth=0.6)
    ax2.set_xlim(0, 10)
    ax2.set_ylim(-4, 3.2)
    ax2.set_xlabel('time (ms)')
    hlabel_y(ax2, r'$I$  (a.u.)')
    ax2.legend(loc='lower right', frameon=False, fontsize=7)
    fig.tight_layout(pad=0.6)
    return fig


def fig_cable_decay():
    fig, ax = plt.subplots(figsize=(6, 3.6))
    x = np.linspace(0, 5, 400)
    V = np.exp(-x)
    # BLUE solid
    ax.plot(x, V, color=BRI610['blue'], linewidth=1.8, linestyle='-',
            label=r'$V(x)/V_0 = e^{-x/\lambda}$')

    # YELLOW marker at (1, 1/e ≈ 0.37)
    ax.plot([1], [1 / np.e], marker='o', markersize=5.5,
            color=BRI610['yellow'],
            markeredgecolor=BRI610['ink'], markeredgewidth=0.6, zorder=5)
    # Secondary marker at 2λ — neutral ink to keep yellow as the singular callout
    ax.plot([2], [1 / np.e ** 2], marker='o', markersize=4.5,
            color=BRI610['ink_faint'],
            markeredgecolor=BRI610['ink_dim'], markeredgewidth=0.5, zorder=4)

    ax.annotate(r'$1/e$  at $x=\lambda$', xy=(1, 1 / np.e),
                xytext=(1.5, 0.82), color=BRI610['ink'],
                arrowprops=dict(arrowstyle='-', color=BRI610['ink_faint'], lw=0.6))
    ax.annotate(r'$1/e^{2}$  at $x=2\lambda$', xy=(2, 1 / np.e ** 2),
                xytext=(3.0, 0.32), color=BRI610['ink_dim'],
                arrowprops=dict(arrowstyle='-', color=BRI610['ink_faint'], lw=0.6))

    ax.set_xlim(0, 5)
    ax.set_ylim(0, 1.05)
    ax.set_xticks([0, 1, 2, 3, 4, 5])
    ax.set_xticklabels(['0', r'$\lambda$', r'$2\lambda$', r'$3\lambda$', r'$4\lambda$', r'$5\lambda$'])
    ax.set_xlabel(r'distance  $x/\lambda$')
    hlabel_y(ax, r'$V(x)/V_0$')
    ax.set_title('Passive cable: spatial decay')
    ax.legend(loc='upper right', frameon=False)
    fig.tight_layout(pad=0.6)
    return fig


def fig_ghk_bars():
    fig, ax = plt.subplots(figsize=(6, 3.6))
    perms = [r'$P_K$', r'$P_{Na}$', r'$P_{Cl}$']
    ratios = [1.0, 0.04, 0.45]
    # P_K → CYAN (K+), P_Na → BLUE (Na+), P_Cl → GREEN (passive)
    colors = [BRI610['cyan'], BRI610['blue'], BRI610['green']]
    bars = ax.bar(perms, ratios, color=colors, width=0.55,
                  edgecolor=BRI610['ink_dim'], linewidth=0.6)
    # YELLOW outline highlight on dominant P_K
    bars[0].set_edgecolor(BRI610['yellow'])
    bars[0].set_linewidth(2.4)

    for bar, val in zip(bars, ratios):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.02, f'{val:g}',
                ha='center', va='bottom', color=BRI610['ink'], fontsize=8)
    ax.set_xticks(range(3))
    ax.set_xticklabels(perms)
    hlabel_y(ax, 'relative permeability  (rest)')
    ax.set_ylim(0, 1.18)
    ax.set_title(r'GHK weighted permeabilities — $P_K$ dominates at rest')

    formula = (r'$V_m=\dfrac{RT}{F}\,\ln\dfrac{P_K[K]_o+P_{Na}[Na]_o+P_{Cl}[Cl]_i}'
               r'{P_K[K]_i+P_{Na}[Na]_i+P_{Cl}[Cl]_o}$')
    ax.text(0.5, -0.32, formula, transform=ax.transAxes,
            ha='center', va='top', color=BRI610['ink'], fontsize=8.5,
            bbox=dict(boxstyle='round,pad=0.5',
                      facecolor=BRI610['paper'],
                      edgecolor=BRI610['rule_soft'], linewidth=0.5))
    fig.tight_layout(pad=0.6)
    fig.subplots_adjust(bottom=0.30)
    return fig


def fig_rate_vs_temporal():
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 3.6),
                                    gridspec_kw={'height_ratios': [1, 1], 'hspace': 0.65})
    rate_times = np.linspace(0.07, 0.93, 5)
    temp_times = np.array([0.05, 0.13, 0.27, 0.55, 0.92])

    # INK rasters for both
    for tspk in rate_times:
        ax1.vlines(tspk, 0, 1, color=BRI610['ink'], linewidth=1.4)
    for tspk in temp_times:
        ax2.vlines(tspk, 0, 1, color=BRI610['ink'], linewidth=1.4)

    for ax, label in ((ax1, 'rate code (regular)'),
                      (ax2, 'temporal code (precise ISIs)')):
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_yticks([])
        for s in ('top', 'right', 'left'):
            ax.spines[s].set_visible(False)
        ax.spines['bottom'].set_color(BRI610['ink_dim'])
        ax.set_title(label, loc='left', fontsize=8.5, color=BRI610['ink'], pad=3)

    ax1.set_xticklabels([])
    ax2.set_xlabel('time (s)')
    # rate annotation top — neutral
    ax1.text(1.0, 1.18, r'$\bar r = 5\,\mathrm{Hz}$', ha='right', va='bottom',
             color=BRI610['ink_dim'], fontsize=8.5)
    ax2.text(1.0, 1.18, r'$\bar r = 5\,\mathrm{Hz}$ (matched)',
             ha='right', va='bottom', color=BRI610['ink_dim'], fontsize=8.5)
    # YELLOW callout — the message: precise timing in the bottom panel
    ax2.text(0.5, -0.55, 'precise timing carries the information',
             ha='center', va='top', color=BRI610['yellow'],
             fontsize=8.5, fontweight='bold')
    fig.tight_layout(pad=0.6)
    return fig


def fig_phase_precession():
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 3.6),
                                    gridspec_kw={'height_ratios': [1.8, 1], 'hspace': 0.45})
    rng = np.random.default_rng(3)
    pos = np.linspace(0, 1, 80)
    phase = 350 - 320 * pos + rng.normal(0, 12, size=pos.size)
    # INK_DIM scatter (data is neutral context)
    ax1.scatter(pos, phase, s=10, color=BRI610['ink_dim'], alpha=0.85,
                edgecolors='none')
    ax1.scatter(pos, phase + 360, s=10, color=BRI610['ink_dim'], alpha=0.40,
                edgecolors='none')

    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 720)
    ax1.set_yticks([0, 180, 360, 540, 720])
    ax1.set_yticklabels(['0°', '180°', '360°', '540°', '720°'])
    hlabel_y(ax1, r'$\theta$ phase')
    ax1.set_title('Hippocampal phase precession')

    # YELLOW direction arrow — running direction (entry → exit)
    ax1.annotate('', xy=(0.92, 80), xytext=(0.08, 80),
                 arrowprops=dict(arrowstyle='-|>', color=BRI610['yellow'],
                                 lw=1.8, mutation_scale=14))
    ax1.text(0.5, 30, 'running direction', ha='center', va='bottom',
             color=BRI610['yellow'], fontsize=8, fontweight='bold')

    ax1.axvline(0.05, color=BRI610['ink_faint'], linewidth=0.7, linestyle=(0, (3, 3)))
    ax1.axvline(0.95, color=BRI610['ink_faint'], linewidth=0.7, linestyle=(0, (3, 3)))
    ax1.text(0.07, 600, 'field entry', ha='left', va='center',
             color=BRI610['ink_dim'], fontsize=7.5,
             bbox=dict(boxstyle='round,pad=0.15', facecolor=BRI610['paper'],
                       edgecolor='none'))
    ax1.text(0.93, 600, 'field exit', ha='right', va='center',
             color=BRI610['ink_dim'], fontsize=7.5,
             bbox=dict(boxstyle='round,pad=0.15', facecolor=BRI610['paper'],
                       edgecolor='none'))

    # Theta sinusoid — CYAN (rhythmic reference)
    tt = np.linspace(0, 1, 600)
    theta = np.sin(2 * np.pi * 8 * tt)
    ax2.plot(tt, theta, color=BRI610['cyan'], linewidth=1.5, linestyle='-')
    ax2.set_xlim(0, 1)
    ax2.set_ylim(-1.4, 1.4)
    ax2.set_yticks([])
    ax2.set_xlabel('position in place field (norm.)')
    hlabel_y(ax2, r'$\theta$ ref.', fontsize=8)
    for s in ('top', 'right', 'left'):
        ax2.spines[s].set_visible(False)
    fig.tight_layout(pad=0.6)
    return fig


# ===========================================================================
# GROUP B — SCHEMATICS
# ===========================================================================

def hatched_rect(ax, x, y, w, h, hatch='//', fc=None, ec=None, lw=0.8):
    if fc is None:
        fc = BRI610['paper']
    if ec is None:
        ec = BRI610['ink']
    p = Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec, linewidth=lw,
                  hatch=hatch)
    ax.add_patch(p)
    return p


def fig_bilayer_capacitor():
    fig = plt.figure(figsize=(6, 3.6))
    ax = schematic_ax(fig, xlim=(0, 100), ylim=(0, 60))

    plate_w, plate_h = 50, 4.5
    plate_x = 10
    top_y = 38
    bot_y = 17
    # INK strokes for plates
    hatched_rect(ax, plate_x, top_y, plate_w, plate_h, hatch='////',
                 fc=BRI610['rule_soft'], ec=BRI610['ink_dim'])
    hatched_rect(ax, plate_x, bot_y, plate_w, plate_h, hatch='////',
                 fc=BRI610['rule_soft'], ec=BRI610['ink_dim'])

    # Phospholipid heads + tails — INK_DIM (neutral schematic)
    for xpos in np.linspace(plate_x + 2, plate_x + plate_w - 2, 12):
        ax.add_patch(Circle((xpos, top_y + plate_h + 1.4), 1.3,
                            facecolor=BRI610['ink_dim'], edgecolor='none'))
        ax.plot([xpos, xpos], [top_y + plate_h, top_y + plate_h - 4.4],
                color=BRI610['ink_dim'], linewidth=0.6)
        ax.add_patch(Circle((xpos, bot_y - 1.4), 1.3,
                            facecolor=BRI610['ink_dim'], edgecolor='none'))
        ax.plot([xpos, xpos], [bot_y, bot_y + 4.4],
                color=BRI610['ink_dim'], linewidth=0.6)

    # YELLOW thickness arrow + label 'd'
    ax.annotate('', xy=(plate_x + plate_w + 2, top_y),
                xytext=(plate_x + plate_w + 2, bot_y + plate_h),
                arrowprops=dict(arrowstyle='<->', color=BRI610['yellow'], lw=1.6))
    ax.text(plate_x + plate_w + 4.5, (top_y + bot_y + plate_h) / 2, r'$d$',
            ha='left', va='center', color=BRI610['yellow'], fontsize=11,
            fontweight='bold')

    # Capacitor symbol — INK
    cap_x = 78
    ax.plot([cap_x - 5, cap_x + 5], [42, 42], color=BRI610['ink'], linewidth=1.4)
    ax.plot([cap_x - 5, cap_x + 5], [38, 38], color=BRI610['ink'], linewidth=1.4)
    ax.plot([cap_x, cap_x], [42, 47], color=BRI610['ink'], linewidth=1.0)
    ax.plot([cap_x, cap_x], [38, 33], color=BRI610['ink'], linewidth=1.0)
    ax.text(cap_x, 49, r'$C_m$', ha='center', va='bottom', color=BRI610['ink'])

    ax.text(plate_x - 1, top_y + plate_h / 2, 'extracellular', ha='right',
            va='center', color=BRI610['ink_dim'], fontsize=8)
    ax.text(plate_x - 1, bot_y + plate_h / 2, 'cytoplasm', ha='right',
            va='center', color=BRI610['ink_dim'], fontsize=8)

    ax.text(50, 6, r'$C_m = \dfrac{\varepsilon\,\varepsilon_0}{d}$',
            ha='center', va='center', color=BRI610['ink'], fontsize=10,
            bbox=dict(boxstyle='round,pad=0.4', facecolor=BRI610['paper'],
                      edgecolor=BRI610['rule_soft'], linewidth=0.5))

    ax.set_title('Lipid bilayer as parallel-plate capacitor', pad=4)
    fig.tight_layout(pad=0.5)
    return fig


def fig_membrane_rc_circuit():
    fig = plt.figure(figsize=(6, 3.6))
    ax = schematic_ax(fig, xlim=(0, 100), ylim=(0, 60))

    rail_y_top = 46
    rail_y_bot = 14
    # INK rails
    ax.plot([10, 90], [rail_y_top, rail_y_top], color=BRI610['ink'], linewidth=1.2)
    ax.plot([10, 90], [rail_y_bot, rail_y_bot], color=BRI610['ink'], linewidth=1.2)
    ax.text(10, rail_y_top + 1.4, 'extracellular', color=BRI610['ink_dim'],
            ha='left', va='bottom', fontsize=8)
    ax.text(10, rail_y_bot - 1.4, 'cytoplasm', color=BRI610['ink_dim'],
            ha='left', va='top', fontsize=8)

    # Resistor — INK
    rx = 40
    ax.plot([rx, rx], [rail_y_top, 38], color=BRI610['ink'], linewidth=1.0)
    ax.plot([rx, rx], [22, rail_y_bot], color=BRI610['ink'], linewidth=1.0)
    zig_y = np.linspace(38, 22, 9)
    zig_x = rx + np.array([0, 2.5, -2.5, 2.5, -2.5, 2.5, -2.5, 2.5, 0])
    ax.plot(zig_x, zig_y, color=BRI610['ink'], linewidth=1.0)
    ax.text(rx - 5, 30, r'$R_m$', ha='right', va='center', color=BRI610['ink'])

    # Capacitor — INK
    cx = 62
    ax.plot([cx, cx], [rail_y_top, 32], color=BRI610['ink'], linewidth=1.0)
    ax.plot([cx, cx], [28, rail_y_bot], color=BRI610['ink'], linewidth=1.0)
    ax.plot([cx - 5, cx + 5], [32, 32], color=BRI610['ink'], linewidth=1.4)
    ax.plot([cx - 5, cx + 5], [28, 28], color=BRI610['ink'], linewidth=1.4)
    ax.text(cx + 5, 30, r'$C_m$', ha='left', va='center', color=BRI610['ink'])

    # YELLOW current source I_inj
    ix = 20
    ax.plot([ix, ix], [rail_y_top, 35], color=BRI610['yellow'], linewidth=1.3)
    ax.plot([ix, ix], [25, rail_y_bot], color=BRI610['yellow'], linewidth=1.3)
    ax.add_patch(Circle((ix, 30), 5, facecolor=BRI610['paper'],
                        edgecolor=BRI610['yellow'], linewidth=1.6))
    ax.annotate('', xy=(ix, 32.5), xytext=(ix, 27.5),
                arrowprops=dict(arrowstyle='-|>', color=BRI610['yellow'], lw=1.2,
                                mutation_scale=10))
    ax.text(ix - 7, 30, r'$I_{inj}$', ha='right', va='center',
            color=BRI610['yellow'], fontweight='bold')

    ax.text(50, 5, r'$I_{inj}=C_m\,\dfrac{dV_m}{dt}+\dfrac{V_m-V_{rest}}{R_m}$',
            ha='center', va='center', color=BRI610['ink'], fontsize=9.5,
            bbox=dict(boxstyle='round,pad=0.4', facecolor=BRI610['paper'],
                      edgecolor=BRI610['rule_soft'], linewidth=0.5))

    ax.set_title('Membrane RC circuit (KCL)', pad=4)
    fig.tight_layout(pad=0.5)
    return fig


def fig_ion_channel_subunit():
    fig = plt.figure(figsize=(6, 3.6))
    ax = schematic_ax(fig, xlim=(0, 100), ylim=(0, 60))

    # Left: Kv tetramer — CYAN outline (K+ → cyan)
    cx_l, cy_l = 26, 32
    r_sub = 6
    sub_offsets = [(-9, 0), (9, 0), (0, 9), (0, -9)]
    sub_labels = [r'$\alpha_1$', r'$\alpha_2$', r'$\alpha_3$', r'$\alpha_4$']
    label_pos = [(-9 - 7, 0), (9 + 7, 0), (0, 9 + 8), (0, -9 - 8)]
    label_ha = ['right', 'left', 'center', 'center']
    label_va = ['center', 'center', 'bottom', 'top']
    for (dx, dy), lbl, (lx, ly), ha, va in zip(sub_offsets, sub_labels, label_pos,
                                                label_ha, label_va):
        ax.add_patch(Circle((cx_l + dx, cy_l + dy), r_sub,
                            facecolor=BRI610['paper'],
                            edgecolor=BRI610['cyan'], linewidth=1.4))
        ax.text(cx_l + lx, cy_l + ly, lbl, ha=ha, va=va,
                color=BRI610['ink_dim'], fontsize=7.5)
    ax.add_patch(Circle((cx_l, cy_l), 2.6, facecolor=BRI610['paper'],
                        edgecolor=BRI610['ink_dim'], linewidth=0.7))
    ax.text(cx_l, 8, r'Kv  ($n^{4}$)', ha='center', va='center',
            color=BRI610['ink'], fontsize=9)
    ax.text(cx_l, 51, '4 α-subunits', ha='center', va='bottom',
            color=BRI610['ink_dim'], fontsize=7.5)

    # Right: Nav — BLUE outline (Na+ → blue)
    cx_r, cy_r = 72, 36
    dom_labels = ['I', 'II', 'III', 'IV']
    for (dx, dy), lbl, (lx, ly), ha, va in zip(sub_offsets, dom_labels, label_pos,
                                                label_ha, label_va):
        ax.add_patch(Circle((cx_r + dx, cy_r + dy), r_sub,
                            facecolor=BRI610['paper'],
                            edgecolor=BRI610['blue'], linewidth=1.4))
        ax.text(cx_r + lx, cy_r + ly, lbl, ha=ha, va=va,
                color=BRI610['ink_dim'], fontsize=7.5)
    ax.add_patch(Circle((cx_r, cy_r), 2.6, facecolor=BRI610['paper'],
                        edgecolor=BRI610['ink_dim'], linewidth=0.7))

    # RED inactivation ball-and-chain
    chain_x = np.linspace(cx_r + 1, cx_r + 12, 30)
    chain_y = cy_r - 9 + 0.8 * np.sin(np.linspace(0, 4 * math.pi, 30))
    ax.plot(chain_x, chain_y, color=BRI610['ink_dim'], linewidth=0.8)
    ax.add_patch(Circle((cx_r + 13.3, cy_r - 9), 2.4,
                        facecolor=BRI610['red'], edgecolor='none'))
    ax.text(cx_r + 13.3, cy_r - 13.5, 'inact.\nball',
            ha='center', va='top', color=BRI610['red'], fontsize=7)

    ax.text(cx_r, 8, r'Nav  ($m^{3}h$)', ha='center', va='center',
            color=BRI610['ink'], fontsize=9)
    ax.text(cx_r, 51, '4 pseudo-domains', ha='center', va='bottom',
            color=BRI610['ink_dim'], fontsize=7.5)

    ax.set_title('Voltage-gated channel architecture', pad=4)
    fig.tight_layout(pad=0.5)
    return fig


def fig_synapse_chemical():
    fig = plt.figure(figsize=(6, 3.6))
    ax = schematic_ax(fig, xlim=(0, 100), ylim=(0, 60))

    # Pre-terminal — INK anatomy
    pre = mpatches.FancyBboxPatch((6, 35), 38, 18,
                                  boxstyle='round,pad=0.6,rounding_size=2',
                                  facecolor=BRI610['rule_soft'],
                                  edgecolor=BRI610['ink_dim'], linewidth=0.8)
    ax.add_patch(pre)
    ax.text(25, 55, 'presynaptic terminal', ha='center', va='bottom',
            color=BRI610['ink_dim'], fontsize=8)

    # Vesicles — INK outlines
    for vx, vy in [(14, 46), (20, 49), (26, 47), (33, 48), (38, 45)]:
        ax.add_patch(Circle((vx, vy), 1.6, facecolor=BRI610['paper'],
                            edgecolor=BRI610['ink_dim'], linewidth=0.7))

    # YELLOW fusing vesicle at active zone
    ax.add_patch(Circle((25, 38), 2.3, facecolor=BRI610['yellow'],
                        edgecolor=BRI610['ink'], linewidth=0.6))
    ax.text(25, 32.5, 'fusion', ha='center', va='top',
            color=BRI610['yellow'], fontsize=7.5, fontweight='bold')

    # Cleft
    ax.plot([6, 44], [33, 33], color=BRI610['ink_dim'], linewidth=0.8)
    ax.plot([6, 44], [27, 27], color=BRI610['ink_dim'], linewidth=0.8)
    ax.text(48, 30, 'cleft', ha='left', va='center',
            color=BRI610['ink_dim'], fontsize=7.5)

    # Neurotransmitters — INK
    for nx, ny in [(20, 30), (24, 31), (28, 30), (32, 31), (22, 28.5), (30, 29)]:
        ax.add_patch(Circle((nx, ny), 0.7, facecolor=BRI610['ink'], edgecolor='none'))

    # Post membrane
    post = mpatches.FancyBboxPatch((6, 9), 38, 17,
                                   boxstyle='round,pad=0.6,rounding_size=2',
                                   facecolor=BRI610['rule_soft'],
                                   edgecolor=BRI610['ink_dim'], linewidth=0.8)
    ax.add_patch(post)
    for rx, lbl in [(15, 'AMPA'), (35, 'NMDA')]:
        ax.add_patch(Rectangle((rx - 3, 23), 6, 4, facecolor=BRI610['paper'],
                               edgecolor=BRI610['ink_dim'], linewidth=1.0))
        ax.text(rx, 18.5, lbl, ha='center', va='center',
                color=BRI610['ink'], fontsize=8)
    ax.text(25, 12, 'postsynaptic membrane', ha='center', va='center',
            color=BRI610['ink_dim'], fontsize=8)

    # Inset EPSP — BLUE trace
    ix0, iy0, iw, ih = 60, 18, 33, 28
    ax.add_patch(FancyBboxPatch((ix0, iy0), iw, ih,
                                boxstyle='round,pad=0.4,rounding_size=1.5',
                                facecolor=BRI610['paper'],
                                edgecolor=BRI610['rule_soft'], linewidth=0.6))
    tt = np.linspace(0, 1, 400)
    epsp = -65 + 12 * tt * np.exp(-(tt - 0.15) * 6) * (tt > 0.05)
    px = ix0 + 4 + (iw - 8) * tt
    py = iy0 + 4 + (ih - 10) * (epsp + 70) / 18
    ax.plot(px, py, color=BRI610['blue'], linewidth=1.6, linestyle='-')
    ax.plot([ix0 + 4, ix0 + iw - 4], [iy0 + 4 + (ih - 10) * 5 / 18] * 2,
            color=BRI610['ink_faint'], linewidth=0.6, linestyle=(0, (3, 3)))
    ax.text(ix0 + iw / 2, iy0 + ih + 1.0, 'EPSP',
            ha='center', va='bottom', color=BRI610['ink'], fontsize=8.5)
    ax.text(ix0 + iw - 2, iy0 + 4 + (ih - 10) * 5 / 18 - 0.5,
            r'$V_{rest}$', ha='right', va='top',
            color=BRI610['ink_dim'], fontsize=7)

    ax.set_title('Chemical synapse', pad=4)
    fig.tight_layout(pad=0.5)
    return fig


def fig_ap_unmyelinated():
    fig = plt.figure(figsize=(6, 3.6))
    ax = schematic_ax(fig, xlim=(0, 100), ylim=(0, 60))

    axon_y = 30
    ax.add_patch(FancyBboxPatch((6, axon_y - 5), 88, 10,
                                boxstyle='round,pad=0.0,rounding_size=4',
                                facecolor=BRI610['rule_soft'],
                                edgecolor=BRI610['ink_dim'], linewidth=0.8))

    # RED refractory zone
    ax.add_patch(Rectangle((6, axon_y - 5), 24, 10,
                           facecolor=BRI610['red'], alpha=0.22,
                           edgecolor='none'))
    ax.text(18, axon_y + 11, 'refractory', ha='center', va='bottom',
            color=BRI610['red'], fontsize=7.5)

    # Patches: leftmost = INK_FAINT (past/future faded), middle/right = BLUE active gradient
    patch_xs = [16, 30, 44, 58, 72]
    # Strategy: leftmost two are past (INK_FAINT faded), then BLUE active patch with rising alpha
    colors = [BRI610['ink_faint'], BRI610['ink_faint'],
              BRI610['blue'], BRI610['blue'], BRI610['blue']]
    alphas = [0.25, 0.40, 0.55, 0.80, 1.0]
    for px, c, a in zip(patch_xs, colors, alphas):
        ax.add_patch(Circle((px, axon_y), 4, facecolor=c,
                            edgecolor='none', alpha=a))

    # YELLOW direction arrow
    ax.annotate('', xy=(86, axon_y), xytext=(72, axon_y),
                arrowprops=dict(arrowstyle='-|>', color=BRI610['yellow'],
                                lw=1.8, mutation_scale=14))
    ax.text(89, axon_y + 5.2, 'forward', ha='right', va='bottom',
            color=BRI610['yellow'], fontsize=8, fontweight='bold')

    ax.text(50, 9, 'unidirectional spread (continuous conduction)',
            ha='center', va='center', color=BRI610['ink_dim'], fontsize=8)
    ax.set_title('AP propagation — unmyelinated axon', pad=4)
    fig.tight_layout(pad=0.5)
    return fig


def fig_ap_myelinated():
    fig = plt.figure(figsize=(6, 3.6))
    ax = schematic_ax(fig, xlim=(0, 100), ylim=(0, 60))

    axon_y = 30
    ax.add_patch(FancyBboxPatch((4, axon_y - 2.5), 92, 5,
                                boxstyle='round,pad=0.0,rounding_size=2',
                                facecolor=BRI610['rule_soft'],
                                edgecolor=BRI610['ink_dim'], linewidth=0.6))

    sheath_segments = [(8, 22), (28, 22), (50, 22), (72, 22)]
    for x0, w in sheath_segments:
        ax.add_patch(FancyBboxPatch((x0, axon_y - 6), w, 12,
                                    boxstyle='round,pad=0.0,rounding_size=3',
                                    facecolor=BRI610['paper'],
                                    edgecolor=BRI610['ink_dim'],
                                    linewidth=1.0))
    # Nodes: past = INK_FAINT, active = BLUE solid, next = BLUE faded
    node_xs = [22, 44, 66, 88]
    # index 1 (44) is the active node, index 2 (66) is the next, 0 is past, 3 is future
    node_colors = [BRI610['ink_faint'], BRI610['blue'],
                   BRI610['blue'], BRI610['ink_faint']]
    node_alphas = [0.4, 1.0, 0.45, 0.4]
    for i, (nx, c, a) in enumerate(zip(node_xs, node_colors, node_alphas)):
        ax.add_patch(Circle((nx, axon_y), 3.0, facecolor=c,
                            edgecolor='none', alpha=a))
        ax.text(nx, axon_y - 8.5, f'N{i+1}', ha='center', va='top',
                color=BRI610['ink_dim'], fontsize=7)

    # YELLOW saltatory jump arrow
    ax.annotate('', xy=(node_xs[2] - 3, axon_y + 8),
                xytext=(node_xs[1] + 3, axon_y + 8),
                arrowprops=dict(arrowstyle='-|>', color=BRI610['yellow'],
                                lw=1.8, mutation_scale=14,
                                connectionstyle='arc3,rad=-0.35'))
    ax.text((node_xs[1] + node_xs[2]) / 2, axon_y + 17, 'saltatory jump',
            ha='center', va='center', color=BRI610['yellow'], fontsize=8,
            fontweight='bold')

    # faded jumps elsewhere — INK_FAINT
    for (a, b) in [(node_xs[0], node_xs[1]), (node_xs[2], node_xs[3])]:
        ax.annotate('', xy=(b - 3, axon_y + 8), xytext=(a + 3, axon_y + 8),
                    arrowprops=dict(arrowstyle='-|>', color=BRI610['ink_faint'],
                                    lw=0.9, mutation_scale=10,
                                    connectionstyle='arc3,rad=-0.35',
                                    alpha=0.55))

    ax.text(19, axon_y - 12, 'myelin sheath', ha='center', va='top',
            color=BRI610['ink_dim'], fontsize=7.5)

    ax.set_title('AP propagation — myelinated axon (saltatory)', pad=4)
    fig.tight_layout(pad=0.5)
    return fig


def fig_nernst_balance():
    fig = plt.figure(figsize=(6, 3.6))
    ax = schematic_ax(fig, xlim=(0, 100), ylim=(0, 60))

    ax.add_patch(Rectangle((6, 12), 38, 36, facecolor=BRI610['rule_soft'],
                          edgecolor=BRI610['ink_dim'], linewidth=0.8))
    ax.add_patch(Rectangle((56, 12), 38, 36, facecolor=BRI610['paper'],
                          edgecolor=BRI610['ink_dim'], linewidth=0.8))

    mem_x = 47
    ax.plot([mem_x, mem_x], [10, 50], color=BRI610['ink'], linewidth=1.4)
    ax.plot([mem_x + 3, mem_x + 3], [10, 50], color=BRI610['ink'], linewidth=1.4)
    for py in [22, 30, 38]:
        ax.add_patch(Rectangle((mem_x, py - 1), 3, 2, facecolor=BRI610['paper'],
                              edgecolor='none'))

    # K+ ions — CYAN (K+ semantic)
    left_grid_x = [12, 18, 24, 30, 36, 42]
    left_grid_y = [16, 24, 32, 40]
    left_pts = [(x, y) for y in left_grid_y for x in left_grid_x]
    left_pts = [(x, y) for (x, y) in left_pts
                if not (28 <= y <= 32) and not (43 <= y <= 45 and x > 32)
                and not (16 <= y <= 20 and x > 32)]
    right_grid = [(60, 16), (74, 16), (88, 16),
                  (60, 32), (88, 32),
                  (60, 40), (74, 40), (88, 40)]
    right_pts = [(x, y) for (x, y) in right_grid
                 if not (15 <= y <= 17 and 56 < x < 70)
                 and not (43 <= y <= 45 and 56 < x < 70)]
    for (x, y) in left_pts:
        ax.text(x, y, r'K$^+$', ha='center', va='center',
                color=BRI610['cyan'], fontsize=7.5)
    for (x, y) in right_pts:
        ax.text(x, y, r'K$^+$', ha='center', va='center',
                color=BRI610['cyan'], fontsize=7.5)

    # GREEN diffusion arrow (gradient)
    ax.annotate('', xy=(64, 44), xytext=(36, 44),
                arrowprops=dict(arrowstyle='-|>', color=BRI610['green'],
                                lw=1.6, mutation_scale=12))
    ax.text(50, 50.5, 'diffusion', ha='center', va='center',
            color=BRI610['green'], fontsize=8, fontweight='bold')

    # BLUE electric arrow (voltage)
    ax.annotate('', xy=(36, 18), xytext=(64, 18),
                arrowprops=dict(arrowstyle='-|>', color=BRI610['blue'],
                                lw=1.6, mutation_scale=12))
    ax.text(50, 7.5, 'electric force', ha='center', va='center',
            color=BRI610['blue'], fontsize=8, fontweight='bold')

    ax.text(25, 55, r'high $[K^+]_i$', ha='center', va='bottom',
            color=BRI610['ink'], fontsize=8.5)
    ax.text(75, 55, r'low $[K^+]_o$', ha='center', va='bottom',
            color=BRI610['ink'], fontsize=8.5)

    # YELLOW E_K equilibrium label
    ax.text(50, 30, r'$E_K$', ha='center', va='center',
            color=BRI610['yellow'], fontsize=11, fontweight='bold',
            bbox=dict(boxstyle='circle,pad=0.3', facecolor=BRI610['paper'],
                      edgecolor=BRI610['yellow'], linewidth=1.6))

    ax.set_title('Nernst equilibrium: diffusion vs. electric force', pad=4)
    fig.tight_layout(pad=0.5)
    return fig


# ===========================================================================
# Driver
# ===========================================================================
FIGURES = [
    ('rc_charging_curve.svg', fig_rc_charging),
    ('ohmic_iv.svg', fig_ohmic_iv),
    ('action_potential_phases.svg', fig_action_potential_phases),
    ('hh_gating_variables.svg', fig_hh_gating),
    ('voltage_clamp_protocol.svg', fig_voltage_clamp),
    ('cable_decay_spatial.svg', fig_cable_decay),
    ('ghk_weighted_log.svg', fig_ghk_bars),
    ('rate_vs_temporal_codes.svg', fig_rate_vs_temporal),
    ('hippocampal_phase_precession.svg', fig_phase_precession),
    ('bilayer_capacitor.svg', fig_bilayer_capacitor),
    ('membrane_rc_circuit.svg', fig_membrane_rc_circuit),
    ('ion_channel_subunit.svg', fig_ion_channel_subunit),
    ('synapse_chemical.svg', fig_synapse_chemical),
    ('ap_propagation_unmyelinated.svg', fig_ap_unmyelinated),
    ('ap_propagation_myelinated.svg', fig_ap_myelinated),
    ('nernst_diffusion_balance.svg', fig_nernst_balance),
]


def main():
    apply_bri610_style()
    rows = []
    overall_ok = True
    for name, builder in FIGURES:
        np.random.seed(0)
        fig = builder()
        items = collect_text_bboxes(fig)
        text_count = len(items)
        pairs = check_overlaps(fig)
        yellow = count_yellow(fig)
        path = save(fig, name)
        plt.close(fig)
        import xml.etree.ElementTree as ET
        try:
            ET.parse(path)
            xml_ok = True
        except Exception as e:
            xml_ok = False
            print(f"  XML PARSE FAIL: {e}")
        status = 'OK' if (not pairs and xml_ok) else 'FAIL'
        if pairs:
            overall_ok = False
            print(f"  OVERLAPS in {name}:")
            for a, b in pairs:
                print(f"    - {a!r}  <->  {b!r}")
        rows.append((name, text_count, len(pairs), yellow, status))

    print('\n=== Per-figure report ===')
    print(f"{'file':45s} {'texts':>6s} {'overlaps':>9s} {'yellow':>6s}  status")
    for r in rows:
        print(f"{r[0]:45s} {r[1]:>6d} {r[2]:>9d} {r[3]:>6d}  {r[4]}")

    if not overall_ok:
        sys.exit(1)


if __name__ == '__main__':
    main()
