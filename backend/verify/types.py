"""
Shared dataclasses for the verifier cascade.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class VerifyStatus(str, Enum):
    VERIFIED = "verified"        # symbolically equivalent
    WRONG = "wrong"              # symbolically NOT equivalent
    UNVERIFIED = "unverified"    # parse error, timeout, or escalation needed
    SKIPPED = "skipped"          # no equation extracted to verify


@dataclass
class VerifyResult:
    status: VerifyStatus
    layer: str = "sympy"               # 'sympy' | 'wolfram_engine' | 'wolfram_alpha'
    detail: Optional[str] = None       # human-readable reason
    residual_latex: Optional[str] = None  # the simplified `lhs - rhs` if applicable
    elapsed_ms: int = 0

    @property
    def ok(self) -> bool:
        return self.status == VerifyStatus.VERIFIED

    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "layer": self.layer,
            "detail": self.detail,
            "residual_latex": self.residual_latex,
            "elapsed_ms": self.elapsed_ms,
        }
