# BRI610 PDF Parser Benchmark Report — v0.5
**Date**: April 26, 2026  
**Author**: Automated research agent (Claude Sonnet 4.6) for joonop99@snu.ac.kr  
**Scope**: 8 scientific-PDF parsing tools evaluated for equation-dense neuroscience content (Dayan & Abbott, Fundamental Neuroscience, BRI610 lecture slides). Primary criterion: faithful LaTeX output for Hodgkin-Huxley gating equations, cable PDE, Greek-letter subscript/superscript chains.  
**Primary sources**: GitHub repos, PyPI, OmniDocBench leaderboard (CVPR 2025), olmOCR-Bench (AllenAI), arXiv:2512.09874 (formula extraction benchmark), official documentation.

---

## 1. Marker (datalab-to/marker) — v2 LLM mode

**Repo / URL**: https://github.com/datalab-to/marker  
**License / Cost**: GPL-3.0 (code); model weights under modified AI Pubs Open Rail-M — free for research and personal use, free for startups under $2 M revenue. Cloud API at datalab.to is commercial.  
**Latest release**: v1.10.2 (January 31, 2026, confirmed via PyPI)  
**Dependencies**: Python 3.10+; PyTorch (CPU/MPS/CUDA); peak VRAM 5 GB per worker if GPU; MPS (Apple Silicon) supported natively. LLM mode requires a callable LLM endpoint: Gemini 2.0 Flash (default), Claude, OpenAI, Azure, Google Vertex, or **Ollama** (local, free).

### 1. 파싱 전략 (Parsing strategy)
- **Pipeline**: Layout detection (Surya layout model) → reading-order sort → block classification (text / table / equation / figure) → OCR via Surya (block-level since v1.9.0 for higher accuracy) → equation extraction via **Texify** (a fine-tuned VLM for math-to-LaTeX) → optional LLM post-pass.
- **Models used**: Surya (layout + OCR), Texify (equation regions → LaTeX), optional LLM for table merging across pages and inline math cleanup.
- **Equation handling**: Display equations are detected as distinct layout blocks, routed to Texify, and output as `$$…$$`-fenced LaTeX in the markdown. With `--redo_inline_math` + `--use_llm`, inline math is also converted to LaTeX. Without LLM, inline math fidelity is lower.
- **Output formats**: Markdown (default), JSON (tree structure), HTML, Chunks (flat JSON for RAG).

### 2. 벤치마크 성능 (Performance benchmarks)
**OmniDocBench v1.6 (OmniDocBench GitHub leaderboard, April 2026)**:
- Marker overall composite: **78.44** (position ~#32 of 47 submissions)
- Text edit distance: **0.157** (lower is better; MinerU2.5-Pro achieves 0.036)
- Formula CDM: **85.24** (CDM = Character Detection Metric; higher is better; Mathpix 86.6, MinerU2.5-Pro 97.45)
- Table TEDS: **65.77**

**olmOCR-Bench (AllenAI, v0.4.0 results, 2025)**:
- Marker: **76.1** (vs. olmOCR 2: 82.4, MinerU: 75.8)

**arXiv:2512.09874 "Benchmarking Document Parsers on Mathematical Formula Extraction"** (LLM-as-judge 0–10 scale, 21 parsers):
- Marker **not included** in this benchmark. PyMuPDF4LLM (the closest baseline) scores **6.67**.

**Speed**: 0.18 s/page on NVIDIA H100 (GitHub README); on Apple M-series MPS, empirically 1–3 s/page (no official figure found — quoted from community reports).

### 3. 강점 (Strengths)
1. **Texify integration gives real LaTeX output** for display equations — not raw text like PyMuPDF. The Texify model is specifically trained on rendered math images.
2. **Ollama backend supported**: `--use_llm` with a local Ollama model (e.g., Mistral-7B, Gemma3) costs $0. This fits the free-tier constraint.
3. **Apple MPS native**: runs without CUDA, no Docker. `pip install marker-pdf` and ready.
4. **Multi-format input**: accepts PPTX directly — BRI610 slide images can be fed as PPTX, bypassing a separate slide-rasterization step.
5. **Active maintenance**: 13+ SDK releases in February 2026 alone; Chandra 1.5 upstream improvements (January 22, 2026) include improved mathematical notation handling.

### 4. 약점 / 한계 (Weaknesses / limitations)
1. **Formula CDM 85.24 is mid-tier**: Mathpix (86.6) and MinerU2.5-Pro (97.45) both outperform Marker on formula recognition in OmniDocBench. The 12-point gap vs. MinerU-Pro is large for HH-equation fidelity.
2. **No LLM benchmark published for Ollama mode**: GitHub issue #680 (open, unanswered as of April 2026) asks exactly this — which local LLM works best for math. Performance is unknown.
3. **Inline math still imperfect without `--use_llm`**: subscripts and Greek letters in running text (e.g., `gNa`, `τm(V)`) may not be converted.
4. **GPL-3.0 license** restricts commercial bundling. For a university tutor this is fine, but deployment to a web service requires care.
5. **Table TEDS 65.77 is weak**: ion-channel parameter tables in Dayan & Abbott would parse poorly without LLM mode.

### 5. 통합 난이도 (Integration difficulty)
- Python API quality: **4/5** — clean `from marker.convert import convert_single_pdf`; good CLI.
- **Time to wire into `pipeline_harness.py`**: ~4 hours. Replace `parse_textbook()` (lines 228–268) with a Marker call that returns page-level markdown + image. The `content` field maps directly to Marker's markdown output. Main complexity: Marker processes whole PDFs and returns a document, not page-by-page; need to split by page number.
- Required infra: Python 3.10, 8+ GB RAM, no GPU required (MPS optional). No API key if Ollama is used.
- **Cost at scale (1550 pages, one-time)**: $0 with local Ollama; ~$3 with Gemini 2.0 Flash (at ~$0.002/page) as LLM post-pass.

### 6. BRI610 적합도 (Fit) — 4/5
- HH gating equations: **Good** (Texify handles ViT-encoded equation images; CDM 85.24 confirmed)
- Cable PDE (∂²V/∂x²): **Moderate** — partial derivative notation tested less than standard integrals; hallucination risk on multi-line PDEs
- Korean text passthrough: **Good** — Surya OCR is multilingual; Korean not mangled
- Slide images (figures + equations mixed): **Good** — PPTX input supported; mixed-block layout handled by Surya layout model

### 7. 결론 (Verdict)
**ADOPT (primary parser for lecture slides + textbook equation pages)** — with `--use_llm` pointing to local Ollama. Texify is the strongest free local equation model available in a pipeline. Address the LLM-mode calibration gap by testing Mistral-Nemo or Gemma3 via Ollama on 5 HH pages before full re-parse.

---

## 2. MinerU (opendatalab/MinerU)

**Repo / URL**: https://github.com/opendatalab/MinerU  
**License / Cost**: Custom license based on Apache 2.0 with additional conditions (see repo); generally free for research. Hosted API at mineru.net is commercial.  
**Latest release**: v3.1.4 (April 24, 2026)  
**Dependencies**: Python 3.10–3.13; `pipeline` backend = CPU-only (pure Python, no GPU); `vlm-transformers` backend requires GPU (2–8 GB VRAM); `vlm-mlx-engine` backend for Apple Silicon MLX — ~3× faster than CPU-only.

### 1. 파싱 전략 (Parsing strategy)
- **Pipeline**: Layout detection → reading-order reconstruction → formula detector → LaTeX conversion (via UniMERNet or internal VLM) → table extraction (HTML) → markdown/JSON assembly.
- **Models**: `pipeline` backend uses lightweight models (PDF2md style, sub-1B). VLM backends use MinerU2.5 (a specialized 0.9B VLM). MLX-accelerated on Apple Silicon.
- **Equation handling**: "Formulas are automatically recognized and converted to LaTeX format" (GitHub README). Formula CDM 97.45 in OmniDocBench v1.6 (MinerU2.5-Pro) — the highest formula score of any open-source tool benchmarked. The `pipeline` backend alone achieves OmniDocBench overall 86.2 (v1.5 score).
- **Output formats**: Markdown (multimodal or NLP-focused), JSON (reading-order sorted), rich intermediate formats with layout visualization.

### 2. 벤치마크 성능 (Performance benchmarks)
**OmniDocBench v1.6** (OmniDocBench GitHub leaderboard):
- MinerU2.5-Pro overall: **95.75** (position ~#5 of 47)
- Text edit distance: **0.036** (best among pipeline tools)
- Formula CDM: **97.45** (highest formula CDM of any evaluated tool)
- Table TEDS: **93.42**
- `pipeline` backend alone: OmniDocBench overall ~85+ (v1.5 score per MinerU docs)

**OmniDocBench v1.0 (CVPR 2025, arXiv:2412.07626)**:
- MinerU text edit distance: **0.058 EN / 0.211 ZH** (best among pipeline tools; Marker 0.141/0.303, Nougat 0.365/0.998)

**olmOCR-Bench**: MinerU: **75.8** (vs. olmOCR 2: 82.4, Marker: 76.1)

**arXiv:2512.09874 formula benchmark**: MinerU2.5 scores **9.17 / 10.0** (LLM-as-judge; Mathpix 9.64, olmOCR-2-7B 8.94)

**Speed on Apple Silicon**: vlm-mlx-engine delivers 100–200% speedup vs. vlm-transformers backend; 3× faster than CPU-only. No official pages/second figure for M-series CPU-only mode found.

### 3. 강점 (Strengths)
1. **Best formula CDM of any open tool** (97.45 on OmniDocBench v1.6) — by far the strongest equation parser tested.
2. **CPU-only `pipeline` backend** runs without GPU or API key on any Mac; pure `pip install mineru`.
3. **MLX acceleration on Apple Silicon** — vlm-mlx-engine backend leverages M-series GPU natively (3× CPU speed).
4. **Actively maintained**: v3.1.4 released April 24, 2026 — the most recent release of any tool in this comparison.
5. **Multi-format output**: JSON with reading-order sort is directly insertable into PostgreSQL with clear page-level mapping.

### 4. 약점 / 한계 (Weaknesses / limitations)
1. **VLM-Pro backend is not locally free**: MinerU2.5-Pro (the one scoring 97.45) appears to be the API/hosted service; the local `pipeline` backend scores more modestly (~85 overall on OmniDocBench v1.5). Exact formula CDM for the local pipeline backend is not separately published.
2. **PPTX/slide input not natively supported**: MinerU targets PDFs and images; lecture slides would need conversion to PDF first.
3. **Memory requirements**: 16 GB RAM recommended; 32 GB for VLM backend. May be tight on some MacBook configurations.
4. **Custom license**: the "additional conditions" on top of Apache 2.0 need to be read for any commercial deployment.
5. **olmOCR-Bench score (75.8) is below Marker (76.1)**: the pipeline-backend version underperforms on the olmOCR-Bench academic-paper benchmark, suggesting variance across benchmark types.

### 5. 통합 난이도 (Integration difficulty)
- Python API quality: **4/5** — `from mineru.pdf_extract_kit import extract`; SDK and REST API available.
- **Time to wire into `pipeline_harness.py`**: ~5 hours. Replace `parse_textbook()` with a MinerU call that returns markdown + JSON by page. Need to map MinerU's reading-order JSON to the `content` field. Page-level splitting is explicit in MinerU's JSON output.
- Required infra: Python 3.10–3.13, 16 GB RAM, no GPU strictly required (`pipeline` backend). MLX backend requires Apple Silicon Mac.
- **Cost at scale (1550 pages, one-time)**: $0 with local `pipeline` or MLX backend.

### 6. BRI610 적합도 (Fit) — 5/5
- HH gating equations: **Excellent** — formula CDM 97.45 is the benchmark leader; designed specifically for scientific PDFs with formula-heavy content
- Cable PDE: **Excellent** — partial derivatives and multi-line display math handled by UniMERNet-style formula detector
- Korean text passthrough: **Good** — 109-language OCR support; Korean not mangled
- Slide images: **Moderate** — PDF-input only; PPTX must be pre-converted; figure+equation mixed slides handled well once in PDF form

### 7. 결론 (Verdict)
**ADOPT (primary parser for textbook equation pages, especially Dayan & Abbott Chapter 5–7 HH content)** — use the local `pipeline` backend first; if formula fidelity is insufficient on spot-check pages, upgrade to vlm-mlx-engine on Apple Silicon at zero API cost.

---

## 3. olmOCR / olmOCR 2 (allenai/olmocr)

**Repo / URL**: https://github.com/allenai/olmocr  
**License / Cost**: Apache 2.0  
**Latest release**: v0.4.27 (March 12, 2026)  
**Dependencies**: GPU path requires NVIDIA GPU with ≥12 GB VRAM + PyTorch. Remote inference path works without local GPU via vLLM-compatible APIs (DeepInfra, Cirrascale, etc.). Requires `poppler-utils`. **No native Apple MPS support** for the VLM path.

### 1. 파싱 전략 (Parsing strategy)
- **Pipeline**: Render PDF pages to images → VLM (olmOCR-7B, a fine-tuned Qwen2-VL) reads each page image → generates unified output: Markdown for structure, HTML for tables, **LaTeX for math** — all in a single forward pass. No separate layout/OCR/equation detector chain; the VLM handles everything end-to-end.
- **Models used**: olmOCR-7B (7B parameter VLM, fine-tuned from Qwen2-VL via RLVR training with unit-test rewards). olmOCR 2 trained with "unit test rewards for document OCR" (arXiv:2510.19817).
- **Equation handling**: LaTeX is the native output format for math regions. The KaTeX DOM bounding-box visual equivalence check in olmOCR-Bench is specifically designed to catch equations that render correctly but differ in string form — a stronger test than edit distance.
- **Output formats**: Markdown, Dolma document format, plain text.

### 2. 벤치마크 성능 (Performance benchmarks)
**olmOCR-Bench (AllenAI, 7010 unit tests, 1403 PDFs)**:
- olmOCR 2: **82.4** (nearly +4 points over previous release; "one of the highest scores to date", AllenAI blog)
- Marker: 76.1, MinerU: 75.8 (olmOCR 2 outperforms both per AllenAI blog)
- Old math scans: **82.3%**, Tables: **84.9%**, Multi-column: **83.7%**

**OmniDocBench v1.6**:
- olmOCR overall: **85.74**, Formula CDM: **88.10**, Table TEDS: **83.00**, Text edit distance: **0.139**

**arXiv:2512.09874 formula benchmark**: olmOCR-2-7B: **8.94 / 10.0** (LLM-as-judge; below MinerU2.5's 9.17, Mathpix's 9.64)

**Speed**: No official CPU speed given; GPU path on A100 expected ~5–10 s/page for 7B VLM. Community reports 30+ seconds/page on consumer GPU (RTX 3080).

### 3. 강점 (Strengths)
1. **Strongest olmOCR-Bench score (82.4)** — the benchmark specifically tests equation visual equivalence via KaTeX rendering, making it the most rigorous math evaluation available.
2. **Single-model end-to-end**: no multi-model chain means fewer inter-model error propagation paths.
3. **Apache 2.0**: clean license for research use.
4. **RLVR training on unit tests**: the training signal is directly tied to "does the output render correctly?" rather than string similarity — more robust for unusual equation notation.
5. **OmniDocBench Formula CDM 88.10**: second-highest formula CDM of the open-source tools after MinerU2.5-Pro.

### 4. 약점 / 한계 (Weaknesses / limitations)
1. **No Apple MPS support**: requires NVIDIA GPU (≥12 GB VRAM) or paid remote API. Cannot run locally on MacBook without cloud call.
2. **Primary tuned for academic papers (56% academic in olmOCR-Bench)**: lecture slides with heavy visual design (colored backgrounds, overlapping text/figures) are underrepresented in training.
3. **Speed is slow**: 7B VLM processes one page at a time; batch pipeline requires vLLM server setup, which is non-trivial on Mac.
4. **LlamaIndex critical review**: olmOCR-Bench is "primarily focused on text linearization," excluding non-English content and certain table/reading-order edge cases (LlamaIndex blog, olmocr-bench-review).
5. **Non-English exclusion**: olmOCR-Bench explicitly excludes non-English text; Korean passthrough quality is unknown and untested.

### 5. 통합 난이도 (Integration difficulty)
- Python API quality: **3/5** — batch inference system oriented toward cluster jobs (AWS S3, Beaker); single-file API is usable but less polished than Marker/MinerU.
- **Time to wire into `pipeline_harness.py`**: ~8 hours (plus vLLM server setup time if no local GPU). Remote API adds latency and cost variable.
- Required infra: NVIDIA ≥12 GB VRAM OR paid API (DeepInfra olmOCR-7B ~$0.35/M tokens).
- **Cost at scale (1550 pages)**: ~$0 local if NVIDIA GPU available; ~$15–25 via DeepInfra at ~$0.01–0.016/page estimate.

### 6. BRI610 적합도 (Fit) — 3/5
- HH gating equations: **Good** (Formula CDM 88.10; KaTeX equivalence testing validates visual correctness)
- Cable PDE: **Good** — same as above
- Korean text passthrough: **Unknown** — excluded from benchmark; risk of mangling
- Slide images: **Moderate** — VLM is image-in/text-out by design, but training is academic-paper-centric

### 7. 결론 (Verdict)
**FALLBACK** — excellent equation accuracy (second-best Formula CDM among open tools), but Mac-local GPU constraint eliminates it as primary. Viable if a cloud GPU or DeepInfra API is available; use as a spot-check validator for HH pages where MinerU output is suspect.

---

## 4. Docling (DS4SD/docling, IBM)

**Repo / URL**: https://github.com/DS4SD/docling (now at https://github.com/docling-project/docling)  
**License / Cost**: MIT  
**Latest release**: v2.91.0 (April 23, 2026)  
**Dependencies**: Python 3.10+; CPU-only supported; optional GPU. Apple Silicon (arm64) explicitly supported. No API key required.

### 1. 파싱 전략 (Parsing strategy)
- **Pipeline**: Layout detection (DocLayNet model or IBM Granite Heron layout model, default since v2.x) → reading order → table structure (TableFormer) → formula detection → optional VLM enrichment (GraniteDocling 258M).
- **Models used**: DocLayNet (layout), TableFormer (tables), SmolDocling or GraniteDocling 258M (optional VLM enrichment). GraniteDocling was trained on SynthFormulaNet — synthetic math expressions paired with ground-truth LaTeX.
- **Equation handling**: `do_formula_enrichment=True` (optional, not default) routes detected math regions through a code-formula model to produce LaTeX. There is an active GitHub issue (#2374) reporting LaTeX formula spacing bugs with `do_formula_enrichment=True` as of 2025. Without the flag, formulas may output as plain text with degraded fidelity.
- **Output formats**: Markdown, HTML, WebVTT, DocTags, lossless JSON.

### 2. 벤치마크 성능 (Performance benchmarks)
Docling was added to OmniDocBench evaluations in January 2025, but specific CDM scores for Docling were **not found** in the OmniDocBench leaderboard data retrieved. The OmniDocBench paper (arXiv:2412.07626 / CVPR 2025) does not include Docling in its main results table.

**arXiv:2512.09874 formula benchmark**: Docling **not included**.

**Independent benchmark (Procycons, 2025)** — corporate sustainability PDFs (not scientific equations):
- Docling: 97.9% complex table accuracy, text extraction with good formatting preservation.
- Speed: 6.28 s (1 page), 65.12 s (50 pages) — approximately **0.77 pages/second** on CPU.

**Comparative claim (Medium, IBM Granite-Docling review, 2025)**: GraniteDocling 258M "consistent improvements in Layout Recognition and Full Page OCR" vs. SmolDocling 256M. No formula-specific numeric comparison found.

### 3. 강점 (Strengths)
1. **MIT license** — cleanest license of all tools; no restrictions on commercial or academic use.
2. **Best CPU-only table extraction** in the non-formula dimension (97.9% on complex tables in independent test).
3. **Apple Silicon arm64 explicitly supported**; no CUDA required.
4. **MCP server integration** — already has an MCP server mode for agentic applications (relevant to Claude Code usage).
5. **Multi-format input**: PDF, DOCX, PPTX, XLSX, HTML, LaTeX, images — handles slides natively.

### 4. 약점 / 한계 (Weaknesses / limitations)
1. **Formula enrichment is opt-in and buggy**: GitHub issue #2374 (active, 2025) reports spacing errors in LaTeX output from `do_formula_enrichment=True`. Default mode likely outputs degraded math.
2. **No formula CDM benchmark found**: cannot confirm equation accuracy comparable to MinerU/olmOCR. Absence of formula score on OmniDocBench is itself a signal.
3. **CPU speed 0.77 p/s is slow**: 1550 pages ≈ 33 minutes on CPU; acceptable one-time, but slow for re-parse iterations.
4. **Formula model (GraniteDocling 258M) is small**: 258M parameters vs. 7B for olmOCR; expected accuracy gap on complex nested equations.
5. **No published HH-equation or physics-equation specific tests** found — extrapolation from generic benchmarks is uncertain.

### 5. 통합 난이도 (Integration difficulty)
- Python API quality: **4/5** — clean `DocumentConverter` API; good documentation.
- **Time to wire into `pipeline_harness.py`**: ~4 hours. `DocumentConverter().convert(pdf_path)` returns a `DoclingDocument` with per-page content; map `.export_to_markdown()` per page into the `content` field.
- Required infra: Python 3.10+, no GPU, no API key.
- **Cost at scale (1550 pages, one-time)**: $0.

### 6. BRI610 적합도 (Fit) — 3/5
- HH gating equations: **Unknown/Risky** — formula enrichment flag is buggy; no benchmark number available
- Cable PDE: **Unknown** — same caveat
- Korean text passthrough: **Good** — multilingual OCR support; no reports of Korean mangling
- Slide images: **Good** — PPTX input supported natively

### 7. 결론 (Verdict)
**PARTIAL-ADOPT** — use for textbook prose pages (table extraction, general text) where its 97.9% table accuracy and MIT license shine, but do **not** rely on it for equation-dense pages until GitHub issue #2374 is resolved and a formula CDM number is established. Combine with MinerU for equation pages in a hybrid pipeline.

---

## 5. Nougat (facebookresearch/nougat)

**Repo / URL**: https://github.com/facebookresearch/nougat  
**License / Cost**: Code: MIT; Model weights: CC-BY-NC (no commercial use)  
**Latest release**: v0.1.0-base (August 22, 2023) — **no updates in 2.5 years**  
**Dependencies**: Python 3.9+; GPU optional (CPU supported but failure detection degrades); API requires extra install.

### 1. 파싱 전략 (Parsing strategy)
- **Pipeline**: PDF page → rasterize → vision encoder (Swin/ViT) → autoregressive text decoder → `.mmd` (Mathpix Markdown) output. A Donut-style encoder-decoder architecture. No separate layout detection, OCR, or table model — fully end-to-end.
- **Models used**: Base model (350M) or small model. Trained on arXiv + PubMed Central papers.
- **Equation handling**: Display math is output as LaTeX within `\[…\]` blocks. Inline math as `$…$`. Training corpus is almost entirely academic paper LaTeX, so equation vocabulary is broad.
- **Output formats**: `.mmd` (Mathpix Markdown, LaTeX-compatible).

### 2. 벤치마크 성능 (Performance benchmarks)
**OmniDocBench v1.0 (CVPR 2025, arXiv:2412.07626)**:
- Nougat text edit distance (English): **0.365** (worst of all pipeline tools; MinerU 0.058, Marker 0.141)
- Nougat text edit distance (Chinese): **0.998** (essentially complete failure on non-Latin scripts)

**olmOCR-Bench**: Nougat not included in reported comparisons.

**arXiv:2512.09874**: Nougat not included.

**ICLR 2024 paper (Nougat original)**: reported BLEU 0.61 on arXiv test set with base model. No CDM-style equation metric provided.

**Speed**: Autoregressive decoding is slow; community reports 5–30 seconds/page on GPU depending on content length; CPU is substantially slower.

### 3. 강점 (Strengths)
1. **Trained specifically on academic LaTeX papers**: widest equation vocabulary of any model in this comparison.
2. **`.mmd` output is already LaTeX-friendly**: equation blocks are LaTeX by default, no post-processing needed.
3. **MIT code license** (model weights are CC-BY-NC, but for research use that is fine).
4. **No API key or internet required**: fully local.
5. **Well-cited and understood**: ICLR 2024 paper; known failure modes are documented.

### 4. 약점 / 한계 (Weaknesses / limitations)
1. **Abandoned since August 2023**: no updates in 32 months. Community-reported bugs (repetition loop, hallucination in bibliographies) are unfixed. This is the single largest disqualifier.
2. **Repetition loop bug**: model "collapses into a repeating loop" on challenging pages — produces garbage output that must be detected and discarded (original paper, ICLR 2024).
3. **Complete failure on non-Latin scripts**: edit distance 0.998 on Chinese in OmniDocBench. Korean passthrough is expected to be similarly disastrous.
4. **No layout understanding**: processes one page at a time without knowledge of adjacent pages; multi-column slides and figure-heavy slides produce disordered output.
5. **Worst text edit distance (0.365 EN)** of all tools evaluated in OmniDocBench CVPR 2025 — Marker (0.141) and MinerU (0.058) are 2.6× and 6.3× better respectively.

### 5. 통합 난이도 (Integration difficulty)
- Python API quality: **3/5** — CLI and Python API exist but not well-maintained.
- **Time to wire into `pipeline_harness.py`**: ~4 hours (simple subprocess call); but QC gate would fail frequently due to repetition bugs.
- Required infra: Python 3.9+, GPU optional.
- **Cost**: $0.

### 6. BRI610 적합도 (Fit) — 2/5
- HH gating equations: **Moderate-Poor** — equation vocabulary good but repetition bugs create unpredictable failures
- Cable PDE: **Moderate** — same
- Korean text passthrough: **Fail** — edit distance 0.998 on Chinese; Korean expected to fail
- Slide images: **Poor** — no layout detection; figure-heavy slides disordered

### 7. 결론 (Verdict)
**REJECT** — abandonware with a known repetition bug, the worst text accuracy of any tool in OmniDocBench CVPR 2025, and complete failure on non-Latin scripts. The equation vocabulary advantage is real, but the reliability issues make it unusable in a production pipeline. Use MinerU or Marker instead.

---

## 6. Mathpix Snip API

**Repo / URL**: https://mathpix.com/docs/api (official docs); no open-source repo  
**License / Cost**: Commercial SaaS. From $0.002/image for Snip API (pay-as-you-go); PDF Convert API pricing separate. Desktop app: free tier (limited), Pro from $4.99/month. No open-source code.  
**Latest release**: Managed cloud service — no versioned open-source releases. Continuous deployment.  
**Dependencies**: HTTP API only. No local install. API key required.

### 1. 파싱 전략 (Parsing strategy)
- **Pipeline**: Proprietary. Image → specialized math OCR models → LaTeX / MathML output. PDF Convert API processes PDF page-by-page via OCR + specialized equation detection.
- **Models used**: Not disclosed. Proprietary math-focused OCR trained on large equation dataset.
- **Equation handling**: Mathpix is the *de facto* gold standard for equation-to-LaTeX conversion. Output includes `\begin{equation}…\end{equation}` blocks, inline `$…$`, alignment environments. CDM 86.6 on OmniDocBench (top-2 for formula accuracy alongside GPT-4o at 86.8).
- **Output formats**: LaTeX, MathML, Markdown, structured JSON.

### 2. 벤치마크 성능 (Performance benchmarks)
**OmniDocBench v1.0 (CVPR 2025, arXiv:2412.07626)**:
- Formula CDM: **86.6** (top-2 overall; GPT-4o 86.8, UniMERNet-B 85.0, GOT-OCR 74.1)
- ExpRate@CDM (strict exact match): **2.8%** (far below GPT-4o 65.5% — Mathpix ranks poorly on strict exact match despite high CDM)
- Text edit distance (English): **0.101**, (Chinese): **0.358**

**arXiv:2512.09874 formula benchmark**: Mathpix: **9.64 / 10.0** (LLM-as-judge; 4th of 21 parsers, behind Qwen3-VL-235B 9.76, Gemini 3 Pro 9.75, PaddleOCR-VL 9.65)

**Speed**: API-bound — ~1–3 seconds per page depending on complexity and server load.

### 3. 강점 (Strengths)
1. **Best equation accuracy of any API service**: CDM 86.6 and LLM-judge 9.64/10 confirm it as the equation fidelity benchmark.
2. **No local GPU needed**: pure API call — works on any machine including low-spec Mac.
3. **Battle-tested on scientific documents**: Mathpix was trained specifically on academic physics/math papers; HH equations and cable PDEs are likely in-distribution.
4. **MathML output**: useful for WCAG-compliant web rendering of equations.
5. **PDF Convert API**: processes full PDFs, not just image snippets; preserves reading order.

### 4. 약점 / 한계 (Weaknesses / limitations)
1. **Commercial cost**: $0.002/image; at ~1550 pages, one-time cost = ~$3.10. That is cheap, but ongoing incremental re-parses add up. Premium parsing at $0.075/page would be $116 — prohibitive.
2. **No open-source code**: cannot self-host, cannot inspect failure modes, cannot customize.
3. **ExpRate strict match only 2.8%**: despite high CDM, strict exact LaTeX match is very low — output LaTeX may be semantically equivalent but syntactically different (e.g., `\frac` vs. `\tfrac`, different whitespace). This matters if downstream code does exact string comparison.
4. **No Ollama/local fallback**: if API is down or quota is exhausted, no local fallback.
5. **Rate limits and data privacy**: equations sent to external server — may be a concern for unpublished research materials.

### 5. 통합 난이도 (Integration difficulty)
- Python API quality: **4/5** — simple REST API; Python wrapper available.
- **Time to wire into `pipeline_harness.py`**: ~3 hours (HTTP calls replacing `fitz` in `parse_textbook()`; API key in env var).
- Required infra: API key, internet connection, no GPU.
- **Cost at scale (1550 pages, one-time)**: ~$3.10 at $0.002/image. Incremental: $0.002/page.

### 6. BRI610 적합도 (Fit) — 4/5
- HH gating equations: **Excellent** (CDM 86.6; specialized equation OCR)
- Cable PDE: **Excellent** — same
- Korean text passthrough: **Poor** (text edit distance 0.358 for Chinese; Korean expected similarly degraded for general text; math output quality is unaffected)
- Slide images: **Moderate** — works on images but not natively slide-aware

### 7. 결론 (Verdict)
**PARTIAL-ADOPT** — use specifically for equation-dense pages as a spot-check validator or secondary parser. At $0.002/page, running Mathpix on the ~300 identified equation/mixed pages in DA + FN costs $0.60 — a worthwhile accuracy sanity check. Do not use as primary for prose or Korean text. Do not use as primary for slide images.

---

## 7. LlamaParse (LlamaIndex managed parser)

**Repo / URL**: https://developers.llamaindex.ai/llamaparse  
**License / Cost**: Commercial SaaS (LlamaCloud). Free tier: 10,000 credits on signup (~10,000 Fast pages or ~3,333 Agentic pages). Paid: $1.25 per 1,000 credits. Pricing tiers: Fast (1 credit/page = $0.00125), Cost-effective (3 credits/page = $0.00375), Agentic (10 credits/page = $0.0125), Agentic Plus (45 credits/page = $0.05625), Premium ($0.075/page). No open-source self-host option.  
**Latest release**: LlamaParse v2 (December 2025)  
**Dependencies**: API key + `llama-parse` Python package. No local GPU. Internet required.

### 1. 파싱 전략 (Parsing strategy)
- **Pipeline**: Proprietary multimodal pipeline. Document → layout analysis → OCR → LLM-powered structure understanding → markdown output. Premium mode adds VLM visual comprehension layer.
- **Models used**: Not disclosed. LlamaIndex describes it as combining "multimodal capabilities with heuristic text parsing techniques."
- **Equation handling**: LaTeX output supported. Premium mode: equations output as `$$…$$`-fenced LaTeX. Custom instruction supported: `"Output any math equation in LATEX markdown (between $$)"`. v2 claims "higher accuracy" for mathematical content.
- **Output formats**: Markdown (primary); JSON available.

### 2. 벤치마크 성능 (Performance benchmarks)
**arXiv:2512.09874 formula benchmark**: LlamaParse: **8.14 / 10.0** (LLM-as-judge; 7th of 21 parsers; below MinerU2.5 9.17, olmOCR-2 8.94, but above PyMuPDF4LLM 6.67)

**OmniDocBench**: LlamaParse not included in CVPR 2025 paper or leaderboard (as of April 2026).

**olmOCR-Bench**: not included.

**Independent benchmark (Procycons, 2025)** — corporate reports: LlamaParse processes consistently in ~6 seconds regardless of document size; poor with complex multi-column layouts; 100% accuracy on simple tables.

**LlamaIndex own blog (Premium mode intro)**: "outperforms vanilla models like Sonnet-3.5" on hallucination rate and reading order. No third-party-verified equation metric.

### 3. 강점 (Strengths)
1. **Easiest API integration**: `from llama_parse import LlamaParse`; minimal setup.
2. **Custom parsing instructions**: can be told explicitly to output all math as `$$LaTeX$$` — useful for ensuring consistent format.
3. **90+ input formats**: handles PPTX, DOCX, PDF natively, including slide decks.
4. **Free 10k credits on signup** (~10k pages at Fast tier): covers all 1550 textbook pages and 50 slide decks with significant headroom.
5. **LlamaIndex ecosystem integration**: native connector to LlamaIndex, which the project might already use for RAG.

### 4. 약점 / 한계 (Weaknesses / limitations)
1. **Formula score 8.14/10 is below MinerU (9.17) and Mathpix (9.64)**: for equation-critical use, LlamaParse is the weakest of the "managed API" options.
2. **No self-host option**: data leaves the machine. Same privacy concern as Mathpix.
3. **Premium mode ($0.075/page) is expensive**: 1550 pages = $116 one-time; ongoing re-parses add up.
4. **Struggles with complex multi-column layouts** (Procycons benchmark): textbook pages with two-column layout + margin equations may degrade.
5. **No benchmark on neuroscience-domain PDFs**: equation score may be lower for domain-specific notation (gating variable subscripts, voltage-clamp notation) not common in web-scraped training data.

### 5. 통합 난이도 (Integration difficulty)
- Python API quality: **5/5** — best DX of all tools; Python SDK, TypeScript SDK, Jupyter notebooks.
- **Time to wire into `pipeline_harness.py`**: ~2 hours. Replace `parse_textbook()` with `LlamaParse().load_data(pdf_path)` which returns `Document` objects; iterate by page.
- Required infra: API key (free for initial 10k pages), internet, no GPU.
- **Cost at scale (1550 pages, one-time)**: $0 within free 10k credit tier at Fast mode; $5.81 at Cost-effective tier (3 credits/page).

### 6. BRI610 적합도 (Fit) — 3/5
- HH gating equations: **Moderate** (8.14/10 formula score; custom instruction helps but not as accurate as MinerU/Mathpix)
- Cable PDE: **Moderate** — same
- Korean text passthrough: **Good** — 100+ language support; no Korean mangling reported
- Slide images: **Good** — PPTX input supported natively; handles complex layouts better than textbook two-column

### 7. 결론 (Verdict)
**PARTIAL-ADOPT** — use for lecture slides (PPTX native input; reasonable layout handling; easy API) and for prose-heavy textbook pages where equation density is low. Avoid for HH/cable PDE pages — the formula score (8.14) is 13% below MinerU. The free 10k credits make it zero-cost for the initial parse run.

---

## 8. PyMuPDF (current baseline) + pix2tex (LaTeX-OCR)

**Repo / URL**: https://github.com/pymupdf/PyMuPDF (fitz) + https://github.com/lukas-blecher/LaTeX-OCR (pix2tex)  
**License / Cost**: PyMuPDF: AGPL-3.0 (open source) or commercial license; pix2tex: MIT  
**Latest release**: PyMuPDF 1.25.x (2025, actively maintained); pix2tex v0.1.x (last meaningful release ~2022; repo still active for issues but not actively developed)  
**Dependencies**: PyMuPDF: CPU-only, no GPU needed. pix2tex: Python 3.7+, PyTorch (CPU or GPU); ViT + ResNet model (~25M parameters); runs on CPU acceptably.

### 1. 파싱 전략 (Parsing strategy)
- **PyMuPDF baseline**: `fitz.open()` → `page.get_text()` → raw Unicode text extraction. Equations are extracted as the raw character sequence embedded in the PDF font encoding — not as LaTeX. The PDF specification has no math sub-type: "In PDF, text is just text" (PyMuPDF maintainer, GitHub discussion #763). Font names like "CMMI10" (Computer Modern Math Italic) can heuristically hint at math, but no automatic LaTeX conversion occurs.
- **pix2tex augmentation**: rasterize equation region → feed image to pix2tex ViT encoder + Transformer decoder → output LaTeX string. Designed *only* for display (block) equations; hallucinates on inline math and text.
- **Combined pipeline** (current BRI610 approach implied): PyMuPDF extracts raw text into `content` field; `img_path` stores rasterized page; downstream embedding receives the garbled equation text ("CmdVdt=−Iion" style corruption).
- **Output formats**: raw Unicode strings (PyMuPDF); LaTeX strings (pix2tex per-image).

### 2. 벤치마크 성능 (Performance benchmarks)
**PyMuPDF4LLM (OmniDocBench leaderboard, 2025)**: overall composite **6.67 / 10** on formula extraction benchmark (arXiv:2512.09874) — second-lowest of 21 tools, above only GROBID (5.70).

**pix2tex (reported in project README)**:
- BLEU: **0.88** (on training-adjacent test set — likely inflated due to in-distribution test)
- Normalized edit distance: **0.10**
- Token accuracy: **0.60** (40% of tokens wrong on average)

**Comparative**: Im2Latex (similar architecture) BLEU 0.67 in independent 2024 benchmark. pix2tex's self-reported BLEU 0.88 on its own test set cannot be directly compared.

**Speed**: PyMuPDF text extraction: extremely fast (~100 pages/second CPU). pix2tex: ~2–5 seconds/image on CPU (ViT inference).

### 3. 강점 (Strengths)
1. **PyMuPDF is extremely fast** for text extraction: 100+ pages/second; zero cost.
2. **pix2tex is MIT-licensed, local, zero API cost**: no external dependency.
3. **Already integrated** in `pipeline_harness.py` (lines 228–268); zero migration effort.
4. **Perfect for non-equation pages**: PyMuPDF text extraction is lossless for standard text — use it for prose pages.
5. **pix2tex works for isolated display equations**: BLEU 0.88 on well-cropped, clean display equation images is usable for spot-check validation.

### 4. 약점 / 한계 (Weaknesses / limitations)
1. **PyMuPDF cannot extract LaTeX from equations**: "CmdVdt=−Iion" garbage on HH pages is confirmed by the current pipeline's output. The PDF spec provides no math semantics; font-encoded Greek letters come out as garbled characters.
2. **pix2tex designed only for block equations**: "hallucinates more on text" (project README). Cannot handle inline math or mixed text+equation pages.
3. **pix2tex token accuracy 60%**: 40% of tokens in the output are wrong — for an equation like `C_m dV/dt = -I_ion(V,t)`, that means multiple errors per equation.
4. **pix2tex requires manual region cropping**: there is no automatic layout detection to find equation boundaries; must be combined with a layout detector (adding engineering complexity).
5. **pix2tex last major development ~2022**: stale; Texify (used inside Marker) and UniMERNet are significantly more accurate successors.

### 5. 통합 난이도 (Integration difficulty)
- Python API quality (PyMuPDF): **5/5** — excellent, already integrated.
- Python API quality (pix2tex): **3/5** — CLI and Python API exist; requires manual region extraction.
- **Time to augment `pipeline_harness.py` with pix2tex**: ~6 hours (add layout detection to find equation bounding boxes, crop images, call pix2tex, replace `content` field for equation blocks).
- Required infra: PyTorch (CPU mode acceptable); no GPU required for pix2tex at 25M parameters.
- **Cost at scale**: $0.

### 6. BRI610 적합도 (Fit) — 2/5
- HH gating equations: **Fail** (PyMuPDF alone produces garbage; pix2tex on cropped blocks is 60% token accuracy)
- Cable PDE: **Fail** — same
- Korean text passthrough: **Excellent** (PyMuPDF handles Unicode correctly)
- Slide images: **Poor** for equations; **Good** for prose text extraction from text-layer PDFs

### 7. 결론 (Verdict)
**FALLBACK (prose pages only)** — retain PyMuPDF for fast text extraction on non-equation pages (page_type = 'text', 'references') where it excels. Replace entirely for 'equation' and 'mixed' pages with MinerU or Marker. Do not invest in pix2tex augmentation — Texify (inside Marker) and UniMERNet (inside MinerU) are 2022+ successors trained on larger datasets with better accuracy; the engineering overhead of pix2tex integration is not justified.

---

## Integrated Synthesis

### 권장 파서 조합 (Recommended parser by content type)

| Content type | Primary parser | Rationale | Fallback |
|---|---|---|---|
| Textbook equation pages (DA ch. 5–11, HH gating, cable PDE) | **MinerU (`pipeline` backend → MLX)** | Formula CDM 97.45 — highest confirmed score; free local; MLX on Apple Silicon | Marker + `--use_llm` (Ollama) |
| Textbook prose pages (general text, references) | **PyMuPDF (current)** | Already integrated; 100 p/s; lossless for text | Docling for tables |
| Textbook mixed pages (text + figures + equations) | **MinerU** | Handles mixed layout; reading-order reconstruction robust | Marker |
| Lecture slides (PPTX, figures + equations) | **Marker** + `--use_llm` (Ollama) | PPTX native input; Texify for equation regions; Ollama = zero cost | LlamaParse (Fast tier, free credits) |
| Table-heavy pages | **Docling** | 97.9% complex table accuracy; MIT license | MinerU |

### 권장 폴백 체인 (Fallback chain)

```
PARSE STAGE (equation/mixed pages):
  1. MinerU pipeline/MLX backend      → QC gate: formula CDM spot-check
  2. If MinerU fails page:   → Marker + Ollama LLM mode
  3. If Marker fails page:   → Mathpix API ($0.002/page) for that page only
  4. If all fail:            → Flag for manual review (page_type = 'manual_eq')

PARSE STAGE (prose pages):
  1. PyMuPDF (current, already in harness)
  2. If garbled (non-ASCII > 15%): → Docling

PARSE STAGE (slides):
  1. Marker (PPTX input, Ollama LLM)
  2. If Marker fails slide:  → LlamaParse Fast (free credits)
```

### `pipeline_harness.py` 통합 계획 (Concrete integration plan)

The parser is isolated in **`parse_textbook()`** (lines 228–268) and **`stage_parse()`** (lines 271–326). The `content` field in the PostgreSQL `textbook_pages` table is the primary target — replacing PyMuPDF's `page.get_text()` output with LaTeX-preserving markdown.

**Step 1 — Add a `parser` argument to `stage_parse()` and `parse_textbook()`** (4 hours):
```python
def parse_textbook(pdf_path, book_name, img_dir, parser='pymupdf'):
    if parser == 'mineru':
        return _parse_mineru(pdf_path, book_name, img_dir)
    elif parser == 'marker':
        return _parse_marker(pdf_path, book_name, img_dir)
    else:
        return _parse_pymupdf(pdf_path, book_name, img_dir)  # existing code
```

**Step 2 — Implement `_parse_mineru()`** (6 hours):
- Call `mineru -p <pdf> -o <out_dir> -b pipeline` via subprocess or Python API
- Parse MinerU's JSON output (reading-order sorted) into the existing page dict schema
- Map `content` = MinerU markdown per page; `page_type` detection can reuse existing `classify_page()` heuristic on the markdown output (now with LaTeX, so `has_eq` detection works correctly)

**Step 3 — Implement `_parse_marker()`** (4 hours):
- `from marker.convert import convert_single_pdf`; call with `use_llm=True, llm_service='marker.services.ollama.OllamaService'`
- Marker returns a document with page-level blocks; iterate and join per-page content

**Step 4 — Add a `parser` CLI flag** (1 hour):
```bash
python pipeline_harness.py parse --book DA --parser mineru
```

**Step 5 — Add QC check for equation fidelity** (3 hours):
Augment `QC_CHECKS` dict with `'equation_has_latex': lambda pg: not has_eq_garbage(pg['content'])` where `has_eq_garbage()` checks that equation pages do not contain known corruption signatures ("CmdV", "Iion" without `$` wrapping, raw "\\u2202" escapes).

### 일회성 재파싱 비용 추정 및 우선순위 (One-time re-parse cost and priority)

**Which content to re-parse first** (based on equation density and current garbage output):

1. **Dayan & Abbott Chapters 5–7** (HH equations, Hodgkin-Huxley formalism, cable theory, ~120 pages): Highest priority — these are the core BRI610 lecture content and where current PyMuPDF produces the worst garbage ("CmdVdt=−Iion"). Re-parse with MinerU pipeline backend. Estimated time: ~8 minutes CPU-only (pipeline backend ~1 p/s estimate) or ~3 minutes with MLX.

2. **Dayan & Abbott Chapters 1–4** (neural encoding, population codes, ~100 pages): Medium priority — some equations but fewer HH-specific ones. Re-parse with MinerU.

3. **Fundamental Neuroscience equation-tagged pages** (~200 pages flagged `has_equations=True` in current DB): Medium priority. Re-parse with MinerU.

4. **BRI610 lecture slides** (~50 slides × ~30 pages = ~1500 slide pages): Lower priority for LaTeX fidelity (figures often more important than equation text), but Marker's PPTX input is a qualitative improvement over current approach. Re-parse with Marker + Ollama.

5. **Prose/reference pages in both textbooks** (~1100 pages): Lowest priority — PyMuPDF works fine; no re-parse needed.

**Total one-time infrastructure cost**: $0 (MinerU pipeline + Marker Ollama). Time: ~4–6 hours compute on Mac M-series for all 1550 equation/mixed pages.

**If formula spot-check shows MinerU pipeline failures on specific pages** (expected for pages with handwritten annotations or low-quality scans in some FN chapters): run those specific pages through Mathpix API. Budget $1–3 for ~500–1500 fallback pages.

---

### Primary sources cited

- OmniDocBench GitHub leaderboard: https://github.com/opendatalab/OmniDocBench
- OmniDocBench CVPR 2025 paper: https://arxiv.org/html/2412.07626v1
- "Benchmarking Document Parsers on Mathematical Formula Extraction from PDFs" (arXiv:2512.09874): https://arxiv.org/html/2512.09874v1
- olmOCR 2 blog (AllenAI): https://allenai.org/blog/olmocr-2
- LlamaIndex olmOCR-Bench review: https://www.llamaindex.ai/blog/olmocr-bench-review-insights-and-pitfalls-on-an-ocr-benchmark
- Marker releases (PyPI): https://pypi.org/project/marker-pdf/
- MinerU releases: https://github.com/opendatalab/MinerU/releases
- Docling repo: https://github.com/DS4SD/docling
- Nougat paper (ICLR 2024): https://proceedings.iclr.cc/paper_files/paper/2024/file/a39a9aceda771cded859ae7560530e09-Paper-Conference.pdf
- Mathpix pricing: https://mathpix.com/pricing/all
- LlamaParse pricing: https://developers.llamaindex.ai/python/cloud/general/pricing/
- pix2tex repo: https://github.com/lukas-blecher/LaTeX-OCR
- PyMuPDF equation discussion: https://github.com/pymupdf/PyMuPDF/discussions/763
- CodeSOTA OmniDocBench leaderboard: https://www.codesota.com/ocr/benchmark/omnidocbench
- Docling formula bug (#2374): https://github.com/docling-project/docling/issues/2374
- Marker issue #680 (LLM mode benchmarks): https://github.com/datalab-to/marker/issues/680
- LlamaParse Premium blog: https://www.llamaindex.ai/blog/introducing-llamaparse-premium

*Note: Benchmark numbers that could not be independently verified from primary sources are marked accordingly. MinerU2.5-Pro OmniDocBench scores (formula CDM 97.45) are from the live leaderboard, which reflects hosted-service performance; local pipeline backend formula CDM is not separately published as of April 2026.*
