# BRI610 Tutor — Embedding Model Benchmark Report
**Version**: v0.5  
**Date**: April 2026  
**Scope**: RAG layer evaluation for a Korean+English Computational Neuroscience tutor  
**Current corpus**: 199 slides (multimodal) + 1,304 textbook pages = 1,503 chunks  
**Current model**: `nvidia/llama-nemotron-embed-vl-1b-v2:free` (2048-dim, multimodal)  
**Infrastructure**: PostgreSQL + pgvector, OpenRouter API, local Ollama on Apple M-series Mac  
**Query profile**: Korean + English bilingual (e.g., "Nernst 방정식 유도"), text-only prose retrieval + slide-image retrieval with equations

Benchmarks cited: MTEB English v2, MMTEB (Massive Multilingual Text Embedding Benchmark, arXiv:2502.13595), BEIR (NDCG@10), ViDoRe (Visual Document Retrieval), MIRACL (multilingual retrieval, 18 languages). Scores are taken from official model cards, papers, or blog posts as of April 2026. Where data is absent, the phrase **"no public benchmark"** is used rather than a fabricated number.

---

## 1. nvidia/llama-nemotron-embed-vl-1b-v2

**Provider / Repo**: NVIDIA — [https://huggingface.co/nvidia/llama-nemotron-embed-vl-1b-v2](https://huggingface.co/nvidia/llama-nemotron-embed-vl-1b-v2)  
**License / Cost**: NVIDIA Open Model License Agreement (commercial use permitted); Llama 3.2 Community License Agreement for the LM backbone. Open weights. Free on OpenRouter (`nvidia/llama-nemotron-embed-vl-1b-v2:free`; $0/M tokens).  
**Dimensions**: 2048 (fixed)  
**Max input**: 10,240 tokens; up to 6 image tiles × 256 tokens + 1 thumbnail (~1,792 visual tokens per image)  
**Multimodal**: yes

### 1. 아키텍처 개요 (Architecture)
Eagle VLM Transformer Encoder: a 1B Llama 3.2 language model (16 layers, 973M transformer + 262M token embedding) fused with a SigLIP2 400M vision encoder via tile-based processing (up to 6 tiles × 256 tokens). Total ~1.7B parameters. Released December 2025. Fine-tuned on 1.5M supervised + 12M semi-supervised text pairs and ~2.57M images from Eagle2 and public datasets (~1.6B total text tokens). No MS MARCO usage (commercial-friendly). Supports text-only, image-only, and image+text document embedding under a unified encoder.

### 2. 벤치마크 성능 (Benchmarks)
- **MTEB (English)**: no public benchmark — model card reports chunk retrieval only
- **MMTEB / multilingual**: no public benchmark
- **BEIR (Recall@5, chunk retrieval avg)**: 69.19% (BEIR + TechQA combined); MIRACL Recall@5 = 60.48%; MLDR Recall@5 = 60.09%; MLQA Recall@5 = 79.90%; overall avg Recall@5 = 67.42%
- **ViDoRe (Recall@5, multimodal avg across DC10k + Earnings V2 + ViDoRe V1/V2/V3)**:
  - Text-only mode: 71.04%
  - Image-only mode: 71.20%
  - Image+Text mode: 73.24%
- **Math/STEM-specific**: no public benchmark

### 3. 강점 (Strengths)
1. **Truly multimodal in a single encoder**: one model embeds slide images, OCR-less equation renders, and text passages into the same 2048-dim space — no dual-index complexity.
2. **Free on OpenRouter**: $0/M tokens, no re-embedding cost for ongoing ingestion.
3. **10,240-token context**: handles full textbook pages with long equations comfortably.
4. **Competitive visual retrieval**: Recall@5 ≥ 73% in image+text mode across ViDoRe family, outperforming CLIP-based baselines.
5. **Open weights with commercial license**: can be self-hosted via vLLM on a cloud GPU if OpenRouter rate limits become binding.

### 4. 약점 / 한계 (Weaknesses / limitations)
1. **No MTEB English or MMTEB multilingual score published**: impossible to compare text-only retrieval quality to the leaderboard at a standard 56-task level.
2. **Korean/Korean-STEM retrieval unverified**: no MIRACL-Ko or KLUE benchmark number; multilingual training data is undisclosed.
3. **Vision-first architecture**: SigLIP2 vision encoder dominates parameter count; for pure-text retrieval of dense prose, dedicated text encoders likely outperform.
4. **Flash Attention 2 requirement**: Mac M-series local run not natively supported (requires Linux + NVIDIA GPU); Ollama support absent.
5. **Fixed 2048-dim**: no Matryoshka truncation; pgvector index cost is permanent even if future text models use 1024 dims.

### 5. 한국어 지원 (Korean support)
- **Officially supported**: not benchmarked. The Llama 3.2 backbone was trained on multilingual data and supports Korean, but no Korean retrieval benchmark is cited in the model card or NVIDIA documentation. MIRACL score of 60.48% Recall@5 is an aggregate over 18 languages; Korean breakdown not published.
- **KLUE / KOR-STS / Korean retrieval**: no data.

### 6. STEM / Math 적합도 (STEM/math fitness)
- No STEM-specific retrieval evaluation published. The image+text mode should theoretically handle LaTeX-rendered equations embedded in slide images, but empirical nDCG on equation-heavy corpora is absent.

### 7. 통합 비용 (Integration cost for us)
- **OpenRouter**: `nvidia/llama-nemotron-embed-vl-1b-v2:free` — available now, $0/M tokens
- **HuggingFace**: `nvidia/llama-nemotron-embed-vl-1b-v2` — open weights, self-hostable with vLLM
- **Ollama**: not available; requires NVIDIA GPU + Flash Attention 2
- **Cost for 1,503 pages**: $0 (free tier on OpenRouter)
- **pgvector dimension change**: none required (current = 2048)

### 8. 결론 (Verdict)
**PRIMARY MULTIMODAL INDEX (baseline)**. Retain for slide-image embedding. Its free tier, 2048-dim alignment, and multimodal capability are unmatched at zero cost. The critical gap is unknown Korean text retrieval quality — this drives the evaluation of dedicated text models below.

---

## 2. Qwen3-Embedding-8B

**Provider / Repo**: Alibaba / QwenLM — [https://huggingface.co/Qwen/Qwen3-Embedding-8B](https://huggingface.co/Qwen/Qwen3-Embedding-8B)  
**License / Cost**: Apache 2.0 (fully open, commercial use permitted)  
**Dimensions**: 4,096 native; Matryoshka Representation Learning (MRL) supports any user-defined dimension from 32 to 4,096  
**Max input**: 32,768 tokens  
**Multimodal**: no (text only)

### 1. 아키텍처 개요 (Architecture)
Decoder-only Transformer based on the Qwen3-8B foundation model (36 layers, BF16). Converted to a bidirectional encoder for embedding via instruction-tuning on 16.4M+ multilingual query-passage pairs. Supports task-specific instruction prefixes ("Instruct: Given a …\nQuery:") that improve retrieval by 1–5% over instruction-free mode. Trained with synthetic hard negatives and MRL loss. Available via `sentence-transformers`, `transformers`, `vLLM`, and HuggingFace TEI.

### 2. 벤치마크 성능 (Benchmarks)
- **MTEB English v2**: Mean (Task) = 75.22; Mean (Type) = 68.71 — Retrieval 69.44, Classification 90.43, STS 88.58, Clustering 58.57
- **MMTEB / multilingual**: Mean (Task) = 70.58 — **ranked #1 on MTEB multilingual leaderboard as of June 5, 2025** — Retrieval 86.40, Bitext Mining 80.89, STS 81.08, Clustering 57.65
- **C-MTEB (Chinese)**: Mean (Task) = 73.84; Retrieval 78.21
- **BEIR**: no separate published BEIR NDCG@10 figure; retrieval score subsumed into MTEB English v2 retrieval = 69.44 (15 tasks)
- **ViDoRe / VisRAG**: N/A (text-only model)
- **Math/STEM**: no public STEM-specific benchmark; MTEB-Code = 80.68 (code retrieval, shows strong symbolic reasoning)

### 3. 강점 (Strengths)
1. **#1 MMTEB multilingual score (70.58)** as of mid-2025: strongest multilingual text retrieval benchmark published.
2. **Apache 2.0**: no commercial restrictions; can be embedded in production pipelines.
3. **MRL 32–4,096**: can emit 1,024-dim vectors to match existing index or extend to 4,096 for maximum accuracy.
4. **32K context**: handles multi-page textbook chunks without truncation.
5. **Ollama native**: `ollama pull qwen3-embedding:8b` — runs locally on M-series Mac.

### 4. 약점 / 한계 (Weaknesses / limitations)
1. **Memory-heavy locally**: 8B parameters require ~16GB RAM (Q8 quant ~8.5GB) — tight on 16GB M-series; Q4_K_M (~4.5GB) usable with accuracy tradeoff.
2. **Text-only**: cannot embed slide images; multimodal index must remain separate.
3. **No Korean-specific benchmark published**: MMTEB covers Korean within 100+ languages but per-language breakdown not in official docs.
4. **Latency at full 4,096-dim**: pgvector HNSW index build time and query latency increase with dimension; MRL truncation recommended.
5. **Relatively new (June 2025)**: limited third-party validation of STEM/neuroscience domain transfer.

### 5. 한국어 지원 (Korean support)
- **Officially supported**: yes (100+ languages via Qwen3 multilingual pre-training); MMTEB #1 overall implies strong Korean performance, but explicit KLUE/KOR-STS numbers are not published.
- **KLUE / Korean retrieval**: no public breakdown. Community comparisons (Aryan Kumar, Medium, 2025) show Qwen3-Embedding outperforming BGE-M3 on a Korean QA test set, but methodology is informal.

### 6. STEM / Math 적합도 (STEM/math fitness)
- MTEB-Code score 80.68 demonstrates strong symbolic/structured-text retrieval. No neuroscience-specific evaluation exists. The Qwen3 base model has strong reasoning over scientific text; the embedding model inherits this representation.

### 7. 통합 비용 (Integration cost for us)
- **OpenRouter**: not listed as an embedding endpoint (LLM-only router); not available
- **HuggingFace Inference**: `Qwen/Qwen3-Embedding-8B` — self-host via TEI or vLLM
- **Ollama**: `ollama pull qwen3-embedding:8b` (official library entry) — free local use
- **Cost**: $0 (self-hosted)
- **Re-embedding 1,503 pages**: 0 USD (local Ollama); time ~15–45 min on M-series at Q4_K_M
- **pgvector dimension change**: yes — from 2048 → recommend 1,024 (MRL) to keep index cost manageable; requires `ALTER TABLE` + reindex

### 8. 결론 (Verdict)
**PRIMARY-CANDIDATE** for text index. Best published multilingual retrieval scores, Apache 2.0 license, Ollama-native, zero cost. The key risk is local RAM on a 16GB Mac (use Q4_K_M or Q5_K_M quant). Strongly recommend A/B test against current VL model for text-only prose retrieval on the 1,304 textbook pages.

---

## 3. Qwen3-Embedding-4B

**Provider / Repo**: Alibaba / QwenLM — [https://huggingface.co/Qwen/Qwen3-Embedding-4B](https://huggingface.co/Qwen/Qwen3-Embedding-4B)  
**License / Cost**: Apache 2.0  
**Dimensions**: 2,560 native; MRL 32–2,560  
**Max input**: 32,768 tokens  
**Multimodal**: no

### 1. 아키텍처 개요 (Architecture)
Same training recipe as 8B but built on the Qwen3-4B backbone. Fewer layers, smaller hidden size (2,560 vs. 4,096). Instruction-aware via task prefix. Available on Ollama as `qwen3-embedding:4b`.

### 2. 벤치마크 성능 (Benchmarks)
- **MTEB English v2**: Mean (Task) = 74.60; Mean (Type) = 68.10 (–0.62 vs. 8B)
- **MMTEB multilingual**: Mean (Task) = 69.45 (–1.13 vs. 8B); ranked #3–4 as of June 2025
- **C-MTEB**: Mean (Task) = 72.27; Retrieval 77.50 (approx.)
- **BEIR**: no separate published figure
- **ViDoRe / VisRAG**: N/A
- **Math/STEM**: no public benchmark

### 3. 강점 (Strengths)
1. **Near-8B accuracy at half the weight**: MMTEB 69.45 vs. 70.58 (8B) — only 1.6% gap.
2. **Fits comfortably on 16GB M-series**: Q4_K_M ~2.2GB; Q8 ~4.4GB — ample headroom.
3. **Apache 2.0, zero cost, Ollama-native**: identical access to 8B.
4. **2,560-dim native**: closer to current 2048-dim index; MRL to 1,024 still practical.
5. **32K context**: full textbook pages without truncation.

### 4. 약점 / 한계 (Weaknesses / limitations)
1. **1.1-point MMTEB gap vs. 8B**: measurable but small; worth verifying on our domain.
2. **Text-only**: slide images require a separate multimodal index.
3. **No Korean-specific breakdown**: same limitation as 8B.
4. **2,560-dim pgvector column**: differs from both current 2048 and the 8B's 4,096; if switching between sizes, schema must change.
5. **Newer model, limited community validation**.

### 5. 한국어 지원 (Korean support)
- Same as 8B — officially 100+ languages, no KLUE breakdown published. Expected strong CJK coverage via Qwen3 pre-training.

### 6. STEM / Math 적합도 (STEM/math fitness)
- Similar to 8B; MTEB-Code score for 4B not separately published but expected ~78–80. No STEM domain evaluation.

### 7. 통합 비용 (Integration cost for us)
- **OpenRouter**: not available
- **HuggingFace**: `Qwen/Qwen3-Embedding-4B`
- **Ollama**: `ollama pull qwen3-embedding:4b` — confirmed in library
- **Cost**: $0
- **Re-embedding 1,503 pages**: 0 USD, ~8–20 min on M-series at Q4_K_M
- **pgvector dimension change**: yes — recommend MRL to 1,024 for consistency with 8B migration path

### 8. 결론 (Verdict)
**SECONDARY-INDEX (A/B test)**. Ideal fallback if 8B is too slow for real-time query latency on M-series. Use 4B for the text index during development; benchmark against 8B via offline nDCG on the textbook corpus before committing to production. If 8B fits RAM, prefer 8B.

---

## 4. Voyage-3-large + voyage-multimodal-3 (Voyage AI)

**Provider / Repo**: Voyage AI (MongoDB) — [https://docs.voyageai.com](https://docs.voyageai.com)  
**License / Cost**:
- voyage-3-large: proprietary API; $0.18/M tokens (legacy tier; no new free tokens)
- voyage-multimodal-3: proprietary API; $0.12/M text tokens + $0.60/B pixels; first 200M text tokens + 150B pixels free (new accounts)
**Dimensions**:
- voyage-3-large: 2,048 / 1,024 / 512 / 256 (MRL)
- voyage-multimodal-3: 1,024 (fixed)
**Max input**: 32,000 tokens (both models)  
**Multimodal**: voyage-3-large = no; voyage-multimodal-3 = yes (text + images)

### 1. 아키텍처 개요 (Architecture)
**voyage-3-large**: Proprietary dense text encoder trained with Matryoshka learning and quantization-aware training. Claims 9.74% avg improvement over OpenAI text-embedding-3-large and 20.71% over Cohere embed-v3-English across 100 datasets in 8 domains. Supports 32-bit, int8, uint8, and binary quantization.

**voyage-multimodal-3**: Vision-language Transformer encoder (proprietary) processing interleaved text and images within a single backbone — not a dual-tower CLIP architecture. Evaluated on 20 multimodal datasets covering table/figure retrieval, document screenshot retrieval (ViDoRe), and text-to-photo. A newer version `voyage-multimodal-3.5` was released January 2026 with video support and flexible dimensions (256–2048).

### 2. 벤치마크 성능 (Benchmarks)

**voyage-3-large**:
- **MTEB (English)**: no public MTEB leaderboard score (proprietary, not submitted)
- **MMTEB / multilingual**: no public benchmark
- **BEIR**: Voyage AI reports 9.74% average improvement over OpenAI text-embedding-3-large across 100 datasets — concrete NDCG@10 by dataset not published
- **ViDoRe**: N/A (text-only)
- **Math/STEM**: no public benchmark

**voyage-multimodal-3**:
- **ViDoRe (document screenshot retrieval)**: +26.54% over CLIP-ViT-L-14; +25.84% over Cohere multimodal v3 (relative improvement; absolute NDCG not published)
- **Table/figure retrieval**: +41.44% over CLIP large; +43.37% over Cohere multimodal v3
- **Text retrieval (34 datasets)**: +5.13% over OpenAI text-embedding-3-large
- **MTEB**: no public submission

### 3. 강점 (Strengths)
1. **voyage-multimodal-3 purpose-built for document images**: slides, PDFs, tables, figures — strong fit for 199 slides.
2. **Single-backbone multimodal**: no dual-encoder mismatch between query (text) and document (image) spaces.
3. **voyage-3-large 32K context**: matches Qwen3 for long textbook passages.
4. **Matryoshka support on voyage-3-large**: can compress to 256 dims for prototyping.
5. **voyage-multimodal-3 free tier (new accounts)**: 200M text tokens + 150B pixels — sufficient for full 1,503-page re-embed.

### 4. 약점 / 한계 (Weaknesses / limitations)
1. **Proprietary / closed weights**: no local deployment; data leaves device.
2. **No MTEB score submitted**: impossible to independently compare text retrieval quality vs. Qwen3.
3. **Korean / multilingual**: voyage-multimodal-3 is primarily English-focused; no multilingual benchmark published. voyage-3-large also lacks a multilingual MTEB number.
4. **voyage-3-large is legacy**: Voyage has moved to voyage-4-large ($0.12/M); continued investment in voyage-3-large unclear.
5. **voyage-multimodal-3 1,024-dim fixed**: pgvector index requires schema change from current 2,048-dim.

### 5. 한국어 지원 (Korean support)
- **voyage-3-large**: no public multilingual benchmark; likely partial support
- **voyage-multimodal-3**: no multilingual benchmark cited; English-first
- **KLUE / Korean retrieval**: no data for either model

### 6. STEM / Math 적합도 (STEM/math fitness)
- No STEM-specific benchmark for either model. voyage-multimodal-3 handles equation-heavy PDF images by encoding the rendered page as an image, bypassing LaTeX parsing entirely — pragmatically useful for our slides.

### 7. 통합 비용 (Integration cost for us)
- **OpenRouter**: not available (embedding-specific API direct from Voyage)
- **HuggingFace / Ollama**: not available (closed weights)
- **voyage-3-large**: $0.18/M tokens; 1,503 pages × ~1,000 tokens avg = ~1.5M tokens → ~$0.27
- **voyage-multimodal-3**: 199 slides × image pixels ≈ minimal pixel cost + text tokens → estimate < $0.05 (within free tier)
- **pgvector dimension change**: yes — voyage-multimodal-3 = 1,024; voyage-3-large = 2,048 (matches current); dual-column schema recommended

### 8. 결론 (Verdict)
**NICHE-USE** for voyage-multimodal-3 as a benchmark comparison target for slide retrieval (to evaluate whether Nemotron VL outperforms it). **REJECT** for voyage-3-large as primary text index: proprietary, no multilingual MTEB, Korean unvalidated, and open-source alternatives (Qwen3-Embedding) demonstrably lead on MMTEB.

---

## 5. Cohere embed-v4 / embed-multilingual-v3

**Provider / Repo**: Cohere — [https://docs.cohere.com](https://docs.cohere.com)  
**License / Cost**:
- embed-v4: proprietary API; $0.10/M tokens (embed-v4-light: $0.02/M)
- embed-multilingual-v3.0: proprietary API; $0.10/M tokens (via CohereLabs HF checkpoint for self-host with Cohere license)
**Dimensions**:
- embed-v4: 1,536 / 1,024 / 512 / 256 (MRL)
- embed-multilingual-v3.0: 1,024 (fixed)
**Max input**: embed-v4 = 128,000 tokens; embed-multilingual-v3.0 = 512 tokens  
**Multimodal**: embed-v4 = yes (multimodal: text + image interleaved); embed-multilingual-v3.0 = no

### 1. 아키텍처 개요 (Architecture)
**embed-v4**: Proprietary encoder trained on 1.2 trillion tokens (3× more than v3). Uses contrastive learning with dynamic batching, synthetic hard negatives, and multi-task training across 50+ task types. Supports unified multimodal input (text + image), 128K context, and Matryoshka dimensions.

**embed-multilingual-v3.0**: Earlier generation proprietary encoder; 1024-dim, 512-token limit, 100+ language support, contrastive training.

### 2. 벤치마크 성능 (Benchmarks)

**embed-v4**:
- **MTEB (English)**: Mean = 66.8; Retrieval = 55.1; Classification = 74.2
- **MMTEB / multilingual**: English = 68.2, Chinese = 65.1, Spanish = 64.8, Arabic = 62.3, Hindi = 61.7 (no Korean breakdown)
- **BEIR**: NQ +6.6%, HotpotQA +6.2%, SciFact +8.5%, Climate-FEVER +22.9% vs. embed-v3
- **ViDoRe**: Amazon Nova MME achieves +5.1pps higher NDCG@5 vs. embed-v4 on ViDoRe V2 — implies embed-v4 ViDoRe score is in the 80–85% range (absolute score not published by Cohere)
- **Math/STEM**: no public benchmark

**embed-multilingual-v3.0**:
- **MTEB**: no standalone published MTEB score; embed-v3 family score reported at 64.2 avg
- **BEIR**: state-of-the-art at launch (2023); since surpassed by open-source models
- **ViDoRe**: N/A

### 3. 강점 (Strengths)
1. **embed-v4 128K context**: by far the largest context window of any model reviewed — can embed entire lecture chapters.
2. **embed-v4 multimodal + text unified**: single model for both text and image retrieval.
3. **35% cross-lingual retrieval improvement** (embed-v4 vs. embed-v3).
4. **Cohere API robust infrastructure**: enterprise SLA, dedicated endpoints, no cold starts.
5. **MRL on embed-v4**: flexible 256–1,536 dims.

### 4. 약점 / 한계 (Weaknesses / limitations)
1. **embed-multilingual-v3 hard 512-token limit**: truncates textbook pages; unsuitable as primary text index without chunking.
2. **Proprietary weights**: no local Ollama deployment; data leaves device.
3. **MTEB 66.8 for embed-v4**: well below Qwen3-Embedding-8B (75.22) on English; below Llama-Embed-Nemotron-8B (MMTEB 69.46) multilingual.
4. **Korean benchmark absent**: no KLUE or Korean retrieval score published.
5. **Cost at scale**: $0.10/M tokens; for ongoing daily queries, cost adds up vs. free local alternatives.

### 5. 한국어 지원 (Korean support)
- **embed-v4**: officially 100+ languages; cross-lingual improvement of 35% claimed but no Korean-specific score published.
- **embed-multilingual-v3.0**: 100+ languages; no KLUE data.
- **KLUE / Korean retrieval**: no data for either model.

### 6. STEM / Math 적합도 (STEM/math fitness)
- SciFact BEIR improvement (+8.5%) suggests some STEM-text retrieval benefit, but the score baseline is embed-v3, not a competitive open-source model. No neuroscience-specific evaluation.

### 7. 통합 비용 (Integration cost for us)
- **OpenRouter**: not available (Cohere direct API or AWS Bedrock)
- **HuggingFace**: `CohereLabs/Cohere-embed-multilingual-v3.0` checkpoint (non-commercial license)
- **Ollama**: not available
- **Cost for 1,503 pages** (embed-v4): ~1.5M tokens × $0.10/M = **$0.15**
- **pgvector dimension change**: yes — embed-v4 default 1,536 ≠ current 2,048

### 8. 결론 (Verdict)
**REJECT** as primary. MTEB 66.8 trails Qwen3-Embedding-8B by 8.4 points; Korean unvalidated; proprietary with no local option. embed-v4's 128K context is compelling for ultra-long documents but not needed for our 1,024-token chunks. **NICHE-USE** only if Cohere API access is already established and multimodal unification (single API for text+image) is the overriding constraint.

---

## 6. Jina-embeddings-v4 / v3 (Jina AI)

**Provider / Repo**: Jina AI — [https://huggingface.co/jinaai/jina-embeddings-v4](https://huggingface.co/jinaai/jina-embeddings-v4) / [https://jina.ai/models/jina-embeddings-v3/](https://jina.ai/models/jina-embeddings-v3/)  
**License / Cost**:
- jina-embeddings-v4: Qwen Research License (non-commercial research only); API free-tier 10M tokens, then throttled
- jina-embeddings-v3: CC-BY-NC-4.0 (non-commercial); API pricing not public
**Dimensions**:
- v4: 2,048 (MRL: 128, 256, 512, 1,024, 2,048); multi-vector 128-dim for late interaction
- v3: 1,024 (MRL: 32–1,024)
**Max input**: v4 = 32,768 tokens; v3 = 8,192 tokens  
**Multimodal**: v4 = yes (text + images + PDFs); v3 = no

### 1. 아키텍처 개요 (Architecture)
**jina-embeddings-v4**: 3.8B parameters based on Qwen2.5-VL-3B-Instruct. Supports single-vector (dense) and multi-vector (late interaction, ColBERT-style) retrieval. Task-specific LoRA adapters for retrieval, text-matching, and code. 30+ languages. Released ~mid-2025.

**jina-embeddings-v3**: 570M parameters, XLM-RoBERTa-style encoder extended with task-specific LoRA adapters. 108 languages. 8,192-token context. Dense retrieval only.

### 2. 벤치마크 성능 (Benchmarks)

**jina-embeddings-v4**:
- **MTEB (English)**: 55.97 (below v3)
- **MMTEB multilingual**: 66.49 (+14% vs. v3's 58.58)
- **LongEmbed**: 67.11
- **ViDoRe (single-vector)**: 84.11; **multi-vector**: 90.17 — state-of-the-art ViDoRe at launch
- **Jina-VDR (multilingual visual doc retrieval)**: multi-vector 80.2
- **Math/STEM**: no public benchmark

**jina-embeddings-v3**:
- **MTEB English**: avg 65.52 (Classification 82.58, STS 85.80)
- **MMTEB multilingual**: 58.58
- **BEIR**: competitive at launch (2024); surpassed since
- **ViDoRe**: N/A

### 3. 강점 (Strengths)
1. **jina-v4 ViDoRe 90.17 (multi-vector)**: highest ViDoRe score in this comparison — exceptional slide-image retrieval.
2. **Unified multimodal + multilingual in one model** (v4): text, image, and PDF native.
3. **jina-v3 CC-BY-NC-4.0 + open weights**: self-hostable for research use.
4. **v4 PDF-native**: directly embeds PDF URLs — reduces preprocessing pipeline.
5. **32K context (v4)**: handles long textbook passages.

### 4. 약점 / 한계 (Weaknesses / limitations)
1. **Non-commercial license on both v3 and v4**: the project is educational/research — this is borderline acceptable, but limits any commercialization path.
2. **jina-v4 MTEB English 55.97**: significantly below Qwen3-Embedding-8B (75.22); text-only retrieval is weaker.
3. **API throttled for v4** (Qwen Research License prevents Jina from commercializing): limited throughput; not suitable for production load.
4. **v3's 8,192-token limit and 65.52 MTEB**: inferior to Qwen3-4B on both context and accuracy.
5. **No Ollama support**: HuggingFace only; local inference requires vLLM or sentence-transformers.

### 5. 한국어 지원 (Korean support)
- **v4**: 30+ languages supported; Korean not explicitly listed among the 34 training languages. Partial support via Qwen2.5-VL backbone (which has CJK coverage).
- **v3**: 108 languages; Korean likely included but no KLUE/KOR-STS score published.
- **KLUE / Korean retrieval**: no data.

### 6. STEM / Math 적합도 (STEM/math fitness)
- v4 embeds equation-heavy slide images (ViDoRe 84.11 single-vector) — directly relevant to our slide corpus. No text-based STEM benchmark cited.

### 7. 통합 비용 (Integration cost for us)
- **OpenRouter**: not available
- **HuggingFace**: `jinaai/jina-embeddings-v4` / `jinaai/jina-embeddings-v3`
- **Ollama**: not available
- **API (v4)**: free-tier 10M tokens (non-commercial); throttled thereafter
- **Cost for 1,503 pages**: $0 within 10M token free tier (text); image pricing N/A (research use)
- **pgvector dimension change**: v4 default = 2,048 (matches current); no change needed

### 8. 결론 (Verdict)
**NICHE-USE** — specifically for a multimodal slide retrieval A/B test. jina-v4's ViDoRe 90.17 (multi-vector) is the highest in this survey and should be compared against Nemotron VL's 73.24 on our 199 slides. **REJECT** for primary text index: MTEB 55.97, non-commercial license, no Ollama, API throttling.

---

## 7. BGE-M3 (BAAI)

**Provider / Repo**: BAAI — [https://huggingface.co/BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3)  
**License / Cost**: MIT (open, commercial use permitted)  
**Dimensions**: 1,024 (fixed; no MRL)  
**Max input**: 8,192 tokens  
**Multimodal**: no

### 1. 아키텍처 개요 (Architecture)
XLM-RoBERTa (BERT-style) extended to 8,192 tokens via RetroMAE pretraining. Supports three retrieval modes simultaneously: **dense** (single 1024-dim vector), **sparse** (BM25-like lexical weights per token), and **multi-vector / ColBERT** (per-token vectors). Self-knowledge distillation unifies the three heads. 100+ languages. Released January 2024. Also available as `dragonkue/BGE-m3-ko` — a Korean-fine-tuned variant.

### 2. 벤치마크 성능 (Benchmarks)
- **MTEB (English)**: approximately 64.2 avg across 56 tasks (2024 estimate, surpassed by newer models)
- **MMTEB multilingual**: No MMTEB submission; predates the benchmark. MIRACL nDCG@10 (18 languages): **dense = 67.8** (vs. E5-large 65.4); **combined modes = 70.0**
- **BEIR**: competitive at launch (2024); outperformed mE5-large by ~5.5 points on multilingual tasks; no updated BEIR table post-2024
- **ViDoRe**: N/A
- **Math/STEM**: no public benchmark

### 3. 강점 (Strengths)
1. **Tri-mode retrieval (dense + sparse + ColBERT)**: hybrid retrieval via a single model — particularly powerful for keyword-exact STEM terminology (e.g., "Nernst equation" vs. "Nernst 방정식").
2. **MIT license**: fully open, commercial use unrestricted.
3. **Ollama-native**: `ollama pull bge-m3` — runs on M-series Mac out of the box.
4. **8,192-token context**: handles full textbook pages.
5. **Korean fine-tuned variant available** (`dragonkue/BGE-m3-ko`): explicit Korean adaptation.

### 4. 약점 / 한계 (Weaknesses / limitations)
1. **1,024-dim fixed**: no MRL; pgvector index requires schema change from current 2,048 but cannot be further compressed.
2. **MTEB ~64.2**: notably below Qwen3-Embedding-8B (75.22); competitiveness eroded since mid-2024.
3. **BERT-style max 8K tokens**: shorter than 32K offered by Qwen3 or Nemotron VL.
4. **Dense mode only for pgvector**: sparse and multi-vector modes require a separate keyword/ColBERT index; adds infrastructure complexity.
5. **No active development**: BAAI's recent work focuses on bge-multilingual-gemma2; BGE-M3 is unlikely to receive further updates.

### 5. 한국어 지원 (Korean support)
- **Officially supported**: yes — 100+ languages including Korean. MIRACL Korean is included in the 18-language aggregate score.
- **`dragonkue/BGE-m3-ko`**: Korean-finetuned adapter on top of BGE-M3; available on HuggingFace and Ollama.
- **KLUE / KOR-STS**: no standalone published score, but MIRACL aggregate (67.8 NDCG@10) provides the best public multilingual evidence in this survey.

### 6. STEM / Math 적합도 (STEM/math fitness)
- Sparse retrieval head provides BM25-style lexical matching — excellent for exact STEM terminology retrieval ("nDCG@10 ion channel conductance"). No TheoremQA or ScienceQA evaluation published.

### 7. 통합 비용 (Integration cost for us)
- **OpenRouter**: not available
- **HuggingFace**: `BAAI/bge-m3` (sentence-transformers, FlagEmbedding)
- **Ollama**: `ollama pull bge-m3` — confirmed available
- **Cost**: $0 (local)
- **Re-embedding 1,503 pages**: $0, ~10–20 min on M-series
- **pgvector dimension change**: yes — 1,024 ≠ 2,048; schema change required

### 8. 결론 (Verdict)
**SECONDARY-INDEX (A/B test)**. The hybrid retrieval (dense+sparse) is uniquely valuable for mixed Korean/English STEM queries — exact bilingual terminology matching benefits from BM25-sparse head. However, MTEB 64.2 lags Qwen3-Embedding-8B by 11 points. Use as a sparse-retrieval complement to Qwen3 dense, not as the sole primary.

---

## 8. NV-Embed-v2 / Llama-Embed-Nemotron-8B (NVIDIA)

**Provider / Repo**: NVIDIA — NV-Embed-v2: [https://huggingface.co/nvidia/NV-Embed-v2](https://huggingface.co/nvidia/NV-Embed-v2); Nemotron-8B: [https://huggingface.co/nvidia/llama-embed-nemotron-8b](https://huggingface.co/nvidia/llama-embed-nemotron-8b)  
**License / Cost**:
- NV-Embed-v2: CC-BY-NC-4.0 (**non-commercial only**)
- Llama-Embed-Nemotron-8B: Customized NSCL-v1 (**research/non-commercial only**)
**Dimensions**:
- NV-Embed-v2: 4,096 (fixed; latent-attention pooling)
- Nemotron-8B: 4,096 (fixed)
**Max input**: 32,768 tokens (both)  
**Multimodal**: no (text only)

### 1. 아키텍처 개요 (Architecture)
**NV-Embed-v2**: Decoder-only Transformer (Mistral-7B-v0.1, 8B params) with a novel latent-attention pooling layer replacing mean/CLS pooling. Fine-tuned using two-stage training: unsupervised contrastive + supervised instruction fine-tuning. MTEB #1 as of August 2024 with 72.31 across 56 tasks.

**Llama-Embed-Nemotron-8B**: Decoder-only Transformer (Llama-3.1-8B, 7.5B params, bidirectional attention). Fine-tuned on 16.4M multilingual query-passage pairs from a hybrid of public and synthetically generated data. MMTEB #1 as of October 2025 with 69.46 mean + 39,573 Borda votes across 131 tasks and 1,038 languages.

### 2. 벤치마크 성능 (Benchmarks)

**NV-Embed-v2**:
- **MTEB (English)**: 72.31 avg (56 tasks, Aug 2024) — #1 at time of release; retrieval avg = 62.65
- **MMTEB**: not submitted; predates MMTEB prominence
- **BEIR**: multiple BEIR tasks included within MTEB 72.31; specific NDCG@10 not broken out publicly
- **ViDoRe**: N/A
- **Math/STEM**: no public benchmark

**Llama-Embed-Nemotron-8B**:
- **MMTEB (multilingual v2)**: Mean (Task) = 69.46; **Borda count = 39,573 (#1 as of Oct 2025)**; 131 tasks, 9 task types, 20 domains
- **MTEB (English)**: no standalone score published; subsumed in MMTEB
- **BEIR**: no standalone score; included within MMTEB retrieval tasks
- **ViDoRe**: N/A
- **Math/STEM**: no public benchmark

### 3. 강점 (Strengths)
1. **NV-Embed-v2 MTEB 72.31**: highest MTEB English score of any model in this survey for its era.
2. **Nemotron-8B MMTEB #1 (Oct 2025)**: #1 multilingual Borda count, 1,038-language coverage.
3. **32K context**: handles full textbook pages.
4. **vLLM and TensorRT ready**: production-grade inference stack.
5. **Both available on HuggingFace**: open weights (though non-commercial only).

### 4. 약점 / 한계 (Weaknesses / limitations)
1. **Non-commercial license on both models**: a research project — borderline acceptable; **cannot be used in a commercial product**.
2. **4,096-dim fixed, no MRL**: double the current 2,048 dims; pgvector storage and index cost doubles.
3. **No Ollama support**: neither model is in the Ollama library; local use requires GPU + vLLM (not available on Apple MPS).
4. **OpenRouter lists only the VL model (text-only 8B not available)**: no free-tier API access for Nemotron-8B text model.
5. **Nemotron-8B lacks standalone MTEB English score**: hard to compare with Qwen3-Embedding-8B on English STEM text.

### 5. 한국어 지원 (Korean support)
- **Nemotron-8B**: MMTEB covers 1,038 languages including Korean; MMTEB #1 position implies strong multilingual coverage. No KLUE-specific score published.
- **NV-Embed-v2**: English-focused; no multilingual benchmark published.

### 6. STEM / Math 적합도 (STEM/math fitness)
- No STEM-specific benchmark for either. NV-Embed-v2 was fine-tuned on diverse retrieval pairs including scientific text; MTEB 72.31 encompasses BEIR SciFact (scientific claims). No TheoremQA or neuroscience-specific eval.

### 7. 통합 비용 (Integration cost for us)
- **OpenRouter**: Nemotron-8B text model not listed; VL model only (separate)
- **HuggingFace**: open weights (non-commercial)
- **Ollama**: not available
- **API**: NVIDIA NIM (cloud) — enterprise pricing, not free-tier
- **Re-embedding 1,503 pages**: requires cloud GPU or NVIDIA NIM; cost unknown
- **pgvector dimension change**: yes — 4,096 ≠ 2,048; significant schema change + memory overhead

### 8. 결론 (Verdict)
**REJECT** for primary text index. Non-commercial license conflicts with potential commercialization; no Ollama/local support on M-series Mac; 4,096-dim pgvector overhead without MRL. Nemotron-8B's MMTEB #1 is impressive, but Qwen3-Embedding-8B (MMTEB #3 at 70.58) is only 0.12 points behind with Apache 2.0 + Ollama native. NV-Embed-v2's MTEB 72.31 is for a legacy English-only model with non-commercial license — also rejected.

---

## 9. OpenAI text-embedding-3-large

**Provider / Repo**: OpenAI — [https://platform.openai.com/docs/guides/embeddings](https://platform.openai.com/docs/guides/embeddings)  
**License / Cost**: Proprietary API; $0.13/M tokens  
**Dimensions**: 3,072 (MRL; reducible to any size, e.g., 256 retains strong performance)  
**Max input**: 8,192 tokens  
**Multimodal**: no

### 1. 아키텍처 개요 (Architecture)
Proprietary Transformer encoder. Third-generation OpenAI embedding model, released January 2024. Uses Matryoshka representation learning for flexible dimensionality. Trained on broad multilingual corpora. Supports signed/unsigned int8 and binary quantization.

### 2. 벤치마크 성능 (Benchmarks)
- **MTEB (English)**: 64.6 avg across 56 tasks
- **MMTEB / multilingual**: no dedicated submission; MIRACL avg = 54.9 (18 languages)
- **BEIR**: strong at launch (2024); serves as a common baseline — Voyage-3-large reports +9.74% over this model
- **ViDoRe**: N/A
- **Math/STEM**: no public benchmark

### 3. 강점 (Strengths)
1. **Battle-tested, universal API**: production-grade uptime, no model management, OpenAI ecosystem integration.
2. **MRL flexible dims**: 256–3,072; can fit various pgvector configurations.
3. **Well-known baseline**: large body of RAG literature benchmarks against it.
4. **Simple API**: `client.embeddings.create(model="text-embedding-3-large", input=...)`.
5. **$0.13/M**: competitive against Voyage.

### 4. 약점 / 한계 (Weaknesses / limitations)
1. **MTEB 64.6**: significantly below Qwen3-Embedding-8B (75.22), Nemotron-8B MMTEB (69.46), and even BGE-M3 MIRACL (67.8). Clearly not state-of-the-art in 2026.
2. **MIRACL 54.9**: weakest multilingual retrieval score in this survey; poor for Korean-English bilingual queries.
3. **8,192-token limit**: shorter than Qwen3 or BGE-M3 variants.
4. **Proprietary / no local option**: data must go to OpenAI servers.
5. **Closed weights**: no fine-tuning for STEM/neuroscience domain.

### 5. 한국어 지원 (Korean support)
- **Officially multilingual**: yes, but MIRACL 54.9 is the lowest multilingual score in this survey. Korean retrieval quality is likely below alternatives.
- **KLUE / Korean retrieval**: no data published.

### 6. STEM / Math 적합도 (STEM/math fitness)
- No STEM-specific evaluation. Common usage in scientific RAG applications, but outperformed by newer models on BEIR SciFact and similar.

### 7. 통합 비용 (Integration cost for us)
- **OpenRouter**: available as `openai/text-embedding-3-large` — $0.13/M tokens
- **HuggingFace / Ollama**: not available
- **Cost for 1,503 pages**: ~1.5M tokens × $0.13/M = **$0.20**
- **pgvector dimension change**: yes — 3,072 ≠ 2,048 (or use MRL to 1,024/2,048)

### 8. 결론 (Verdict)
**REJECT**. MTEB 64.6 and MIRACL 54.9 place it at the bottom of the text retrieval league for 2026, despite its familiarity. Qwen3-Embedding-8B offers 75.22 MTEB for free locally. The only remaining use case would be an existing OpenAI-centric stack with no tolerance for self-hosting — which does not apply here.

---

## 10. multilingual-e5-large-instruct (Microsoft)

**Provider / Repo**: Microsoft (intfloat) — [https://huggingface.co/intfloat/multilingual-e5-large-instruct](https://huggingface.co/intfloat/multilingual-e5-large-instruct)  
**License / Cost**: MIT (fully open, commercial use permitted)  
**Dimensions**: 1,024 (fixed; no MRL)  
**Max input**: 512 tokens  
**Multimodal**: no

### 1. 아키텍처 개요 (Architecture)
24-layer XLM-RoBERTa-based encoder (560M parameters). Two-stage training: (1) contrastive pre-training on 1 billion weakly supervised multilingual text pairs, (2) supervised fine-tuning on E5-mistral instruction datasets. Instruction-aware: queries must include a task description prefix. Supports 94+ languages. Lightweight compared to all other models in this survey.

### 2. 벤치마크 성능 (Benchmarks)
- **MTEB (English)**: approximately 64.9 avg (community-reported; official score via microsoft/unilm repo)
- **MMTEB multilingual (old leaderboard, pre-MMTEB v2)**: overall Borda count 1,244; avg 63.4 — **ranked #1 among publicly available models with ≤600M parameters** (MMTEB paper, arXiv:2502.13595)
- **BEIR**: competitive as of 2024; outperformed by newer models
- **ViDoRe**: N/A
- **Math/STEM**: no public benchmark

### 3. 강점 (Strengths)
1. **Best small-model multilingual score**: MMTEB 63.4 with only 560M params — extremely efficient.
2. **MIT license**: fully commercial, no restrictions.
3. **Ollama-native**: multiple community builds available (`blaifa/multilingual-e5-large-instruct`, `qllama/multilingual-e5-large-instruct`).
4. **Fast inference**: 560M params → very low latency on M-series CPU/MPS.
5. **Proven multilingual coverage**: 94+ languages explicitly in training; proven MIRACL performance.

### 4. 약점 / 한계 (Weaknesses / limitations)
1. **512-token hard limit**: textbook pages typically exceed this; aggressive chunking required, losing cross-sentence context.
2. **MTEB ~64.9**: below Qwen3-Embedding-8B by >10 points; outdated in 2026.
3. **No MRL**: fixed 1,024 dims; pgvector schema change required.
4. **No STEM-specific tuning**: general multilingual model; neuroscience domain transfer untested.
5. **Instruction requirement on queries only**: asymmetry adds API complexity (documents embedded differently from queries).

### 5. 한국어 지원 (Korean support)
- **Officially supported**: yes — 94+ languages including Korean. MMTEB's multilingual benchmark includes Korean tasks.
- **KLUE / KOR-STS**: no standalone benchmark published; the model was evaluated on MIRACL aggregate (Korean included in 18-language set).
- Historically considered one of the stronger open-source models for Korean retrieval before Qwen3-Embedding release.

### 6. STEM / Math 적합도 (STEM/math fitness)
- No STEM-specific evaluation. General multilingual encoder; fine-tuned on diverse retrieval pairs. 512-token limit is a practical constraint for equation-dense paragraphs.

### 7. 통합 비용 (Integration cost for us)
- **OpenRouter**: not available
- **HuggingFace**: `intfloat/multilingual-e5-large-instruct`
- **Ollama**: available via community builds (`blaifa/multilingual-e5-large-instruct`)
- **Cost**: $0 (local)
- **Re-embedding 1,503 pages**: $0; very fast — ~3–5 min on M-series (560M params)
- **pgvector dimension change**: yes — 1,024 ≠ 2,048

### 8. 결론 (Verdict)
**REJECT** as primary in 2026. The 512-token limit makes it structurally incompatible with full-page textbook embedding. MTEB 64.9 is no longer competitive. However, it is a useful **sanity-check baseline** for multilingual retrieval quality in the A/B test (fast, free, MIT-licensed). If Ollama RAM is critically constrained (e.g., 8GB Mac), this is the emergency fallback — but Qwen3-4B at similar RAM cost delivers far superior accuracy.

---

## Integrated Synthesis (통합 결론)

### Primary Text Embedding Recommendation

**Qwen3-Embedding-8B is the recommended primary text embedding model** for Korean+English STEM retrieval. Its MMTEB multilingual score of 70.58 leads the entire leaderboard as of mid-2025, its MTEB English v2 score of 75.22 is the highest among all models reviewed, it carries an Apache 2.0 license with no commercial restrictions, and it runs natively on Ollama (`ollama pull qwen3-embedding:8b`) on an Apple M-series Mac. For a 16GB RAM machine, the Q4_K_M quantization (~4.5GB) is recommended, accepting a small accuracy tradeoff (~1–2%) in exchange for comfortable memory headroom. The MRL capability allows emitting 1,024-dim vectors to keep pgvector index cost half that of native 4,096-dim, while still outperforming every competing model at 1,024 dims.

If local memory is genuinely constrained, **Qwen3-Embedding-4B** (MMTEB 69.45, Q4_K_M ~2.2GB) is a near-identical accuracy-per-cost alternative.

### Multimodal Slide Index: Keep Nemotron VL or Replace?

**Retain `nvidia/llama-nemotron-embed-vl-1b-v2` as the slide-image index for now**, but run an A/B test against `jina-embeddings-v4` (ViDoRe 90.17 multi-vector vs. Nemotron's 73.24 image+text Recall@5). Jina-v4's 17-point advantage on ViDoRe is striking, but the non-commercial Qwen Research License and API throttling make it unsuitable for production. `voyage-multimodal-3` (now legacy; succeed by voyage-multimodal-3.5) is a clean proprietary alternative with a free-tier for the initial re-embed, but its 1,024-dim fixed output and no multilingual benchmark make it a poor long-term choice. The recommended path: (a) keep Nemotron VL at $0/M on OpenRouter as production multimodal index, (b) run a single offline nDCG@5 evaluation of jina-v4 on the 199 slides to quantify the gap, (c) if gap > 10 nDCG points on our corpus, revisit once jina-v4 gets a permissive license or Nemotron ColEmbed V2 is publicly accessible.

### A/B Test Design

1. **Offline evaluation corpus**: manually annotate 80–120 (query, relevant-chunk) pairs drawn from actual student questions on the BRI610 corpus. Target 40 text-prose pairs (textbook pages) and 40 visual pairs (slide images). Include 20 purely Korean queries, 20 English, and 20 mixed bilingual.
2. **Metrics**: nDCG@5, Recall@5, MRR@10 per query set.
3. **Conditions**: (A) current Nemotron VL text-mode vs. (B) Qwen3-Embedding-8B Q4_K_M, both at cosine similarity with pgvector HNSW index.
4. **Statistical test**: paired Wilcoxon signed-rank test on nDCG@5 scores (n=80 pairs, α=0.05).
5. **Success threshold**: if Condition B achieves nDCG@5 ≥ Condition A + 0.03 (3 absolute points), migrate primary text index.

### Re-embedding Cost Estimate

| Scenario | Tokens (est.) | Cost |
|---|---|---|
| Qwen3-Embedding-8B (Ollama local) | 1,503 pages × ~800 tokens avg = ~1.2M | $0 |
| Nemotron VL re-embed slides (OpenRouter free) | 199 slides (image tokens) | $0 |
| voyage-multimodal-3 (free tier, new account) | 199 images < 150B pixel free tier | $0 |
| OpenAI text-embedding-3-large (if chosen) | 1.2M tokens × $0.13/M | ~$0.16 |
| Cohere embed-v4 (if chosen) | 1.2M tokens × $0.10/M | ~$0.12 |

**Total cost for the recommended migration (Qwen3-8B local + Nemotron VL free): $0.**

### Recommended pgvector Schema Change

To support a safe A/B migration without downtime:

```sql
-- Add new column alongside existing 2048-dim column
ALTER TABLE embeddings
  ADD COLUMN text_embedding_v2 vector(1024);  -- Qwen3 MRL at 1024

-- Populate v2 in batches (offline re-embed)
-- Once validated, drop v1:
-- ALTER TABLE embeddings DROP COLUMN text_embedding_v1;

-- New HNSW index on v2:
CREATE INDEX ON embeddings USING hnsw (text_embedding_v2 vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);
```

The dual-column approach (`text_embedding_v1 vector(2048)` + `text_embedding_v2 vector(1024)`) allows A/B queries to run simultaneously against the same corpus without dual-ingestion risk. The 1,024-dim Qwen3 MRL column uses 50% less storage per vector than the current 2,048-dim Nemotron column, and pgvector HNSW build time is roughly proportional to dim × n, so the index rebuilds approximately twice as fast.

---

*Report compiled April 2026. Benchmark data sourced from official model cards (Hugging Face), NVIDIA NIM documentation, Voyage AI blog, Jina AI model pages, MMTEB paper (arXiv:2502.13595), and Qwen3-Embedding technical report (arXiv:2506.05176). All scores reflect publicly available data at time of writing; where no public number exists, "no public benchmark" is stated explicitly.*
