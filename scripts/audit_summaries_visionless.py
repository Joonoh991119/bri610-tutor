#!/usr/bin/env python3
"""
audit_summaries_visionless.py — Cross-model critique of all 6 cached lecture
summaries by *3 different LLMs* (DeepSeek v4 pro, Kimi K 2.6, free Qwen).

Each reviewer scores 0–10 on 6 axes:
  1. Pedagogical clarity (graduate student perspective)
  2. Scientific accuracy (vs slide content)
  3. Layout / readability (sections, transitions, density)
  4. Citation discipline (slide-only)
  5. Coverage of slide content
  6. Memorability / intuition (analogies)

Discrepancies between reviewers (>2-point spread) flag controversial sections
for the next iteration. Output saved to `logs/summary_audit_<ts>.json` and a
human-readable markdown digest at `docs/audit/summary_audit_<ts>.md`.
"""
from __future__ import annotations
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "backend"))

from db_pool import acquire, release  # noqa: E402
from harness import call_llm  # noqa: E402


REVIEWER_ROLES = {
    "factual":    "lens_factual",      # DeepSeek v4 pro primary
    "pedagogical":"lens_pedagogical",  # Kimi K 2.6 primary
    "korean":     "lens_korean",       # qwen3-235b primary
}


def fetch_summaries():
    conn = acquire()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT lecture, lecture_title, summary
                FROM lecture_summaries
                WHERE lecture IN ('L3','L4','L5','L6','L7','L8')
                ORDER BY lecture
            """)
            return [{"lecture": l, "title": t, "summary": s} for l, t, s in cur.fetchall()]
    finally:
        release(conn)


_PROMPT_TEMPLATE = """당신은 BRI610 컴퓨터신경과학 박사과정생을 위한 학습 자료를 엄격히 평가하는 사이언스 리뷰어입니다.

다음 강의 핸드아웃을 평가하세요. 6개 축에 0–10 점수와 짧은 *구체적* 비판을 작성:

1. **Pedagogical clarity**: 박사과정생이지만 미분방정식·전자기학에 약한 학생이 이해 가능한가? 점프 없이 단계적인가?
2. **Scientific accuracy**: 모든 식·수치·인과 주장이 옳은가? 단위, 부호 오류 없는가?
3. **Layout / readability**: 섹션 길이, 그림 위치, 전환부 자연스러움
4. **Citation discipline**: 모든 인용이 [Slide L# p.#] 형식이며 슬라이드만 참조하는가?
5. **Coverage of slide content**: 강의 슬라이드의 *핵심* 개념을 빠짐없이 다루는가?
6. **Memorability / intuition**: 비유와 직관이 명확한가? 추상적이지 않고 *기억에 남는가*?

응답은 *반드시 JSON*. 코드펜스 금지. 각 축에 score (정수 0-10) 와 critique (≤120자):

{
  "scores": {
    "pedagogical_clarity": INT,
    "scientific_accuracy": INT,
    "layout_readability": INT,
    "citation_discipline": INT,
    "coverage": INT,
    "memorability": INT
  },
  "critiques": {
    "pedagogical_clarity": "...",
    "scientific_accuracy": "...",
    "layout_readability": "...",
    "citation_discipline": "...",
    "coverage": "...",
    "memorability": "..."
  },
  "top_3_concrete_fixes": ["fix 1", "fix 2", "fix 3"]
}"""


async def review_summary_with(reviewer_role: str, lecture: str, summary: str) -> dict:
    user = f"강의: {lecture}\n\n요약 본문 (전체):\n---\n{summary[:14000]}\n---"
    res = await call_llm(
        role=REVIEWER_ROLES[reviewer_role],
        system=_PROMPT_TEMPLATE,
        user=user,
        temperature=0.0,
        max_tokens=900,
        cache=True,
    )
    raw = res.get("text") or ""
    # Find JSON in response
    s, e = raw.find("{"), raw.rfind("}") + 1
    parsed = None
    if s >= 0 and e > s:
        try:
            parsed = json.loads(raw[s:e])
        except Exception:
            pass
    return {
        "reviewer": reviewer_role,
        "route_used": res.get("route_used"),
        "raw_text": raw[:300],
        "parsed": parsed,
    }


async def review_one(lecture: str, summary: str) -> dict:
    print(f"  reviewing {lecture}...")
    tasks = [
        review_summary_with(role, lecture, summary)
        for role in REVIEWER_ROLES
    ]
    reviews = await asyncio.gather(*tasks, return_exceptions=True)
    norm = []
    for rev in reviews:
        if isinstance(rev, Exception):
            norm.append({"reviewer": "?", "error": str(rev)})
        else:
            norm.append(rev)
    return {"lecture": lecture, "reviews": norm}


def aggregate(reviews_by_lec: list[dict]) -> dict:
    """Compute per-lecture average + spread + flagged axes."""
    out = []
    for r in reviews_by_lec:
        scores_per_axis = {}
        for review in r["reviews"]:
            p = review.get("parsed")
            if not p:
                continue
            for axis, val in (p.get("scores") or {}).items():
                scores_per_axis.setdefault(axis, []).append(val)
        avg = {a: round(sum(v)/len(v), 1) for a, v in scores_per_axis.items() if v}
        spread = {a: max(v) - min(v) for a, v in scores_per_axis.items() if len(v) > 1}
        flagged = [a for a, s in spread.items() if s >= 3]
        out.append({
            "lecture": r["lecture"],
            "avg_scores": avg,
            "score_spread": spread,
            "controversial_axes": flagged,
            "min_axis": min(avg, key=avg.get) if avg else None,
            "min_score": min(avg.values()) if avg else None,
        })
    return out


async def main():
    summaries = fetch_summaries()
    print(f"auditing {len(summaries)} summaries × {len(REVIEWER_ROLES)} reviewers …")
    t0 = time.time()
    detailed = []
    for s in summaries:
        d = await review_one(s["lecture"], s["summary"])
        detailed.append(d)
    elapsed = time.time() - t0

    agg = aggregate(detailed)
    summary_obj = {
        "audited_at": datetime.now().isoformat(timespec="seconds"),
        "elapsed_s": round(elapsed, 1),
        "reviewer_routes": REVIEWER_ROLES,
        "aggregated": agg,
        "detailed": detailed,
    }
    out_dir = ROOT / "logs"
    out_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"summary_audit_{ts}.json"
    out_path.write_text(json.dumps(summary_obj, ensure_ascii=False, indent=2))

    # Markdown digest
    md = ["# Summary Cross-Model Audit",
          f"Audited {datetime.now().isoformat(timespec='seconds')} · "
          f"{len(summaries)} summaries × {len(REVIEWER_ROLES)} reviewers · "
          f"elapsed {round(elapsed,1)} s\n"]
    for a in agg:
        md.append(f"## {a['lecture']}")
        md.append(f"- Avg scores: {a['avg_scores']}")
        if a['controversial_axes']:
            md.append(f"- **Controversial** (≥3 spread): {a['controversial_axes']}")
        md.append(f"- Weakest axis: **{a['min_axis']}** ({a['min_score']}/10)")
        # First fix from each reviewer
        d = next(x for x in detailed if x['lecture'] == a['lecture'])
        for r in d["reviews"]:
            p = (r.get("parsed") or {})
            fixes = p.get("top_3_concrete_fixes") or []
            if fixes:
                md.append(f"  - {r['reviewer']} top fix: {fixes[0]}")
        md.append("")
    md_path = ROOT / "docs" / "audit" / f"summary_audit_{ts}.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text("\n".join(md))

    print(f"\nJSON report: {out_path}")
    print(f"MD digest:   {md_path}")
    for a in agg:
        print(f"  {a['lecture']}: avg={a['avg_scores']}, weak={a['min_axis']} ({a['min_score']})")


if __name__ == "__main__":
    asyncio.run(main())
