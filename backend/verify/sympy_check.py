"""
SymPy-backed verifier. Returns VerifyResult.

Strategy: parse both sides, then `simplify(lhs - rhs)`. If the result is
identically zero (or equivalent up to expansion), the equation is verified.
On any parse / timeout / unsupported-expression error we return UNVERIFIED
so the caller can escalate to the Wolfram layer (P3.3) when wired.
"""
from __future__ import annotations

import time
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

from .preprocess import preprocess_hh_cable
from .types import VerifyResult, VerifyStatus

log = logging.getLogger(__name__)

# Lazy import so the rest of the backend can boot even if sympy isn't present
_sympy = None
_parse_latex = None


def _ensure_sympy():
    global _sympy, _parse_latex
    if _sympy is not None:
        return _sympy, _parse_latex
    try:
        import sympy as sp
        from sympy.parsing.latex import parse_latex
        _sympy = sp
        _parse_latex = parse_latex
        return sp, parse_latex
    except ImportError as e:
        log.warning("sympy not installed; verifier will return unverified for all inputs")
        _sympy = False
        _parse_latex = False
        return False, False


# Single executor shared across calls so we don't churn threads on every verify.
_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="sympy_verify")


def _do_verify(lhs_latex: str, rhs_latex: str) -> VerifyResult:
    sp, parse_latex = _ensure_sympy()
    if not sp:
        return VerifyResult(
            status=VerifyStatus.UNVERIFIED,
            layer="sympy",
            detail="sympy not installed",
        )

    try:
        lhs = parse_latex(preprocess_hh_cable(lhs_latex))
        rhs = parse_latex(preprocess_hh_cable(rhs_latex))
    except Exception as e:
        return VerifyResult(
            status=VerifyStatus.UNVERIFIED,
            layer="sympy",
            detail=f"parse error: {type(e).__name__}: {e}",
        )

    try:
        diff_raw = lhs - rhs
    except Exception as e:
        return VerifyResult(
            status=VerifyStatus.UNVERIFIED,
            layer="sympy",
            detail=f"subtract error: {type(e).__name__}: {e}",
        )

    # Multi-pass equivalence check. Each pass tries a different normalization;
    # if any pass produces zero, the equation is verified.
    def _is_zero(expr) -> bool:
        try:
            if expr == 0:
                return True
            if hasattr(expr, "equals"):
                eq = expr.equals(0)
                if eq is True:
                    return True
        except Exception:
            return False
        return False

    last_residual = diff_raw
    passes = [
        ("simplify",       lambda d: sp.simplify(d)),
        ("expand+simplify",lambda d: sp.simplify(sp.expand(d))),
        ("logcombine",     lambda d: sp.simplify(sp.logcombine(d, force=True))),
        ("trigsimp",       lambda d: sp.simplify(sp.trigsimp(d))),
        ("together",       lambda d: sp.simplify(sp.together(d))),
        ("radsimp",        lambda d: sp.simplify(sp.radsimp(sp.expand(d)))),
    ]
    for name, op in passes:
        try:
            d = op(diff_raw)
            last_residual = d
            if _is_zero(d):
                return VerifyResult(status=VerifyStatus.VERIFIED, layer="sympy", detail=f"zero after {name}")
        except Exception:
            continue

    # Last resort: numeric sampling at random points. Only useful for finite-domain
    # symbolic expressions, but cheap enough to try.
    try:
        free = list(diff_raw.free_symbols)
        import random
        for _ in range(5):
            subs = {s: random.uniform(0.5, 2.0) for s in free}
            val = complex(diff_raw.evalf(subs=subs))
            if abs(val) > 1e-7:
                break
        else:
            return VerifyResult(status=VerifyStatus.VERIFIED, layer="sympy",
                                detail="zero by numeric sampling (5 random points)")
    except Exception:
        pass

    return VerifyResult(
        status=VerifyStatus.WRONG,
        layer="sympy",
        detail="symbolically not equivalent",
        residual_latex=str(last_residual),
    )


def sympy_verify(lhs_latex: str, rhs_latex: str, *, timeout: float = 5.0) -> VerifyResult:
    """
    Verify whether `lhs_latex` and `rhs_latex` are symbolically equivalent.

    Wraps the actual sympy work in a thread with a timeout so a pathological
    expression cannot hang the request thread.
    """
    t0 = time.perf_counter()
    fut = _pool.submit(_do_verify, lhs_latex, rhs_latex)
    try:
        result = fut.result(timeout=timeout)
    except FuturesTimeout:
        result = VerifyResult(
            status=VerifyStatus.UNVERIFIED,
            layer="sympy",
            detail=f"timeout after {timeout:.1f}s",
        )
        # Best effort cancel; CPython sympy is not interruptible from outside
        # but the future will be discarded.
    result.elapsed_ms = int((time.perf_counter() - t0) * 1000)
    return result
