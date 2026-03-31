# BRI610 AI Tutor

AI-powered study assistant for BRI610 Computational Neuroscience (SNU BCS, Prof. Jeehyun Kwag).

Multi-agent RAG system with multimodal retrieval over lecture slides, Dayan & Abbott, and Fundamental Neuroscience.

## Architecture

```
User Query → Router Agent → Specialized Agent (Tutor|Quiz|Exam|Summary|Derive)
                                    ↓
                           Hybrid Retriever (RRF fusion)
                           ├── Nemotron VL multimodal vectors (slides as images)
                           ├── Nemotron VL text vectors (textbook chunks)
                           └── FTS5 keyword search
```

**Models (all free via OpenRouter):**
- **Reasoning:** `qwen/qwen3.6-plus-preview:free`
- **Embedding:** `nvidia/llama-nemotron-embed-vl-1b-v2:free` (2048-dim, image+text)

**Agent Team:**
- **Router** — classifies intent → dispatches to specialist
- **Tutor** — Q&A, concept explanation with citations
- **Derive** — step-by-step math derivations (Nernst, GHK, HH, Cable)
- **Quiz** — generates MCQ/short answer/derivation problems
- **Exam** — mock exams with grading and feedback
- **Summary** — per-lecture review with equations and concept maps

## Data

| Source | Records | Embedding |
|--------|---------|-----------|
| Lecture Slides (L2-L6) | 199 | Image (multimodal) |
| Dayan & Abbott | 408 chunks | Text |
| Fundamental Neuroscience | 1,585 chunks | Text |
| **Total** | **2,192** | |

## Quick Start

### Prerequisites
- Python 3.10+, Node.js 18+
- [OpenRouter API key](https://openrouter.ai/keys) (free tier models)

### 1. Setup
```bash
git clone https://github.com/Joonoh991119/bri610-tutor.git
cd bri610-tutor
cp .env.example .env
# Edit .env: add your OPENROUTER_API_KEY

# Download DB from releases
wget -P data/ https://github.com/Joonoh991119/bri610-tutor/releases/download/v0.1.0/bri610_lectures.db
```

### 2. Generate Embeddings (first time only)
```bash
cd pipeline
python embed_all.py --key $OPENROUTER_API_KEY --db ../data/bri610_lectures.db
```

### 3. Backend
```bash
cd backend
pip install -r requirements.txt
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
| `DATA_DIR` | `../data` | Path to DB + images |

## License

For personal educational use only. Lecture materials © Prof. Jeehyun Kwag, SNU.
Textbook content © respective publishers.
