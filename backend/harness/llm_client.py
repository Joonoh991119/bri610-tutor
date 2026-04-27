"""
Single LLM call site for the entire backend. All agents call through here so we get:

  * Per-route model selection (high-perf paid for reasoning, cheap for utilities).
  * Cascading fallback: paid OpenRouter → free OpenRouter → local Ollama.
  * Retries with exponential backoff on 429 / connection errors.
  * Latency + token telemetry to `analytics_events`.
  * Optional response cache by sha256(prompt) so re-runs of Multi-Lens reviewers
    on identical artifacts don't burn tokens.

Why this matters (from `feedback_v05_priorities.md`):
    "자원 소모가 있더라도 고성능 모델을 활용 (local or Openrouter)" — favor performance
    over cost for load-bearing routes (Tutor, Derive, Consultant, Lens reviewers,
    QuestionGenerator). Free tier is fine for utility (Router, Persona narrator).

The route table below is the SINGLE source of truth for which model handles which
agent. Tune here, not in agents.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import random
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx

from .telemetry import emit_event

log = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────
# Route table — which model serves which agent role
# ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class RouteSpec:
    name: str                       # logical agent role
    primary: str                    # OpenRouter model id (paid SOTA)
    fallback_or: str                # OpenRouter free / cheaper fallback
    fallback_ollama: str            # Local Ollama tag
    temperature: float = 0.7
    max_tokens: int = 4096


# v0.5 default routes — budget-respecting ($20 cap; free-tier default, paid only for
# high-leverage gates). Override via env: BRI610_ROUTE_<NAME>_<FIELD>=value.
#
# PAID is reserved for: lens_factual (factual leak destroys bank), consultant (small
# strategy calls), quiz_generator (one-time offline batch). Everything else free.
# Real OpenRouter model IDs (verified against /api/v1/models).
# Free-tier IDs use the `:free` suffix where available; otherwise pick the cheapest paid.
_OR_QWEN35_PLUS  = "qwen/qwen3.5-plus-02-15"      # ~$0.20/Mt — cheap, good Korean
_OR_QWEN36_PLUS  = "qwen/qwen3.6-plus"            # latest qwen
_OR_QWEN35_122B  = "qwen/qwen3.5-122b-a10b"       # MoE big
_OR_MAX_THINKING = "qwen/qwen3-max-thinking"      # reasoning-tuned
_PAID_SONNET     = "anthropic/claude-sonnet-4-6"  # PAID — quality gates only

# Cost-effective deep-reasoning OpenRouter models (verified IDs).
# Used as DEFAULT for chat / derive / summary / quiz / lens reviewers (cross-model audit).
# NOT for coding (coding routes still use Sonnet/Opus).
_REVIEW_DEEPSEEK   = "deepseek/deepseek-v4-pro"      # paid, deep reasoning, science-strong
_DEEPSEEK_FLASH    = "deepseek/deepseek-v4-flash"    # paid, 3× cheaper than v4-pro for utility roles
_REVIEW_KIMI       = "moonshotai/kimi-k2.6"          # paid, premium reasoning (NB: $4.66/M completion)
_REVIEW_DSR1       = "deepseek/deepseek-r1-0528"     # math/derivation chain-of-thought

# Local Ollama tags (verified from `ollama list`).
# NOTE: qwen3.6 series in Ollama may have thinking-mode that returns empty
# user-visible content when called via /api/chat. Use qwen2.5:14b-instruct as
# primary fallback for general use — fast, Korean-fluent, non-thinking.
# Reserve qwen3.6:35b-a3b only for math/reasoning where we WANT chain-of-thought.
_OLL_PRIMARY = "qwen2.5:14b-instruct"     # 9 GB, predictable, Korean-strong
_OLL_BIG     = "qwen2.5:14b-instruct"     # alias — keeping shape stable
_OLL_QUICK   = "qwen2.5:7b-instruct"      # 4.7 GB, fastest
_OLL_MATH    = "qwen3.6:35b-a3b"          # MoE thinking — for derive role
_OLL_GEMMA   = "gemma4:26b"               # diverse-perspective second opinion

ROUTES: dict[str, RouteSpec] = {
    # Routing principle (revised 2026-04-27, post-telemetry-audit):
    # Make **DeepSeek V4 Pro the dominant primary** across all reasoning
    # roles. Reserve Kimi K 2.6 for routes where Korean naturalness or
    # pedagogical-style reasoning specifically benefits (persona narrator,
    # lens_pedagogical fallback). Use DeepSeek V4 Flash (3× cheaper) for
    # utility roles (priority scoring, difficulty classification). Reserve
    # qwen3.6-plus for Korean-correctness lens only.
    #
    # Audit (24h before 2026-04-27 ~19:30): kimi-k2.6 had 131 calls vs
    # deepseek-v4-pro only 48 — that's why this rebalance was needed.
    #
    "router":           RouteSpec("router",           _OR_QWEN35_PLUS,  _OR_QWEN36_PLUS, _OLL_QUICK,   0.0,  10),
    "tutor":            RouteSpec("tutor",            _REVIEW_DEEPSEEK, _REVIEW_KIMI,    _OLL_PRIMARY, 0.65, 4096),
    "derive":           RouteSpec("derive",           _REVIEW_DSR1,     _REVIEW_DEEPSEEK,_OLL_MATH,    0.3,  4096),  # R1 chain-of-thought primary
    "consultant":       RouteSpec("consultant",       _REVIEW_DEEPSEEK, _PAID_SONNET,    _OLL_PRIMARY, 0.0,  300),
    # SWITCHED: kimi → deepseek primary
    "explain_my_answer":RouteSpec("explain_my_answer",_REVIEW_DEEPSEEK, _REVIEW_KIMI,    _OLL_PRIMARY, 0.5,  1500),
    "quiz_generator":   RouteSpec("quiz_generator",   _REVIEW_DEEPSEEK, _REVIEW_KIMI,    _OLL_PRIMARY, 0.5,  3000),
    "priority_scorer":  RouteSpec("priority_scorer",  _DEEPSEEK_FLASH,  _REVIEW_DEEPSEEK,_OLL_PRIMARY, 0.0,  500),  # cheap utility
    # Lens reviewers — cross-model auditing
    "lens_factual":     RouteSpec("lens_factual",     _REVIEW_DEEPSEEK, _PAID_SONNET,    _OLL_PRIMARY, 0.0,  700),
    "lens_pedagogical": RouteSpec("lens_pedagogical", _REVIEW_DEEPSEEK, _REVIEW_KIMI,    _OLL_PRIMARY, 0.0,  500),  # SWITCHED
    "lens_korean":      RouteSpec("lens_korean",      _OR_QWEN36_PLUS,  _REVIEW_KIMI,    _OLL_PRIMARY, 0.0,  400),  # qwen for Korean correctness
    "lens_difficulty":  RouteSpec("lens_difficulty",  _DEEPSEEK_FLASH,  _REVIEW_DEEPSEEK,_OLL_PRIMARY, 0.0,  300),  # cheap utility
    # Kimi only where its Korean fluency / narrator voice specifically helps
    "persona_narrator": RouteSpec("persona_narrator", _REVIEW_KIMI,     _REVIEW_DEEPSEEK,_OLL_PRIMARY, 0.55, 700),
    "summary":          RouteSpec("summary",          _REVIEW_DEEPSEEK, _REVIEW_KIMI,    _OLL_PRIMARY, 0.45, 4500),
    "diagnostic":       RouteSpec("diagnostic",       _OR_QWEN35_PLUS,  _DEEPSEEK_FLASH, _OLL_QUICK,   0.0,  300),
    "default":          RouteSpec("default",          _REVIEW_DEEPSEEK, _REVIEW_KIMI,    _OLL_PRIMARY, 0.6,  2048),
}

# Allow env overrides per route: BRI610_ROUTE_<NAME>_<FIELD>=value
def _apply_env_overrides() -> None:
    for name, spec in list(ROUTES.items()):
        prefix = f"BRI610_ROUTE_{name.upper()}_"
        kw = {}
        for field_name in ("primary", "fallback_or", "fallback_ollama"):
            v = os.environ.get(prefix + field_name.upper())
            if v:
                kw[field_name] = v
        if kw:
            ROUTES[name] = RouteSpec(name=name, **{**spec.__dict__, **kw})

_apply_env_overrides()

# ──────────────────────────────────────────────────────────────────
# Backend endpoints
# ──────────────────────────────────────────────────────────────────

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat")
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# Optional response cache for idempotent reviewer calls
_CACHE: dict[str, str] = {}
_CACHE_MAX = int(os.environ.get("BRI610_LLM_CACHE_MAX", "1024"))


def _cache_key(model: str, system: str, user: str, history: list, temp: float) -> str:
    h = hashlib.sha256()
    h.update(model.encode()); h.update(b"|")
    h.update(system.encode()); h.update(b"|")
    h.update(user.encode()); h.update(b"|")
    h.update(json.dumps(history or [], ensure_ascii=False).encode()); h.update(b"|")
    h.update(f"{temp:.3f}".encode())
    return h.hexdigest()


# ──────────────────────────────────────────────────────────────────
# OpenRouter call
# ──────────────────────────────────────────────────────────────────

async def _openrouter(model: str, system: str, user: str, history: list,
                       temperature: float, max_tokens: int) -> tuple[str, dict]:
    if not OPENROUTER_KEY:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    msgs = [{"role": "system", "content": system}]
    if history:
        msgs.extend(history[-6:])
    msgs.append({"role": "user", "content": user})

    async with httpx.AsyncClient(timeout=180.0) as client:
        r = await client.post(
            OPENROUTER_URL,
            headers={"Authorization": f"Bearer {OPENROUTER_KEY}",
                     "Content-Type": "application/json",
                     "HTTP-Referer": "https://bri610-tutor.local",
                     "X-Title": "BRI610 AI Tutor"},
            json={"model": model, "messages": msgs,
                  "temperature": temperature, "max_tokens": max_tokens},
        )
        r.raise_for_status()
        data = r.json()
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage") or {}
        meta = {
            "tokens_in":  usage.get("prompt_tokens"),
            "tokens_out": usage.get("completion_tokens"),
            "raw_finish": data["choices"][0].get("finish_reason"),
        }
        return text, meta


# ──────────────────────────────────────────────────────────────────
# Ollama call (last-resort fallback)
# ──────────────────────────────────────────────────────────────────

async def _ollama(model: str, system: str, user: str, history: list,
                   temperature: float, max_tokens: int) -> tuple[str, dict]:
    msgs = [{"role": "system", "content": system}]
    if history:
        msgs.extend(history[-6:])
    msgs.append({"role": "user", "content": user})

    async with httpx.AsyncClient(timeout=300.0) as client:
        r = await client.post(
            OLLAMA_URL,
            json={"model": model, "messages": msgs, "stream": False,
                  "options": {"temperature": temperature, "num_predict": max_tokens}},
        )
        r.raise_for_status()
        data = r.json()
        text = data.get("message", {}).get("content", "")
        # Strip <think>...</think> blocks (DeepSeek-R1 distill always emits them)
        if "<think>" in text and "</think>" in text:
            import re
            text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
        meta = {"tokens_in": data.get("prompt_eval_count"),
                "tokens_out": data.get("eval_count")}
        return text, meta


# ──────────────────────────────────────────────────────────────────
# Public entry point
# ──────────────────────────────────────────────────────────────────

async def call_llm(
    *,
    role: str,
    system: str,
    user: str,
    history: Optional[list] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    user_id: Optional[int] = None,
    session_id: Optional[str] = None,
    cache: bool = False,
) -> dict:
    """
    Make one LLM call for the named agent role. Cascades through:
        primary (paid)  →  fallback_or (cheap/free)  →  fallback_ollama (local)
    on 429 / 5xx / connection errors. Emits a `agent_call` telemetry event.

    Returns:
        {"text": str, "route_used": str, "elapsed_ms": int, "tokens_in": int|None,
         "tokens_out": int|None, "error": str|None}
    """
    spec = ROUTES.get(role) or ROUTES["default"]
    temp = temperature if temperature is not None else spec.temperature
    mt   = max_tokens   if max_tokens   is not None else spec.max_tokens

    if cache:
        key = _cache_key(spec.primary, system, user, history or [], temp)
        if key in _CACHE:
            return {"text": _CACHE[key], "route_used": "cache", "elapsed_ms": 0,
                    "tokens_in": None, "tokens_out": None, "error": None}

    candidates = [
        ("openrouter", spec.primary),
        ("openrouter", spec.fallback_or),
        ("ollama",     spec.fallback_ollama),
    ]
    last_err: Optional[Exception] = None
    t0 = time.perf_counter()
    for backend, model in candidates:
        for attempt in range(3):
            try:
                if backend == "openrouter":
                    text, meta = await _openrouter(model, system, user, history or [], temp, mt)
                else:
                    text, meta = await _ollama(model, system, user, history or [], temp, mt)
                elapsed = int((time.perf_counter() - t0) * 1000)
                route_used = f"{backend}:{model}"
                emit_event(
                    event_kind="agent_call",
                    user_id=user_id, session_id=session_id, agent=role,
                    ms=elapsed,
                    tokens_in=meta.get("tokens_in"),
                    tokens_out=meta.get("tokens_out"),
                    llm_route=route_used,
                    payload={"temperature": temp, "max_tokens": mt},
                )
                if cache:
                    if len(_CACHE) >= _CACHE_MAX:
                        _CACHE.pop(next(iter(_CACHE)))
                    _CACHE[key] = text
                return {"text": text, "route_used": route_used, "elapsed_ms": elapsed,
                        "tokens_in": meta.get("tokens_in"),
                        "tokens_out": meta.get("tokens_out"),
                        "error": None}
            except httpx.HTTPStatusError as e:
                code = e.response.status_code
                last_err = e
                if code == 429:
                    # quota: backoff then try same backend once more, then fall through
                    await asyncio.sleep(min(15, 2 ** (attempt + 1)) + random.uniform(0, 0.5))
                    continue
                if 500 <= code < 600:
                    await asyncio.sleep(min(8, 2 ** attempt))
                    continue
                # 4xx other: don't retry on this backend, escalate
                break
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.HTTPError) as e:
                last_err = e
                await asyncio.sleep(min(8, 2 ** attempt))
                continue
            except Exception as e:
                last_err = e
                break
        # all attempts on this backend failed; cascade to next
        log.warning("LLM route %s exhausted (%s); cascading", model, last_err)
    # full cascade failed
    elapsed = int((time.perf_counter() - t0) * 1000)
    emit_event(
        event_kind="agent_call_failed",
        user_id=user_id, session_id=session_id, agent=role,
        ms=elapsed,
        payload={"error": repr(last_err)} if last_err else {},
    )
    return {"text": "", "route_used": "FAILED", "elapsed_ms": elapsed,
            "tokens_in": None, "tokens_out": None,
            "error": repr(last_err) if last_err else "all routes exhausted"}
