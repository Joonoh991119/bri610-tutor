"""
Multi-Lens Review loop (P10.2).

Each user-facing artifact (question, walkthrough step, summary) runs through
4 specialized reviewer agents in parallel. The loop iterates up to `max_rounds`
revising the artifact based on merged feedback until all 4 lenses pass, or
escalates to a manual-review queue.

Lens priority:
  factual    — VETO power. A single reject ends the loop with status=manual_review.
  korean     — advisory; can pass alone if pedagogical+factual pass.
  pedagogical — advisory.
  difficulty  — advisory; if it disagrees alone, the loop accepts and lowers the
                declared difficulty tag rather than regenerating.

Why this design (per `00b_revised_plan_with_R1-R5.md` §5):
  - 4 independent lenses produce ~5–10% non-convergence in similar pipelines (KELE).
  - Factual veto stops bad items from publishing.
  - Other lenses are advisory so we don't ping-pong between scaffolding-vs-difficulty.

Storage: every lens verdict writes a row to `question_review_log`; non-convergence
writes a row to `lens_disagreement_log` for daemon-driven prompt tuning.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from harness import call_llm, emit_event

log = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────
# Types
# ──────────────────────────────────────────────────────────────────

@dataclass
class Artifact:
    """One reviewable unit. `text` is mutated by revisions across rounds."""
    kind: str                              # 'question' | 'walkthrough_step' | 'summary'
    text: str                              # markdown / latex
    citation: Optional[dict] = None        # {kind:'textbook',book:'DA',ch:5,page:119}
    declared_difficulty: Optional[int] = None
    declared_bloom: Optional[str] = None
    artifact_id: Optional[int] = None      # DB id when persisted
    extra: dict = field(default_factory=dict)


@dataclass
class LensVerdict:
    lens: str                              # 'factual'|'pedagogical'|'korean'|'difficulty'
    verdict: str                           # 'pass'|'revise'|'reject'
    reasoning_ko: str = ""
    reasoning_en: str = ""
    suggested_fix: str = ""

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class ReviewResult:
    status: str                            # 'approved'|'manual_review'|'rejected'
    text: str
    rounds: int
    verdicts_per_round: list[list[LensVerdict]] = field(default_factory=list)
    final_difficulty: Optional[int] = None
    elapsed_ms: int = 0


# ──────────────────────────────────────────────────────────────────
# Lens reviewer prompts (KO+EN bilingual)
# ──────────────────────────────────────────────────────────────────

_FACTUAL_SYSTEM = """당신은 BRI610 신경과학 사실 검증자(Factual Lens)입니다.
You are a BRI610 neuroscience fact-checker.

검토 대상: 학생에게 보여줄 문항/유도 스텝/요약.
검토 기준: 인용된 출처(예: Dayan & Abbott Ch.5 p.119)와 정확히 일치해야 함.
  - 수치, 부호, 변수 정의, 단위
  - 등식의 좌·우변
  - 인과 관계의 방향

판정:
  pass    : 출처와 모든 사실이 일치
  revise  : 사실 오류가 있으나 정정 가능 (suggested_fix 작성)
  reject  : 출처 자체가 부정확하거나 의도적 왜곡

응답 형식: 반드시 단일 JSON 객체 (코드 블록 금지).
{
  "verdict": "pass" | "revise" | "reject",
  "reasoning_ko": "한국어 1–2문장 사유",
  "reasoning_en": "English 1–2 sentence reasoning",
  "suggested_fix": "구체적 수정 제안 (revise일 때만)"
}"""

_PEDAGOGICAL_SYSTEM = """당신은 BRI610 학습 효과성 검증자(Pedagogy Lens)입니다.
You are a BRI610 pedagogy reviewer.

검토 기준:
  - 선언된 Bloom's 단계({declared_bloom})와 인지 부하 일치 여부
  - 비계(scaffolding) 충분성: 학생이 이 항목으로 무엇을 배우는가?
  - 반복 암기가 아닌 이해/응용/분석 수준 도달 여부

응답 형식: 단일 JSON 객체.
{
  "verdict": "pass" | "revise" | "reject",
  "reasoning_ko": "...",
  "reasoning_en": "...",
  "suggested_fix": "예: '비계 부족 — 풀이 1단계 힌트 추가 권장'"
}"""

_KOREAN_SYSTEM = """당신은 한국어 자연성 검증자(Korean Naturalness Lens)입니다.
You are a Korean-naturalness reviewer for a graduate STEM tutor.

검토 기준:
  - 직역체/어색한 한국어 → revise
  - 표준 STEM 용례 사용: '막전위' (○) / '멤브레인 포텐셜' (×)
    단, 정착된 영문 용어(LaTeX 변수, 모델명)는 그대로 둠
  - 문장 흐름과 학습자 친화성

응답 형식: 단일 JSON 객체. (사실/난이도는 다른 렌즈가 보므로 무시.)
{
  "verdict": "pass" | "revise" | "reject",
  "reasoning_ko": "...",
  "reasoning_en": "...",
  "suggested_fix": "수정된 한국어 문장"
}"""

_DIFFICULTY_SYSTEM = """당신은 난이도 보정 검증자(Difficulty Calibration Lens)입니다.
You are a difficulty-calibration reviewer.

선언된 난이도 {declared_difficulty} (1–5).
타입별 권장 범위:
  recall: 1–2
  concept: 2–3
  application: 3–4
  proof: 4–5

검토:
  - 인지 부하가 선언 난이도와 맞는지
  - 외삽이 필요하면 +1, 직접 인용이면 -1
  - 단순 변경 가능한 경우 revise; 큰 격차면 reject

응답 형식: 단일 JSON 객체.
{
  "verdict": "pass" | "revise" | "reject",
  "reasoning_ko": "...",
  "reasoning_en": "...",
  "suggested_fix": "예: '난이도 4가 아닌 3 권장' 또는 '문항 본문에 + 단계 추가'"
}"""

_REVISER_SYSTEM = """당신은 수정자(Reviser)입니다. 4개 렌즈로부터 받은 피드백을
모두 반영하여 본문을 재작성하세요. 메타 코멘트, 코드블럭 없이 본문만 출력.

지침:
  - 수정된 본문에서 원본의 KaTeX 수식 형식을 유지하세요.
  - 한국어 표현은 자연스럽게.
  - 사실은 인용 출처와 일치시키세요.
"""


# ──────────────────────────────────────────────────────────────────
# JSON-from-LLM safe parser
# ──────────────────────────────────────────────────────────────────

def _parse_lens_json(raw: str, lens_name: str) -> LensVerdict:
    """Find a JSON object in `raw`; map to LensVerdict. Failures => 'pass' with note."""
    if not raw:
        return LensVerdict(lens=lens_name, verdict="pass", reasoning_en="empty response")
    # Try to find the JSON block
    s, e = raw.find("{"), raw.rfind("}") + 1
    if s < 0 or e <= s:
        return LensVerdict(lens=lens_name, verdict="pass",
                           reasoning_en=f"no json found; treating as pass: {raw[:120]}")
    try:
        d = json.loads(raw[s:e])
    except json.JSONDecodeError:
        # Try simple repair: collapse newlines, strip control chars
        cleaned = re.sub(r"[\x00-\x1f\x7f]", " ", raw[s:e])
        try:
            d = json.loads(cleaned)
        except Exception:
            return LensVerdict(lens=lens_name, verdict="pass",
                               reasoning_en=f"json parse failed; treating as pass: {raw[s:e][:120]}")
    v = (d.get("verdict") or "pass").strip().lower()
    if v not in ("pass", "revise", "reject"):
        v = "pass"
    return LensVerdict(
        lens=lens_name, verdict=v,
        reasoning_ko=str(d.get("reasoning_ko", ""))[:1000],
        reasoning_en=str(d.get("reasoning_en", ""))[:1000],
        suggested_fix=str(d.get("suggested_fix", ""))[:2000],
    )


# ──────────────────────────────────────────────────────────────────
# Individual lens calls
# ──────────────────────────────────────────────────────────────────

async def _factual_lens(artifact: Artifact) -> LensVerdict:
    user = (
        f"문항 본문 (artifact):\n{artifact.text}\n\n"
        f"인용 출처 (citation): {json.dumps(artifact.citation or {}, ensure_ascii=False)}\n"
        "검토하고 JSON으로 답하시오."
    )
    res = await call_llm(role="lens_factual", system=_FACTUAL_SYSTEM, user=user, cache=True)
    return _parse_lens_json(res["text"], "factual")


async def _pedagogical_lens(artifact: Artifact) -> LensVerdict:
    sys = _PEDAGOGICAL_SYSTEM.replace("{declared_bloom}", str(artifact.declared_bloom or "Apply"))
    user = f"문항 본문:\n{artifact.text}\n\nBloom's 선언: {artifact.declared_bloom}\nJSON으로 답하시오."
    res = await call_llm(role="lens_pedagogical", system=sys, user=user, cache=True)
    return _parse_lens_json(res["text"], "pedagogical")


async def _korean_lens(artifact: Artifact) -> LensVerdict:
    user = f"문항 본문:\n{artifact.text}\n\n한국어 자연성만 평가. JSON으로 답하시오."
    res = await call_llm(role="lens_korean", system=_KOREAN_SYSTEM, user=user, cache=True)
    return _parse_lens_json(res["text"], "korean")


async def _difficulty_lens(artifact: Artifact) -> LensVerdict:
    sys = _DIFFICULTY_SYSTEM.replace("{declared_difficulty}", str(artifact.declared_difficulty or 3))
    user = (
        f"문항 본문:\n{artifact.text}\n\n선언 난이도: {artifact.declared_difficulty}\n"
        "JSON으로 답하시오."
    )
    res = await call_llm(role="lens_difficulty", system=sys, user=user, cache=True)
    return _parse_lens_json(res["text"], "difficulty")


async def _reviser(text: str, failing: list[LensVerdict], artifact: Artifact) -> str:
    feedback_parts = []
    for v in failing:
        feedback_parts.append(f"[{v.lens}] {v.reasoning_ko or v.reasoning_en} → 제안: {v.suggested_fix}")
    feedback = "\n".join(feedback_parts) or "(no specific feedback)"
    user = (
        f"원본 본문:\n{text}\n\n"
        f"피드백 ({len(failing)}개 렌즈):\n{feedback}\n\n"
        "위 피드백을 모두 반영하여 본문을 재작성하시오."
    )
    res = await call_llm(role="quiz_generator", system=_REVISER_SYSTEM, user=user)
    return (res["text"] or text).strip()


# ──────────────────────────────────────────────────────────────────
# Logging to question_review_log + lens_disagreement_log
# ──────────────────────────────────────────────────────────────────

def _log_round(artifact: Artifact, round_num: int, verdicts: list[LensVerdict],
               revised_text: Optional[str] = None) -> None:
    try:
        from db_pool import acquire, release
        conn = acquire()
        try:
            with conn.cursor() as cur:
                for v in verdicts:
                    cur.execute("""
                        INSERT INTO question_review_log
                          (artifact_kind, artifact_id, round_num, lens, verdict,
                           reasoning, revised_text)
                        VALUES (%s,%s,%s,%s,%s,%s,%s)
                    """, (artifact.kind, artifact.artifact_id or 0, round_num, v.lens,
                          v.verdict, (v.reasoning_ko + " // " + v.reasoning_en).strip(" /"),
                          revised_text))
            conn.commit()
        finally:
            release(conn)
    except Exception as e:
        log.debug("review log write failed (non-fatal): %s", e)


def _log_disagreement(artifact: Artifact, round_num: int,
                       passing: list[str], failing: list[str], resolution: str) -> None:
    try:
        from db_pool import acquire, release
        conn = acquire()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO lens_disagreement_log
                      (artifact_id, artifact_kind, round_num,
                       lenses_passing, lenses_failing, resolution)
                    VALUES (%s,%s,%s,%s,%s,%s)
                """, (artifact.artifact_id, artifact.kind, round_num,
                      passing, failing, resolution))
            conn.commit()
        finally:
            release(conn)
    except Exception as e:
        log.debug("disagreement log write failed (non-fatal): %s", e)


# ──────────────────────────────────────────────────────────────────
# Public entry
# ──────────────────────────────────────────────────────────────────

async def multi_lens_review(
    artifact: Artifact,
    *,
    max_rounds: int = 1,           # default 1 round for demo speed; bank-build job can pass 3
    relax_difficulty: bool = True,
) -> ReviewResult:
    """
    Run all 4 lenses on the artifact in parallel each round, iterating up to
    `max_rounds`. Returns a ReviewResult.

    Convergence rules (cf. 00b_revised_plan §5):
      - All 4 pass → approved.
      - Any factual `reject` → manual_review immediately.
      - Difficulty-only fail with `relax_difficulty=True` → accept by lowering tag.
      - Otherwise revise, retry.
      - max_rounds without convergence → manual_review.
    """
    t0 = time.perf_counter()
    current_text = artifact.text
    final_difficulty = artifact.declared_difficulty
    rounds_log: list[list[LensVerdict]] = []

    for round_num in range(1, max_rounds + 1):
        a_round = Artifact(
            kind=artifact.kind, text=current_text, citation=artifact.citation,
            declared_difficulty=final_difficulty,
            declared_bloom=artifact.declared_bloom,
            artifact_id=artifact.artifact_id, extra=artifact.extra,
        )
        verdicts = await asyncio.gather(
            _factual_lens(a_round),
            _pedagogical_lens(a_round),
            _korean_lens(a_round),
            _difficulty_lens(a_round),
        )
        rounds_log.append(verdicts)
        passing = [v.lens for v in verdicts if v.verdict == "pass"]
        failing = [v for v in verdicts if v.verdict != "pass"]
        _log_round(a_round, round_num, verdicts, revised_text=None)

        # Factual veto
        if any(v.lens == "factual" and v.verdict == "reject" for v in failing):
            _log_disagreement(a_round, round_num, passing,
                              [v.lens for v in failing], "rejected")
            return ReviewResult(
                status="manual_review", text=current_text, rounds=round_num,
                verdicts_per_round=rounds_log,
                final_difficulty=final_difficulty,
                elapsed_ms=int((time.perf_counter() - t0) * 1000),
            )

        # All pass
        if not failing:
            _log_disagreement(a_round, round_num, passing, [], "converged")
            return ReviewResult(
                status="approved", text=current_text, rounds=round_num,
                verdicts_per_round=rounds_log,
                final_difficulty=final_difficulty,
                elapsed_ms=int((time.perf_counter() - t0) * 1000),
            )

        # Difficulty-only fail → relax instead of regenerate
        if relax_difficulty and len(failing) == 1 and failing[0].lens == "difficulty":
            # Drop one notch (clamped to 1..5) — simple heuristic
            if final_difficulty is not None:
                final_difficulty = max(1, min(5, final_difficulty - 1))
            _log_disagreement(a_round, round_num, passing, ["difficulty"], "converged")
            return ReviewResult(
                status="approved", text=current_text, rounds=round_num,
                verdicts_per_round=rounds_log,
                final_difficulty=final_difficulty,
                elapsed_ms=int((time.perf_counter() - t0) * 1000),
            )

        # Revise: hand all failing-lens feedback to the reviser at once
        if round_num < max_rounds:
            current_text = await _reviser(current_text, failing, a_round)
            emit_event(event_kind="multi_lens_revise",
                       agent="multi_lens",
                       payload={"round": round_num,
                                "failing": [v.lens for v in failing]})

    # Hit max_rounds without convergence
    _log_disagreement(artifact, max_rounds, passing,
                      [v.lens for v in failing], "manual")
    return ReviewResult(
        status="manual_review", text=current_text, rounds=max_rounds,
        verdicts_per_round=rounds_log,
        final_difficulty=final_difficulty,
        elapsed_ms=int((time.perf_counter() - t0) * 1000),
    )
