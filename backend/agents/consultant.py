"""
backend.agents.consultant — KELE Consultant-Teacher agent.

Implements the KELE 8-move taxonomy for pedagogical strategy selection.
Given the student's latest input and the current walkthrough state, picks
exactly ONE move and returns it as structured JSON.

Move taxonomy (BRI610 8-move):
  analogy                      — explain via cross-domain analogy
  prerequisite_check           — probe whether a prereq concept is solid
  derivation_prompt            — redirect to do the derivation themselves
  counterexample               — surface a case that breaks their assumption
  dimensional_analysis         — guide through a dimension/unit check
  limiting_case                — apply a known limit to test consistency
  direct_explanation_with_followup — explain directly, then pose a follow-up
  socratic_exit                — full solution reveal + re-explain in own words

LLM call: harness.call_llm(role='consultant', ..., temperature=0.0)
Returns: {"move": str, "target": str, "reason": str}
"""
from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING

from harness import call_llm

if TYPE_CHECKING:
    from .walkthrough import WalkthroughState, WalkthroughStep

log = logging.getLogger(__name__)

VALID_MOVES = frozenset({
    "analogy",
    "prerequisite_check",
    "derivation_prompt",
    "counterexample",
    "dimensional_analysis",
    "limiting_case",
    "direct_explanation_with_followup",
    "socratic_exit",
})

_SYSTEM_PROMPT = """\
당신은 BRI610 계산신경과학(Computational Neuroscience) 대학원 세미나의 KELE 컨설턴트-교사(consultant-teacher)입니다.
You are a KELE consultant-teacher in a BRI610 Computational Neuroscience PhD seminar.

## 역할 (Role)
학생의 답변 및 현재 학습 단계를 분석하여 **정확히 하나의 교수 전략(pedagogical move)**을 선택합니다.
Analyze the student's response and current walkthrough step, then choose exactly ONE pedagogical move.

## 8-Move Taxonomy
1. **analogy** — 다른 물리/수학 도메인의 유추로 개념 재설명.
   *Use when*: 학생이 올바른 수식은 알지만 물리적 직관이 부재할 때.
2. **prerequisite_check** — 선행 개념(미적분, 열역학, Markov 과정 등) 이해 여부 점검.
   *Use when*: 학생의 오류가 현재 개념이 아닌 선행 개념에서 기인할 때.
3. **derivation_prompt** — 학생 스스로 유도(derivation)를 시도하도록 구체적 단계 제시.
   *Use when*: 학생이 답을 암기했거나 결과만 말할 때.
4. **counterexample** — 학생의 가정을 무너뜨리는 반례 제시.
   *Use when*: 학생의 답이 특수 경우에만 맞는 일반화 오류일 때.
5. **dimensional_analysis** — 차원 분석으로 식의 정합성 검증 유도.
   *Use when*: 학생의 식이 차원적으로 불일치하거나 단위 감각이 없을 때.
6. **limiting_case** — 극한 조건(α_n >> β_n, x→∞ 등)에서 식 검증.
   *Use when*: 학생의 답이 형식적으로 옳아 보이나 극한 거동 이해가 불확실할 때.
7. **direct_explanation_with_followup** — 직접 설명 후 즉시 후속 질문.
   *Use when*: 학생이 3번 이상 실패하거나 완전히 막혔을 때.
8. **socratic_exit** — 정답 전체 공개 + 학생 자신의 말로 재설명 요청.
   *Use when*: mode_lock_failures ≥ 3 이거나 완전한 막힘이 명백할 때.

## 출력 형식 (Output — JSON ONLY, no markdown)
{"move": "<move_name>", "target": "<specific_concept_or_formula>", "reason": "<1–2 sentences in Korean>"}

출력은 반드시 위 JSON 하나만. 설명 없음.
Output ONLY the JSON object above. No prose, no code fences."""


def _build_user_prompt(
    step: "WalkthroughStep",
    user_input: str,
    mode_lock_failures: int,
    attempts: int,
    history_tail: list[dict],
) -> str:
    history_str = ""
    if history_tail:
        history_str = "\n\n## 최근 대화 (Recent history, last 3 turns)\n"
        for h in history_tail[-3:]:
            role_label = "학생" if h.get("role") == "user" else "튜터"
            history_str += f"**{role_label}**: {h.get('content', '')[:200]}\n"

    return f"""\
## 현재 워크스루 단계 (Current walkthrough step)
- step_id: {step.step_id}
- kind: {step.kind}
- expected_concept: {step.expected_concept}
- accepts_latex: {step.accepts_latex}

## 학생 입력 (Student input)
{user_input[:600]}

## 상태 (State)
- mode_lock_failures: {mode_lock_failures} (socratic_exit threshold = 3)
- attempts on this step: {attempts}
{history_str}

어떤 move를 선택하겠습니까? JSON만 출력하세요."""


async def pick_move(
    step: "WalkthroughStep",
    state: "WalkthroughState",
    user_input: str,
) -> dict:
    """
    Returns dict with keys: move, target, reason.
    On any failure, falls back to direct_explanation_with_followup.
    """
    # Immediate override: mode_lock_failures >= 3 → always socratic_exit
    if state.mode_lock_failures >= 3:
        return {
            "move": "socratic_exit",
            "target": step.expected_concept,
            "reason": f"3번 실패 누적 — 정답을 공개하고 학생 스스로 재설명하도록 유도합니다. (mode_lock_failures={state.mode_lock_failures})",
        }

    user_prompt = _build_user_prompt(
        step=step,
        user_input=user_input,
        mode_lock_failures=state.mode_lock_failures,
        attempts=state.attempts,
        history_tail=state.history,
    )

    result = await call_llm(
        role="consultant",
        system=_SYSTEM_PROMPT,
        user=user_prompt,
        temperature=0.0,
        max_tokens=300,
        session_id=state.session_id,
    )

    raw = (result.get("text") or "").strip()
    # Strip possible code fences the model may emit despite instructions
    raw = re.sub(r"^```[a-zA-Z]*\n?", "", raw).rstrip("`").strip()

    try:
        parsed = json.loads(raw)
        move = parsed.get("move", "")
        if move not in VALID_MOVES:
            log.warning("consultant returned invalid move '%s'; falling back", move)
            parsed["move"] = "direct_explanation_with_followup"
        return parsed
    except (json.JSONDecodeError, AttributeError):
        log.warning("consultant returned non-JSON: %r; falling back", raw[:200])
        return {
            "move": "direct_explanation_with_followup",
            "target": step.expected_concept,
            "reason": "LLM 응답 파싱 실패 — 직접 설명으로 전환합니다.",
        }
