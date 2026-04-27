"""
LaTeX → SymPy-parseable string preprocessor for BRI610 derivations.

Why: sympy.parsing.latex.parse_latex (antlr4 backend) has several footguns for
graduate-biophysics LaTeX:
  1. `\\bar{g}_{Na}` is not a recognized command — must be rewritten.
  2. `\\partial` is unsupported (open issue #4438) — rewrite as Derivative.
  3. `\\alpha_n (1-n)` is parsed as a *function call* `alpha_n` applied to
     `(1-n)`, not implicit multiplication. We insert explicit `\\cdot`.
  4. `Co` and similar multi-letter identifiers are tokenised as `C*o` (each
     letter a separate symbol). We wrap known multi-letter constants in
     `\\mathrm{...}` which parse_latex treats as a single Symbol.

The mapping is invertible only for display purposes; for verification we just
need symbolic equivalence after substitution.
"""
import re

# ──────────────────────────────────────────────────────────────────
# 1. Multi-letter identifiers that need to stay atomic in SymPy.
#    Map LaTeX surface form → \mathrm{ASCII} so parse_latex keeps it as one Symbol.
#    Order: longest first (so `\bar{g}_{Na}` matches before `\bar{g}`).
# ──────────────────────────────────────────────────────────────────
_ATOM_MAP: list[tuple[str, str]] = [
    # Conductances (max + per-gate)
    (r"\bar{g}_{Na}",  r"\mathrm{gNa_bar}"),
    (r"\bar{g}_K",     r"\mathrm{gK_bar}"),
    (r"\bar{g}_{L}",   r"\mathrm{gL_bar}"),
    (r"\bar{g}_L",     r"\mathrm{gL_bar}"),
    # Reversal potentials
    (r"E_{Na}",        r"\mathrm{ENa}"),
    (r"E_{K}",         r"\mathrm{EK}"),
    (r"E_K",           r"\mathrm{EK}"),
    (r"E_{L}",         r"\mathrm{EL}"),
    (r"E_L",           r"\mathrm{EL}"),
    (r"E_{Ca}",        r"\mathrm{ECa}"),
    # Voltages
    (r"V_{rest}",      r"\mathrm{Vrest}"),
    (r"V_{th}",        r"\mathrm{Vth}"),
    (r"V_m",           r"\mathrm{Vm}"),
    (r"V_{m}",         r"\mathrm{Vm}"),
    # Cable
    (r"\lambda^2",     r"\mathrm{lam2}"),
    (r"R_m",           r"\mathrm{Rm}"),
    (r"R_i",           r"\mathrm{Ri}"),
    (r"C_m",           r"\mathrm{Cm}"),
    (r"I_{ion}",       r"\mathrm{Iion}"),
    (r"I_{inj}",       r"\mathrm{Iinj}"),
    (r"I_{Na}",        r"\mathrm{INa}"),
    (r"I_K",           r"\mathrm{IK}"),
    (r"I_{L}",         r"\mathrm{IL}"),
    (r"I_L",           r"\mathrm{IL}"),
    # Concentration notation [X]_o / [X]_i — convert to atomic identifiers
    (r"[Na]_o",        r"\mathrm{Na_out}"),
    (r"[Na]_i",        r"\mathrm{Na_in}"),
    (r"[K]_o",         r"\mathrm{K_out}"),
    (r"[K]_i",         r"\mathrm{K_in}"),
    (r"[Cl]_o",        r"\mathrm{Cl_out}"),
    (r"[Cl]_i",        r"\mathrm{Cl_in}"),
    (r"[Ca]_o",        r"\mathrm{Ca_out}"),
    (r"[Ca]_i",        r"\mathrm{Ca_in}"),
    # Generic outer/inner concentration (chem convention) when no ion specified
    (r"C_o",           r"\mathrm{Cout}"),
    (r"C_i",           r"\mathrm{Cin}"),
]

# ──────────────────────────────────────────────────────────────────
# 2. Derivative rewrites
# ──────────────────────────────────────────────────────────────────
# Higher-order partials (must run before 1st-order)
_PARTIAL_2ND_RE = re.compile(
    r"\\frac\{\\partial\^?\{?2\}?\s*([A-Za-z_][A-Za-z0-9_]*)\}\{\\partial\s*([A-Za-z_][A-Za-z0-9_]*)\^?\{?2\}?\}"
)
_PARTIAL_1ST_RE = re.compile(
    r"\\frac\{\\partial\s*([A-Za-z_][A-Za-z0-9_]*)\}\{\\partial\s*([A-Za-z_][A-Za-z0-9_]*)\}"
)
# Ordinary derivative \frac{dX}{dY}
_ORDDERIV_RE = re.compile(
    r"\\frac\{d\s*([A-Za-z_][A-Za-z0-9_]*)\}\{d\s*([A-Za-z_][A-Za-z0-9_]*)\}"
)

# ──────────────────────────────────────────────────────────────────
# 3. Implicit-multiplication fixer
#    `\alpha_n (1-n)` is parsed as function call by SymPy parse_latex.
#    Insert \cdot between (Greek letter ± subscript) and `(`.
# ──────────────────────────────────────────────────────────────────
_GREEK_NAMES = (
    "alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta",
    "iota", "kappa", "lambda", "mu", "nu", "xi", "pi", "rho", "sigma",
    "tau", "upsilon", "phi", "chi", "psi", "omega",
)
_GREEK_PAREN_RE = re.compile(
    r"(\\(?:" + "|".join(_GREEK_NAMES) + r")(?:_\{?\w+\}?)?)\s*\(",
)
# Same for \mathrm{...} atoms followed by ( — but NOT \mathrm{Derivative}(...)
# which is a deliberate function form we emit ourselves above.
_MATHRM_PAREN_RE = re.compile(
    r"(\\mathrm\{(?!Derivative\b)[^}]+\})\s*\(",
)


def preprocess_hh_cable(latex: str) -> str:
    """
    Apply the BRI610 symbol map + derivative rewrites + implicit-multiplication
    fixer so SymPy's parse_latex produces a sane expression tree.
    """
    s = latex.strip().strip("$").strip()

    # 1. Higher-order partials FIRST (the regex would otherwise match the 1st-order pattern)
    s = _PARTIAL_2ND_RE.sub(r"\\mathrm{Derivative}(\1, \2, \2)", s)
    s = _PARTIAL_1ST_RE.sub(r"\\mathrm{Derivative}(\1, \2)", s)
    s = _ORDDERIV_RE.sub(r"\\mathrm{Derivative}(\1, \2)", s)

    # 2. BRI610 named atoms (longest first), wrap in \mathrm{} so parse_latex keeps them whole
    for src, dst in _ATOM_MAP:
        s = s.replace(src, dst)

    # 3. Disambiguate Greek-with-subscript followed by `(` from function call
    s = _GREEK_PAREN_RE.sub(r"\1 \\cdot (", s)
    s = _MATHRM_PAREN_RE.sub(r"\1 \\cdot (", s)

    return s
