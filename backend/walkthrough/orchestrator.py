"""
backend.walkthrough.orchestrator — Main walkthrough step function.

State-machine driven walkthrough flow:
  1. On first call (user_input empty, no step started): emit step 1 narration.
  2. On subsequent calls with user_input:
     a. Enforce structured-input gate: "내가 이해한 바", "내가 시도한 것", "막힌 부분"
        must all be non-empty for socratic/derive_attempt steps. Raises 422 on failure.
     b. Run Consultant to pick pedagogical move.
     c. If step accepts_latex and input contains $...$: run SymPy verifier.
     d. On verifier 'wrong': increment mode_lock_failures, generate Explain-My-Answer.
     e. On 3+ failures: trigger socratic_exit (full reveal + re-explain prompt).
     f. Otherwise: generate next narration via Tutor based on move.
  3. Return normalized response dict.

Sessions are stored in in-memory dict (lost on restart, per spec).
"""
from __future__ import annotations

import logging
import re
import uuid
from typing import Optional

from agents.walkthrough import (
    WALKTHROUGHS,
    WalkthroughState,
    WalkthroughMeta,
    WalkthroughStep,
    get_walkthrough,
)
from agents.consultant import pick_move
from harness import call_llm
from verify import verify_equation

log = logging.getLogger(__name__)

# In-memory session store {session_id -> WalkthroughState}
_SESSIONS: dict[str, WalkthroughState] = {}

# ────────────────────────────────────────────────────────────────
# Structured-input gate
# ────────────────────────────────────────────────────────────────

_GATE_FIELDS = [
    ("내가 이해한 바", "이해한"),
    ("내가 시도한 것", "시도한"),
    ("막힌 부분", "막힌"),
]

_GATE_REQUIRED_KINDS = {"socratic", "derive_attempt"}


def _check_structured_gate(step: WalkthroughStep, user_input: str) -> list[str]:
    """
    Returns list of missing field labels. Empty list = gate passed.
    Only enforced for socratic / derive_attempt steps.
    """
    if step.kind not in _GATE_REQUIRED_KINDS:
        return []

    missing = []
    text_lower = user_input.lower()
    for label, keyword in _GATE_FIELDS:
        # Flexible: look for the keyword OR the label itself in input
        if keyword not in text_lower and label not in user_input:
            missing.append(label)
    return missing


# ────────────────────────────────────────────────────────────────
# LaTeX extraction
# ────────────────────────────────────────────────────────────────

def _extract_latex(text: str) -> Optional[tuple[str, str]]:
    """
    Extract first $lhs = rhs$ or $expr$ from user input.
    Returns (lhs, rhs) tuple or None if no inline math found.
    """
    # Match $...$ blocks
    matches = re.findall(r"\$([^$]+)\$", text)
    if not matches:
        return None

    # Take the first match; split on first = sign
    expr = matches[0].strip()
    if "=" in expr:
        parts = expr.split("=", 1)
        return parts[0].strip(), parts[1].strip()

    # No equals sign — treat whole expr as LHS with empty RHS
    return expr, ""


# ────────────────────────────────────────────────────────────────
# LLM narration helpers
# ────────────────────────────────────────────────────────────────

_TUTOR_SYSTEM = """\
당신은 BRI610 계산신경과학 박사 과정 세미나의 AI 튜터입니다.
You are an AI tutor for a BRI610 Computational Neuroscience PhD seminar.

**Rules:**
- 한국어 주체 + 영어 전문용어 병기 (Korean prose, English technical terms inline).
- Graduate-seminar register: "우리는 보인다", "주목하자" — not undergraduate "알아봅시다".
- Cite slides as [Slide Lx py] inline when referencing content.
- PhD-level depth: assume the student knows calculus, linear algebra, basic thermodynamics.
- Maximum 350 words per response.
- If explaining a pedagogical move: label it subtly as a tutor action (e.g., "유추(analogy)를 통해 살펴보겠습니다").
- Never give the full derivation away unless move is 'socratic_exit' or 'direct_explanation_with_followup'.
"""

_EXPLAIN_MY_ANSWER_SYSTEM = """\
당신은 BRI610 계산신경과학 박사 과정 세미나의 오류 분석 튜터입니다.
You explain WHY a student's LaTeX derivation is incorrect, using the SymPy residual as evidence.

Rules:
- 한국어 주체 + 영어 전문용어.
- 잔차(residual)의 의미를 수식으로 보여주고, 어디서 틀렸는지 정확히 지적하라.
- Graduate register. Max 250 words.
- End with one concrete corrective question (not the answer).
"""


async def _narrate_step(
    step: WalkthroughStep,
    move: Optional[str],
    move_data: Optional[dict],
    state: WalkthroughState,
    user_input: str,
    extra_context: str = "",
) -> str:
    """Generate tutor narration for the next step or current step continuation."""
    slide_ref_str = ", ".join(step.slide_refs) if step.slide_refs else ""
    cite_block = f"\n참고 슬라이드: [{slide_ref_str}]" if slide_ref_str else ""

    if move == "socratic_exit":
        # Full reveal + re-explain request
        reveal = step.hint_md or step.prompt_md
        user_msg = f"""\
move = socratic_exit
학생이 이 단계에서 3번 실패했습니다. 정답과 완전한 해설을 제공하고, 학생에게 자신의 말로 재설명하도록 요청하세요.

Step prompt:\n{step.prompt_md}{cite_block}
Expected concept: {step.expected_concept}
Hint/Solution:\n{reveal}

학생 입력:\n{user_input[:400]}"""
    elif move == "direct_explanation_with_followup":
        user_msg = f"""\
move = direct_explanation_with_followup
학생이 막혀 있습니다. 핵심 개념을 직접 설명하고 즉시 후속 질문을 하세요.

Step prompt:\n{step.prompt_md}{cite_block}
Expected concept: {step.expected_concept}
{extra_context}
학생 입력:\n{user_input[:400]}"""
    elif move:
        move_target = (move_data or {}).get("target", step.expected_concept)
        move_reason = (move_data or {}).get("reason", "")
        user_msg = f"""\
move = {move}
target: {move_target}
reason: {move_reason}

현재 단계:\n{step.prompt_md}{cite_block}
Expected concept: {step.expected_concept}
{extra_context}
학생 입력:\n{user_input[:400]}

선택된 move({move})에 따라 응답을 생성하세요."""
    else:
        # No move — initial narration of a new step
        user_msg = f"""\
새로운 워크스루 단계를 소개하세요 (move=none, initial narration).

Step prompt:\n{step.prompt_md}{cite_block}
Expected concept: {step.expected_concept}"""

    result = await call_llm(
        role="tutor",
        system=_TUTOR_SYSTEM,
        user=user_msg,
        session_id=state.session_id,
        history=state.history[-6:] if state.history else [],
    )
    return (result.get("text") or "").strip()


async def _explain_my_answer(
    step: WalkthroughStep,
    user_input: str,
    student_lhs: str,
    student_rhs: str,
    residual_latex: str,
    state: WalkthroughState,
) -> str:
    """Generate Explain-My-Answer response for a wrong LaTeX submission."""
    user_msg = f"""\
학생 LaTeX 제출:
  LHS: {student_lhs}
  RHS: {student_rhs}

SymPy 검증 잔차(residual): {residual_latex}

현재 단계에서 기대하는 개념: {step.expected_concept}
기대 정답 (LHS = RHS): {step.expected_lhs} = {step.expected_rhs}

왜 학생 답이 틀렸는지 잔차를 이용해 정확히 설명하고, 정정 유도 질문(corrective question)으로 마무리하세요."""

    result = await call_llm(
        role="explain_my_answer",
        system=_EXPLAIN_MY_ANSWER_SYSTEM,
        user=user_msg,
        session_id=state.session_id,
    )
    return (result.get("text") or "").strip()


# ────────────────────────────────────────────────────────────────
# Public API
# ────────────────────────────────────────────────────────────────

def start_walkthrough(walkthrough_id: str, user_id: int) -> dict:
    """
    Create a new session and return {session_id, first_step}.
    The caller should immediately call step_walkthrough with empty user_input
    to get the first narration.
    """
    wt = get_walkthrough(walkthrough_id)
    if not wt:
        raise ValueError(f"Unknown walkthrough_id: {walkthrough_id!r}")

    session_id = str(uuid.uuid4())
    state = WalkthroughState(
        session_id=session_id,
        walkthrough_id=walkthrough_id,
        lecture_id=wt.lecture_id,
        topic=wt.topic,
        current_step=0,
        attempts=0,
        mode_lock_failures=0,
    )
    _SESSIONS[session_id] = state

    first = wt.steps[0]
    return {
        "session_id": session_id,
        "first_step": {
            "step_id": first.step_id,
            "kind": first.kind,
            "prompt_md": first.prompt_md,
            "slide_refs": first.slide_refs,
            "accepts_latex": first.accepts_latex,
            "step_num": 1,
            "total_steps": wt.num_steps,
        },
    }


def get_session_state(session_id: str) -> Optional[dict]:
    """Return current session state dict for restoration, or None if not found."""
    state = _SESSIONS.get(session_id)
    if not state:
        return None
    wt = get_walkthrough(state.walkthrough_id)
    step = wt.steps[state.current_step] if wt else None
    return {
        "session_id": state.session_id,
        "walkthrough_id": state.walkthrough_id,
        "lecture_id": state.lecture_id,
        "topic": state.topic,
        "current_step": state.current_step,
        "step_id": step.step_id if step else None,
        "attempts": state.attempts,
        "mode_lock_failures": state.mode_lock_failures,
        "is_complete": state.is_complete,
        "total_steps": wt.num_steps if wt else 0,
    }


async def step_walkthrough(
    session_id: str,
    user_input: str,
    latex_attempt: Optional[str] = None,
) -> dict:
    """
    Main walkthrough step function.

    Args:
        session_id:     Active session UUID.
        user_input:     Student's text submission (may be empty for first narration).
        latex_attempt:  Optional separate LaTeX string (used when student submits
                        LaTeX via the dedicated textarea rather than inline $...$).

    Returns dict:
        {
          step_id, narration_md, move_used, verifier_result,
          input_gate: {required, missing},
          is_complete,
          mode_lock_failures,
          step_num, total_steps,
        }

    Raises:
        ValueError  — session not found or walkthrough not found
        ValueError  — with message starting "GATE:" when gate check fails (caller
                      translates to 422)
    """
    state = _SESSIONS.get(session_id)
    if not state:
        raise ValueError(f"Session not found: {session_id!r}")

    wt = get_walkthrough(state.walkthrough_id)
    if not wt:
        raise ValueError(f"Walkthrough not found: {state.walkthrough_id!r}")

    if state.is_complete:
        return {
            "step_id": None,
            "narration_md": "**워크스루가 이미 완료되었습니다.** 새 세션을 시작하거나 다른 워크스루를 선택하세요.",
            "move_used": None,
            "verifier_result": None,
            "input_gate": {"required": [], "missing": []},
            "is_complete": True,
            "mode_lock_failures": state.mode_lock_failures,
            "step_num": wt.num_steps,
            "total_steps": wt.num_steps,
        }

    step = wt.steps[state.current_step]

    # ── Case 1: Initial narration (no user input yet) ─────────────────────────
    if not user_input.strip():
        narration = await _narrate_step(
            step=step, move=None, move_data=None,
            state=state, user_input="",
        )
        return {
            "step_id": step.step_id,
            "narration_md": narration,
            "move_used": None,
            "verifier_result": None,
            "input_gate": {
                "required": [f[0] for f in _GATE_FIELDS] if step.kind in _GATE_REQUIRED_KINDS else [],
                "missing": [],
            },
            "is_complete": False,
            "mode_lock_failures": state.mode_lock_failures,
            "step_num": state.current_step + 1,
            "total_steps": wt.num_steps,
        }

    # ── Case 2: Student submitted input ──────────────────────────────────────

    # 2a. Structured-input gate
    missing_fields = _check_structured_gate(step, user_input)
    if missing_fields:
        return {
            "step_id": step.step_id,
            "narration_md": None,
            "move_used": None,
            "verifier_result": None,
            "input_gate": {
                "required": [f[0] for f in _GATE_FIELDS],
                "missing": missing_fields,
            },
            "is_complete": False,
            "mode_lock_failures": state.mode_lock_failures,
            "step_num": state.current_step + 1,
            "total_steps": wt.num_steps,
            "gate_error": True,
        }

    # Append to history
    state.history.append({"role": "user", "content": user_input[:1000]})
    state.attempts += 1

    # 2b. Consultant picks move
    move_data = await pick_move(step=step, state=state, user_input=user_input)
    move = move_data.get("move", "direct_explanation_with_followup")

    # 2c. LaTeX verification (if applicable)
    verifier_result = None
    narration = ""

    # Determine LaTeX to verify
    latex_to_verify = latex_attempt or ""
    if not latex_to_verify and step.accepts_latex:
        extracted = _extract_latex(user_input)
        if extracted:
            student_lhs, student_rhs = extracted
            latex_to_verify = f"{student_lhs} = {student_rhs}"

    if step.accepts_latex and latex_to_verify and step.expected_lhs:
        # Parse student LHS/RHS
        if "=" in latex_to_verify:
            parts = latex_to_verify.split("=", 1)
            student_lhs = parts[0].strip()
            student_rhs = parts[1].strip()
        else:
            student_lhs = latex_to_verify.strip()
            student_rhs = ""

        try:
            vr = verify_equation(student_lhs, student_rhs)
            status = getattr(vr, "status", None)
            if status is not None:
                status_str = status.value if hasattr(status, "value") else str(status)
            else:
                status_str = "unverified"
            residual = getattr(vr, "residual_latex", "") or ""
            verifier_result = {
                "status": status_str,
                "layer": getattr(vr, "layer", "sympy"),
                "residual_latex": residual,
                "elapsed_ms": getattr(vr, "elapsed_ms", 0),
            }

            if status_str == "wrong":
                state.mode_lock_failures += 1
                narration = await _explain_my_answer(
                    step=step,
                    user_input=user_input,
                    student_lhs=student_lhs,
                    student_rhs=student_rhs,
                    residual_latex=residual,
                    state=state,
                )
                # After narration, re-check if now at threshold
                if state.mode_lock_failures >= 3:
                    move = "socratic_exit"
                    move_data["move"] = move
                    # Generate fresh socratic_exit narration
                    narration = await _narrate_step(
                        step=step, move=move, move_data=move_data,
                        state=state, user_input=user_input,
                    )
            elif status_str in ("correct", "equivalent"):
                # Correct answer — advance step
                narration = await _advance_step(wt, state, step, move_data, user_input)
                state.history.append({"role": "assistant", "content": narration[:600]})
                return _build_response(step, state, wt, narration, move_data, verifier_result)
        except Exception as exc:
            log.warning("verifier raised: %s", exc)
            verifier_result = {"status": "unverified", "layer": "error", "residual_latex": "", "elapsed_ms": 0}

    # 2d. If no verifier or verifier not wrong: generate narration from move
    if not narration:
        if move == "socratic_exit" or state.mode_lock_failures >= 3:
            move = "socratic_exit"
            move_data["move"] = move
            narration = await _narrate_step(
                step=step, move=move, move_data=move_data,
                state=state, user_input=user_input,
            )
        elif step.kind in ("explain", "checkpoint") or move in (
            "direct_explanation_with_followup", "analogy", "prerequisite_check",
            "counterexample", "dimensional_analysis", "limiting_case",
        ):
            # For explain/checkpoint steps or non-derivation moves: may advance
            narration = await _narrate_step(
                step=step, move=move, move_data=move_data,
                state=state, user_input=user_input,
            )
            # Advance if step was explain/checkpoint (no verification needed)
            if step.kind in ("explain", "checkpoint"):
                adv_narration = await _advance_step(wt, state, step, move_data, user_input)
                if adv_narration:
                    narration = adv_narration
        else:
            narration = await _narrate_step(
                step=step, move=move, move_data=move_data,
                state=state, user_input=user_input,
            )

    state.history.append({"role": "assistant", "content": narration[:600]})
    return _build_response(step, state, wt, narration, move_data, verifier_result)


async def _advance_step(
    wt: WalkthroughMeta,
    state: WalkthroughState,
    current_step: WalkthroughStep,
    move_data: dict,
    user_input: str,
) -> str:
    """Advance state to next step and narrate it. Returns narration text."""
    next_idx = state.current_step + 1
    if next_idx >= len(wt.steps):
        state.is_complete = True
        state.current_step = len(wt.steps) - 1
        # Final completion message
        comp_result = await call_llm(
            role="tutor",
            system=_TUTOR_SYSTEM,
            user=f"워크스루 '{wt.title_ko}'의 모든 단계를 성공적으로 완료했습니다. 학생을 격려하고 핵심 takeaway를 간결하게(3줄 이내) 요약하세요.",
            session_id=state.session_id,
        )
        return (comp_result.get("text") or "").strip()

    state.current_step = next_idx
    state.attempts = 0
    next_step = wt.steps[next_idx]
    return await _narrate_step(
        step=next_step, move=None, move_data=None,
        state=state, user_input="",
    )


def _build_response(
    step: WalkthroughStep,
    state: WalkthroughState,
    wt: WalkthroughMeta,
    narration: str,
    move_data: dict,
    verifier_result: Optional[dict],
) -> dict:
    current_step_obj = wt.steps[state.current_step]
    return {
        "step_id": current_step_obj.step_id,
        "narration_md": narration,
        "move_used": move_data.get("move"),
        "move_reason": move_data.get("reason"),
        "verifier_result": verifier_result,
        "input_gate": {
            "required": [f[0] for f in _GATE_FIELDS]
            if current_step_obj.kind in _GATE_REQUIRED_KINDS else [],
            "missing": [],
        },
        "is_complete": state.is_complete,
        "mode_lock_failures": state.mode_lock_failures,
        "step_num": state.current_step + 1,
        "total_steps": wt.num_steps,
    }
