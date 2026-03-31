# BRI610 AI Tutor

AI-powered study assistant for BRI610 Computational Neuroscience (SNU BCS, Prof. Jeehyun Kwag).

RAG-based tutoring over lecture slides + Dayan & Abbott textbook, powered by local LLM (Ollama).

## Features

- **Tutor Chat** — Ask questions, get answers with slide/textbook citations
- **Math Derivations** — Step-by-step equation derivations (Nernst, GHK, HH, Cable)
- **Quiz Generator** — Auto-generated practice questions by topic/difficulty
- **Exam Summaries** — Per-lecture key concept summaries
- **Slide Browser** — Visual slide gallery with navigation
- **Full-text Search** — SQLite FTS5 across 199 slides + 408 textbook chunks

## Architecture

```
Frontend (React + Vite)  →  Backend (FastAPI)  →  Ollama (local LLM)
                                    ↓
                           SQLite FTS5 Database
                           ├── slides (OCR from lecture PDFs)
                           └── textbook_chunks (Dayan & Abbott)
```

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- [Ollama](https://ollama.ai) installed and running

### 1. Setup Ollama
```bash
ollama pull llama3.1:8b   # or any preferred model
ollama serve              # start the server
```

### 2. Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

### 4. (Optional) Build Lecture DB
If you need to rebuild the database from source PDFs:
```bash
cd pipeline
python build_lecture_db.py    # OCR lecture slides
python build_textbook_db.py   # Parse Dayan & Abbott
```

## Configuration

Environment variables (or `.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.1:8b` | Model to use |
| `DATA_DIR` | `../data` | Path to DB + images |

## Data

| Source | Records | Type |
|--------|---------|------|
| Lecture Slides (L2-L6) | 199 | OCR-extracted text + images |
| Dayan & Abbott Textbook | 408 chunks | Chapter/section text |

### Lecture Coverage
- **L2**: Introduction to Computational Neuroscience (68 slides)
- **L3**: Neural Membrane Biophysics I (34 slides)
- **L4**: Neural Membrane Biophysics II (31 slides)
- **L5**: Action Potential & Hodgkin-Huxley (34 slides)
- **L6**: Cable Theory & AP Propagation (32 slides)

## License

For personal educational use only. Lecture materials © Prof. Jeehyun Kwag, SNU.
Textbook content © Dayan & Abbott, MIT Press.
