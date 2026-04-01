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
from agents import AgentTeam
from db import DB

DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "data"))
IMG_DIR = os.path.join(DATA_DIR, "lecture_images")
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")
CHAT_MODEL = os.environ.get("CHAT_MODEL", "qwen/qwen3.6-plus-preview:free")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "nvidia/llama-nemotron-embed-vl-1b-v2:free")
DB_DSN = os.environ.get("DATABASE_URL", "dbname=bri610 user=tutor password=tutor610 host=localhost")

app = FastAPI(title="BRI610 AI Tutor", version="0.3.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# PostgreSQL-backed retriever and DB
retriever = HybridRetriever(OPENROUTER_KEY, EMBED_MODEL, DB_DSN)
team = AgentTeam(retriever, OPENROUTER_KEY, CHAT_MODEL)
db = DB(DB_DSN)

if os.path.isdir(IMG_DIR):
    app.mount("/images", StaticFiles(directory=IMG_DIR), name="images")

# ─── Request Models ───

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

# ─── Endpoints ───

@app.get("/api/health")
def health():
    stats = db.stats()
    return {
        "status": "ok",
        "version": "0.3.0",
        "backend": "postgresql+pgvector",
        "chat_model": CHAT_MODEL,
        "embed_model": EMBED_MODEL,
        "db": stats,
        "retrieval": "hybrid_rrf",
    }

@app.get("/api/lectures")
def list_lectures():
    return db.list_lectures()

@app.get("/api/slide-image/{lecture}/{page}")
def get_slide_image(lecture: str, page: int):
    path = os.path.join(IMG_DIR, lecture, f"p{page:02d}.jpg")
    if not os.path.isfile(path):
        raise HTTPException(404)
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
