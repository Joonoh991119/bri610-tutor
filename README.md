# BRI610 AI Tutor

AI-powered study assistant for BRI610 Computational Neuroscience (SNU BCS, Prof. Jeehyun Kwag).

Multi-agent RAG system with multimodal retrieval over lecture slides, Dayan & Abbott, and Fundamental Neuroscience. PostgreSQL + pgvector backend.

## Architecture

```
User Query → Router Agent → Specialized Agent (Tutor|Quiz|Exam|Summary|Derive)
                                    ↓
                           Hybrid Retriever (RRF fusion)
                           ├── Nemotron VL image vectors (slides, figure pages)
                           ├── Nemotron VL text vectors (textbook pages)
                           ├── PostgreSQL pgvector cosine search
                           └── PostgreSQL full-text search (tsvector)
```

**Pipeline: Parse → QC → Embed**
```
PDF → Parser Agent (classify: text|equation|mixed|figure|references)
    → QC Agent (6 checks: content, chapter, type, blank, image, length)
    → Embedder Agent (text embed + image embed for visual pages)
    → PostgreSQL pgvector
```

**Models (free via OpenRouter):**
- **Reasoning:** `qwen/qwen3.6-plus-preview:free`  
- **Embedding:** `nvidia/llama-nemotron-embed-vl-1b-v2:free` (2048-dim, multimodal)

## Data

| Source | Pages | QC Passed | Embedding Strategy |
|--------|-------|-----------|-------------------|
| Lecture Slides (L2-L6) | 199 | 199 | Image (multimodal) ✅ |
| Dayan & Abbott | 446 | 394 | Text primary + Image (equation/figure pages) |
| Fundamental Neuroscience | 1,275 | 910 | Text primary + Image (equation/figure pages) |

## Quick Start

### Prerequisites
- Python 3.10+, Node.js 18+
- PostgreSQL 16+ with pgvector extension
- [OpenRouter API key](https://openrouter.ai/keys)

### 1. Database Setup
```bash
# Install pgvector
sudo apt install postgresql-16-pgvector

# Create database
sudo -u postgres psql -c "CREATE DATABASE bri610;"
sudo -u postgres psql -c "CREATE USER tutor WITH PASSWORD 'tutor610';"
sudo -u postgres psql -d bri610 -c "CREATE EXTENSION vector;"
sudo -u postgres psql -d bri610 -c "GRANT ALL ON SCHEMA public TO tutor;"

# Apply schema
psql -d bri610 -U tutor -f pipeline/schema.sql
```

### 2. Pipeline: Parse → QC → Embed
```bash
cd pipeline
export OPENROUTER_API_KEY=sk-or-v1-...

# Parse textbooks into pages
python pipeline_harness.py parse --book DA
python pipeline_harness.py parse --book FN

# Run QC checks
python pipeline_harness.py qc --fix

# Embed (batch, repeat until done)
python pipeline_harness.py embed --key $OPENROUTER_API_KEY --batch 50

# Check progress
python pipeline_harness.py status
```

### 3. Backend
```bash
cd backend
pip install -r requirements.txt
export OPENROUTER_API_KEY=sk-or-v1-...
uvicorn main:app --port 8000 --reload
```

### 4. Frontend
```bash
cd frontend
npm install && npm run dev
```

Open http://localhost:3000

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | (required) | OpenRouter API key |
| `CHAT_MODEL` | `qwen/qwen3.6-plus-preview:free` | Reasoning model |
| `EMBED_MODEL` | `nvidia/llama-nemotron-embed-vl-1b-v2:free` | Embedding model |
| `DATABASE_URL` | `dbname=bri610 user=tutor ...` | PostgreSQL connection |

## Agent Team

| Agent | Role | Trigger |
|-------|------|---------|
| **Router** | Classify intent | Auto on every message |
| **Tutor** | Q&A, concept explanation | "explain", "what is" |
| **Derive** | Step-by-step math | "derive", "prove", "show" |
| **Quiz** | Generate practice Qs | "quiz", "test me" |
| **Exam** | Mock exams + grading | "exam", "grade" |
| **Summary** | Lecture review | "summarize", "key points" |

## License

Personal educational use only. Lecture materials © Prof. Jeehyun Kwag, SNU.
