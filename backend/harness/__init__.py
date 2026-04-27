"""
backend.harness — coordination layer that wraps every LLM call, registers
domain hooks, and emits telemetry.

Modeled on SciLingo's `_llm_client.py` + `enrichment_daemon.py` pattern.

Public surface:
    from backend.harness import llm, hooks, telemetry
    from backend.harness.llm_client import call_llm, RouteSpec
    from backend.harness.hooks import register, fire
"""
from .llm_client import call_llm, RouteSpec, ROUTES
from .hooks import register, fire, HOOKS
from .telemetry import emit_event

__all__ = [
    "call_llm", "RouteSpec", "ROUTES",
    "register", "fire", "HOOKS",
    "emit_event",
]
