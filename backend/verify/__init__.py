"""
backend.verify — symbolic-math verifier cascade for the Derive agent + walkthrough hooks.

Cascade order (cheapest → most expensive):
  1. SymPy (sympy.parsing.latex) — local, ~ms latency, ADOPT-AS-PRIMARY
  2. Wolfram Engine (free non-commercial dev license) — handles \\partial natively
  3. WolframAlpha Show-Steps API — last resort, cap 2k/month, cache by hash

Public API:
    verify_equation(latex_lhs, latex_rhs, *, timeout=5) -> VerifyResult
    annotate_derivation(steps: list[Step]) -> list[AnnotatedStep]
"""
from .types import VerifyResult, VerifyStatus
from .preprocess import preprocess_hh_cable
from .sympy_check import sympy_verify

__all__ = [
    "VerifyResult",
    "VerifyStatus",
    "preprocess_hh_cable",
    "sympy_verify",
    "verify_equation",
]


def verify_equation(latex_lhs: str, latex_rhs: str, *, timeout: float = 5.0) -> "VerifyResult":
    """
    Cascade verifier. Tries SymPy first; if SymPy parse fails or times out,
    Wolfram Engine and WolframAlpha layers can be plugged in here later (P3.3, P3.4).

    For v0.5.0-alpha we ship SymPy + a stable timeout, and return `unverified`
    on any escalation case so the caller never crashes.
    """
    return sympy_verify(latex_lhs, latex_rhs, timeout=timeout)
