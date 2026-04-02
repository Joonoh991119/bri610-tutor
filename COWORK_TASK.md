# BRI610 AI Tutor — Cowork Autonomous Task

## Role
You are an autonomous DevOps/ML-Ops agent. Execute the full BRI610 AI Tutor embedding pipeline, PostgreSQL backend validation, and E2E system test on this local Ubuntu machine. Work independently. Do not ask for confirmation — all permissions are pre-granted below.

## ALL PERMISSIONS GRANTED
- **File system**: full read/write in `~/bri610-tutor/` and `~/`
- **PostgreSQL**: `db=bri610, user=tutor, password=tutor610, host=localhost`
- **Network**: OpenRouter API calls (embedding + chat models)
- **Git**: push to `Joonoh991119/bri610-tutor` (PAT in `~/.git-credentials`)
- **Processes**: start/stop uvicorn, npm dev, psql queries
- **Package install**: pip install, npm install as needed

## Credentials
```
OPENROUTER_API_KEY=<user will set in env or provide when asked>
DATABASE_URL=dbname=bri610 user=tutor password=tutor610 host=localhost
GitHub: PAT already in ~/.git-credentials (Contents write + Administration)
Zotero: API key BBqwwUnxFM9weV8alj0Lo3gB, userID=15708780
```

## Repository & Current State
```
~/bri610-tutor/  (Joonoh991119/bri610-tutor, branch: main)
Latest commit: 8dbf960
Version: v0.3.1

Key files:
  pipeline/pipeline_harness.py   — Stage-gate orchestrator (Parse→QC→Embed→Verify)
  backend/retriever.py           — Hybrid retriever (pgvector + FTS + RRF fusion)
  backend/db.py                  — PostgreSQL access layer
  backend/main.py                — FastAPI v0.3
  backend/agents.py              — Agent team (Router + Tutor/Derive/Quiz/Exam/Summary)
  AGENT.md                       — Full architecture docs
```

### PostgreSQL State
```
Database: bri610 (pgvector extension enabled)
Tables:
  slides          — 199 rows, ALL have embedding (image, 2048-dim Nemotron VL)
  textbook_pages  — 1721 rows total
                    1304 QC-passed (qc_status='passed')
                    417 skipped (references, front matter)
                    0 text_embedding (PENDING — this is the main task)
                    0 image_embedding (PENDING)
  qc_log          — QC audit trail
```

## TASK: Execute Sequentially

### Phase 1: Environment Verification
```bash
cd ~/bri610-tutor && git pull origin main

# Install deps
pip install psycopg2-binary pgvector pymupdf requests httpx fastapi uvicorn pydantic

# Verify PostgreSQL is running and accessible
psql -d bri610 -U tutor -c "SELECT COUNT(*) AS slides_embedded FROM slides WHERE embedding IS NOT NULL;"
# EXPECTED: 199

psql -d bri610 -U tutor -c "SELECT qc_status, COUNT(*) FROM textbook_pages GROUP BY qc_status ORDER BY qc_status;"
# EXPECTED: passed=1304, skipped=417 (maybe pending=0)

psql -d bri610 -U tutor -c "SELECT COUNT(*) AS text_emb FROM textbook_pages WHERE text_embedding IS NOT NULL;"
# EXPECTED: 0 (not yet embedded)

# Verify OPENROUTER_API_KEY is set
echo "API key set: ${OPENROUTER_API_KEY:+YES}"
# If not set, stop and ask user
```

**GATE**: All 3 queries return expected values and API key is set. If PostgreSQL is not running: `sudo systemctl start postgresql`. If API key missing: ask user once, then proceed.

### Phase 2: Run Embedding Pipeline (Main Task)
```bash
cd ~/bri610-tutor/pipeline
python pipeline_harness.py run --key $OPENROUTER_API_KEY --batch 50
```

**What the pipeline does automatically:**
1. **Skip Parse** — 1721 pages already in DB
2. **Skip QC** — 1304 already passed, 0 pending
3. **Embed (loops)** — batch 50 at a time until all 1304 pages done:
   - `text_embedding`: ALL 1304 QC-passed pages (full content, up to 32k chars)
   - `image_embedding`: equation/mixed/figure pages only (~400-500 pages)
   - Commits every 10 pages (crash-safe)
   - Auto-retries on rate limit (429) with exponential backoff
4. **Verify** — checks text_embedding and image_embedding coverage

**Expected duration**: 30-90 minutes (free tier, 0.3s delay between requests)

**If interrupted** (rate limit, network, etc.): just re-run the same command. It resumes from where it stopped — already-embedded pages are skipped.

**Monitor in separate terminal:**
```bash
cd ~/bri610-tutor/pipeline && python pipeline_harness.py status
```

**GATE**: Pipeline report in `logs/pipeline_report_*.json` shows Verify stage passed. If Embed stage has remaining > 0, re-run until 0.

### Phase 3: Verify Embedding Completeness
```bash
psql -d bri610 -U tutor -c "
  SELECT book,
    COUNT(*) FILTER (WHERE qc_status='passed') AS passed,
    COUNT(*) FILTER (WHERE qc_status='passed' AND text_embedding IS NOT NULL) AS text_emb,
    COUNT(*) FILTER (WHERE qc_status='passed' AND page_type IN ('mixed','figure','equation')) AS visual,
    COUNT(*) FILTER (WHERE qc_status='passed' AND page_type IN ('mixed','figure','equation') AND image_embedding IS NOT NULL) AS img_emb
  FROM textbook_pages GROUP BY book ORDER BY book;
"
```

**EXPECTED:**
```
       book             | passed | text_emb | visual | img_emb
------------------------+--------+----------+--------+---------
 Dayan_Abbott           |    394 |      394 |   ~150 |    ~150
 Fundamental_Neuroscience |    910 |      910 |   ~300 |    ~300
```

**GATE**: `text_emb = passed` for both books (100% coverage). `img_emb ≈ visual` (≥95%).

### Phase 4: Backend E2E Test
```bash
cd ~/bri610-tutor/backend
export OPENROUTER_API_KEY=$OPENROUTER_API_KEY
uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
sleep 3

# Test 1: Health
echo "=== TEST 1: Health ==="
curl -sf http://localhost:8000/api/health | python3 -m json.tool
# CHECK: status=ok, backend=postgresql+pgvector, db.embedded > 1400

# Test 2: Lectures
echo "=== TEST 2: Lectures ==="
curl -sf http://localhost:8000/api/lectures | python3 -c "
import json,sys; d=json.load(sys.stdin)
print(f'Lectures: {len(d[\"lectures\"])}')
print(f'Textbook chapters: {len(d[\"textbooks\"])}')
assert len(d['lectures']) == 5, 'Expected 5 lectures'
print('PASS')
"

# Test 3: Hybrid Search (vector + FTS)
echo "=== TEST 3: Hybrid Search ==="
curl -sf -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Nernst equation membrane potential", "limit": 5}' | python3 -c "
import json,sys; results=json.load(sys.stdin)
print(f'Results: {len(results)}')
sources = set(r['source'] for r in results)
print(f'Sources: {sources}')
assert len(results) > 0, 'No search results'
print('PASS')
"

# Test 4: Agent Chat (English)
echo "=== TEST 4: Chat (English) ==="
curl -sf -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Explain the Hodgkin-Huxley model", "mode": "auto"}' | python3 -c "
import json,sys; d=json.load(sys.stdin)
print(f'Agent: {d[\"agent\"]}')
print(f'Sources: {len(d[\"sources\"])}')
print(f'Answer length: {len(d[\"answer\"])} chars')
assert d['agent'] in ('tutor','derive'), f'Unexpected agent: {d[\"agent\"]}'
assert len(d['answer']) > 100, 'Answer too short'
print('PASS')
"

# Test 5: Quiz Generation
echo "=== TEST 5: Quiz ==="
curl -sf -X POST http://localhost:8000/api/quiz \
  -H "Content-Type: application/json" \
  -d '{"topic": "cable equation", "lecture": "L6", "num_questions": 3}' | python3 -c "
import json,sys; d=json.load(sys.stdin)
if 'questions' in d:
    print(f'Questions: {len(d[\"questions\"])}')
    print('PASS')
else:
    print(f'Raw response (parse may fail): {str(d)[:200]}')
    print('WARN: quiz JSON parse issue, but endpoint works')
"

# Test 6: Korean Language
echo "=== TEST 6: Chat (Korean) ==="
curl -sf -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Goldman 방정식의 유도과정을 설명해줘", "mode": "derive"}' | python3 -c "
import json,sys; d=json.load(sys.stdin)
print(f'Agent: {d[\"agent\"]}')
print(f'Answer preview: {d[\"answer\"][:150]}...')
assert len(d['answer']) > 50
print('PASS')
"

# Cleanup
kill $BACKEND_PID 2>/dev/null
echo ""
echo "=== ALL BACKEND TESTS COMPLETE ==="
```

**GATE**: All 6 tests print PASS (Test 5 WARN is acceptable).

### Phase 5: Frontend Smoke Test
```bash
cd ~/bri610-tutor/frontend
npm install 2>/dev/null
npm run dev &
FRONTEND_PID=$!
sleep 5

# Verify frontend serves
curl -sf http://localhost:3000 | head -5
# CHECK: HTML with <div id="root">

kill $FRONTEND_PID 2>/dev/null
echo "Frontend serves successfully"
```

### Phase 6: Commit & Tag Release
```bash
cd ~/bri610-tutor

# Add pipeline logs/reports
git add -A
git diff --cached --stat

git commit -m "feat: v0.3.1 — 1304 textbook pages embedded, E2E validated

Embedding complete:
- 199 slides: image embedding (Nemotron VL 2048-dim)
- 1304 textbook pages: text embedding (all) + image embedding (visual)
- Dual retrieval: max(text_sim, img_sim) per page
- Pipeline stage-gate: Parse→QC→Embed→Verify all passed

E2E tests passed:
- Health, Lectures, Hybrid Search, Chat (EN+KR), Quiz
- Agent routing: tutor, derive, quiz, exam, summary
- PostgreSQL pgvector + tsvector FTS + RRF fusion"

git push origin main
git tag -a v0.3.1 -m "v0.3.1: Full embedding + E2E validated"
git push origin v0.3.1

# Optional: DB dump as release asset
pg_dump -U tutor bri610 --no-owner --no-privileges | gzip > /tmp/bri610_v031.sql.gz
echo "DB dump ready: /tmp/bri610_v031.sql.gz (upload to GitHub release manually)"
```

## Error Recovery

| Symptom | Fix |
|---------|-----|
| `connection refused` on psql | `sudo systemctl start postgresql` |
| `Rate limited` during embed | Automatic retry. If pipeline exits, re-run same command |
| `No module named X` | `pip install psycopg2-binary pgvector pymupdf requests httpx fastapi uvicorn` |
| `text_embedding IS NULL` after run | Check `logs/pipeline_*.log`, re-run `embed --key ... --batch 50` |
| Frontend can't reach backend | Ensure uvicorn on :8000, check `frontend/vite.config.js` proxy |
| Git push rejected | `git pull --rebase origin main` then push again |
| `OPENROUTER_API_KEY` not set | Ask user once, export it, then proceed |

## Success Criteria (Checklist)
- [ ] `pipeline_harness.py status`: 1304/1304 text_emb, ~450/~450 img_emb
- [ ] `curl /api/health`: embedded > 1400, backend=postgresql+pgvector
- [ ] `curl /api/search`: returns mixed slide + textbook results with scores
- [ ] `curl /api/chat`: returns agent-routed answers with LaTeX + sources
- [ ] Frontend loads at :3000, all 6 tabs functional
- [ ] `git tag v0.3.1` pushed to GitHub

## Architecture Reference (AGENT.md)
```
Pipeline:  Parse →[≥90%]→ QC →[≥95%]→ Embed(loop) →[≥98%]→ Verify →[≥95%]→ Report
Backend:   FastAPI → HybridRetriever(pgvector cosine + tsvector FTS + RRF α=0.6)
Agents:    Router → Tutor|Derive|Quiz|Exam|Summary (Qwen3.6 via OpenRouter)
Embedding: Nemotron VL 2048-dim — text(all pages) + image(visual pages) dual strategy
DB:        PostgreSQL bri610 — slides(199), textbook_pages(1721), qc_log
```
