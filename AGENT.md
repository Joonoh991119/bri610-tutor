# BRI610 AI Tutor — Agent Workflow & Architecture

## Version: v0.3 (PostgreSQL + pgvector)

---

## System Architecture

```
┌──────────────┐     ┌──────────────────┐     ┌─────────────────────────────┐
│ React Frontend│────▶│ FastAPI Backend   │────▶│ Agent Team (Qwen3.6)        │
│ 6 tabs + KaTeX│     │ main.py v0.3     │     │ Router → Tutor/Derive/Quiz/ │
└──────────────┘     └────────┬─────────┘     │          Exam/Summary       │
                              │                └──────────────┬──────────────┘
                              ▼                               │
                     ┌─────────────────┐                      ▼
                     │ HybridRetriever  │           ┌──────────────────┐
                     │ retriever.py v0.3│           │ Context Builder   │
                     └────────┬────────┘           └──────────────────┘
                              │
                 ┌────────────┼────────────┐
                 ▼            ▼            ▼
          ┌──────────┐ ┌──────────┐ ┌──────────┐
          │ pgvector  │ │ pgvector  │ │ PG FTS   │
          │ slides    │ │ textbook  │ │ tsvector │
          │ (image    │ │ (text +   │ │ (GIN     │
          │  embed)   │ │  image    │ │  index)  │
          │           │ │  dual)    │ │          │
          └──────────┘ └──────────┘ └──────────┘
                 │            │            │
                 └────────────┼────────────┘
                              ▼
                     ┌─────────────────┐
                     │ RRF Fusion      │
                     │ α=0.6 vec       │
                     │ (1-α)=0.4 fts   │
                     └─────────────────┘
```

---

## Pipeline Harness — Stage-Gate Workflow

### Design Principles
1. **Accuracy > Token Efficiency**: Full content embedding (up to 32k chars), no lossy truncation
2. **Zero Information Loss**: Dual embedding (text + image) for visual pages
3. **Stage-Gate QC**: Each stage must pass quality gate before next stage runs
4. **Crash Resilience**: Commit every 10 pages, idempotent operations, resume from failure

### Stages

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌──────────┐
│ PARSE   │───▶│ QC      │───▶│ EMBED   │───▶│ VERIFY   │
│ ≥90%    │    │ ≥95%    │    │ ≥98%    │    │ ≥95%     │
│ pass    │    │ pass    │    │ pass    │    │ coverage │
└─────────┘    └─────────┘    └─────────┘    └──────────┘
   Gate 1         Gate 2      Gate 3 (loop)    Gate 4
```

#### Stage 1: PARSE (Parse Agent)
- **Input**: PDF files (Dayan&Abbott, Fundamental Neuroscience)
- **Process**: PyMuPDF page-level extraction → 6-way classification → PostgreSQL
- **Output**: `textbook_pages` rows with content, metadata, rasterized images
- **Gate**: ≥90% pages successfully parsed and inserted
- **Key**: ALL pages rasterized at 150 DPI (not just visual pages)

#### Stage 2: QC (Quality Check Agent)
- **Input**: Pages with `qc_status='pending'`
- **6 Checks**:
  - `content_not_empty`: >30 chars
  - `chapter_assigned`: TOC mapping succeeded
  - `type_consistent`: page_type matches content features
  - `not_blank_page`: no "intentionally left blank"
  - `image_exists`: rasterized image on disk
  - `reasonable_length`: <15000 chars (no garbled extraction)
- **Output**: `qc_status` = passed/failed/skipped + `qc_log` entries
- **Gate**: ≥95% of non-skipped pages pass all checks

#### Stage 3: EMBED (Embedder Agent)
- **Input**: QC-passed pages without embeddings
- **Strategy (Accuracy-First)**:
  - `text_embedding`: ALL pages with content >50 chars → full text up to 32k chars
  - `image_embedding`: equation/mixed/figure pages → JPEG base64 image
  - Model: `nvidia/llama-nemotron-embed-vl-1b-v2:free` (2048-dim)
- **Loop**: Runs in batches (default 50), repeats until all pages embedded
- **Rate Limit**: 0.3s delay between requests, exponential backoff on 429
- **Gate**: ≥98% of attempted embeddings succeed
- **Crash Safety**: Commits every 10 pages

#### Stage 4: VERIFY (Verification Agent)
- **Checks**:
  - All QC-passed pages have `text_embedding`
  - All visual pages have `image_embedding`
  - Dimension validation (2048)
- **Gate**: ≥95% embedding coverage
- **Output**: JSON report with per-book metrics

### Running the Pipeline

```bash
# Full auto-pipeline (recommended)
python pipeline/pipeline_harness.py run --key $OPENROUTER_API_KEY --batch 50

# Individual stages
python pipeline/pipeline_harness.py parse --book DA
python pipeline/pipeline_harness.py qc --fix
python pipeline/pipeline_harness.py embed --key $OPENROUTER_API_KEY --batch 50
python pipeline/pipeline_harness.py verify
python pipeline/pipeline_harness.py status
```

### Pipeline Reports
- Saved to `logs/pipeline_report_YYYYMMDD_HHMMSS.json`
- Contains per-stage results, pass rates, error lists, metrics

---

## Retrieval Strategy

### Hybrid Retriever v0.3 (PostgreSQL)

| Source | Embedding | Search Method | Score |
|--------|-----------|--------------|-------|
| Slides | image_embedding (2048-dim) | pgvector cosine | 1 - (emb <=> query) |
| Textbook (text pages) | text_embedding (2048-dim) | pgvector cosine | 1 - (emb <=> query) |
| Textbook (visual pages) | text_embedding + image_embedding | pgvector dual | max(text_sim, img_sim) |
| All | content + topics/section_title | PostgreSQL tsvector FTS | ts_rank_cd |

### RRF Fusion
```
score(doc) = Σ  weight / (k + rank + 1)
             sources

k = 60 (standard RRF constant)
α = 0.6 (vector weight)
1 - α = 0.4 (FTS weight)
```

### Key A/B Test Findings
- Text embedding > image embedding for text-extractable pages (8-33% higher cosine sim)
- Image embedding wins for equation-heavy pages where OCR loses formula structure
- Cross-modal retrieval works: text query ↔ slide image (3x similarity differential)
- **Optimal**: text_embedding as primary, image_embedding as supplementary → `max(both)` per page

---

## Agent Team

### Router
- Classifies intent → `tutor` | `derive` | `quiz` | `exam` | `summary`
- Zero-shot classification with Qwen3.6 (temperature=0.0, max_tokens=10)

### Specialist Agents
| Agent | Role | Temperature | Key Feature |
|-------|------|-------------|-------------|
| Tutor | Q&A, concept explanation | 0.7 | Cites [Slide L3 p.29], builds from first principles |
| Derive | Step-by-step math derivation | 0.7 | Every step shown, dimensional analysis |
| Quiz | Practice question generation | 0.8 | JSON output, MCQ/short/derivation/T-F |
| Exam | Mock exam + grading | 0.7 | Point-valued, partial credit |
| Summary | Lecture review + concept map | 0.7 | 6-section structured output |

### Context Flow
```
User Query → Router → Retrieve (top 6-10) → Build Context → Agent → Response
                                                    ↑
                                              HybridRetriever
                                              (pgvector + FTS + RRF)
```

---

## Database Schema (PostgreSQL)

### Tables
```sql
slides (id, lecture, lecture_title, page_num, content, topics,
        img_path, embedding vector(2048), qc_status, qc_notes)
  UNIQUE(lecture, page_num)
  GIN INDEX on tsvector(content || topics)

textbook_pages (id, book, page_num, chapter, chapter_title, section_title,
                content, content_length, has_figures, has_equations,
                has_references, has_captions, n_drawings, n_raster_images,
                page_type, img_path,
                text_embedding vector(2048), image_embedding vector(2048),
                qc_status, qc_notes)
  UNIQUE(book, page_num)
  GIN INDEX on tsvector(content || section_title)

qc_log (id, source_table, source_id, check_name, passed, details jsonb)
```

### Data Inventory
| Source | Total | QC Passed | QC Skipped | Embedded |
|--------|-------|-----------|------------|----------|
| Slides (L2-L6) | 199 | 199 | 0 | 199 (image) |
| Dayan & Abbott | 446 | 394 | 52 | ⏳ pending |
| Fund. Neuroscience | 1275 | 910 | 365 | ⏳ pending |
| **Total** | **1920** | **1503** | **417** | **199 + ⏳ 1304** |

---

## Running the Stack

```bash
# 1. Set API key
export OPENROUTER_API_KEY=<your_key>

# 2. Run embedding pipeline (if not yet done)
cd pipeline && python pipeline_harness.py run --key $OPENROUTER_API_KEY --batch 50

# 3. Start backend
cd backend && uvicorn main:app --host 0.0.0.0 --port 8000

# 4. Start frontend
cd frontend && npm run dev
# → http://localhost:3000
```

---

## File Map

```
bri610-tutor/
├── AGENT.md                    # THIS FILE — workflow docs
├── pipeline/
│   ├── pipeline_harness.py     # Stage-gate orchestrator (parse/qc/embed/verify)
│   ├── embed_all.py            # Legacy SQLite embedder (deprecated)
│   ├── schema.sql              # PostgreSQL DDL
│   ├── build_textbook_db.py    # Legacy SQLite builder (deprecated)
│   └── textbook_pages_manifest.csv  # QC-passed pages inventory
├── backend/
│   ├── main.py                 # FastAPI server v0.3 (PostgreSQL)
│   ├── retriever.py            # Hybrid retriever v0.3 (pgvector + FTS + RRF)
│   ├── db.py                   # DB access layer v0.3 (PostgreSQL)
│   ├── agents.py               # Agent team (Router + 5 specialists)
│   └── requirements.txt
├── frontend/
│   ├── src/App.jsx             # React app (6 tabs)
│   ├── src/components/         # ChatPanel, QuizPanel, ExamPanel, etc.
│   └── ...
├── data/
│   ├── L2/ ... L6/             # Lecture slide images
│   └── textbook_images/        # Rasterized textbook pages
│       ├── DA/                 # Dayan & Abbott
│       └── FN/                 # Fundamental Neuroscience
└── logs/                       # Pipeline execution logs + reports
```

---

## Migration Notes (v0.2 → v0.3)

### What Changed
1. **Database**: SQLite FTS5 → PostgreSQL + pgvector + tsvector GIN
2. **Data model**: `textbook_chunks` (section-level) → `textbook_pages` (page-level)
3. **Embedding**: Single column → Dual columns (`text_embedding` + `image_embedding`)
4. **Retriever**: In-memory cosine → pgvector `<=>` operator
5. **Pipeline**: Manual stages → Stage-gate orchestrator with QC hooks
6. **Logging**: Print statements → Structured logging to file + stdout

### Breaking Changes
- SQLite DB file no longer used by backend
- `textbook_chunks` table replaced by `textbook_pages`
- Backend requires PostgreSQL running on localhost:5432
- `retriever.py` constructor signature changed (no more `db_path`)
