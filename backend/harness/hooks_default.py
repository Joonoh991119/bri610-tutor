"""
Default hook bindings — wires Multi-Lens Review, SymPy verifier, FSRS+gamification
to the 4 hook points exposed by `backend.harness.hooks`. Imported once at backend
startup so all routes implicitly inherit these checks.

Hook points (from `00b_revised_plan_with_R1-R5.md` §6):
  pre_question_display   — quality gate; reject low-priority/manual-review items
  post_answer            — FSRS scheduler + mastery EMA + XP/streak/badges
  pre_derivation         — SymPy verifier on student LaTeX submission
  post_walkthrough_step  — Multi-Lens Review on freshly generated narration
"""
from __future__ import annotations
import logging
import re
from typing import Any, Optional

from .hooks import register
from .telemetry import emit_event

log = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────
# pre_question_display — quality gate before delivery
# ──────────────────────────────────────────────────────────────────

@register("pre_question_display")
async def quality_gate(item: dict, **ctx) -> Optional[dict]:
    """
    Drop bank items that fall below quality threshold or are flagged for manual
    review. Returning None signals rejection; the BankSelector should pull the
    next candidate.

    Threshold rules:
      - priority_score < 0.4  → reject (low pedagogical value)
      - status != 'active'    → reject
      - source_citation.kind != 'slide'  → reject (slide-only mandate)
      - prompt_md missing 'Slide L' substring → reject (no in-body citation)
    """
    if not item:
        return None
    if (item.get("priority_score") or 0) < 0.4:
        emit_event(event_kind="quality_gate_reject", agent="hook",
                   payload={"reason": "low_priority", "item_id": item.get("bank_id")})
        return None
    if (item.get("status") or "active") != "active":
        emit_event(event_kind="quality_gate_reject", agent="hook",
                   payload={"reason": "non_active", "item_id": item.get("bank_id")})
        return None
    cite = item.get("source_citation") or {}
    if cite.get("kind") and cite["kind"] != "slide":
        emit_event(event_kind="quality_gate_reject", agent="hook",
                   payload={"reason": "non_slide_citation", "item_id": item.get("bank_id")})
        return None
    return item


# ──────────────────────────────────────────────────────────────────
# post_answer — FSRS + mastery EMA + gamification
# ──────────────────────────────────────────────────────────────────

@register("post_answer")
async def update_mastery_ema(event: dict, **ctx) -> dict:
    """
    EMA update of `mastery` table on each rated card.
    α = 0.2 (10–20% weight on most-recent review).
    rating: 1 (Again) → score 0.0, 2 (Hard) → 0.4, 3 (Good) → 0.7, 4 (Easy) → 1.0.
    """
    user_id = event.get("user_id") or 1
    rating  = int(event.get("rating") or 0)
    topic   = event.get("topic")
    ctype   = event.get("card_type")
    if not (topic and ctype) or rating == 0:
        return event
    score_map = {1: 0.0, 2: 0.4, 3: 0.7, 4: 1.0}
    new_score = score_map.get(rating, 0.5)
    alpha = 0.2

    try:
        from db_pool import acquire, release
        conn = acquire()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT score, reps, lapses FROM mastery
                    WHERE user_id=%s AND topic=%s AND card_type=%s
                """, (user_id, topic, ctype))
                row = cur.fetchone()
                if row:
                    cur_score, reps, lapses = row
                    smooth = (1 - alpha) * float(cur_score) + alpha * new_score
                    cur.execute("""
                        UPDATE mastery SET score=%s, reps=reps+1,
                          lapses=lapses + %s, updated_at=now()
                        WHERE user_id=%s AND topic=%s AND card_type=%s
                    """, (smooth, 1 if rating == 1 else 0, user_id, topic, ctype))
                else:
                    cur.execute("""
                        INSERT INTO mastery (user_id, topic, card_type, score, reps, lapses)
                        VALUES (%s,%s,%s,%s,1,%s)
                    """, (user_id, topic, ctype, new_score, 1 if rating == 1 else 0))
            conn.commit()
        finally:
            release(conn)
        emit_event(event_kind="mastery_update", user_id=user_id, agent="hook",
                   payload={"topic": topic, "card_type": ctype,
                            "rating": rating, "new_score": new_score})
    except Exception as e:
        log.warning("mastery EMA update failed: %s", e)
    return event


# ──────────────────────────────────────────────────────────────────
# pre_derivation — SymPy verifier prepass
# ──────────────────────────────────────────────────────────────────

_LATEX_DOLLAR = re.compile(r"\$\s*([^$]{2,400}?)\s*\$")

@register("pre_derivation")
async def sympy_prepass(payload: dict, **ctx) -> dict:
    """
    Extract any inline LaTeX `$...$` from a student derivation submission and
    run `verify_equation` on each adjacent pair. Annotate the payload with a
    `verifier_results` list so the agent can decide whether to accept/reject.
    """
    text = payload.get("latex_attempt") or payload.get("text") or ""
    matches = _LATEX_DOLLAR.findall(text)
    if len(matches) < 2:
        payload["verifier_results"] = []
        return payload
    try:
        from verify import verify_equation
    except Exception as e:
        log.debug("verify import failed: %s", e)
        payload["verifier_results"] = []
        return payload

    results = []
    # Verify consecutive equation pairs (transformations)
    for lhs, rhs in zip(matches[:-1], matches[1:]):
        r = verify_equation(lhs, rhs)
        results.append(r.to_dict())
    payload["verifier_results"] = results
    emit_event(event_kind="sympy_prepass", agent="hook",
               payload={"n_eqs": len(matches), "verified_pairs":
                        sum(1 for r in results if r["status"] == "verified")})
    return payload


# ──────────────────────────────────────────────────────────────────
# post_walkthrough_step — Multi-Lens Review on generated narration
# ──────────────────────────────────────────────────────────────────

@register("post_walkthrough_step")
async def lens_review_step(step_output: dict, **ctx) -> dict:
    """
    Run a 1-round Multi-Lens Review on each freshly-generated walkthrough
    narration. If the factual lens vetoes (rejects), mark the step as
    `needs_human_review=True` so the frontend renders a warning banner.

    For demo speed, default max_rounds=1; nightly daemon runs full max_rounds=3.
    """
    narration = step_output.get("narration_md") or ""
    if len(narration.strip()) < 40:
        return step_output
    try:
        from review import multi_lens_review, Artifact
        artifact = Artifact(
            kind="walkthrough_step",
            text=narration,
            citation={"kind": "slide",
                      "lecture": step_output.get("lecture", "L?"),
                      "page":    step_output.get("slide_page", 0)},
            declared_difficulty=step_output.get("declared_difficulty", 3),
            declared_bloom=step_output.get("declared_bloom", "Apply"),
        )
        res = await multi_lens_review(artifact, max_rounds=1)
        step_output["lens_status"] = res.status
        step_output["lens_rounds"] = res.rounds
        if res.status == "manual_review":
            step_output["needs_human_review"] = True
        emit_event(event_kind="post_walkthrough_lens", agent="hook",
                   payload={"status": res.status, "rounds": res.rounds})
    except Exception as e:
        log.debug("post_walkthrough lens review failed: %s", e)
    return step_output


def install():
    """No-op (hooks register at module import). Calling makes intent explicit."""
    log.info("default hooks installed: pre_question_display, post_answer, pre_derivation, post_walkthrough_step")
