"""
Adaptive learning logic for BRI610 SRS — replaces the dumb FIFO queue with a
mastery-aware, topic-balanced selector that escalates difficulty as the student
progresses.

Score for each candidate card (higher = pick first):

    score = 0.45 * fsrs_due_priority
          + 0.30 * mastery_gap_priority
          + 0.15 * topic_balance_bonus
          + 0.10 * difficulty_escalation_bonus

Where:
  fsrs_due_priority = 1.0 if `due` is past, else 1/(1 + days_until_due);
                      New cards get 0.7 (high but below overdue Review).
  mastery_gap_priority = 1 - mastery.score (weakest topic+type combo first).
  topic_balance_bonus  = penalize repeating same topic 4+ times in last 6.
  difficulty_escalation_bonus = bonus for cards 1 step harder than the user's
                                current avg-recently-rated difficulty.

The selector also enforces:
  - At least 2 of the 4 card types in any 8-card session.
  - At most 60% of the session in one topic.
  - Foundation cards (topic='foundations'/'de_em_basics') prioritized when
    mastery on that prereq is < 0.5 — automatic prereq routing per R5.
"""
from __future__ import annotations
import logging
from collections import Counter
from datetime import datetime, timezone
from typing import Optional

log = logging.getLogger(__name__)


# Topic dependency graph: each main topic depends on ≥1 prereq topics.
# When mastery on a prereq is low (<0.5), the selector boosts foundation cards.
PREREQ = {
    "membrane_eq":  ["foundations", "de_em_basics"],
    "Nernst":       ["foundations"],
    "HH":           ["membrane_eq", "Nernst", "foundations"],
    "cable":        ["membrane_eq", "foundations"],
    "L4_synapses":  ["membrane_eq", "Nernst"],
    "L7_models":    ["HH", "membrane_eq"],
    "L8_codes":     ["HH"],
    "model_types":  ["HH", "membrane_eq"],
    "neural_codes": ["HH"],
}


def _fsrs_due_priority(due, now: datetime) -> float:
    """1.0 if overdue; decay for future-due; 0.7 for new (no due yet)."""
    if due is None:
        return 0.7
    days = (due - now).total_seconds() / 86400.0
    if days <= 0:
        return 1.0
    return 1.0 / (1.0 + days)


def _mastery_table(user_id: int, conn) -> dict:
    """Returns {(topic, card_type): score}."""
    out = {}
    with conn.cursor() as cur:
        cur.execute("""
            SELECT topic, card_type, score FROM mastery WHERE user_id = %s
        """, (user_id,))
        for t, ct, s in cur.fetchall():
            out[(t, ct)] = float(s)
    return out


def _recent_topic_history(user_id: int, conn, n: int = 6) -> list[str]:
    """Last n srs_reviews → topics, most recent first."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT q.topic
            FROM srs_reviews r
            JOIN srs_cards c ON c.id = r.card_id
            JOIN question_bank q ON q.id = c.bank_item_id
            WHERE c.user_id = %s
            ORDER BY r.reviewed_at DESC LIMIT %s
        """, (user_id, n))
        return [row[0] for row in cur.fetchall()]


def _recent_difficulty(user_id: int, conn, n: int = 6) -> float:
    """Avg difficulty of last n cards rated (Good or Easy). 3.0 default."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT AVG(q.difficulty)
            FROM srs_reviews r
            JOIN srs_cards c ON c.id = r.card_id
            JOIN question_bank q ON q.id = c.bank_item_id
            WHERE c.user_id = %s AND r.rating >= 3
            AND r.reviewed_at > now() - interval '7 days'
            LIMIT %s
        """, (user_id, n))
        row = cur.fetchone()
        return float(row[0]) if row and row[0] else 3.0


def select_adaptive(user_id: int = 1, limit: int = 10) -> list[dict]:
    """
    Return up to `limit` cards in adaptive order. Replaces dumb queue.

    Schema:
      [{card_id, bank_id, topic, card_type, difficulty, bloom, prompt_md,
        answer_md, rationale_md, source_citation, reasons: [str], score: float}]
    """
    from db_pool import acquire, release
    conn = acquire()
    try:
        now = datetime.now(timezone.utc)
        mastery = _mastery_table(user_id, conn)
        recent_topics = _recent_topic_history(user_id, conn, 6)
        recent_topic_count = Counter(recent_topics)
        avg_diff = _recent_difficulty(user_id, conn, 6)

        # Pull all candidate srs_cards joined with bank
        with conn.cursor() as cur:
            cur.execute("""
                SELECT s.id, s.bank_item_id, s.due, s.last_review, s.state, s.reps, s.lapses,
                       q.topic, q.card_type, q.difficulty, q.bloom,
                       q.prompt_md, q.answer_md, q.rationale_md,
                       q.source_citation, q.priority_score
                FROM srs_cards s
                JOIN question_bank q ON q.id = s.bank_item_id
                WHERE s.user_id = %s
                  AND q.status = 'active'
            """, (user_id,))
            cols = [d.name for d in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]

        if not rows:
            return []

        # Compute scores
        scored = []
        for r in rows:
            reasons = []
            # 1. FSRS due priority (45%)
            fsrs_p = _fsrs_due_priority(r["due"], now)
            if r["due"] and r["due"] <= now:
                reasons.append("overdue")
            elif r["state"] == "New":
                reasons.append("new")

            # 2. Mastery gap (30%) — weakest topic×type first
            m = mastery.get((r["topic"], r["card_type"]), 0.5)
            mastery_gap = max(0.0, 1.0 - m)
            if m < 0.4:
                reasons.append("weak_mastery")

            # 3. Topic balance bonus (15%)
            recent_count = recent_topic_count.get(r["topic"], 0)
            if recent_count >= 4:
                topic_bonus = 0.0
                reasons.append("topic_overrepresented")
            elif recent_count == 0:
                topic_bonus = 1.0
                reasons.append("fresh_topic")
            else:
                topic_bonus = 1.0 - (recent_count / 4.0)

            # 4. Difficulty escalation (10%)
            target_diff = min(5.0, avg_diff + 0.5)
            diff_distance = abs(r["difficulty"] - target_diff)
            diff_bonus = max(0.0, 1.0 - diff_distance / 4.0)

            # 5. Prereq override: if topic has weak prereq, boost foundation cards
            prereq_boost = 0.0
            for pre_topic in PREREQ.get(r["topic"], []):
                pre_keys = [k for k in mastery if k[0] == pre_topic]
                if pre_keys:
                    pre_avg = sum(mastery[k] for k in pre_keys) / len(pre_keys)
                    if pre_avg < 0.5 and r["topic"] in ("foundations", "de_em_basics"):
                        prereq_boost = 0.3
                        reasons.append(f"prereq_for_{pre_topic}")
                        break

            score = (0.45 * fsrs_p
                     + 0.30 * mastery_gap
                     + 0.15 * topic_bonus
                     + 0.10 * diff_bonus
                     + prereq_boost)
            r["score"] = round(score, 4)
            r["reasons"] = reasons
            scored.append(r)

        scored.sort(key=lambda x: -x["score"])

        # Soft constraints: enforce ≥ 2 card types in first `limit` picks,
        # max 60% one topic.
        chosen: list[dict] = []
        topic_counts: Counter = Counter()
        type_set: set[str] = set()
        for r in scored:
            if len(chosen) >= limit:
                break
            # 60% topic cap (don't apply for first 2 picks)
            if len(chosen) >= 2 and topic_counts[r["topic"]] >= max(2, int(0.6 * limit)):
                continue
            chosen.append(r)
            topic_counts[r["topic"]] += 1
            type_set.add(r["card_type"])

        # If we ended with <2 distinct types, swap last item to balance
        if len(type_set) < 2 and len(chosen) >= 2:
            for r in scored:
                if r["card_type"] not in type_set and r not in chosen:
                    chosen[-1] = r
                    type_set.add(r["card_type"])
                    break

        # Format response
        out = []
        for r in chosen:
            for k in ("due", "last_review"):
                if r.get(k):
                    r[k] = r[k].isoformat()
            r["card_id"] = r.pop("id")
            r["bank_id"] = r.pop("bank_item_id")
            out.append(r)
        return out
    finally:
        release(conn)
