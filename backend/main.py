"""
BRI610 AI Tutor — FastAPI Backend v0.2
Agent Team + Hybrid Retrieval (Vector + FTS5)
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os, sqlite3

from retriever import HybridRetriever
from agents import AgentTeam

DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "data"))
DB_PATH = os.path.join(DATA_DIR, "bri610_lectures.db")
IMG_DIR = os.path.join(DATA_DIR, "lecture_images")
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")
CHAT_MODEL = os.environ.get("CHAT_MODEL", "qwen/qwen3.6-plus-preview:free")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "nvidia/llama-nemotron-embed-vl-1b-v2:free")

app = FastAPI(title="BRI610 AI Tutor", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

retriever = HybridRetriever(DB_PATH, OPENROUTER_KEY, EMBED_MODEL)
team = AgentTeam(retriever, OPENROUTER_KEY, CHAT_MODEL)

if os.path.isdir(IMG_DIR):
    app.mount("/images", StaticFiles(directory=IMG_DIR), name="images")

class SearchReq(BaseModel):
    query: str; lecture: Optional[str] = None; limit: int = 8
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

@app.get("/api/health")
def health():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    s = c.execute("SELECT COUNT(*) FROM slides").fetchone()[0]
    t = c.execute("SELECT COUNT(*) FROM textbook_chunks").fetchone()[0]
    e = c.execute("SELECT COUNT(*) FROM slides WHERE embedding IS NOT NULL").fetchone()[0]
    e2 = c.execute("SELECT COUNT(*) FROM textbook_chunks WHERE embedding IS NOT NULL").fetchone()[0]
    conn.close()
    return {"status": "ok", "chat_model": CHAT_MODEL, "embed_model": EMBED_MODEL,
            "db": {"slides": s, "textbook_chunks": t, "total": s+t, "embedded": e+e2},
            "retrieval": "hybrid"}

@app.get("/api/lectures")
def list_lectures():
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row
    lecs = [dict(r) for r in conn.execute("SELECT lecture as id, lecture_title as title, COUNT(*) as slides FROM slides GROUP BY lecture ORDER BY lecture")]
    books = [dict(r) for r in conn.execute("SELECT book, chapter, chapter_title, COUNT(*) as chunks FROM textbook_chunks GROUP BY book, chapter ORDER BY book, CAST(chapter AS INTEGER)")]
    conn.close()
    return {"lectures": lecs, "textbooks": books}

@app.get("/api/slide-image/{lecture}/{page}")
def get_slide_image(lecture: str, page: int):
    path = os.path.join(IMG_DIR, lecture, f"p{page:02d}.jpg")
    if not os.path.isfile(path): raise HTTPException(404)
    return FileResponse(path, media_type="image/jpeg")

@app.post("/api/search")
def search(req: SearchReq):
    return retriever.search(req.query, lecture=req.lecture, limit=req.limit)

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
