# AI Tutor System Benchmark — BRI610 Use Case
**Version**: v0.5 | **Date**: 2026-04 | **Author**: BRI610 Tutor Project (SNU)

Scope: 8 commercial and research AI tutor systems evaluated for adoption into the BRI610 Computational Neuroscience tutor. Constraints: Korean+English bilingual, graduate-level biophysics (Hodgkin-Huxley, cable theory), equation-heavy, free-tier preferred, lecture slides and textbook already RAG-indexed.

---

## 1. Khanmigo (Khan Academy)

**URL/Paper**: https://www.khanmigo.ai/ | https://blog.khanacademy.org/khanmigo-math-computation-and-tutoring-updates/
**License/Cost**: Freemium — free for teachers (US and 180+ countries), $4/month or $44/year for learners; district contracts available at no per-student cost
**Latest version / date checked**: 2026-04 retrieval; Khanmigo math update with GPT-4o backbone, circa 2024-2025

### 1. 목적 (Stated purpose)
Khan Academy의 커리큘럼에 연동된 Socratic AI 과외 도우미로, 정답을 직접 제공하지 않고 질문을 통해 학생 스스로 개념을 발견하게 유도한다. 주요 타겟은 K-12 및 초등 수준 학습자이며 교사 도구로도 활용된다.

### 2. 핵심 설계 / 아키텍처 (Core architecture)
- **Backbone model(s)**: GPT-4 Omni (math tutoring); GPT-4 Turbo from prior to 2024 upgrade
- **Retrieval / RAG strategy**: Context injection — before each response, the system gathers human-written exercise text, hints, step-by-step solutions, and mastery data from the Khan Academy exercise graph; this is NOT a vector-retrieval RAG but a structured context-fetch from their own content database
- **Multi-agent? Single-prompt-system? State machine?**: Single-agent with structured system prompt; no explicit multi-agent orchestration publicly documented
- **Pedagogical pattern**: Socratic — the system is explicitly instructed to ask guiding questions rather than give direct answers; falls back to answers only if student persists
- **Personalization mechanism**: Khanmigo Interests feature reads chat history to identify student passions (e.g., sports, music) and incorporates them into analogies; mastery model from the Khan skill graph is injected as context, triggering prerequisite reviews when gaps are detected
- **Verification or factual grounding mechanism**: A calculator tool is called for numerical computation (instead of relying on LLM arithmetic); visual content is handled by pre-generated textual descriptions of graphics, not live vision. Human-generated exercise solutions are consulted before responding.

### 3. 강점 (Strengths)
1. **Khan curriculum integration**: Tightly coupled to a vetted, sequenced exercise bank; responses are grounded in human-authored hints and solutions, reducing hallucination risk for in-scope problems.
2. **Calculator tool use**: Explicit external calculator for arithmetic prevents the most embarrassing class of math LLM errors.
3. **Mastery-aware context**: Prerequisite skill gaps are detected from Khan's skill graph and surfaced in the conversation, giving structured remediation.
4. **Multi-language expansion**: As of 2025, available in Arabic, Chinese (simplified/traditional), Russian, Ukrainian, Urdu, Vietnamese, in addition to English, Spanish, Portuguese, Hindi.
5. **Teacher free tier + free for US school districts**: Extremely low barrier to deployment at institutional level; New Hampshire deployed statewide at no cost.

### 4. 약점 / 한계 (Weaknesses / known limitations)
1. **Socratic guardrail is weak**: Persistent student prompting causes Khanmigo to break Socratic discipline and provide complete answers. Reported by educator blogger Dan Meyer: "Khanmigo does not love students" — it lacks the resolve a human tutor has. Source: https://danmeyer.substack.com/p/khanmigo-wants-to-love-kids-but-doesnt
2. **Math accuracy remains unreliable outside the exercise bank**: Independent review at mamasmiles.com found incorrect answers in elementary math in the "Tutor me" mode (outside structured exercises). Source: https://www.mamasmiles.com/khanmigo-review/
3. **No vision input from student**: Students cannot upload handwritten work or diagrams for Khanmigo to respond to (as of the reviewed period); the system cannot "see" student work in real time.
4. **Engagement problem with disengaged students**: LinkedIn analysis by educator Richard Tong notes that Khanmigo is ineffective for the 95% of students who are "checked out" — the AI cannot manufacture motivation. Source: https://www.linkedin.com/pulse/khanmigo-great-ready-tutor-student-richard-tong
5. **No transparency reports**: Khan Academy does not publish accuracy benchmarks, response consistency data, or hallucination rates, making it impossible to audit reliability for STEM use. Source: https://aiflowreview.com/khanmigo-ai-review-2025/

### 5. 모방 가능성 (Imitability)
- **Open-source components**: None publicly available — system prompt, exercise DB, and mastery graph are proprietary
- **Cost to recreate locally**: 3/5 — the key insight (inject human-authored solution context before generating a Socratic response) is architecturally simple and reproducible with our own lecture/textbook RAG index. The difficulty is curating structured hint chains.
- **Specific things WE could borrow**:
  - The "gather exercise + hint + solution context BEFORE generating a response" pattern — we can replicate this by retrieving slide segments and textbook derivations from our existing RAG index before each tutor turn.
  - Separate calculator/SymPy tool call for equation evaluation — critical for HH/Cable equation checking.
  - Interest injection into system prompt based on conversation history.

### 6. BRI610 적합도 (Fit for our purpose) — 2/5
K-12 수준 설계. 대학원 수준의 biophysics, HH/Cable 방정식 미분 유도, 한국어 대응 모두 지원하지 않음. 핵심 아이디어(컨텍스트 우선 수집 + Socratic)는 차용 가능하나 시스템 자체는 BRI610에 직접 적용 불가.

### 7. 결론 (Verdict)
**PARTIAL-ADOPT** — Borrow the "context-first structured injection" pattern and external calculator tool call. Skip the platform itself.

---

## 2. Google LearnLM

**URL/Paper**: https://cloud.google.com/solutions/learnlm | https://blog.google/outreach-initiatives/education/google-gemini-learnlm-update/
**License/Cost**: Enterprise/freemium — LearnLM is embedded in Gemini 2.5 (accessible via Gemini app free tier); LearnLM API available via Google Cloud (pay-per-token); Gemini for Education institutional plans; Google One AI Premium at $19.99/month includes advanced features
**Latest version / date checked**: LearnLM fine-tuning infused into Gemini 2.5 Pro, announced Google I/O May 2025; 2026-04 retrieval

### 1. 목적 (Stated purpose)
학습과학(learning science)에 기반해 미세조정된 Gemini 계열 모델로, 단순 답변 제공이 아닌 능동적 학습을 촉진하는 교육 특화 AI다. 타겟은 K-12부터 고등교육까지 포괄하며, Google Classroom 생태계를 통해 교사가 커스텀 AI 튜터를 배포할 수 있다.

### 2. 핵심 설계 / 아키텍처 (Core architecture)
- **Backbone model(s)**: Gemini 2.5 Pro with LearnLM fine-tuning (as of Google I/O 2025); previously a separate LearnLM 1.5 Pro model available via API
- **Retrieval / RAG strategy**: None built-in at the model level; RAG is implemented at the application layer via NotebookLM integration or custom Gems with source documents. The base LearnLM model is fine-tuned for pedagogical behavior, not for retrieval.
- **Multi-agent? Single-prompt-system? State machine?**: Single model with fine-tuned pedagogical RLHF; teachers configure "Gems" (custom system prompts + persona) which are shared with students via Google Classroom — effectively a configurable single-agent setup
- **Pedagogical pattern**: Hybrid — five learning science principles: (1) active learning with practice/feedback, (2) cognitive load management (digestible chunks), (3) personalization, (4) curiosity stimulation, (5) metacognition prompting. Socratic elements present but not the sole mode.
- **Personalization mechanism**: Adapts explanation depth based on learner responses within a session; no persistent cross-session memory in the free tier; institutional deployments may leverage Workspace data
- **Verification or factual grounding mechanism**: Relies on Gemini's base knowledge + user-supplied documents in Gems; no native citation grounding at the LearnLM API level (unlike NotebookLM)

### 3. 강점 (Strengths)
1. **State-of-the-art benchmark performance**: In Google's May 2025 evaluation, Gemini 2.5 Pro outperformed Claude, GPT-4o, and OpenAI o3 across all five pedagogical principle categories rated by education experts.
2. **Google Classroom integration**: Teachers can create Gems, configure knowledge scope and persona, and deploy to an entire class via Classroom — zero student account setup overhead.
3. **Multimodal + math fluency**: Gemini 2.5 handles equations, diagrams, and mixed Korean/English naturally, unlike K-12-specific tutors.
4. **Quantified learning benefit**: Students receiving LearnLM chat-based math tutoring were 5.5 percentage points more likely to solve novel transfer problems than those tutored by humans alone (Google-internal study).
5. **API access**: LearnLM is accessible programmatically, enabling custom pipeline integration with our RAG system.

### 4. 약점 / 한계 (Weaknesses / known limitations)
1. **Evaluation is Google-conducted**: The 5.5 pp improvement claim comes from Google's own study. Independent replication is absent as of 2026-04. Source: https://blog.google/outreach-initiatives/education/google-gemini-learnlm-update/
2. **Pedagogy consistency is opaque**: Fine-tuning makes it hard to predict or control Socratic vs. direct-answer behavior; system prompt overrides may conflict with fine-tuned tendencies in unpredictable ways.
3. **No built-in citation grounding**: Without NotebookLM or a RAG layer, LearnLM can hallucinate citations or equations when departing from high-frequency training data (e.g., exotic HH gating formulas).
4. **Privacy/data concerns in educational settings**: Broader concerns about Google data use in schools are documented in PMC. Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC7972328/
5. **Human social-emotional nuance requires overlay**: The supervised tutoring literature (cited in LearnLM's own tech reports) notes that human facilitators were needed to manage pacing and emotional dynamics that the AI could not address. Source: https://publicservicesalliance.org/2025/05/25/ai-meets-education-discover-the-power-of-google-learnlm/

### 5. 모방 가능성 (Imitability)
- **Open-source components**: LearnLM fine-tuning weights are not public; however, the five pedagogical principles are fully documented and reproducible via system prompting with any capable model
- **Cost to recreate locally**: 2/5 — the pedagogical principles can be encoded into our Claude/GPT-4o system prompt; we cannot reproduce the RLHF fine-tuning, but structured prompting achieves ~80% of the behavioral effect
- **Specific things WE could borrow**:
  - The five-principle framework as a system prompt scaffold (active recall prompt → cognitive load chunking → curiosity hook → metacognitive reflection request)
  - Gem-style configurable persona: teacher creates one config per topic module (HH neurons, cable theory) and students access via shared link

### 6. BRI610 적합도 (Fit for our purpose) — 4/5
Gemini 2.5 Pro는 한국어, 수식, 멀티모달을 모두 처리하며 API 접근이 가능하다. 5가지 학습과학 원칙은 BRI610 수준에 적용 가능하다. 단, RAG 인덱스와의 연동은 별도 구현이 필요하며 비용이 발생한다.

### 7. 결론 (Verdict)
**PARTIAL-ADOPT** — Use LearnLM's five pedagogical principles as our system prompt backbone. Integrate Gemini 2.5 Pro via API as a fallback backbone alongside our primary model. Do not use Google Classroom Gems directly (no institutional account).

---

## 3. OpenAI ChatGPT Study Mode

**URL/Paper**: https://openai.com/index/chatgpt-study-mode/ | https://techcrunch.com/2025/07/29/openai-launches-study-mode-in-chatgpt/
**License/Cost**: Free tier (all logged-in users); Plus/Pro/Team at existing subscription prices ($20–$200/month); Edu plan for institutions
**Latest version / date checked**: Released July 29, 2025; 2026-04 retrieval via Appscribed and EdWeek coverage

### 1. 목적 (Stated purpose)
ChatGPT에 내장된 학습 모드로, 정답 직접 제공 대신 Socratic 질문과 단계별 힌트를 통해 학습자 스스로 개념을 구성하게 유도한다. 타겟은 고등학생~대학생이며 시험 준비, 숙제 보조, 새 주제 학습에 특화되어 있다.

### 2. 핵심 설계 / 아키텍처 (Core architecture)
- **Backbone model(s)**: Not publicly specified; inferred to use GPT-4o or a GPT-4o variant with a Study Mode system prompt layer
- **Retrieval / RAG strategy**: No built-in RAG; relies on the model's parametric knowledge + user-supplied context in the conversation window; memory from previous chats can be injected if enabled
- **Multi-agent? Single-prompt-system? State machine?**: Single-prompt-system — Study Mode is activated by selecting "Study and learn" from the tools menu, which applies a different system prompt configuration to the same underlying model
- **Pedagogical pattern**: Socratic + Scaffolded — asks calibrating questions first, delivers content in small chunks ("starts with the basics and gets more complex"), uses hints and self-reflection prompts before providing answers; built with cognitive scientists and pedagogy experts
- **Personalization mechanism**: ChatGPT memory (if enabled) injects prior conversation history; skill-level calibration happens within each session via initial guiding questions that assess background; no persistent skill graph
- **Verification or factual grounding mechanism**: None beyond the base GPT-4o parametric knowledge; no external retrieval or citation. Students can upload documents into the chat, but Study Mode does not implement a dedicated RAG pipeline.

### 3. 강점 (Strengths)
1. **Zero-friction access**: Available to all logged-in users on Free tier; no institutional agreement needed. A PhD student can use it immediately.
2. **Memory integration**: Prior chat history (via ChatGPT memory) allows the tutor to recall the student's prior misconceptions and build on them across sessions.
3. **Broad STEM coverage**: GPT-4o handles mathematical derivations, LaTeX, and mixed-language queries (Korean+English) competently out of the box.
4. **Designed with domain experts**: Built in collaboration with teachers, cognitive scientists, and pedagogy experts, aligning with established scaffolding literature.
5. **Flexible mode switching**: Users can toggle to normal mode when they need a direct answer — pragmatically useful for quick reference lookups.

### 4. 약점 / 한계 (Weaknesses / known limitations)
1. **No enforcement mechanism**: Students can trivially bypass Study Mode by switching to normal ChatGPT. OpenAI's VP confirmed there are no parental or admin lock-in controls. Source: https://techcrunch.com/2025/07/29/openai-launches-study-mode-in-chatgpt/
2. **No RAG grounding to course materials**: Responses draw on parametric knowledge; for niche topics (e.g., specific HH parameter sets from our textbook), hallucination risk is non-trivial.
3. **Architecture is a black box**: The system prompt driving Study Mode is not published; pedagogical behavior cannot be audited, modified, or customized for graduate-level biophysics.
4. **No skill graph or mastery model**: Each session starts cold (unless memory is enabled); there is no structured representation of what the student knows.
5. **Equation hallucination risk**: Unlike Khanmigo's external calculator, Study Mode has no tool calls for symbolic math verification. For complex HH/Cable derivations, step-level errors may go unchecked. Source: https://www.insidehighered.com/news/tech-innovation/artificial-intelligence/2025/08/07/understanding-value-learning-fuels-chatgpts-study-mode

### 5. 모방 가능성 (Imitability)
- **Open-source components**: System prompt not public; but the described behavior (calibrating questions → chunked scaffolding → hints before answers → reflection prompts) is fully reproducible
- **Cost to recreate locally**: 1/5 — this is precisely what a well-engineered system prompt does. The entire Study Mode pattern can be replicated in our tutor with a careful prompt template.
- **Specific things WE could borrow**:
  - The "calibrate first" pattern: open each session with 2-3 diagnostic questions before delivering any content
  - Progressive chunk delivery: enforce a rule that each tutor turn delivers at most one concept chunk, then asks a check question
  - Reflect-before-answer gate: if student asks a direct question, respond with a hint + "what do you think happens next?" before giving the full derivation

### 6. BRI610 적합도 (Fit for our purpose) — 3/5
즉시 사용 가능하고 한국어, 수식 처리 모두 양호하나, RAG 연동 없고 커스터마이징 불가라는 점이 결정적 한계다. 우리 시스템이 이미 RAG 인덱스를 보유하고 있으므로, Study Mode의 설계 패턴을 자체 시스템에 구현하는 것이 더 낫다.

### 7. 결론 (Verdict)
**PARTIAL-ADOPT** — Copy the "calibrate → chunk → hint → reflect" session pattern into our system prompt. Do not use the platform directly (no course-grounding, no customization).

---

## 4. Google NotebookLM

**URL/Paper**: https://notebooklm.google/ | https://arxiv.org/abs/2504.09720 (peer evaluation as physics tutor)
**License/Cost**: Free tier available; NotebookLM Plus at $19.99/month (included in Google One AI Premium); NotebookLM Enterprise via Google Cloud (custom pricing)
**Latest version / date checked**: Powered by Gemini 3 (from December 2025); integrated into Gemini app April 9, 2026; 2026-04 retrieval

### 1. 목적 (Stated purpose)
사용자가 업로드한 문서에만 근거하여 응답하는 소스 기반 AI 리서치 도구로, 교육 맥락에서는 교사가 커스텀 지식 베이스를 구성하고 학생이 Socratic 문답을 통해 학습하는 튜터로 배포할 수 있다. 타겟은 연구자, 교수자, 대학원생이다.

### 2. 핵심 설계 / 아키텍처 (Core architecture)
- **Backbone model(s)**: Gemini 3 (December 2025 onward); previously Gemini 1.5 Pro
- **Retrieval / RAG strategy**: Source grounding (Google's term for closed RAG) — uploaded documents are converted to vector embeddings; queries retrieve semantically similar chunks and pass them to Gemini with explicit citation requirements. Google engineers deliberately avoided the term "RAG" internally (per North Denver Tribune report), emphasizing that responses must only draw from uploaded sources.
- **Multi-agent? Single-prompt-system? State machine?**: Single-agent with configurable "Training Manual" document that defines persona, conversational strategy, and pedagogical constraints (effectively a structured system prompt embedded as a source document). No code-level multi-agent framework.
- **Pedagogical pattern**: Configurable — default is question-answering; a teacher can configure Socratic behavior by including a pedagogical instruction document as a source. The physics tutor paper (arXiv 2504.09720) demonstrated Socratic questioning is achievable via this configuration.
- **Personalization mechanism**: None persistent; each notebook session starts without student history. Personalization is structural (teacher selects sources per module) not adaptive (no student model).
- **Verification or factual grounding mechanism**: Every response is traceable to a specific source chunk with inline citation markers; this is the system's primary anti-hallucination mechanism. Responses without source support are explicitly flagged.

### 3. 강점 (Strengths)
1. **Closed RAG = strong source fidelity**: Responses cannot stray beyond uploaded documents; for our lecture slides + textbook, this means HH equations and cable theory derivations are drawn only from verified course materials.
2. **Teacher-configurable without code**: A Training Manual document (plain text) defines the tutor's persona, Socratic strategy, and prohibited behaviors — no programming required.
3. **NotebookLM Plus shareable link**: Teachers can share a "chat-only" interface with students (no source access) — closest available analog to our own BRI610 tutor deployment model.
4. **Audio/Video Overviews**: Auto-generated podcast-style summaries of uploaded sources in 80+ languages, useful for passive review. Korean is supported.
5. **Deep Research integration**: As of 2026, can query Google Scholar for supporting literature, useful for graduate-level topics.

### 4. 약점 / 한계 (Weaknesses / known limitations)
1. **Source cap**: 50 sources per notebook; individual source ~500K word limit. A 1,300-page textbook may need to be split across multiple notebooks, breaking cross-chapter retrieval. Source: https://www.atlasworkspace.ai/blog/notebooklm-limitations
2. **No cross-notebook memory**: Notebooks are isolated; a student cannot have a persistent knowledge state across multiple topic-specific notebooks. Source: https://www.xda-developers.com/notebooklm-limitations/
3. **Socratic tension**: Physics tutor evaluation (arXiv 2504.09720) found "some participants became frustrated when the tutor repeatedly withheld a direct solution after several attempts" — students abandoned the tool for unconstrained ChatGPT. This is the fundamental tension of enforced Socratic style.
4. **Age restriction + no institutional auth**: Limited to users 18+ (as of June 2025). No native LMS integration; sharing is via link only, not via a class roster system.
5. **Equation rendering**: NotebookLM outputs plaintext; LaTeX or MathML rendering is not natively supported in the chat interface, which is a significant limitation for equation-heavy courses like BRI610. Source: reviewer reports on g2.com.

### 5. 모방 가능성 (Imitability)
- **Open-source components**: None; Gemini 3 and the embedding pipeline are proprietary. However, the Training Manual approach (embed pedagogical instructions as a source document) is a design pattern we can replicate.
- **Cost to recreate locally**: 2/5 — we already have a Chroma/pgvector RAG index over our lecture slides and textbook. Adding a "Training Manual" source document and citation-enforcement in the system prompt reproduces the core NotebookLM value.
- **Specific things WE could borrow**:
  - The "Training Manual as source document" pattern: write a BRI610-specific pedagogical guide and embed it in our RAG index as a high-priority, always-retrieved document
  - Closed-source enforcement: system prompt instruction to cite slide/textbook chunk ID in every factual claim
  - Shareable read-only chat interface (we already have this via our web deploy)

### 6. BRI610 적합도 (Fit for our purpose) — 4/5
현재 사용 가능한 시스템 중 우리 아키텍처(RAG 인덱스 + 소스 기반 응답)와 가장 유사하다. LaTeX 렌더링 부재와 소스 캡이 주요 제한이나, 설계 패턴은 직접 차용 가능하다.

### 7. 결론 (Verdict)
**PARTIAL-ADOPT** — Replicate the closed-source-grounding + Training Manual pattern in our own pipeline. Consider using NotebookLM as a rapid prototype fallback for topic modules not yet indexed.

---

## 5. KELE (Multi-Agent Socratic Framework)

**URL/Paper**: https://aclanthology.org/2025.findings-emnlp.888/ (Findings of EMNLP 2025)
**License/Cost**: Research paper; SocratTeachLLM model not publicly released as of 2026-04; code/dataset availability not confirmed
**Latest version / date checked**: EMNLP 2025 Findings publication; 2026-04 retrieval

### 1. 목적 (Stated purpose)
Socratic 교수법을 대규모로 자동화하기 위한 멀티 에이전트 LLM 프레임워크로, 계획(planning)과 실행(execution)을 분리된 에이전트가 담당한다. 타겟은 교사의 전문성과 실시간 피드백 역량에 대한 의존도를 줄이려는 교육 AI 연구자 및 기관이다.

### 2. 핵심 설계 / 아키텍처 (Core architecture)
- **Backbone model(s)**: Base LLM not specified in the ACL Anthology abstract; SocratTeachLLM is a fine-tuned model trained on SocratDataset; the consultaent agent and teacher agent may use different models
- **Retrieval / RAG strategy**: Not described — the framework focuses on dialogue structure rather than document retrieval; knowledge is assumed to be in the LLM's weights or provided in context
- **Multi-agent? Single-prompt-system? State machine?**: **Multi-agent** — "consultant–teacher" two-agent system: the Consultant agent handles *teaching planning* (selecting which Socratic strategy to apply), the Teacher agent handles *execution* (generating the actual student-facing dialogue turn)
- **Pedagogical pattern**: **Socratic** — built on a formalized SocRule system encoding 34 Socratic teaching strategies; ensures "logically coherent and hierarchically structured" Socratic dialogue rather than ad-hoc questioning
- **Personalization mechanism**: Not described in available documentation; the framework is strategy-selection focused, not student-model focused
- **Verification or factual grounding mechanism**: Not described; no RAG or tool use mentioned

### 3. 강점 (Strengths)
1. **Principled Socratic formalization**: SocRule encodes 34 distinct teaching strategies with explicit rules — the first systematic attempt to operationalize Socratic method computationally beyond ad-hoc prompting.
2. **Separation of planning and execution**: The consultant-teacher split allows the planning agent to select the pedagogically optimal strategy without contaminating the student-facing turn with meta-reasoning.
3. **SocratDataset**: 42,000+ dialogue turns covering 34 strategies — a large, structured training corpus that could be used for fine-tuning our own model if released.
4. **Outperforms GPT-4o on all 9 Socratic dimensions**: Despite smaller parameter count, SocratTeachLLM beats GPT-4o across all evaluation dimensions — demonstrates that task-specific fine-tuning is more efficient than scale alone.
5. **Comprehensive evaluation framework**: 9-dimensional evaluation covering both single-turn and multi-turn pedagogical quality — provides a reusable benchmark methodology.

### 4. 약점 / 한계 (Weaknesses / known limitations)
1. **No public release**: As of 2026-04, no model weights, code, or dataset are confirmed publicly available. The paper is in ACL Anthology but reproducibility is unclear. Source: https://aclanthology.org/2025.findings-emnlp.888/
2. **No RAG integration**: The framework assumes knowledge is in the model; for domain-specific courses like BRI610 with specialized textbooks, this is a fundamental gap.
3. **No personalization**: SocRule governs strategy selection but there is no student knowledge model or adaptive difficulty. The framework is pedagogically rigid.
4. **Evaluation is paper-internal**: The 9-dimension evaluation framework was designed by the same team; no independent third-party validation cited in available materials.
5. **Domain scope unknown**: All examples in the paper involve general or CS concepts; applicability to mathematical biophysics derivations (HH equations) is untested.

### 5. 모방 가능성 (Imitability)
- **Open-source components**: SocRule framework (conceptually reproducible from paper description); SocratDataset (not confirmed released); SocratTeachLLM (not confirmed released)
- **Cost to recreate locally**: 3/5 — the two-agent planning+execution pattern is architecturally reproducible using any two LLM calls; implementing SocRule from the paper description requires reverse-engineering the 34 strategies from the text
- **Specific things WE could borrow**:
  - The **consultant-teacher agent split**: implement a "strategy selector" agent that picks from a BRI610-specific set of Socratic moves (analogy, counterexample, derivation prompt, prerequisite check) before the student-facing agent generates its response
  - The **9-dimension evaluation framework**: adapt these dimensions to evaluate our own tutor outputs

### 6. BRI610 적합도 (Fit for our purpose) — 3/5
설계 패턴은 우수하나 구현체가 미공개이고 RAG 없음. 멀티 에이전트 Socratic 전략 선택 패턴은 우리 시스템에 직접 구현할 가치가 있다.

### 7. 결론 (Verdict)
**PARTIAL-ADOPT** — Implement the consultant-teacher agent split pattern and a BRI610-specific strategy taxonomy. Do not wait for code release; reconstruct from paper.

---

## 6. SocratiAI / SocratiQ

**URL/Paper**: SocraticAI: https://arxiv.org/abs/2512.03501 | SocratiQ: https://arxiv.org/abs/2502.00341
**License/Cost**: Research prototypes; no commercial licensing; SocratiQ lives at https://socratiq.ai/ (Harvard-affiliated, no pricing listed); SocraticAI is a course deployment at Ashoka University
**Latest version / date checked**: SocraticAI arXiv December 2025; SocratiQ arXiv February 2025; 2026-04 retrieval

### 1. 목적 (Stated purpose)
SocraticAI는 학부 CS 과목에서 LLM을 Socratic 스캐폴드로 제한하는 단일 에이전트 튜터 시스템이고, SocratiQ는 Harvard ML Systems 교재(MLSysBook.ai)에 내장된 온라인 학습 동반자로 개인화된 학습 경로와 퀴즈를 제공한다. 둘 다 타겟은 STEM 학부~대학원생이다.

### 2. 핵심 설계 / 아키텍처 (Core architecture)
- **Backbone model(s)**: SocraticAI — not specified (any LLM via API); SocratiQ — Groq-hosted open-source models (Mixtral-8x7b, Gemma 7b, LLaMA 3.2) as primary; Google Gemini as fallback; GPT-4 tested but too expensive
- **Retrieval / RAG strategy**:
  - SocraticAI: RAG pipeline grounding responses in course lectures, assignments, and textbook excerpts via semantic indexing; Redis for session storage
  - SocratiQ: Custom "bounded learning" algorithm — paragraph fingerprinting (ASCII hash) + binary search + chunked Levenshtein distance ranking returns top-k relevant paragraphs; bounds LLM to textbook content only; 5,000-token budget enforced via Word Co-Occurrence Matrix vectorization
- **Multi-agent? Single-prompt-system? State machine?**: Both are single-agent; SocraticAI uses a modular service-oriented architecture (auth, feedback, admin dashboard, vector retrieval as separate services); SocratiQ is a JavaScript client-side app with Azure Functions serverless backend
- **Pedagogical pattern**:
  - SocraticAI: Socratic — enforces think-articulate-reflect loop; students must submit current understanding + attempted solutions before receiving feedback; few-shot Socratic exemplars in system prompt
  - SocratiQ: Hybrid — Socratic questioning for conceptual content + Bloom's Taxonomy-aligned adaptive quiz generation across 4 difficulty levels; gamified with streaks, badges, engagement heatmap
- **Personalization mechanism**:
  - SocraticAI: Daily 8-query limit per student; multi-stage prompt structure enforcing structured input; Prometheus monitoring of query volume and reflection quality
  - SocratiQ: Knowledge graph tracking section engagement + quiz performance; 4-level difficulty slider (Beginner/Intermediate/Advanced/Expert); IndexedDB for local preference storage; question caching after 10 quizzes per section
- **Verification or factual grounding mechanism**:
  - SocraticAI: RAG grounding to course materials; input sanitization against injection attacks; context management for long conversations
  - SocratiQ: Bounded retrieval (responses cannot draw on knowledge outside textbook chunks); cryptographic PDF hashing for student progress integrity

### 3. 강점 (Strengths)
1. **SocratiQ's bounded retrieval is architecturally elegant**: The fingerprint+Levenshtein algorithm is lightweight, entirely deterministic, and prevents hallucination by construction — no vector DB overhead.
2. **SocraticAI's guardrail design**: Daily query limits + structured input requirement (current understanding + attempted solution) forces deliberate engagement; 75% of students produced substantive reflections within 3 weeks.
3. **SocratiQ's extreme cost efficiency**: Full semester deployment (16 weeks, 20 students) costs $15–$21 with Mixtral-8x7b, vs $400+ with GPT-4. This is a practical blueprint for low-budget academic deployment.
4. **SocratiQ's Bloom's Taxonomy quiz generation**: Expert-level questions require synthesis and optimization reasoning — directly applicable to exam prep for HH derivation and cable equation analysis.
5. **Both systems are open research**: Architecture described in sufficient detail to reproduce; SocratiQ's algorithm pseudocode is published in the paper.

### 4. 약점 / 한계 (Weaknesses / known limitations)
1. **SocratiQ evaluated on only 5 students**: Generalizability claims are extremely weak. Source: https://arxiv.org/abs/2502.00341
2. **SocratiQ question distribution skewed low**: 42% of generated questions are "Remembering" level; only 5% "Evaluating" and 2% "Creating" — insufficient for graduate-level exam prep. Source: https://arxiv.org/abs/2502.00341
3. **SocraticAI prompt circumvention**: A subset of students found ways to reformulate prohibited direct-answer requests despite guardrails. Source: https://arxiv.org/abs/2512.03501
4. **No equation verification**: Neither system has a symbolic math tool; for derivation tasks (e.g., HH gating equation derivation), a student receiving an incorrect intermediate step has no recourse.
5. **SocratiQ's conversation context limitation**: Identified as a known limitation — multi-turn context retention degrades for extended derivation walkthroughs; the 5,000-token budget can truncate long algebraic discussions. Source: https://arxiv.org/abs/2502.00341

### 5. 모방 가능성 (Imitability)
- **Open-source components**: SocratiQ Algorithm 1 (bounded retrieval), Algorithm 2 (token management), full system architecture in paper; SocraticAI service architecture and guardrail design described in paper
- **Cost to recreate locally**: 1/5 (SocratiQ pattern) / 2/5 (SocraticAI pattern) — SocratiQ's bounded retrieval can be implemented in a few hundred lines of Python; SocraticAI's modular architecture mirrors our current stack
- **Specific things WE could borrow**:
  - SocraticAI's **structured input gate**: require students to submit "current understanding + what I've tried" before receiving any tutor response — directly adaptable to our BRI610 chat interface
  - SocratiQ's **Bloom's Taxonomy quiz generation**: generate per-section quizzes at Expert level specifically for BRI610 exam prep (HH parameter sensitivity, cable theory boundary conditions)
  - SocratiQ's **engagement heatmap + streak system**: lightweight gamification for PhD student motivation
  - SocraticAI's **Prometheus monitoring**: query volume, reflection quality metrics for instructor dashboard

### 6. BRI610 적합도 (Fit for our purpose) — 4/5
두 시스템 모두 우리의 기술 스택(RAG + LLM + 웹 인터페이스)과 정확히 일치하는 아키텍처다. SocratiQ의 비용 효율성과 Bloom's Taxonomy 퀴즈, SocraticAI의 구조화된 입력 게이트는 BRI610에 즉시 적용 가능하다. 수식 검증 부재가 유일한 결정적 한계.

### 7. 결론 (Verdict)
**ADOPT** — Implement SocraticAI's structured input gate + SocratiQ's Bloom's Taxonomy quiz generation as the two primary interaction patterns. Add SymPy tool call for equation verification to address the shared weakness.

---

## 7. Synthesis Tutor

**URL/Paper**: https://www.synthesis.com/tutor | https://www.unite.ai/synthesis-tutor-review/
**License/Cost**: Paid subscription (7-day free trial; monthly/annual plans, specific pricing not published on site); no free tier
**Latest version / date checked**: Synthesis Tutor 2.0 announced 2025 (private beta rollout); 2026-04 retrieval

### 1. 목적 (Stated purpose)
K-5(5-11세) 수학 커리큘럼을 위한 AI 기반 적응형 수학 튜터로, 정답 여부가 아닌 사고 과정을 추적하여 난이도를 실시간 조정한다. SpaceX 실험학교 Ad Astra에서 출발한 Josh Dahn이 창업했으며, 타겟은 초등학생과 학부모다.

### 2. 핵심 설계 / 아키텍처 (Core architecture)
- **Backbone model(s)**: Not publicly disclosed; described as a "hybrid AI system" in Tutor 2.0 announcement; the "omnipresent" routing component suggests an orchestration layer above LLM inference
- **Retrieval / RAG strategy**: None — the system is curriculum-sequenced, not document-retrieval-based; content is pre-authored and structured as a K-5 math progression
- **Multi-agent? Single-prompt-system? State machine?**: Tutor 2.0 describes an "omnipresent, hybrid AI system" that guides routing decisions and creates seamless transitions between topics — suggesting a **state machine or workflow orchestrator** above a single LLM, though technical details are not public
- **Pedagogical pattern**: **Adaptive branching** — the system infers the student's current level quickly and adjusts difficulty in real time; uses back-and-forth dialogue, asks questions, and responds to answers (unlike static worksheet digitization). Gamified with Playground (exploration) and Arcade (competition) modes.
- **Personalization mechanism**: Real-time difficulty adjustment based on response patterns; progress bars per topic; mastery-gated advancement through the K-5 curriculum sequence; no cross-session memory beyond curriculum progress tracking
- **Verification or factual grounding mechanism**: Pre-authored content limits hallucination risk; the system operates within a bounded curriculum graph rather than open-ended LLM generation

### 3. 강점 (Strengths)
1. **Adaptive difficulty without student frustration**: The system finds the zone of proximal development quickly (per unit tests reviews) — "figures out a student's level quickly and pushes them slightly beyond their comfort zone without overwhelming them."
2. **Gamification done right**: Two-mode game design (low-stakes exploration vs. high-stakes competitive) addresses different motivational states, reducing the burnout associated with single-mode drill apps.
3. **Routing orchestrator in Tutor 2.0**: The hybrid routing layer signals architectural maturity — topic transitions and pacing are managed algorithmically, not just by the LLM, which is more reliable for curriculum adherence.
4. **Research pedigree**: Claims average student outperforms 99.99% of classroom-taught peers, citing DARPA research lineage (basis not independently verified but consistent with spaced practice literature).
5. **State deployment**: Oklahoma adopted Synthesis Tutor for statewide math improvement initiative (2025), indicating institutional trust.

### 4. 약점 / 한계 (Weaknesses / known limitations)
1. **Age and scope mismatch**: Designed for ages 5-11 (K-5 math only). No content above grade 5. Entirely irrelevant to BRI610 level. Source: https://www.unite.ai/synthesis-tutor-review/
2. **No open architecture**: Backbone model, routing algorithm, and curriculum graph are completely proprietary; nothing to adapt.
3. **Cannot replicate real tutor responsiveness**: Reviews note the system "may feel scripted or repetitive" and "insufficient challenge for advanced learners." Source: https://www.unite.ai/synthesis-tutor-review/
4. **No free tier**: Unlike Khanmigo or ChatGPT Study Mode, there is no free access path for individual students.
5. **Technical architecture opaque**: Tutor 2.0 was described only in a TikTok/LinkedIn announcement — no white paper, no technical documentation, no published evaluation. Source: https://www.tiktok.com/@synthesisschool/video/7463155510875835694

### 5. 모방 가능성 (Imitability)
- **Open-source components**: None
- **Cost to recreate locally**: 5/5 — we would need to build the full curriculum graph, routing orchestrator, and gamification system from scratch with zero reference implementation
- **Specific things WE could borrow**:
  - The **two-mode gamification philosophy** (low-stakes exploration vs. high-stakes exam prep) — apply to BRI610 as "Walkthrough mode" vs. "Exam mode"
  - The **routing orchestrator concept**: a module-level router that decides whether to offer a conceptual walkthrough, a derivation challenge, or a prerequisite review based on student state

### 6. BRI610 적합도 (Fit for our purpose) — 1/5
초등 수학 전용 유료 시스템. 대학원 biophysics와 완전히 무관. 아키텍처 참고 가치는 라우팅 패턴 아이디어 1개로 한정.

### 7. 결론 (Verdict)
**REJECT** — Wrong domain, wrong level, proprietary, no free tier. Borrow only the two-mode gamification philosophy as a design concept.

---

## 8. Duolingo Max

**URL/Paper**: https://blog.duolingo.com/duolingo-max/ | https://openai.com/index/duolingo/ (OpenAI case study)
**License/Cost**: Premium subscription tier — $168/year (~$14/month); Explain My Answer feature moved to free tier (January 2026); Roleplay and Video Call remain Max-only
**Latest version / date checked**: 2026-04 retrieval; Video Call feature added 2025; Explain My Answer free since January 2026

### 1. 목적 (Stated purpose)
GPT-4 기반의 생성형 AI를 Duolingo 언어 학습 앱에 통합하여, 고정된 연습 문제를 넘어 자유 대화 Roleplay와 오답 맥락별 설명(Explain My Answer)을 제공한다. 타겟은 실용 회화 능력 향상을 원하는 언어 학습자(성인)이다.

### 2. 핵심 설계 / 아키텍처 (Core architecture)
- **Backbone model(s)**: GPT-4 (OpenAI API) for Roleplay and Explain My Answer; Birdbrain — Duolingo's internal Llama-based LLM — for adaptive lesson generation and learner data analysis
- **Retrieval / RAG strategy**: None for user-facing AI features; Birdbrain generates lessons from learner performance data + expert-authored templates; GPT-4 Roleplay has no RAG — conversations are open-ended within the target language
- **Multi-agent? Single-prompt-system? State machine?**: Two-model system: Birdbrain (curriculum routing, lesson generation, spaced repetition scheduling) + GPT-4 (open conversation). These operate in separate contexts, not as coordinated agents.
- **Pedagogical pattern**: **Hybrid** — spaced repetition + gamified drill (core Duolingo) + open Socratic roleplay (Max). Explain My Answer provides post-hoc, contextual explanations rather than Socratic pre-guidance.
- **Personalization mechanism**: CEFR-level tracking across lessons; Birdbrain dynamically generates next lesson content based on error patterns and retention curves; Video Call character (Lily) "remembers" prior conversation topics within a session context
- **Verification or factual grounding mechanism**: Safety guardrails via prompt engineering and human review loops on GPT-4 outputs; CEFR alignment checked by Birdbrain; no factual grounding for open Roleplay (intentional — conversational fluency is the goal)

### 3. 강점 (Strengths)
1. **Roleplay engagement**: Users who engaged with Roleplay completed 3x more conversations and 78% reported better real-world conversational readiness (internal Duolingo survey). Demonstrates that open-ended AI conversation significantly boosts engagement over structured drills.
2. **Post-hoc contextual explanation**: Explain My Answer provides natural-language breakdowns of why a specific answer was marked wrong in context — a more effective correction mechanism than binary correct/incorrect.
3. **Two-model architecture insight**: Separating curriculum management (Birdbrain/Llama) from open conversation (GPT-4) is architecturally clean — each model does what it does best.
4. **Spaced repetition integration**: Birdbrain's scheduling is grounded in cognitive science retention literature, driving long-term retention beyond single-session performance.
5. **Scale of deployment**: Millions of daily users provide enormous behavioral data for iterative improvement; the CEFR tracking is a mature, standardized learner model.

### 4. 약점 / 한계 (Weaknesses / known limitations)
1. **Scripted conversation depth**: Roleplay conversations "end quickly" and can feel scripted; the AI cannot sustain open-ended multi-turn technical dialogue. Source: https://duoplanet.com/duolingo-max-review/
2. **Translation-centric pedagogy**: The core Duolingo exercise engine (tap-to-translate, multiple choice, word matching) trains translation skill, not production or reasoning — a pedagogical mismatch for science comprehension tasks. Source: https://blog.thelinguist.com/duolingo-review/
3. **AI answer marking errors**: Users report GPT-4 marks correct answers as wrong, wasting hearts. Source: https://duoplanet.com/duolingo-max-review/
4. **Language-limited**: Max features available only for Spanish, French, German, Italian, Portuguese, Japanese, Korean for English speakers — the Korean tutor use case is partially supported but the system is language-learning, not science-tutoring.
5. **No knowledge grounding**: For language learning this is fine; for STEM tutoring, GPT-4 without RAG means no connection to course materials. Entire architecture is domain-specific to language and inapplicable to biophysics. Source: https://copycatcafe.com/blog/duolingo-max

### 5. 모방 가능성 (Imitability)
- **Open-source components**: Birdbrain (Llama-based, not released); GPT-4 integration pattern is well-documented in OpenAI case study; spaced repetition algorithm is standard (SM-2 or derivative)
- **Cost to recreate locally**: 3/5 — the two-model split (routing LLM + conversation LLM) is reproducible; spaced repetition is open source; the hard part is the massive learner dataset Birdbrain was trained on
- **Specific things WE could borrow**:
  - **Post-hoc contextual explanation pattern**: after a student submits a derivation step, if it contains an error, generate a natural-language explanation of *why that specific error occurred* (not a generic hint) — this is the "Explain My Answer" transplanted to biophysics
  - **Two-model architecture**: separate a "what topic/mode to enter" router from the actual tutor LLM

### 6. BRI610 적합도 (Fit for our purpose) — 1/5
언어 학습 전용 설계. biophysics 교수법과 근본적으로 다른 목적. 단, Post-hoc 맥락별 오류 설명 패턴은 우리 채점 모드에 직접 차용 가능.

### 7. 결론 (Verdict)
**REJECT** (platform) / **PARTIAL-ADOPT** (one pattern) — The platform is irrelevant to BRI610. Borrow only the "Explain My Answer" post-hoc error explanation pattern for our derivation feedback mode.

---

## 통합 종합 분석 (Integrated Synthesis)

### 워크스루 모드 설계에 가장 적합한 2개 시스템

**1위: KELE (EMNLP 2025)** — The consultant-teacher agent split is the most architecturally principled framework for a walkthrough mode. The Consultant selects which Socratic move to apply (analogy, prerequisite check, counterexample, derivation prompt) before the Teacher agent generates the student-facing turn. This decoupling is the key missing piece in our current single-prompt design. The SocRule taxonomy of 34 strategies provides a concrete menu we can reduce to a BRI610-specific set (~8 strategies covering HH derivation, channel gating intuition, cable theory boundary conditions, and dimensional analysis). Even without the released code, this pattern is fully implementable with two LLM calls.

**2위: SocraticAI + SocratiQ (joint)** — Treated as a pair because they are complementary: SocraticAI provides the interaction gate design (structured input enforcement: "state your current understanding + what you tried"), and SocratiQ provides the bounded RAG pattern (deterministic fingerprint retrieval keeps responses within course materials) and the knowledge-graph-based quiz generation. Together they form a complete walkthrough mode pipeline: structured input → bounded retrieval → Socratic response → Bloom's Taxonomy comprehension check.

### 시험 준비 + 유도 훈련(derivation training) 사용 사례에 가장 적합한 1개 시스템

**SocratiQ** — The Bloom's Taxonomy expert-level question generation is the only system in this benchmark explicitly designed to produce synthesis and optimization-level questions from course materials, which is precisely what exam prep for HH derivation and cable equation analysis requires. The 4-level difficulty progression (Beginner through Expert) maps directly onto BRI610's pedagogical arc from intuition building to formal derivation. The bounded retrieval ensures questions are grounded in our actual lecture materials rather than generic textbook content. The $15–21/semester cost for 20 students is a practical reference point.

### 반드시 복사해야 할 설계 패턴 Top 3

**Pattern 1 — Consultant-Teacher Agent Split (from KELE)**
Before generating a student-facing response, run a "strategy selector" agent that receives the student's input, the conversation history, and a BRI610-specific taxonomy of Socratic moves, and outputs a structured strategy tag (e.g., `{move: "prerequisite_check", target: "Nernst equation"}` or `{move: "derivation_prompt", step: 3}`). The teacher agent then generates the response constrained to execute that strategy. This prevents the single-agent Socratic collapse where the model drifts from questioning into lecturing.

**Pattern 2 — Structured Input Gate (from SocraticAI)**
Require the student to submit a structured input before receiving any tutor response: `(a) what I currently understand, (b) what I have tried, (c) where I am stuck`. Implement this as a form overlay or prompt template. The 75% substantive reflection rate at Ashoka University demonstrates this is achievable in 2-3 weeks. For BRI610, adapt to: `(a) which equation/concept, (b) derivation step attempted, (c) specific confusion`. This is the single highest-leverage change to prevent the pattern of students using the tutor as a copy-paste answer engine.

**Pattern 3 — Post-hoc Contextual Error Explanation (from Duolingo's Explain My Answer)**
When a student submits a derivation step or equation and it is incorrect, do not generate a generic hint. Generate an explanation of *why that specific error occurred*: identify the mathematical/conceptual error, name the underlying misconception (e.g., "You treated the membrane conductance as voltage-independent here, but in the HH model gK is a function of V via the n gating variable"), and suggest one targeted question to probe the gap. This requires a two-step pipeline: (1) check the student answer against the solution RAG chunk, (2) if incorrect, generate a contextualized diagnosis. This is more cognitively useful than Socratic withholding alone.

### 절대 복사하면 안 되는 안티패턴 Top 2

**Anti-pattern 1 — Socratic withholding without an exit ramp (NotebookLM / Khanmigo)**
Both NotebookLM (arXiv 2504.09720, physics tutor evaluation) and Khanmigo (Dan Meyer's critique) demonstrate the same failure mode: persistent refusal to provide direct answers causes student frustration and abandonment of the tool in favor of unconstrained ChatGPT. The lesson is that Socratic withholding must be paired with a dignified exit condition — after N unsuccessful hint cycles (e.g., 3), the system should offer to show the full derivation *and then ask the student to re-explain it in their own words*. Pure withholding is not Socratic in spirit; Socrates adjusted based on the interlocutor's state.

**Anti-pattern 2 — No mode lock or enforcement mechanism (ChatGPT Study Mode)**
OpenAI explicitly chose not to implement any parental or administrative controls that would lock students into Study Mode. The result is that study mode is purely voluntary — a student can switch to normal ChatGPT the moment the Socratic friction becomes inconvenient. For a course tutor, this is fatal: the value of the Socratic constraint comes precisely from its consistent application. Our system should implement a configurable "strict mode" that is set per-course by the instructor and cannot be overridden by the student during a session, with audit logging of mode-switch attempts.

---

*Sources consulted: aclanthology.org/2025.findings-emnlp.888, arxiv.org/abs/2512.03501, arxiv.org/abs/2502.00341, arxiv.org/abs/2504.09720, blog.khanacademy.org, khanmigo.ai, blog.google/outreach-initiatives/education/google-gemini-learnlm-update, cloud.google.com/solutions/learnlm, openai.com/index/chatgpt-study-mode, techcrunch.com (Study Mode July 2025), blog.duolingo.com/duolingo-max, openai.com/index/duolingo, synthesis.com/tutor, unite.ai/synthesis-tutor-review, danmeyer.substack.com, duoplanet.com/duolingo-max-review, atlasworkspace.ai/blog/notebooklm-limitations, xda-developers.com/notebooklm-limitations, mamasmiles.com/khanmigo-review*
