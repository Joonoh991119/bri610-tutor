"""
BRI610 AI Tutor — FastAPI Backend v0.3
PostgreSQL + pgvector backend, Agent Team + Hybrid Retrieval
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os

from retriever import HybridRetriever
# Install default hooks at backend startup (registers 4 hook bindings on import)
import harness.hooks_default  # noqa: F401
# v0.4 agents.py — kept for back-compat; v0.5 wraps via harness.
import importlib.util as _ilu
_legacy_agents_path = os.path.join(os.path.dirname(__file__), "agents.py")
if os.path.isfile(_legacy_agents_path):
    _spec = _ilu.spec_from_file_location("legacy_agents", _legacy_agents_path)
    _legacy_agents = _ilu.module_from_spec(_spec)  # type: ignore[arg-type]
    _spec.loader.exec_module(_legacy_agents)        # type: ignore[union-attr]
    AgentTeam = _legacy_agents.AgentTeam
else:
    AgentTeam = None  # demo without legacy agents OK
from db import DB
from srs import schedule_review, queue_due, register_card, select_adaptive
from agents import lecture as lecture_mod
from review import multi_lens_review, Artifact
from agents.persona_narrator import wrap_with_persona, PersonaContext
from verify import verify_equation
from gamification import award_xp, compute_level, check_badges, level_up_celebration
from gamification.rules import xp_to_next_level

DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "data"))
IMG_DIR = os.environ.get("IMG_DIR", DATA_DIR)  # slide images live in data/L2/, data/L3/, etc.
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")
# Default chat model — DeepSeek V4 Pro: best science-reasoning per dollar in
# SOTA tier as of 2026-04. $0.44/M prompt + $0.87/M completion (vs Kimi K2.6's
# $4.66/M completion); 1M context handles lecture + slides + history.
CHAT_MODEL = os.environ.get("CHAT_MODEL", "deepseek/deepseek-v4-pro")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "bge-m3:latest")
DB_DSN = os.environ.get("DATABASE_URL", "dbname=bri610 user=tutor password=tutor610 host=localhost")

app = FastAPI(title="BRI610 AI Tutor", version="0.3.0")
_default_origins = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
_extra = os.environ.get("CORS_ORIGINS", "")  # additional origins (comma-sep) — e.g., LAN IP, ngrok URL
_origins = [o.strip() for o in (_default_origins + "," + _extra).split(",") if o.strip()]
# Fallback: when CORS_ORIGINS contains "*" tag, wildcard (dev/demo only)
if "*" in _origins:
    app.add_middleware(CORSMiddleware, allow_origin_regex=".*",
                       allow_methods=["*"], allow_headers=["*"], allow_credentials=False)
else:
    app.add_middleware(CORSMiddleware, allow_origins=_origins,
                       allow_methods=["*"], allow_headers=["*"])

# PostgreSQL-backed retriever and DB
retriever = HybridRetriever(OPENROUTER_KEY, EMBED_MODEL, DB_DSN)
team = AgentTeam(retriever, OPENROUTER_KEY, CHAT_MODEL)
db = DB(DB_DSN)

if os.path.isdir(IMG_DIR):
    app.mount("/images", StaticFiles(directory=IMG_DIR), name="images")

# ─── Request Models ───

class SearchReq(BaseModel):
    query: str
    source: str = "all"  # "all" | "slides" | "textbook"
    lecture: Optional[str] = None
    limit: int = 8

class ChatReq(BaseModel):
    message: str; lecture: Optional[str] = None; mode: str = "auto"; history: list = []

class QuizReq(BaseModel):
    topic: str; lecture: Optional[str] = None; num_questions: int = 5; difficulty: str = "medium"

class ExamReq(BaseModel):
    lecture: str; duration_min: int = 60; total_points: int = 100

class SummaryReq(BaseModel):
    lecture: str; focus: Optional[str] = None

class GradeReq(BaseModel):
    question: str; answer: str; lecture: Optional[str] = None

class FeedbackReq(BaseModel):
    feedback: str

# v0.5 request models
class SrsReviewReq(BaseModel):
    card_id: int
    rating: int  # 1=Again, 2=Hard, 3=Good, 4=Easy

class VerifyReq(BaseModel):
    lhs: str
    rhs: str

class MultiLensReq(BaseModel):
    text: str
    kind: str = "question"   # 'question'|'walkthrough_step'|'summary'
    declared_difficulty: Optional[int] = None
    declared_bloom: Optional[str] = None
    citation: Optional[dict] = None

class PersonaReq(BaseModel):
    text: str
    name: Optional[str] = None
    last_topic: Optional[str] = None
    recent_struggle: Optional[str] = None
    streak_days: int = 0
    daily_goal_met: bool = False
    user_display_name: Optional[str] = None

# ─── Endpoints ───

@app.get("/api/health")
def health():
    stats = db.stats()
    # Report the ACTIVE primary model from the harness ROUTES table for each
    # user-facing role — the legacy CHAT_MODEL constant is back-compat only and
    # not used by the harness call path.
    active_models = {}
    try:
        from harness.llm_client import ROUTES
        for role in ("tutor", "summary", "derive", "quiz_generator", "default"):
            if role in ROUTES:
                active_models[role] = {
                    "primary": ROUTES[role].primary,
                    "fallback_or": ROUTES[role].fallback_or,
                    "fallback_oll": ROUTES[role].fallback_ollama,
                }
    except Exception as e:
        active_models = {"error": repr(e)}
    return {
        "status": "ok",
        "version": "0.3.0",
        "backend": "postgresql+pgvector",
        "chat_model": active_models.get("tutor", {}).get("primary", CHAT_MODEL),  # tutor is the user-facing chat
        "active_models": active_models,
        "embed_model": EMBED_MODEL,
        "db": stats,
        "retrieval": "hybrid_rrf",
    }

@app.get("/api/db-stats")
def db_stats():
    return db.detailed_stats()

@app.get("/api/lectures")
def list_lectures():
    return db.list_lectures()

@app.get("/api/slide-image/{lecture}/{page}")
def get_slide_image(lecture: str, page: int):
    path = os.path.join(DATA_DIR, lecture, f"p{page:02d}.jpg")
    if not os.path.isfile(path):
        raise HTTPException(404, detail=f"Slide image not found: {lecture}/p{page:02d}.jpg")
    return FileResponse(path, media_type="image/jpeg")

@app.post("/api/search")
def search(req: SearchReq):
    return retriever.search(req.query, source=req.source, lecture=req.lecture, limit=req.limit)

@app.post("/api/chat")
async def chat(req: ChatReq):
    return await team.chat(req.message, lecture=req.lecture, mode=req.mode, history=req.history)

@app.post("/api/quiz")
async def quiz(req: QuizReq):
    return await team.generate_quiz(req.topic, req.lecture, req.num_questions, req.difficulty)

@app.post("/api/exam")
async def exam(req: ExamReq):
    return await team.generate_exam(req.lecture, req.duration_min, req.total_points)

@app.post("/api/summary")
async def summary(req: SummaryReq):
    return await team.generate_summary(req.lecture, req.focus)

@app.post("/api/grade")
async def grade(req: GradeReq):
    return await team.grade_answer(req.question, req.answer, req.lecture)

# ─── Cached Summaries ───

@app.get("/api/summaries/{lecture}")
def get_cached_summary(lecture: str):
    row = db.get_summary(lecture)
    if not row:
        raise HTTPException(404, detail=f"No cached summary for {lecture}")
    return row

@app.post("/api/summaries/{lecture}/generate")
async def generate_and_cache_summary(lecture: str):
    result = await team.generate_summary(lecture)
    lectures_data = db.list_lectures()
    title = next((l["title"] for l in lectures_data["lectures"] if l["id"] == lecture), "")
    db.upsert_summary(lecture, title, result["summary"], result.get("sources", []))
    return db.get_summary(lecture)

@app.post("/api/summaries/{lecture}/feedback")
def submit_feedback(lecture: str, req: FeedbackReq):
    db.save_feedback(lecture, req.feedback)
    return {"status": "ok"}

# ─── v0.5: SRS / Bank / Verify / Multi-Lens / Persona ───

@app.get("/api/v05/status")
def v05_status():
    """One-shot health snapshot of all v0.5 modules."""
    out = {"version": "0.5.0-alpha", "modules": {}}
    try:
        from harness import ROUTES as _R
        out["modules"]["harness"] = {"ok": True, "route_count": len(_R)}
    except Exception as e:
        out["modules"]["harness"] = {"ok": False, "error": repr(e)}
    try:
        import sympy  # noqa
        out["modules"]["sympy"] = {"ok": True, "version": sympy.__version__}
    except Exception as e:
        out["modules"]["sympy"] = {"ok": False, "error": repr(e)}
    try:
        import fsrs  # noqa
        out["modules"]["fsrs"] = {"ok": True}
    except Exception as e:
        out["modules"]["fsrs"] = {"ok": False, "error": repr(e)}
    try:
        from db_pool import _get_pool
        _get_pool()
        out["modules"]["db_pool"] = {"ok": True}
    except Exception as e:
        out["modules"]["db_pool"] = {"ok": False, "error": repr(e)}
    return out


@app.get("/api/srs/queue")
def srs_queue(user_id: int = 1, limit: int = 20):
    """Today's SRS due queue (FSRS-6 scheduled)."""
    try:
        rows = queue_due(user_id=user_id, limit=limit)
        # Stringify timestamps
        for r in rows:
            for k in ("due", "last_review"):
                if r.get(k):
                    r[k] = r[k].isoformat()
        return {"user_id": user_id, "queue": rows, "count": len(rows)}
    except Exception as e:
        raise HTTPException(500, detail=f"srs_queue failed: {e}")


@app.post("/api/srs/review")
def srs_review(req: SrsReviewReq):
    """Submit a card rating (1=Again..4=Easy). Returns updated card state + gamification block."""
    try:
        result = schedule_review(req.card_id, req.rating)
    except ValueError as e:
        raise HTTPException(400, detail=str(e))
    except Exception as e:
        raise HTTPException(500, detail=f"srs_review failed: {e}")

    # ── Gamification post-processing (additive — never mutates result shape) ──
    try:
        from db_pool import acquire as _acquire, release as _release
        import json as _json
        from datetime import datetime as _dt

        conn = _acquire()
        cur  = conn.cursor()
        try:
            # Resolve user from card (default user_id=1 for solo deploy)
            cur.execute("SELECT user_id FROM srs_cards WHERE id = %s", (req.card_id,))
            row = cur.fetchone()
            user_id = row[0] if row else 1

            cur.execute(
                "SELECT xp, level, badges FROM users WHERE id = %s",
                (user_id,)
            )
            urow = cur.fetchone()
            if urow:
                old_xp, old_level, raw_badges = urow
                old_xp    = old_xp or 0
                old_level = old_level or 1
                badges    = raw_badges if isinstance(raw_badges, list) else _json.loads(raw_badges or "[]")

                xp_gained = award_xp(req.rating)
                new_xp    = old_xp + xp_gained
                new_level = compute_level(new_xp)

                # Session context (simple: look up today's counts)
                cur.execute("""
                    SELECT COUNT(*),
                           SUM(CASE WHEN r.rating >= 3 THEN 1 ELSE 0 END)
                    FROM srs_reviews r JOIN srs_cards c ON c.id = r.card_id
                    WHERE c.user_id = %s AND r.reviewed_at::date = CURRENT_DATE
                """, (user_id,))
                tc, tg = cur.fetchone()

                # Card type for badge context
                cur.execute(
                    "SELECT card_type FROM question_bank qb "
                    "JOIN srs_cards sc ON sc.bank_item_id = qb.id WHERE sc.id = %s",
                    (req.card_id,)
                )
                ct_row = cur.fetchone()
                card_type = ct_row[0] if ct_row else "recall"

                hour = _dt.now().hour
                state_for_badges = {
                    "existing_badges":       badges,
                    "streak_days":           0,   # streak is bumped via /me/streak/touch
                    "total_reviews":         int(tc or 0),
                    "session_concept_good":  int(tg or 0) if card_type == "concept" else 0,
                    "session_proof_streak":  3 if (card_type == "proof" and req.rating >= 3) else 0,
                }
                review_ctx = {
                    "rating":           req.rating,
                    "card_type":        card_type,
                    "reviewed_at_hour": hour,
                }
                newly_badges = check_badges(state_for_badges, review_ctx)
                all_badges   = list(set(badges) | set(newly_badges))
                celebration  = level_up_celebration(old_level, new_level)

                cur.execute("""
                    UPDATE users SET xp = %s, level = %s, badges = %s::jsonb WHERE id = %s
                """, (new_xp, new_level, _json.dumps(all_badges), user_id))
                conn.commit()

                result["gamification"] = {
                    "xp_gained":      xp_gained,
                    "new_xp":         new_xp,
                    "new_level":      new_level,
                    "level_up":       celebration,
                    "badges_awarded": newly_badges,
                    "xp_progress":    xp_to_next_level(new_xp),
                }
        finally:
            _release(conn)
    except Exception as _ge:
        # Gamification errors are non-fatal — return result without the block
        result.setdefault("gamification", None)

    return result


@app.get("/api/bank/next")
def bank_next(user_id: int = 1, limit: int = 10):
    """
    v0.5 adaptive selector (replaces the dumb FIFO queue):
      score = 0.45·FSRS due + 0.30·mastery gap + 0.15·topic balance + 0.10·diff escalation
              + prereq boost when foundation mastery is weak.
    """
    rows = select_adaptive(user_id=user_id, limit=limit)
    return {"user_id": user_id, "queue": rows, "count": len(rows), "mode": "adaptive"}


# ─── v0.7: Pre-built quiz bank + take-home exam (course-inheritance) ──

@app.get("/api/quiz/bank/{lecture}")
def quiz_bank_lecture(lecture: str):
    """List all pre-built quiz items for a lecture (MCQ + short-answer)."""
    conn = db._conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, position, kind, prompt_md, choices_json, correct_key,
                       correct_text, accept_patterns, rationale_md, slide_ref,
                       difficulty, bloom, topic_tag
                FROM quiz_items
                WHERE lecture = %s
                ORDER BY position
            """, (lecture,))
            rows = cur.fetchall()
        items = [
            {
                "id": r[0], "position": r[1], "kind": r[2], "prompt_md": r[3],
                "choices": r[4], "correct_key": r[5], "correct_text": r[6],
                "accept_patterns": r[7], "rationale_md": r[8], "slide_ref": r[9],
                "difficulty": r[10], "bloom": r[11], "topic_tag": r[12],
            }
            for r in rows
        ]
        return {"lecture": lecture, "count": len(items), "items": items}
    finally:
        db._close(conn)


@app.get("/api/take-home/{lecture}")
def take_home_lecture(lecture: str):
    """List all take-home exam items for a lecture (derivation + essay)."""
    conn = db._conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, position, kind, prompt_md, model_answer_md, rubric_md,
                       max_points, expected_time_min, slide_ref, topic_tag
                FROM take_home_exam
                WHERE lecture = %s
                ORDER BY position
            """, (lecture,))
            rows = cur.fetchall()
        items = [
            {
                "id": r[0], "position": r[1], "kind": r[2], "prompt_md": r[3],
                "model_answer_md": r[4], "rubric_md": r[5],
                "max_points": r[6], "expected_time_min": r[7],
                "slide_ref": r[8], "topic_tag": r[9],
            }
            for r in rows
        ]
        return {"lecture": lecture, "count": len(items), "items": items}
    finally:
        db._close(conn)


@app.get("/api/course/{lecture}")
def course_view(lecture: str):
    """Course-inheritance view: summary + narration stub-counts + quiz/take-home counts."""
    conn = db._conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT s.lecture, s.summary, s.generated_at,
                       (SELECT COUNT(*) FROM lecture_narrations n WHERE n.lecture=s.lecture) AS narration_steps,
                       (SELECT COUNT(*) FROM quiz_items q WHERE q.lecture=s.lecture) AS quiz_n,
                       (SELECT COUNT(*) FROM take_home_exam t WHERE t.lecture=s.lecture) AS take_home_n
                FROM lecture_summaries s
                WHERE s.lecture = %s
            """, (lecture,))
            row = cur.fetchone()
        if not row:
            raise HTTPException(404, detail=f"No course data for {lecture}")
        return {
            "lecture": row[0],
            "summary": row[1],
            "summary_generated_at": row[2].isoformat() if row[2] else None,
            "narration_steps": row[3],
            "quiz_n": row[4],
            "take_home_n": row[5],
        }
    finally:
        db._close(conn)


# ─── Lecture mode (Opus-designed guided tours) ───────────────────────

@app.get("/api/lecture/list")
def lecture_list():
    return {"plans": lecture_mod.list_plans()}


@app.post("/api/lecture/start")
async def lecture_start(req: dict):
    lecture_id = req.get("lecture_id") or "L3"
    user_id    = int(req.get("user_id") or 1)
    try:
        return lecture_mod.start_lecture(lecture_id, user_id=user_id)
    except ValueError as e:
        raise HTTPException(404, detail=str(e))


@app.post("/api/lecture/narrate")
async def lecture_narrate(req: dict):
    sid    = req.get("session_id")
    expand = bool(req.get("expand", True))
    if not sid:
        raise HTTPException(400, detail="session_id required")
    try:
        return await lecture_mod.narrate_step(sid, expand=expand)
    except KeyError as e:
        raise HTTPException(404, detail=str(e))


@app.post("/api/lecture/advance")
async def lecture_advance(req: dict):
    sid = req.get("session_id")
    if not sid:
        raise HTTPException(400, detail="session_id required")
    try:
        return lecture_mod.advance_lecture(sid)
    except KeyError as e:
        raise HTTPException(404, detail=str(e))


@app.post("/api/lecture/submit")
async def lecture_submit(req: dict):
    sid = req.get("session_id")
    answer = req.get("answer", "")
    if not sid:
        raise HTTPException(400, detail="session_id required")
    try:
        return lecture_mod.submit_intuition(sid, answer)
    except KeyError as e:
        raise HTTPException(404, detail=str(e))


@app.post("/api/verify")
def verify(req: VerifyReq):
    """SymPy symbolic verifier (cascade entry). Returns {status, layer, residual_latex, elapsed_ms}."""
    return verify_equation(req.lhs, req.rhs).to_dict()


@app.post("/api/review/multi-lens")
async def multi_lens(req: MultiLensReq):
    """Run a one-shot Multi-Lens Review on the supplied text. For dev/QA + demo."""
    a = Artifact(
        kind=req.kind, text=req.text,
        citation=req.citation,
        declared_difficulty=req.declared_difficulty,
        declared_bloom=req.declared_bloom,
    )
    res = await multi_lens_review(a, max_rounds=3)
    return {
        "status": res.status, "rounds": res.rounds,
        "text": res.text, "final_difficulty": res.final_difficulty,
        "elapsed_ms": res.elapsed_ms,
        "verdicts_per_round": [[v.to_dict() for v in r] for r in res.verdicts_per_round],
    }


@app.post("/api/users/ensure")
def users_ensure(user_id: int = 1):
    """
    Idempotently create a `users` row for an auto-issued per-browser user_id.
    Called by the frontend on first load (when localStorage has no bri610.user_id).
    Safe under concurrent requests via INSERT ... ON CONFLICT DO NOTHING.
    """
    from db_pool import acquire, release
    conn = acquire()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (id, email, display_name)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (user_id, f'user{user_id}@bri610.local', f'학습자 {user_id}'))
            conn.commit()
        return {"ok": True, "user_id": user_id}
    finally:
        release(conn)


@app.get("/api/me")
def get_me(user_id: int = 1):
    """
    Current-user gamification state.
    Returns: id, email, display_name, streak_days, streak_last_date, xp, level,
             badges, persona_voice, daily_goal_min,
             today_reviewed, today_correct, due_count.
    """
    try:
        from db_pool import acquire as _acquire, release as _release
        conn = _acquire()
        cur  = conn.cursor()
        try:
            cur.execute("""
                SELECT id, email, display_name, streak_days, streak_last_date,
                       xp, level, badges, persona_voice, daily_goal_min
                FROM users WHERE id = %s
            """, (user_id,))
            row = cur.fetchone()
            if row is None:
                raise HTTPException(404, detail=f"User {user_id} not found")
            (uid, email, display_name, streak_days, streak_last_date,
             xp, level, badges, persona_voice, daily_goal_min) = row

            # today_reviewed / today_correct — count srs_reviews for this user today
            cur.execute("""
                SELECT COUNT(*) FILTER (WHERE TRUE)                    AS today_reviewed,
                       COUNT(*) FILTER (WHERE r.rating >= 3)           AS today_correct
                FROM srs_reviews r
                JOIN srs_cards c ON c.id = r.card_id
                WHERE c.user_id = %s
                  AND r.reviewed_at::date = CURRENT_DATE
            """, (user_id,))
            today_reviewed, today_correct = cur.fetchone()

            # due_count — cards due today (due <= now or due is null i.e. new)
            cur.execute("""
                SELECT COUNT(*) FROM srs_cards
                WHERE user_id = %s AND (due IS NULL OR due <= now())
            """, (user_id,))
            (due_count,) = cur.fetchone()

            import json as _json
            _badges = badges if isinstance(badges, list) else _json.loads(badges or "[]")

            return {
                "id":               uid,
                "email":            email,
                "display_name":     display_name,
                "streak_days":      streak_days or 0,
                "streak_last_date": streak_last_date.isoformat() if streak_last_date else None,
                "xp":               xp or 0,
                "level":            level or 1,
                "badges":           _badges,
                "persona_voice":    persona_voice or "뉴런쌤",
                "daily_goal_min":   daily_goal_min or 20,
                "today_reviewed":   int(today_reviewed or 0),
                "today_correct":    int(today_correct or 0),
                "due_count":        int(due_count or 0),
                "xp_progress":      xp_to_next_level(xp or 0),
            }
        finally:
            _release(conn)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=f"get_me failed: {e}")


@app.post("/api/me/streak/touch")
def streak_touch(user_id: int = 1):
    """
    Call at session start: bumps streak if streak_last_date < today,
    resets to 1 if a day was skipped, no-ops if already touched today.
    Returns updated me dict.
    """
    try:
        from db_pool import acquire as _acquire, release as _release
        from datetime import date, timedelta
        conn = _acquire()
        cur  = conn.cursor()
        try:
            cur.execute(
                "SELECT streak_days, streak_last_date FROM users WHERE id = %s",
                (user_id,)
            )
            row = cur.fetchone()
            if row is None:
                raise HTTPException(404, detail=f"User {user_id} not found")
            streak_days, streak_last_date = row
            today = date.today()

            if streak_last_date is None or streak_last_date < today:
                if streak_last_date is not None and streak_last_date < today - timedelta(days=1):
                    # Missed a day — reset streak
                    new_streak = 1
                else:
                    new_streak = (streak_days or 0) + 1
                cur.execute("""
                    UPDATE users
                       SET streak_days = %s, streak_last_date = %s
                     WHERE id = %s
                """, (new_streak, today, user_id))
                conn.commit()
        finally:
            _release(conn)
        return get_me(user_id=user_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=f"streak_touch failed: {e}")


@app.post("/api/persona/wrap")
async def persona_wrap(req: PersonaReq):
    ctx = PersonaContext(
        name=req.name or "뉴런쌤",
        last_topic=req.last_topic,
        recent_struggle=req.recent_struggle,
        streak_days=req.streak_days,
        daily_goal_met=req.daily_goal_met,
        user_display_name=req.user_display_name,
    )
    out = await wrap_with_persona(req.text, ctx)
    return {"text": out}


# ─── v0.5 Walkthrough endpoints ───────────────────────────────────────────────

from walkthrough import step_walkthrough as _step_walkthrough, start_walkthrough as _start_walkthrough, get_session_state as _get_session_state
from agents.walkthrough import list_walkthroughs as _list_walkthroughs


class WalkthroughStartReq(BaseModel):
    walkthrough_id: str
    user_id: int = 1


class WalkthroughStepReq(BaseModel):
    session_id: str
    user_input: str
    latex_attempt: Optional[str] = None


@app.get("/api/walkthrough/list")
def walkthrough_list():
    """List all available walkthroughs (id, title, lecture, topic, num_steps)."""
    return {"walkthroughs": _list_walkthroughs()}


@app.post("/api/walkthrough/start")
def walkthrough_start(req: WalkthroughStartReq):
    """Start a new walkthrough session. Returns {session_id, first_step}."""
    try:
        return _start_walkthrough(req.walkthrough_id, req.user_id)
    except ValueError as e:
        raise HTTPException(404, detail=str(e))


@app.post("/api/walkthrough/step")
async def walkthrough_step(req: WalkthroughStepReq):
    """
    Submit a student response and advance the walkthrough.
    Returns {step_id, narration_md, move_used, verifier_result, input_gate, is_complete}.
    Returns 422 when the structured-input gate is not satisfied.
    """
    try:
        result = await _step_walkthrough(
            session_id=req.session_id,
            user_input=req.user_input,
            latex_attempt=req.latex_attempt,
        )
        # If gate failed, translate to 422
        if result.get("gate_error"):
            missing = result["input_gate"].get("missing", [])
            raise HTTPException(
                422,
                detail={
                    "message": "구조화된 입력이 필요합니다 (Structured input required).",
                    "required": result["input_gate"]["required"],
                    "missing": missing,
                },
            )
        return result
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(404, detail=str(e))
    except Exception as e:
        raise HTTPException(500, detail=f"walkthrough_step failed: {e}")


@app.get("/api/walkthrough/state/{session_id}")
def walkthrough_state(session_id: str):
    """Return current session state for UI restoration."""
    state = _get_session_state(session_id)
    if not state:
        raise HTTPException(404, detail=f"Session not found: {session_id}")
    return state


# ─── Mastery dashboard (topic × Bloom heatmap) ──────────────────────

@app.get("/api/me/mastery")
def me_mastery_grid(user_id: int = 1):
    """
    Returns aggregate mastery per (topic, bloom) cell + recommendations.

    Mastery is computed from FSRS retention rate * accuracy on the most recent
    reviews. Cells with no cards return null. Recommendations select the lowest-
    mastery cells with the most cards (high-leverage targets).
    """
    from db_pool import acquire, release
    from psycopg2.extras import RealDictCursor

    conn = acquire()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Per-cell aggregate from question_bank + srs_cards + recent srs_reviews
            cur.execute("""
                WITH cell_cards AS (
                  SELECT q.topic, COALESCE(q.bloom, 'Understand') AS bloom,
                         q.id AS qid, q.difficulty
                  FROM question_bank q
                  WHERE q.status = 'active'
                ),
                card_perf AS (
                  SELECT cc.topic, cc.bloom, cc.qid,
                         COALESCE(sc.stability, 0)::float AS stability,
                         COALESCE(sc.state, 'New') AS state,
                         (SELECT AVG(CASE WHEN rating >= 3 THEN 1 ELSE 0 END)::float
                          FROM srs_reviews
                          WHERE card_id = sc.id
                            AND reviewed_at > NOW() - INTERVAL '14 days') AS recent_acc
                  FROM cell_cards cc
                  LEFT JOIN srs_cards sc ON sc.bank_item_id = cc.qid
                                         AND sc.user_id = %s
                )
                SELECT topic, bloom,
                       COUNT(*) AS n,
                       AVG(LEAST(stability / 30.0, 1.0)) AS avg_retention,
                       AVG(COALESCE(recent_acc, 0.5)) AS avg_acc
                FROM card_perf
                GROUP BY topic, bloom
                ORDER BY topic, bloom
            """, (user_id,))
            rows = cur.fetchall()

            grid = {}
            for r in rows:
                topic = r['topic']
                bloom = r['bloom']
                ret = float(r['avg_retention'] or 0)
                acc = float(r['avg_acc'] or 0)
                # Mastery = weighted blend; 60% accuracy + 40% retention
                mastery = 0.6 * acc + 0.4 * ret
                grid.setdefault(topic, {})[bloom] = {
                    'mastery': round(mastery, 3),
                    'n':       int(r['n']),
                    'retention': round(ret, 3),
                    'accuracy':  round(acc, 3),
                }

            # Overall stats
            cur.execute("""
                SELECT COUNT(*) FILTER (WHERE due IS NOT NULL AND due <= NOW())  AS due_count,
                       COUNT(*) FILTER (WHERE last_review IS NOT NULL
                                        AND last_review::date = CURRENT_DATE)     AS today_reviewed
                FROM srs_cards WHERE user_id = %s
            """, (user_id,))
            agg = cur.fetchone() or {}

            # Mean mastery across all cells
            all_m = []
            for t in grid.values():
                for b in t.values():
                    all_m.append(b['mastery'])
            mean_mastery = sum(all_m)/len(all_m) if all_m else 0

            # Recommendations: lowest mastery cells with ≥2 cards (high leverage)
            recs = []
            for topic, blooms in grid.items():
                for bloom, cell in blooms.items():
                    if cell['n'] >= 2:
                        recs.append({
                            'topic': topic,
                            'bloom': bloom,
                            'n':     cell['n'],
                            'current_mastery': cell['mastery'],
                            'reason': (
                                f"숙련도 {round(cell['mastery']*100)}% — {cell['n']} 카드 보강 시 가장 많은 격차 해소"
                                if cell['mastery'] < 0.7 else
                                f"숙련도 {round(cell['mastery']*100)}% — 유지 복습"
                            ),
                        })
            recs.sort(key=lambda r: (r['current_mastery'], -r['n']))
            recs = recs[:5]

            return {
                'grid': grid,
                'recommendations': recs,
                'overall': {
                    'mean': round(mean_mastery, 3),
                    'due_count': int(agg.get('due_count') or 0),
                    'today_reviewed': int(agg.get('today_reviewed') or 0),
                },
            }
    finally:
        release(conn)


# ─── Course (1-hour compact L2–L8 study course) ─────────────────────

class CourseAnswerReq(BaseModel):
    run_id: int
    question_id: int
    user_answer: str
    time_spent_s: int = 0


@app.get("/api/course/overview")
def course_overview():
    """Static plan overview — counts per lecture, total time budget."""
    from db_pool import acquire, release
    from psycopg2.extras import RealDictCursor
    conn = acquire()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT lecture, kind, COUNT(*) AS n, SUM(expected_time_s)::int AS total_s
                FROM course_questions
                GROUP BY lecture, kind ORDER BY lecture, kind
            """)
            rows = cur.fetchall()
        plan = {}
        total_s = 0
        for r in rows:
            lec = r["lecture"]
            plan.setdefault(lec, {"mandatory": 0, "applied": 0, "time_s": 0})
            plan[lec][r["kind"]] = r["n"]
            plan[lec]["time_s"] += r["total_s"] or 0
            total_s += r["total_s"] or 0
        return {
            "lectures": [{"lecture": k, **v} for k, v in plan.items()],
            "total_questions": sum(v["mandatory"] + v["applied"] for v in plan.values()),
            "total_time_s": total_s,
            "target_time_s": 3600,
        }
    finally:
        release(conn)


@app.post("/api/course/start")
def course_start(user_id: int = 1):
    """Begin a new run, or resume the latest in-progress one."""
    from db_pool import acquire, release
    from psycopg2.extras import RealDictCursor
    conn = acquire()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, current_index, correct_count, total_attempted
                FROM course_runs
                WHERE user_id = %s AND status = 'in_progress'
                ORDER BY started_at DESC LIMIT 1
            """, (user_id,))
            existing = cur.fetchone()
            if existing:
                return {"run_id": existing["id"], "current_index": existing["current_index"],
                        "resumed": True, "correct": existing["correct_count"],
                        "attempted": existing["total_attempted"]}

            cur.execute("""
                INSERT INTO course_runs (user_id) VALUES (%s) RETURNING id
            """, (user_id,))
            run_id = cur.fetchone()["id"]
            conn.commit()
            return {"run_id": run_id, "current_index": 0, "resumed": False,
                    "correct": 0, "attempted": 0}
    finally:
        release(conn)


@app.get("/api/course/next")
def course_next(run_id: int):
    """Return the next question for this run, or {done: true} if course complete."""
    from db_pool import acquire, release
    from psycopg2.extras import RealDictCursor
    conn = acquire()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT current_index, status FROM course_runs WHERE id=%s
            """, (run_id,))
            run = cur.fetchone()
            if not run:
                raise HTTPException(404, "run_not_found")
            if run["status"] == 'completed':
                return {"done": True}
            idx = run["current_index"]

            cur.execute("""
                SELECT id, lecture, segment_position, kind, prompt_md,
                       slide_page, topic_tag, expected_time_s
                FROM course_questions
                ORDER BY lecture, segment_position
                LIMIT 1 OFFSET %s
            """, (idx,))
            q = cur.fetchone()
            if not q:
                cur.execute("UPDATE course_runs SET status='completed', completed_at=NOW() WHERE id=%s", (run_id,))
                conn.commit()
                return {"done": True}

            cur.execute("SELECT COUNT(*) AS total FROM course_questions")
            total = cur.fetchone()["total"]
            return {
                "done": False,
                "index": idx,
                "total": total,
                "question": dict(q),
            }
    finally:
        release(conn)


@app.post("/api/course/answer")
def course_answer(req: CourseAnswerReq):
    """Submit an answer; grade it; advance index."""
    from db_pool import acquire, release
    from psycopg2.extras import RealDictCursor
    conn = acquire()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT answer_md, rationale_md, slide_page
                FROM course_questions WHERE id=%s
            """, (req.question_id,))
            q = cur.fetchone()
            if not q:
                raise HTTPException(404, "question_not_found")

            # Lightweight grading: keyword overlap. The user can self-grade more rigorously
            # with the SymPy verifier on `/api/verify` for math answers.
            user = (req.user_answer or "").strip().lower()
            answer = (q["answer_md"] or "").lower()
            correct = False
            if user:
                # 30% character coverage of the canonical answer counts as correct
                u_words = set(t for t in user.split() if len(t) > 2)
                a_words = set(t for t in answer.split() if len(t) > 2)
                if a_words:
                    overlap = len(u_words & a_words) / len(a_words)
                    correct = overlap >= 0.30

            cur.execute("""
                INSERT INTO course_responses (run_id, question_id, user_answer_md, correct, time_spent_s)
                VALUES (%s, %s, %s, %s, %s)
            """, (req.run_id, req.question_id, req.user_answer, correct, req.time_spent_s))

            # Atomic increment under row-level lock — prevents two concurrent
            # /api/course/answer calls on the same run from double-incrementing.
            cur.execute("""
                UPDATE course_runs
                SET current_index = current_index + 1,
                    correct_count = correct_count + %s,
                    total_attempted = total_attempted + 1,
                    total_time_s = total_time_s + %s
                WHERE id = %s AND status = 'in_progress'
                RETURNING current_index, correct_count, total_attempted
            """, (1 if correct else 0, req.time_spent_s, req.run_id))
            updated = cur.fetchone()
            conn.commit()

            return {
                "correct": correct,
                "canonical_answer_md": q["answer_md"],
                "rationale_md": q["rationale_md"],
                "slide_page": q["slide_page"],
                "current_index": updated["current_index"],
                "correct_count": updated["correct_count"],
                "total_attempted": updated["total_attempted"],
            }
    finally:
        release(conn)


@app.get("/api/course/run/{run_id}")
def course_run_state(run_id: int):
    from db_pool import acquire, release
    from psycopg2.extras import RealDictCursor
    conn = acquire()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, started_at, completed_at, current_index,
                       correct_count, total_attempted, status, total_time_s
                FROM course_runs WHERE id=%s
            """, (run_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "run_not_found")
            return dict(row)
    finally:
        release(conn)


# ─── Frontend (production build) ───

if os.path.isdir(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="frontend-assets")

    @app.get("/{path:path}")
    def serve_frontend(path: str):
        file = os.path.join(FRONTEND_DIR, path)
        if os.path.isfile(file):
            return FileResponse(file)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
