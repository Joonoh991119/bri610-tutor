# BRI610 AI Tutor — Cowork Migration Task

## Your Identity
You are an autonomous DevOps agent executing the BRI610 AI Tutor embedding pipeline and E2E validation on the user's local Ubuntu machine.

## PERMISSIONS GRANTED (all authorized)
- File system: full read/write in ~/bri610-tutor/ and ~/
- PostgreSQL: db=bri610, user=tutor, password=tutor610 (localhost)
- Network: OpenRouter API calls (embedding + chat)
- Git: push to Joonoh991119/bri610-tutor (PAT configured in ~/.git-credentials)
- Process: start/stop uvicorn, npm dev server, PostgreSQL queries

## Credentials
- **OpenRouter API Key**: set as environment variable `OPENROUTER_API_KEY` (user will provide if not set)
- **PostgreSQL**: `dbname=bri610 user=tutor password=tutor610 host=localhost`
- **GitHub PAT**: already in `~/.git-credentials` (Contents write + Administration)
- **Zotero**: API key `BBqwwUnxFM9weV8alj0Lo3gB`, userID=15708780

## Repository
```
~/bri610-tutor/  (git: Joonoh991119/bri610-tutor, branch: main)
Latest commit: 4eb8071 "feat: v0.3.1 — Stage-gate workflow harness + PostgreSQL backend migration"
```

## Current System State
- **PostgreSQL running**: db `bri610` with pgvector extension
- **Tables**: `slides` (199 rows, all embedded), `textbook_pages` (1721 rows, 1304 QC-passed, 0 embedded), `qc_log`
- **Pipeline code**: v0.3.1 stage-gate harness ready
- **Backend code**: v0.3.0 PostgreSQL-based (retriever.py, db.py, main.py)
- **Frontend**: React+Vite+Tailwind on port 3000, proxy to backend:8000

## TASK: Execute in Order

### Phase 1: Verify Environment
```bash
cd ~/bri610-tutor
git pull origin main
pip install psycopg2-binary pgvector pymupdf requests httpx fastapi uvicorn

# Verify PostgreSQL
psql -d bri610 -U tutor -c "SELECT COUNT(*) FROM slides WHERE embedding IS NOT NULL;"
# Expected: 199

psql -d bri610 -U tutor -c "SELECT qc_status, COUNT(*) FROM textbook_pages GROUP BY qc_status;"
# Expected: passed=1304, skipped=417, pending=0 (or some pending if QC not run yet)

psql -d bri610 -U tutor -c "SELECT COUNT(*) FROM textbook_pages WHERE text_embedding IS NOT NULL;"
# Expected: 0 (embeddings not yet generated)
```

### Phase 2: Run Embedding Pipeline
```bash
cd ~/bri610-tutor/pipeline
export OPENROUTER_API_KEY=<key>

# Full auto-pipeline: will skip Parse+QC (already done), loop Embed, then Verify
python pipeline_harness.py run --key $OPENROUTER_API_KEY --batch 50
```

**What this does:**
1. Skips Parse (1721 pages already in DB)
2. Skips QC (1304 already passed)
3. Runs Embed in batches of 50, loops until all 1304 pages have:
   - `text_embedding`: ALL 1304 pages (full content, up to 32k chars)
   - `image_embedding`: equation/mixed/figure pages (~400-500 pages)
4. Runs Verify to confirm coverage

**Expected duration**: ~30-60 minutes (free tier rate limits, 0.3s between requests)
**Rate limiting**: Automatic exponential backoff on 429 responses
**Crash safety**: Commits every 10 pages. If interrupted, just re-run — it resumes from where it stopped.

**Monitor progress:**
```bash
# In another terminal
cd ~/bri610-tutor/pipeline
python pipeline_harness.py status
```

**If rate-limited or interrupted**, just re-run:
```bash
python pipeline_harness.py run --key $OPENROUTER_API_KEY --batch 50
```

### Phase 3: Verify Embeddings
```bash
# After pipeline completes, verify:
psql -d bri610 -U tutor -c "
  SELECT book,
    COUNT(*) FILTER (WHERE qc_status='passed') AS passed,
    COUNT(*) FILTER (WHERE qc_status='passed' AND text_embedding IS NOT NULL) AS text_emb,
    COUNT(*) FILTER (WHERE qc_status='passed' AND page_type IN ('mixed','figure','equation')) AS visual,
    COUNT(*) FILTER (WHERE qc_status='passed' AND page_type IN ('mixed','figure','equation') AND image_embedding IS NOT NULL) AS img_emb
  FROM textbook_pages GROUP BY book;
"
```

**Expected results:**
| book | passed | text_emb | visual | img_emb |
|------|--------|----------|--------|---------|
| Dayan_Abbott | 394 | 394 | ~150 | ~150 |
| Fundamental_Neuroscience | 910 | 910 | ~300 | ~300 |

### Phase 4: E2E Test — Backend
```bash
cd ~/bri610-tutor/backend
export OPENROUTER_API_KEY=<key>

# Start backend
uvicorn main:app --host 0.0.0.0 --port 8000 &

# Wait for startup
sleep 3

# Test 1: Health check
curl -s http://localhost:8000/api/health | python3 -m json.tool
# Verify: status=ok, backend=postgresql+pgvector, db.embedded > 1400

# Test 2: Lectures list
curl -s http://localhost:8000/api/lectures | python3 -m json.tool
# Verify: 5 lectures (L2-L6), textbook entries with page counts

# Test 3: Hybrid search (vector + FTS)
curl -s -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Nernst equation membrane potential", "limit": 5}' | python3 -m json.tool
# Verify: mix of slide + textbook results with scores

# Test 4: Chat (agent routing)
curl -s -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Explain the Hodgkin-Huxley model step by step", "mode": "auto"}' | python3 -m json.tool
# Verify: agent=tutor or derive, answer with LaTeX equations, sources cited

# Test 5: Quiz generation
curl -s -X POST http://localhost:8000/api/quiz \
  -H "Content-Type: application/json" \
  -d '{"topic": "cable equation", "lecture": "L6", "num_questions": 3}' | python3 -m json.tool
# Verify: JSON with 3 questions, options, answers, explanations

# Test 6: Korean language
curl -s -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Goldman 방정식의 유도과정을 설명해줘", "mode": "derive"}' | python3 -m json.tool
# Verify: Korean response with LaTeX math, step-by-step derivation

# Stop backend
kill %1
```

### Phase 5: E2E Test — Full Stack
```bash
# Terminal 1: Backend
cd ~/bri610-tutor/backend
export OPENROUTER_API_KEY=<key>
uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd ~/bri610-tutor/frontend
npm install  # first time only
npm run dev  # → http://localhost:3000
```

Open http://localhost:3000 in browser and test:
1. **Tutor tab**: Ask "What is the Nernst equation?" → should get cited answer
2. **Search tab**: Search "action potential" → should return slides + textbook pages
3. **Quiz tab**: Generate quiz on "membrane biophysics" → should show MCQ
4. **Slides tab**: Browse L5 slides → images should load
5. **Summary tab**: Summarize L3 → should produce structured summary

### Phase 6: Git Release
```bash
cd ~/bri610-tutor

# Dump current DB schema + data counts for release notes
psql -d bri610 -U tutor -c "\dt+ public.*" > /tmp/db_tables.txt

# Commit any pipeline reports
git add logs/ -f 2>/dev/null
git add -A
git commit -m "feat: v0.3.1 — embedding complete, E2E validated

Embedding stats:
- 199 slides: image embedding (2048-dim Nemotron VL)
- 1304 textbook pages: text embedding (all) + image embedding (visual pages)
- Retriever: pgvector cosine + FTS tsvector + RRF fusion
- Full E2E test passed: search, chat, quiz, exam, summary"

git push origin main

# Create release
git tag v0.3.1
git push origin v0.3.1
```

**Optional: DB backup as release asset**
```bash
pg_dump -U tutor bri610 --no-owner --no-privileges > /tmp/bri610_v031.sql
gzip /tmp/bri610_v031.sql

# Upload via GitHub API (use existing PAT from ~/.git-credentials)
# Or manually upload at: https://github.com/Joonoh991119/bri610-tutor/releases/new
```

## Troubleshooting

### "Rate limited" during embedding
Normal for free tier. The pipeline handles this automatically with exponential backoff. If it exits, just re-run — it resumes from where it stopped.

### "Connection refused" on PostgreSQL
```bash
sudo systemctl start postgresql
sudo -u postgres psql -c "ALTER USER tutor WITH PASSWORD 'tutor610';"
```

### "No module named X"
```bash
pip install psycopg2-binary pgvector pymupdf requests httpx fastapi uvicorn pydantic
```

### "text_embedding IS NULL" after pipeline run
Check logs: `cat ~/bri610-tutor/logs/pipeline_*.log | tail -50`
Re-run embed only: `python pipeline_harness.py embed --key $OPENROUTER_API_KEY --batch 50`

### Frontend can't reach backend
Ensure backend is running on port 8000 and vite proxy is configured:
```javascript
// frontend/vite.config.js → server.proxy
'/api': 'http://localhost:8000'
'/images': 'http://localhost:8000'
```

## Success Criteria
- [ ] `pipeline_harness.py status` shows 1304/1304 text_emb, ~450/~450 img_emb
- [ ] `curl /api/health` returns embedded > 1400
- [ ] `curl /api/search` returns mixed slide+textbook results
- [ ] `curl /api/chat` returns cited answers with LaTeX
- [ ] Frontend loads and all 6 tabs functional
- [ ] Git tag v0.3.1 pushed
