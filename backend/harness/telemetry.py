"""
Telemetry — best-effort fire-and-forget writer for `analytics_events`.

Design:
- Never raises; bad telemetry must not break a user-facing call.
- Async-friendly (uses a background task) so the calling agent doesn't block on DB.
- If the DB pool is unavailable (tests, no PG), logs and drops the event.
"""
from __future__ import annotations

import json
import logging
import threading
from typing import Optional

log = logging.getLogger(__name__)


def _enqueue_write(row: dict) -> None:
    """Run the actual INSERT in a daemon thread so the caller doesn't block."""
    def _do():
        try:
            from db_pool import acquire, release
        except Exception:
            log.debug("db_pool unavailable; dropping telemetry event %s", row.get("event_kind"))
            return
        try:
            conn = acquire()
        except Exception as e:
            log.debug("telemetry: pool acquire failed: %s", e)
            return
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO analytics_events
                      (event_kind, user_id, session_id, agent, ms,
                       tokens_in, tokens_out, llm_route, payload)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
                """, (
                    row["event_kind"], row.get("user_id"), row.get("session_id"),
                    row.get("agent"), row.get("ms"),
                    row.get("tokens_in"), row.get("tokens_out"),
                    row.get("llm_route"),
                    json.dumps(row.get("payload") or {}, ensure_ascii=False),
                ))
            conn.commit()
        except Exception as e:
            log.debug("telemetry insert failed: %s", e)
            try: conn.rollback()
            except Exception: pass
        finally:
            try: release(conn)
            except Exception: pass

    t = threading.Thread(target=_do, name="telemetry-write", daemon=True)
    t.start()


def emit_event(
    *,
    event_kind: str,
    user_id: Optional[int] = None,
    session_id: Optional[str] = None,
    agent: Optional[str] = None,
    ms: Optional[int] = None,
    tokens_in: Optional[int] = None,
    tokens_out: Optional[int] = None,
    llm_route: Optional[str] = None,
    payload: Optional[dict] = None,
) -> None:
    """
    Fire-and-forget write to analytics_events. Safe to call before DB is up.
    """
    _enqueue_write({
        "event_kind": event_kind,
        "user_id": user_id,
        "session_id": session_id,
        "agent": agent,
        "ms": ms,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "llm_route": llm_route,
        "payload": payload,
    })
