"""
Persona narrator (P8.2): wraps Tutor / Derive / Summary text with `뉴런쌤` voice.

Why: per `feedback_v05_user_requirements.md` R3 — "Interactive, addictive UI + persona".
Why a post-processor (not a baked-in system prompt): the persona must EVOLVE per
session — referencing the user's last topic, recent struggle, streak day. A static
system-prompt persona can't do that. This wrapper has access to per-user context.

Why cheap free-tier: persona styling doesn't need SOTA reasoning; it needs Korean
fluency, which Qwen3-30B-a3b handles.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from harness import call_llm

DEFAULT_NAME = "뉴런쌤"


@dataclass
class PersonaContext:
    name: str = DEFAULT_NAME
    last_topic: Optional[str] = None        # e.g., "HH gating"
    streak_days: int = 0
    recent_struggle: Optional[str] = None   # e.g., "Nernst sign convention"
    daily_goal_met: bool = False
    user_display_name: Optional[str] = None  # e.g., "준오"


_PERSONA_SYSTEM_TEMPLATE = """당신은 BRI610 컴퓨터신경과학 튜터의 페르소나 '뉴런쌤'입니다.
You wrap an upstream Tutor's response with a brief, warm Korean opener and (optionally) a closer.

페르소나:
  - 이름: {name}
  - 톤: 친근한 선배 연구자. 압도하지 않음. 학생 입장에서 함께 생각함.
  - 한국어 기본. 영어 전문용어는 그대로.
  - 이모지 사용 안 함.
  - 단답·과장·인사말 남발 금지. 한 줄 오프닝 + 본문 + 한 줄 마무리.

컨텍스트 (있으면 활용):
  - 최근 다룬 주제: {last_topic}
  - 학생이 최근 어려워한 부분: {recent_struggle}
  - 연속 학습일: {streak_days}일
  - 오늘 목표 달성 여부: {daily_goal_met}
  - 학생 이름 (호칭 가능): {user_display_name}

작업: 아래 본문을 그대로 보존(특히 LaTeX 수식 $...$, 코드블록, 인용 [Slide L# p#])하면서,
앞과 뒤에 짧은 페르소나 발화를 자연스럽게 끼워넣으세요.
스트릭이 있다면 짧게 격려, 최근 어려움이 있다면 잇기 문장.

출력은 새 본문 markdown만. 메타 코멘트 금지."""


def _format_system(ctx: PersonaContext) -> str:
    return _PERSONA_SYSTEM_TEMPLATE.format(
        name=ctx.name or DEFAULT_NAME,
        last_topic=ctx.last_topic or "(none)",
        recent_struggle=ctx.recent_struggle or "(none)",
        streak_days=ctx.streak_days,
        daily_goal_met="달성" if ctx.daily_goal_met else "아직",
        user_display_name=ctx.user_display_name or "학생",
    )


async def wrap_with_persona(
    text: str,
    ctx: Optional[PersonaContext] = None,
    *,
    skip_if_short: int = 50,
) -> str:
    """
    Post-process an agent's text response with persona voice.

    `skip_if_short`: if the text is shorter than this many chars (e.g., a one-line
    derivation step), skip wrapping — overhead noise > value.
    """
    if not text or len(text.strip()) < skip_if_short:
        return text
    ctx = ctx or PersonaContext()
    res = await call_llm(
        role="persona_narrator",
        system=_format_system(ctx),
        user=f"본문:\n{text}\n\n위 본문을 페르소나 발화로 감싸 출력하시오.",
        cache=False,
    )
    return (res["text"] or text).strip()
