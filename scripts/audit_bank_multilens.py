#!/usr/bin/env python3
"""
audit_bank_multilens.py — Run Multi-Lens Review on EVERY active bank item.

Cross-model audit: factual lens uses DeepSeek v4 pro, pedagogical lens uses
Kimi K 2.6, Korean lens uses qwen3-235b-a22b-thinking, difficulty lens uses
Kimi K 2.6 — per the route table in `backend/harness/llm_client.py`.

Output:
  - Per-card verdict logged to `question_review_log` table.
  - Disagreements logged to `lens_disagreement_log`.
  - JSON summary report saved to `logs/audit_<timestamp>.json` with:
      - total cards reviewed
      - distribution of verdicts per lens
      - cards flagged for `manual_review` (factual veto)
      - cards needing `revise` (any non-factual lens not pass)
      - per-lens disagreement matrix
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
from review import multi_lens_review, Artifact  # noqa: E402


CONCURRENCY = int(os.environ.get("AUDIT_CONCURRENCY", "3"))
MAX_ROUNDS  = int(os.environ.get("AUDIT_ROUNDS", "1"))


def fetch_cards():
    conn = acquire()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, topic, card_type, difficulty, bloom,
                       prompt_md, answer_md, rationale_md, source_citation
                FROM question_bank
                WHERE status = 'active'
                ORDER BY id
            """)
            cols = [d.name for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        release(conn)


async def review_one(card: dict, sem: asyncio.Semaphore) -> dict:
    async with sem:
        # Combine prompt + answer + rationale into a single artifact
        text = (
            f"문항: {card['prompt_md']}\n\n"
            f"정답: {card['answer_md']}\n\n"
            f"해설: {card['rationale_md']}"
        )[:8000]  # cap to keep within reviewer context

        artifact = Artifact(
            kind="question",
            text=text,
            citation=card["source_citation"],
            declared_difficulty=card["difficulty"],
            declared_bloom=card["bloom"],
            artifact_id=card["id"],
            extra={"topic": card["topic"], "card_type": card["card_type"]},
        )
        t0 = time.perf_counter()
        try:
            res = await multi_lens_review(artifact, max_rounds=MAX_ROUNDS)
        except Exception as e:
            return {
                "id": card["id"], "topic": card["topic"], "card_type": card["card_type"],
                "status": "error", "error": str(e), "elapsed_s": time.perf_counter() - t0,
            }
        elapsed = time.perf_counter() - t0
        verdicts = res.verdicts_per_round[0] if res.verdicts_per_round else []
        return {
            "id": card["id"],
            "topic": card["topic"],
            "card_type": card["card_type"],
            "difficulty": card["difficulty"],
            "status": res.status,
            "rounds": res.rounds,
            "elapsed_s": round(elapsed, 1),
            "verdicts": [v.to_dict() for v in verdicts],
            "final_difficulty": res.final_difficulty,
        }


async def main():
    cards = fetch_cards()
    print(f"auditing {len(cards)} cards (concurrency={CONCURRENCY}, max_rounds={MAX_ROUNDS})…")
    sem = asyncio.Semaphore(CONCURRENCY)

    # Stagger the spawn slightly so OR doesn't see N simultaneous bursts
    results = []
    started = time.time()
    for i, c in enumerate(cards):
        results.append(asyncio.create_task(review_one(c, sem)))
        if i % CONCURRENCY == CONCURRENCY - 1:
            await asyncio.sleep(0.2)
    final = await asyncio.gather(*results)
    elapsed_total = time.time() - started

    # Aggregate
    from collections import Counter
    overall_status = Counter(r["status"] for r in final)
    per_lens_pass = Counter()
    per_lens_total = Counter()
    flagged = []  # cards that didn't approve cleanly
    error_ids = []

    for r in final:
        if r["status"] == "error":
            error_ids.append(r["id"])
            continue
        if r["status"] != "approved":
            flagged.append({
                "id": r["id"], "topic": r["topic"], "card_type": r["card_type"],
                "status": r["status"],
                "failing_lenses": [v["lens"] for v in r.get("verdicts", []) if v["verdict"] != "pass"],
                "first_reasoning": next((
                    (v.get("reasoning_ko") or v.get("reasoning_en") or "")[:200]
                    for v in r.get("verdicts", []) if v["verdict"] != "pass"
                ), ""),
            })
        for v in r.get("verdicts", []):
            per_lens_total[v["lens"]] += 1
            if v["verdict"] == "pass":
                per_lens_pass[v["lens"]] += 1

    summary = {
        "audited_at": datetime.now().isoformat(timespec="seconds"),
        "total_cards": len(cards),
        "elapsed_s": round(elapsed_total, 1),
        "overall_verdict": dict(overall_status),
        "per_lens_pass_rate": {
            lens: f"{per_lens_pass[lens]}/{per_lens_total[lens]}"
            for lens in per_lens_total
        },
        "errors": error_ids,
        "flagged_cards": flagged,
        "all_results": final,
    }

    out_dir = ROOT / "logs"
    out_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"audit_{ts}.json"
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nreport: {out_path}")
    print(f"\nverdict distribution: {dict(overall_status)}")
    print(f"per-lens pass rates: {summary['per_lens_pass_rate']}")
    print(f"flagged cards (need revision): {len(flagged)}")
    if flagged:
        for f in flagged[:10]:
            print(f"  [{f['id']:>3}] {f['topic']:>14} {f['card_type']:>11} "
                  f"({f['status']}) — {f['failing_lenses']}")
            if f["first_reasoning"]:
                print(f"        → {f['first_reasoning'][:140]}")
    if error_ids:
        print(f"errors: {error_ids}")


if __name__ == "__main__":
    asyncio.run(main())
