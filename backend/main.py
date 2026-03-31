"""
BRI610 AI Tutor — FastAPI Backend
RAG over lecture slides + Dayan & Abbott textbook
LLM: Ollama (local) with configurable model
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os

from rag import RAGEngine
from db import DB

# --- Config ---
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "data"))
DB_PATH = os.path.join(DATA_DIR, "bri610_lectures.db")
IMG_DIR = os.path.join(DATA_DIR, "lecture_images")
OLLAMA_BASE = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")

# --- App ---
app = FastAPI(title="BRI610 AI Tutor", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

db = DB(DB_PATH)
rag = RAGEngine(db, ollama_base=OLLAMA_BASE, model=OLLAMA_MODEL)

# Serve slide images
if os.path.isdir(IMG_DIR):
    app.mount("/images", StaticFiles(directory=IMG_DIR), name="images")


# --- Models ---
class SearchRequest(BaseModel):
    query: str
    source: str = "all"  # all | slides | textbook
    lecture: Optional[str] = None
    limit: int = 8

class ChatRequest(BaseModel):
    message: str
    lecture: Optional[str] = None
    mode: str = "tutor"  # tutor | quiz | summary | derive
    history: list = []

class QuizRequest(BaseModel):
    topic: str
    lecture: Optional[str] = None
    num_questions: int = 5
    difficulty: str = "medium"  # easy | medium | hard

class SummaryRequest(BaseModel):
    lecture: str  # L2-L6
    focus: Optional[str] = None  # optional topic focus


# --- Routes ---
@app.get("/api/health")
def health():
    stats = db.stats()
    return {"status": "ok", "db": stats, "model": OLLAMA_MODEL}

@app.get("/api/lectures")
def list_lectures():
    return db.list_lectures()

@app.get("/api/slide/{lecture}/{page}")
def get_slide(lecture: str, page: int):
    result = db.get_slide(lecture, page)
    if not result:
        raise HTTPException(404, "Slide not found")
    return result

@app.get("/api/slide-image/{lecture}/{page}")
def get_slide_image(lecture: str, page: int):
    path = os.path.join(IMG_DIR, lecture, f"p{page:02d}.jpg")
    if not os.path.isfile(path):
        raise HTTPException(404, "Image not found")
    return FileResponse(path, media_type="image/jpeg")

@app.post("/api/search")
def search(req: SearchRequest):
    return rag.search(req.query, source=req.source, lecture=req.lecture, limit=req.limit)

@app.post("/api/chat")
async def chat(req: ChatRequest):
    return await rag.chat(req.message, lecture=req.lecture, mode=req.mode, history=req.history)

@app.post("/api/quiz")
async def generate_quiz(req: QuizRequest):
    return await rag.generate_quiz(req.topic, lecture=req.lecture,
                                    num_questions=req.num_questions, difficulty=req.difficulty)

@app.post("/api/summary")
async def generate_summary(req: SummaryRequest):
    return await rag.generate_summary(req.lecture, focus=req.focus)
