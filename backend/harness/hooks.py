"""
Hook registry — a tiny dispatcher so v0.5 features can attach behavior to
well-known points in the request lifecycle without Tutor/Derive/SRS code
needing to know about them.

Hook types (from `00b_revised_plan_with_R1-R5.md` §6):
  pre_question_display   (item) -> item | None    # filter/quality gate; return None to reject
  post_answer            (review_event) -> None   # FSRS update + mastery EMA + XP/streak/badges
  pre_derivation         (latex_attempt) -> latex_attempt | None  # SymPy verifier prepass
  post_walkthrough_step  (step_output, session) -> step_output     # Multi-Lens Review wrap
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable

log = logging.getLogger(__name__)

HookFn = Callable[..., Awaitable[Any]]

HOOKS: dict[str, list[HookFn]] = {
    "pre_question_display":  [],
    "post_answer":           [],
    "pre_derivation":        [],
    "post_walkthrough_step": [],
}


def register(hook_name: str):
    """Decorator. Use as `@register("pre_question_display")` on an async fn."""
    if hook_name not in HOOKS:
        raise KeyError(f"unknown hook: {hook_name}")

    def deco(fn: HookFn) -> HookFn:
        HOOKS[hook_name].append(fn)
        log.info("registered hook %s -> %s", hook_name, fn.__qualname__)
        return fn
    return deco


async def fire(hook_name: str, payload: Any, **ctx) -> Any:
    """
    Run all registered handlers for the named hook in registration order.
    Each handler receives the (possibly-modified) payload from the prior handler
    and may return a new payload, the same payload, or None (to reject).
    """
    if hook_name not in HOOKS:
        raise KeyError(f"unknown hook: {hook_name}")
    current = payload
    for fn in HOOKS[hook_name]:
        try:
            current = await fn(current, **ctx)
        except Exception as e:
            log.exception("hook %s in %s raised; continuing chain", fn.__qualname__, hook_name)
            continue
        if current is None:
            log.info("hook %s rejected payload at %s", hook_name, fn.__qualname__)
            return None
    return current


def clear(hook_name: str | None = None) -> None:
    """Test-only: clear hooks for one name or all."""
    if hook_name is None:
        for k in HOOKS:
            HOOKS[k].clear()
    else:
        HOOKS[hook_name].clear()
