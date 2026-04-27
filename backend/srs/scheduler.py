"""
FSRS-6 wrapper. Ships with sensible defaults; parameters can be optimized
on accumulated review history (P10.4 daemon job, post-MVP).

Uses py-fsrs 6.3.1 (`pip install fsrs`). The schema lives in
`pipeline/migrations/002_v05_schema.sql` — `srs_cards` + `srs_reviews`.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

log = logging.getLogger(__name__)

# Lazy import so backend boots without fsrs installed in dev environments
_fsrs_mod = None
_scheduler = None


def _get_scheduler():
    global _fsrs_mod, _scheduler
    if _scheduler is not None:
        return _scheduler
    try:
        import fsrs as F
        _fsrs_mod = F
        _scheduler = F.Scheduler()  # default 21-param FSRS-6
        return _scheduler
    except ImportError:
        log.warning("fsrs not installed; SRS will be a no-op (cards will not advance)")
        _fsrs_mod = False
        return None


def _state_to_str(state) -> str:
    # py-fsrs 6.x State may be IntEnum — `str(state)` could yield '1', so use .name.
    name = getattr(state, "name", None) or str(state).rsplit(".", 1)[-1]
    # Normalize case
    return {"NEW": "New", "LEARNING": "Learning", "REVIEW": "Review", "RELEARNING": "Relearning"}.get(name.upper(), name.title())


def _str_to_state(s: str):
    F = _fsrs_mod
    if not F:
        return None
    m = {"New": F.State.Learning, "Learning": F.State.Learning,
         "Review": F.State.Review, "Relearning": F.State.Relearning}
    # py-fsrs 6.x doesn't have `New` in its State enum; cards start as Learning at first rating.
    return m.get(s, F.State.Learning)


def register_card(user_id: int, bank_item_id: int) -> int:
    """Insert a fresh `srs_cards` row in 'New' state. Returns card id."""
    from db_pool import acquire, release
    conn = acquire()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO srs_cards (user_id, bank_item_id, state)
                VALUES (%s,%s,'New')
                ON CONFLICT (user_id, bank_item_id) DO UPDATE SET state = srs_cards.state
                RETURNING id
            """, (user_id, bank_item_id))
            row = cur.fetchone()
            conn.commit()
            return row[0]
    finally:
        release(conn)


def queue_due(user_id: int, limit: int = 20) -> list[dict]:
    """Return up to `limit` cards due for review (or new), with bank fields joined."""
    from db_pool import acquire, release
    conn = acquire()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT s.id AS card_id, s.state, s.due, s.last_review,
                       s.reps, s.lapses,
                       q.id AS bank_id, q.topic, q.card_type, q.difficulty, q.bloom,
                       q.prompt_md, q.answer_md, q.rationale_md, q.source_citation
                FROM srs_cards s
                JOIN question_bank q ON q.id = s.bank_item_id
                WHERE s.user_id = %s
                  AND q.status = 'active'
                  AND (s.due IS NULL OR s.due <= now() OR s.state = 'New')
                ORDER BY s.due ASC NULLS FIRST, q.priority_score DESC
                LIMIT %s
            """, (user_id, limit))
            cols = [d.name for d in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        return rows
    finally:
        release(conn)


def schedule_review(card_id: int, rating: int) -> dict:
    """
    Apply FSRS-6 scheduling to `card_id` with the given rating (1=Again..4=Easy).
    Returns updated state. Logs an `srs_reviews` row.
    """
    if rating not in (1, 2, 3, 4):
        raise ValueError("rating must be 1..4 (Again, Hard, Good, Easy)")

    from db_pool import acquire, release
    conn = acquire()
    try:
        with conn.cursor() as cur:
            # Row-level lock: prevents concurrent srs_review on the same card
            # from racing on stability/difficulty updates.
            cur.execute("""
                SELECT id, user_id, bank_item_id, state, stability, difficulty,
                       due, last_review, reps, lapses
                FROM srs_cards WHERE id = %s
                FOR UPDATE
            """, (card_id,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"srs_card {card_id} not found")
            (cid, user_id, bank_item_id, state_str, stab, diff,
             due, last_review, reps, lapses) = row

            now = datetime.now(timezone.utc)
            sched = _get_scheduler()
            if sched is None:
                # py-fsrs not installed — fake-advance by 1 day
                new_state, new_stab, new_diff = "Learning", (stab or 0) + 1.0, diff or 5.0
                new_due = now.replace(microsecond=0)
                from datetime import timedelta
                new_due = new_due + timedelta(days=1 if rating >= 3 else 0)
                elapsed = 0.0; scheduled = 1.0
            else:
                F = _fsrs_mod
                # FSRS-6 expects stability/difficulty=None for new (never-reviewed) cards;
                # passing 0 makes pow(stability, neg) raise.
                is_new = state_str == "New" or (stab is None and diff is None) or (stab == 0 and diff == 0 and reps == 0)
                card = F.Card(
                    card_id=cid,
                    state=_str_to_state("Learning" if is_new else state_str),
                    stability=None if is_new else (stab if stab is not None else None),
                    difficulty=None if is_new else (diff if diff is not None else None),
                    due=due if due is not None else now,
                    last_review=last_review,
                    step=0 if is_new else None,
                )
                rating_enum = {1: F.Rating.Again, 2: F.Rating.Hard,
                               3: F.Rating.Good, 4: F.Rating.Easy}[rating]
                card, log = sched.review_card(card, rating_enum, review_datetime=now)
                new_state = _state_to_str(card.state)
                new_stab = float(card.stability or 0)
                new_diff = float(card.difficulty or 0)
                new_due = card.due
                elapsed = float(getattr(log, "elapsed_days", 0) or 0)
                scheduled = float(getattr(log, "scheduled_days", 0) or 0)

            new_lapses = lapses + (1 if rating == 1 else 0)
            new_reps = reps + 1

            cur.execute("""
                UPDATE srs_cards
                SET state=%s, stability=%s, difficulty=%s,
                    due=%s, last_review=%s, reps=%s, lapses=%s
                WHERE id=%s
            """, (new_state, new_stab, new_diff, new_due, now,
                  new_reps, new_lapses, cid))

            cur.execute("""
                INSERT INTO srs_reviews (card_id, rating, elapsed_days, scheduled_days)
                VALUES (%s,%s,%s,%s)
            """, (cid, rating, elapsed, scheduled))

            conn.commit()
        return {
            "card_id": cid, "state": new_state,
            "stability": new_stab, "difficulty": new_diff,
            "due": new_due.isoformat() if new_due else None,
            "reps": new_reps, "lapses": new_lapses,
            "scheduled_days": scheduled,
        }
    finally:
        release(conn)
