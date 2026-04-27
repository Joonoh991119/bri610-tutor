"""
QuestionGenerator agent — P7.2 of the v0.5 plan.

Generates ONE PhD-rigor bank item per call, grounded in lecture slides
retrieved via RAG.  All mandates from:
  - memory/feedback_phd_rigor.md   (per-type rubric)
  - memory/feedback_lecture_only_scope.md  (slides-only primary citation)

Usage (from scripts/generate_bank_v2.py or tests):
    from agents.question_generator import generate_question
    item = await generate_question(
        topic="HH", card_type="proof", difficulty=4, bloom="Analyze",
        slide_context="...", slide_refs=[{lecture, page, title}, ...],
        mastery_target="HH_markov_reduction",
    )
"""
from __future__ import annotations

import json
import logging
import re
from typing import Optional

log = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────
# System prompt — encodes both rubrics verbatim
# ──────────────────────────────────────────────────────────────────

_SYSTEM_TEMPLATE = """\
당신은 BRI610 전산신경과학 (SNU BCS) 문제 은행 생성기입니다.
You are the BRI610 computational neuroscience question-bank generator for SNU BCS.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[A] 대상 학습자 / TARGET LEARNER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
박사과정 수준 (PhD-level) — 단순 암기가 아닌 가정(assumption), 식별성(identifiability),
경계 조건(boundary condition), 비선형 시스템의 한계, 방법론적 함정 등을 다루어야 합니다.
"알아봅시다" 어조 금지. 대학원 세미나 수준 ("우리는 다음을 보인다") 사용.

─────────────────────────────────────────────
[B] 카드 유형별 필수 기준 / PER-TYPE MANDATORY RUBRIC
─────────────────────────────────────────────

recall (난이도 2–3):
  • 공식 하나를 단순히 "쓰시오"는 거부 기준.
  • 반드시: 공식 + 그 공식이 성립하는 체제/가정 명시 + 매개변수 식별성 힌트.
  예: "HH g_K = g̅_K n⁴ 를 쓰고, 이 표현이 실패하는 두 조건을 서술하라."

concept (난이도 3–4):
  • 반드시: 두 관점 이상 대비 (열역학적 vs 운동학적; 결정론적 vs 확률론적;
    단일구획 vs cable; 속도코드 vs 시간코드 등).
  • 순수 정의형 답으로 PASS 불가.

application (난이도 3–5):
  • 반드시: 절차 수준 질문 (데이터셋 X와 조건 Y가 주어졌을 때 분석 단계 서술,
    매개변수 식별성 확인, 경계조건, 적합 함수 형식, 예상 실패 모드 포함).
  • 수치 응용은 반드시 차원 분석 및 자릿수 추정 포함 (단순 대입 금지).

proof (난이도 4–5):
  • 반드시: 비자명한 중간 단계 포함 (변수 분리, 기저 변환, 극한/한계 케이스,
    차원적으로 비자명한 상쇄, 다중 상태 Markov 축약 등).
  • 각 단계에서 사용되는 가정을 명시해야 함.
  • 마지막에 건전성 검사 (limiting case, 차원 확인, 알려진 결과와의 일치) 필수.

─────────────────────────────────────────────
[C] 인용 규칙 / CITATION RULES (강제)
─────────────────────────────────────────────
1. 반드시 primary citation = slide (kind = 'slide').
   아래 slide_refs 화이트리스트에서만 인용하십시오:
   {slide_refs_block}

2. 교재 (Dayan & Abbott, FN)는 rationale_md 내 선택적 심화 참고문헌으로만 허용.
   예: "더 깊은 유도는 Dayan & Abbott Ch.5 §5.6 참조."

3. 저명 원저 논문 (Hodgkin & Huxley 1952, Goldman 1943, Rall 1962, ...)은
   source_citation.primary 필드에 슬라이드 인용과 함께 허용. 슬라이드가 명시적으로
   그 논문을 참조할 때만 사용.

─────────────────────────────────────────────
[D] 언어 규칙 / LANGUAGE RULES
─────────────────────────────────────────────
• 본문(prompt_md, answer_md, rationale_md): 한국어 (Korean).
• 기술 용어: 영문 그대로 (예: conductance, gating variable, leak current).
• STEM 표준 용어 사용: 막전위, 평형전위, 게이팅 변수 (멤브레인 포텐셜 금지).
• LaTeX: $...$ (inline), $$...$$ (display). KaTeX-compatible.

─────────────────────────────────────────────
[E] 오개념 레이어 / MISCONCEPTION LAYER (필수)
─────────────────────────────────────────────
rationale_md 에 반드시 "**흔한 오류**:" 또는 "**Common error**:" 로 시작하는
구체적인 학생 오류를 이름을 붙여 명시해야 합니다. 단순히 정답을 반복하는 것 금지.

─────────────────────────────────────────────
[F] 교차 주제 연계 / CROSS-TOPIC LINKAGE
─────────────────────────────────────────────
자연스러울 때 다른 주제와 명시적으로 연결. 예:
  "**Cross-link**: HH ↔ cable — 케이블 방정식의 능동 전도 항이 HH 게이팅을 직접 사용함."
  "**Cross-link**: Nernst ↔ ion-channel kinetics — GHK 전류 식과 NMDA 마그네슘 블록."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[G] 출력 형식 / OUTPUT FORMAT (strict JSON, no extra text)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Return EXACTLY one JSON object. No markdown fence, no preamble, no trailing text.

{{
  "prompt_md":       "<한국어 문제. LaTeX OK. 반드시 **Setup** 블록으로 시작. 세부 질문 (a)(b) 포함>",
  "answer_md":       "<단계별 한국어 해답. 수식 LaTeX. (a)(b) 구조 유지>",
  "rationale_md":    "<한국어. 오개념 레이어 필수. 교차 연결 포함. 선택적 교재 심화 참고>",
  "source_citation": {{
    "kind":    "slide",
    "lecture": "<e.g. L5>",
    "page":    <int>,
    "primary": "<선택: 원저 논문 APA 약식, 슬라이드가 해당 논문 인용 시>"
  }},
  "mastery_target":  "<concept id string>"
}}
"""

_RETRY_SYSTEM_TEMPLATE = """\
이전 응답이 유효한 JSON이 아니었습니다. 반드시 순수 JSON 객체만 반환하십시오.
코드 펜스(```), 서문, 후문 일체 금지. 키: prompt_md, answer_md, rationale_md,
source_citation (kind, lecture, page, primary), mastery_target.
이전 응답:
{previous_response}
"""

_USER_TEMPLATE = """\
다음 슬라이드 컨텍스트를 바탕으로 주어진 조건의 문제 1개를 생성하십시오.

## 생성 조건
- 주제 (topic): {topic}
- 카드 유형 (card_type): {card_type}
- 난이도 (difficulty): {difficulty} / 5
- Bloom 수준 (bloom): {bloom}
- 목표 숙련 개념 (mastery_target): {mastery_target}

## 슬라이드 컨텍스트 (RAG 검색 결과)
{slide_context}

## 슬라이드 인용 화이트리스트
{slide_refs_block}

## 지시사항
1. 위 [A]–[F] 규칙을 모두 준수하십시오.
2. source_citation.lecture 와 source_citation.page 는 반드시 위 화이트리스트 중에서 선택.
3. 순수 JSON만 반환. 마크다운 펜스 없음.
"""


# ──────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────

def _build_slide_refs_block(slide_refs: list[dict]) -> str:
    if not slide_refs:
        return "(no slides retrieved — use best available lecture reference)"
    lines = []
    for r in slide_refs:
        lec   = r.get("lecture", "?")
        page  = r.get("page", "?")
        title = r.get("title", "")
        lines.append(f"  - lecture={lec}, page={page}  [{title}]")
    return "\n".join(lines)


def _extract_json(text: str) -> Optional[dict]:
    """
    Extract first JSON object from LLM response.
    Handles code-fence wrapping and leading/trailing prose.
    """
    if not text:
        return None
    # strip ```json ... ``` or ``` ... ``` wrappers
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = text.replace("```", "")
    # find first { ... } spanning the full depth
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                blob = text[start:i+1]
                try:
                    return json.loads(blob)
                except json.JSONDecodeError:
                    return None
    return None


def _validate_item(item: dict, slide_refs: list[dict]) -> list[str]:
    """
    Return list of validation errors. Empty list = OK.
    Enforces:
      - required keys present and non-empty
      - source_citation.kind == 'slide'
      - source_citation.lecture + page present
    """
    errors: list[str] = []
    required = ("prompt_md", "answer_md", "rationale_md", "source_citation", "mastery_target")
    for k in required:
        if not item.get(k):
            errors.append(f"Missing or empty key: {k}")

    cit = item.get("source_citation") or {}
    if not isinstance(cit, dict):
        errors.append("source_citation must be a dict")
        return errors

    if cit.get("kind") != "slide":
        errors.append(f"source_citation.kind = {cit.get('kind')!r} — must be 'slide'")

    if not cit.get("lecture"):
        errors.append("source_citation.lecture is missing")
    if not cit.get("page"):
        errors.append("source_citation.page is missing")

    # Warn (not hard-error) if lecture not in whitelist
    if slide_refs and cit.get("lecture"):
        valid_lectures = {r.get("lecture") for r in slide_refs}
        if cit["lecture"] not in valid_lectures:
            log.warning(
                "source_citation.lecture=%r not in slide_refs whitelist %s",
                cit["lecture"], valid_lectures,
            )

    return errors


# ──────────────────────────────────────────────────────────────────
# Public entry point
# ──────────────────────────────────────────────────────────────────

async def generate_question(
    *,
    topic: str,
    card_type: str,              # 'recall'|'concept'|'application'|'proof'
    difficulty: int,             # 1..5
    bloom: str,                  # Bloom level matching difficulty
    slide_context: str,          # retrieved slide content (RAG result)
    slide_refs: list[dict],      # [{lecture, page, title}] — whitelist for citation
    mastery_target: str,
) -> Optional[dict]:
    """
    Generate ONE bank-quality item.

    Returns a validated dict with keys:
        prompt_md, answer_md, rationale_md, source_citation, mastery_target
    Returns None if generation fails after one retry.

    Uses harness.llm_client.call_llm(role='quiz_generator', ...) which cascades
    through OpenRouter → Ollama qwen2.5:14b-instruct on failures.
    """
    # Import here to avoid circular import at package level
    from harness.llm_client import call_llm  # type: ignore[import]

    slide_refs_block = _build_slide_refs_block(slide_refs)

    system_prompt = _SYSTEM_TEMPLATE.format(
        slide_refs_block=slide_refs_block,
    )
    user_prompt = _USER_TEMPLATE.format(
        topic=topic,
        card_type=card_type,
        difficulty=difficulty,
        bloom=bloom,
        mastery_target=mastery_target,
        slide_context=slide_context[:4000] if slide_context else "(none)",
        slide_refs_block=slide_refs_block,
    )

    log.info(
        "QuestionGenerator: topic=%s type=%s diff=%d bloom=%s",
        topic, card_type, difficulty, bloom,
    )

    # ── First attempt ──────────────────────────────────────────────
    result = await call_llm(
        role="quiz_generator",
        system=system_prompt,
        user=user_prompt,
        temperature=0.5,
        max_tokens=2500,
    )

    if result.get("error"):
        log.error("QuestionGenerator LLM error on first attempt: %s", result["error"])
        raw_text = ""
    else:
        raw_text = result.get("text", "")

    log.debug(
        "QuestionGenerator raw response (first 300): %r route=%s",
        raw_text[:300], result.get("route_used"),
    )

    item = _extract_json(raw_text)

    # ── Retry with stricter prompt if parse failed ─────────────────
    if item is None:
        log.warning(
            "QuestionGenerator: JSON parse failed on first attempt (topic=%s %s); "
            "raw_text[:200]=%r; retrying...",
            topic, card_type, raw_text[:200],
        )
        retry_system = (
            system_prompt
            + "\n\n"
            + _RETRY_SYSTEM_TEMPLATE.format(previous_response=raw_text[:1000])
        )
        retry_user = (
            "출력은 JSON 객체 하나만. 서문도 후문도 없이. "
            "반드시 prompt_md, answer_md, rationale_md, source_citation, mastery_target 키 포함.\n\n"
            + user_prompt
        )
        result2 = await call_llm(
            role="quiz_generator",
            system=retry_system,
            user=retry_user,
            temperature=0.3,
            max_tokens=2500,
        )
        raw_text2 = result2.get("text", "")
        item = _extract_json(raw_text2)

    if item is None:
        log.error(
            "QuestionGenerator: JSON parse failed on retry too (topic=%s %s). Returning None.",
            topic, card_type,
        )
        return None

    # ── Validate ───────────────────────────────────────────────────
    errors = _validate_item(item, slide_refs)
    if errors:
        log.warning(
            "QuestionGenerator: item for topic=%s %s has validation issues: %s",
            topic, card_type, errors,
        )
        # Fix kind if it got set wrong — hard constraint
        cit = item.get("source_citation")
        if isinstance(cit, dict):
            if cit.get("kind") != "slide":
                log.warning("Overriding source_citation.kind to 'slide'")
                cit["kind"] = "slide"
            # If no valid lecture from whitelist, pick first ref
            if slide_refs and not cit.get("lecture"):
                cit["lecture"] = slide_refs[0]["lecture"]
                cit["page"] = slide_refs[0].get("page", 1)

    # ── Inject mastery_target if LLM left it out ───────────────────
    if not item.get("mastery_target"):
        item["mastery_target"] = mastery_target

    return item
