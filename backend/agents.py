"""
BRI610 Agent Team — Router + 4 specialized agents
All agents use OpenRouter Qwen3.6-plus-preview (free tier)
"""
import httpx
import json
from typing import Optional

# ─── Agent System Prompts ───

ROUTER_PROMPT = """You are a routing agent for a neuroscience study assistant.
Given the student's message, classify the intent into exactly ONE of:
- tutor: general Q&A, concept explanation, "what is", "explain", "how does"
- derive: mathematical derivation, equation proof, step-by-step math, "derive", "prove", "show that"
- quiz: generate practice questions, "quiz me", "test me", "practice problems"
- exam: mock exam, grading, exam preparation, "exam", "mock test", "grade my answer"
- summary: lecture summary, review, concept map, "summarize", "review", "key points"

Respond with ONLY the intent word, nothing else."""

TUTOR_PROMPT = """You are an expert AI tutor for BRI610 Computational Neuroscience at Seoul National University (Prof. Jeehyun Kwag).

Your knowledge sources:
- Lecture slides (L2: Intro CompNeuro, L3: Membrane Biophysics I, L4: Membrane Biophysics II, L5: Action Potential & HH, L6: Cable Theory)
- "Theoretical Neuroscience" by Dayan & Abbott
- "Fundamental Neuroscience" (3rd ed.)

Rules:
1. Answer in the SAME LANGUAGE as the student (Korean or English)
2. ALWAYS cite sources: [Slide L3 p.29] or [Dayan&Abbott Ch.5 §5.6] or [Fund.Neuro Ch.6]
3. For equations: use LaTeX notation ($E = \\frac{RT}{zF}\\ln\\frac{[ion]_o}{[ion]_i}$)
4. Explain from first principles, then build up
5. Reference specific slide numbers for diagrams
6. Ask a follow-up question to check understanding"""

DERIVE_PROMPT = """You are a mathematical derivation specialist for computational neuroscience.

Rules:
1. Show EVERY step clearly — do not skip any algebra
2. Use LaTeX for all equations
3. Define every variable when first introduced
4. State assumptions explicitly before each derivation
5. Number your steps
6. At the end, verify the result by dimensional analysis or limiting cases
7. Cite the source (lecture slide or textbook) for each key equation
8. Answer in the same language as the student"""

QUIZ_PROMPT = """You are a quiz generator for BRI610 Computational Neuroscience.

Generate questions in this EXACT JSON format:
```json
{
  "questions": [
    {
      "id": 1,
      "type": "multiple_choice",
      "question": "...",
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
      "answer": "B",
      "explanation": "...",
      "difficulty": "medium",
      "source": "Slide L3 p.29"
    }
  ]
}
```

Question types: multiple_choice, short_answer, derivation, true_false
Always include explanation and source citation.
Match the requested difficulty level.
Answer in the same language as the student."""

EXAM_PROMPT = """You are an exam preparation and grading agent for BRI610 Computational Neuroscience.

You can:
1. Generate mock exams (mix of MCQ, short answer, derivation problems)
2. Grade student answers (provide score, corrections, and detailed feedback)
3. Identify weak areas and suggest study priorities

Format mock exams clearly with point values.
When grading, be fair but rigorous — partial credit for partially correct derivations.
Reference the specific lecture material or textbook section for each question.
Answer in the same language as the student."""

SUMMARY_PROMPT = """You are a study summary specialist for BRI610 Computational Neuroscience.

Generate structured summaries with:
1. **Core Concepts** — key definitions and ideas (numbered)
2. **Key Equations** — every important formula with ALL variables defined
3. **Important Figures** — reference slide numbers for critical diagrams
4. **Concept Connections** — how this topic connects to other lectures
5. **Exam Focus** — likely exam topics and common pitfalls
6. **Study Checklist** — actionable items the student should be able to do

Use LaTeX for equations. Be comprehensive but concise.
Answer in the same language as the student."""

AGENT_MAP = {
    "tutor": TUTOR_PROMPT,
    "derive": DERIVE_PROMPT,
    "quiz": QUIZ_PROMPT,
    "exam": EXAM_PROMPT,
    "summary": SUMMARY_PROMPT,
}


class AgentTeam:
    def __init__(self, retriever, openrouter_key: str,
                 chat_model: str = "qwen/qwen3.6-plus-preview:free"):
        self.retriever = retriever
        self.api_key = openrouter_key
        self.chat_model = chat_model
        self.chat_url = "https://openrouter.ai/api/v1/chat/completions"

    async def _llm(self, system: str, user: str, history: list = None,
                   max_tokens: int = 4096, temperature: float = 0.7) -> str:
        messages = [{"role": "system", "content": system}]
        if history:
            messages.extend(history[-6:])
        messages.append({"role": "user", "content": user})

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                r = await client.post(self.chat_url,
                    headers={"Authorization": f"Bearer {self.api_key}",
                             "Content-Type": "application/json"},
                    json={"model": self.chat_model, "messages": messages,
                          "max_tokens": max_tokens, "temperature": temperature})
                r.raise_for_status()
                return r.json()["choices"][0]["message"]["content"]
            except httpx.ConnectError:
                return "[Error] Cannot connect to OpenRouter API"
            except httpx.HTTPStatusError as e:
                return f"[Error] OpenRouter {e.response.status_code}: {e.response.text[:200]}"
            except Exception as e:
                return f"[Error] {type(e).__name__}: {str(e)}"

    async def route(self, message: str) -> str:
        """Classify user intent"""
        result = await self._llm(ROUTER_PROMPT, message, max_tokens=10, temperature=0.0)
        intent = result.strip().lower().split()[0] if result else "tutor"
        if intent not in AGENT_MAP:
            intent = "tutor"
        return intent

    def _build_context(self, results: list, max_chars: int = 6000) -> str:
        parts = []
        total = 0
        for r in results:
            if r["source"] == "slide":
                header = f"[Slide {r['lecture']} p.{r['page']}] {r['title']}"
            else:
                header = f"[{r['book']} Ch.{r['chapter']} §{r.get('section','')}] {r.get('section_title','')}"
            content = r["content"][:1200]
            block = f"{header}\n{content}\n"
            if total + len(block) > max_chars:
                break
            parts.append(block)
            total += len(block)
        return "\n---\n".join(parts)

    def _format_sources(self, results):
        sources = []
        seen = set()
        for r in results:
            if r["source"] == "slide":
                key = f"{r['lecture']}-{r['page']}"
                if key not in seen:
                    seen.add(key)
                    sources.append({"type": "slide", "lecture": r["lecture"],
                                    "page": r["page"], "title": r["title"]})
            else:
                key = f"{r['book']}-{r['chapter']}-{r.get('section','')}"
                if key not in seen:
                    seen.add(key)
                    sources.append({"type": "textbook", "book": r["book"],
                                    "chapter": r["chapter"],
                                    "section": r.get("section",""),
                                    "title": r.get("section_title",""),
                                    "pages": r.get("pages","")})
        return sources

    async def chat(self, message: str, lecture: Optional[str] = None,
                   mode: Optional[str] = None, history: list = None):
        """Main entry point — routes to appropriate agent"""
        # Auto-route if mode not specified
        if not mode or mode == "auto":
            mode = await self.route(message)

        # Retrieve context
        results = self.retriever.search(message, lecture=lecture, limit=6)
        context = self._build_context(results)
        sources = self._format_sources(results)

        # Build agent prompt
        system = AGENT_MAP.get(mode, TUTOR_PROMPT)
        user_prompt = f"""Retrieved context from lecture materials and textbooks:
---
{context}
---

Student's message: {message}"""

        answer = await self._llm(system, user_prompt, history)

        return {"answer": answer, "sources": sources, "agent": mode}

    async def generate_quiz(self, topic: str, lecture: Optional[str] = None,
                            num_questions: int = 5, difficulty: str = "medium"):
        results = self.retriever.search(topic, lecture=lecture, limit=8)
        context = self._build_context(results, max_chars=4000)

        prompt = f"""Based on this material, generate {num_questions} {difficulty}-level questions about "{topic}".

Context:
---
{context}
---

Generate the quiz in JSON format as specified in your instructions."""

        raw = await self._llm(QUIZ_PROMPT, prompt, temperature=0.8)

        # Parse JSON
        try:
            start = raw.find('{')
            end = raw.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(raw[start:end])
        except json.JSONDecodeError:
            pass
        return {"raw_response": raw, "parse_error": True}

    async def generate_exam(self, lecture: str, duration_min: int = 60,
                            total_points: int = 100):
        results = self.retriever.search(f"lecture {lecture} key concepts equations",
                                         lecture=lecture, limit=10)
        context = self._build_context(results, max_chars=5000)

        prompt = f"""Create a mock exam for lecture {lecture}.
Duration: {duration_min} minutes, Total: {total_points} points.

Material:
---
{context}
---

Include:
- 5 MCQ (2 pts each = 10 pts)
- 3 short answer (10 pts each = 30 pts)
- 2 derivation problems (30 pts each = 60 pts)

Format clearly with point values."""

        answer = await self._llm(EXAM_PROMPT, prompt, temperature=0.7)
        return {"lecture": lecture, "exam": answer,
                "sources": self._format_sources(results)}

    async def generate_summary(self, lecture: str, focus: Optional[str] = None):
        query = f"lecture {lecture} key concepts"
        if focus:
            query += f" {focus}"
        results = self.retriever.search(query, lecture=lecture, limit=10)
        context = self._build_context(results, max_chars=5000)

        prompt = f"""Summarize lecture {lecture} for exam preparation.
{f'Focus on: {focus}' if focus else ''}

Material:
---
{context}
---"""

        answer = await self._llm(SUMMARY_PROMPT, prompt)
        return {"lecture": lecture, "summary": answer,
                "sources": self._format_sources(results)}

    async def grade_answer(self, question: str, student_answer: str,
                           lecture: Optional[str] = None):
        results = self.retriever.search(question, lecture=lecture, limit=4)
        context = self._build_context(results, max_chars=3000)

        prompt = f"""Grade this student's answer:

Question: {question}

Student's Answer: {student_answer}

Reference Material:
---
{context}
---

Provide: score (out of 10), detailed corrections, and what was missing."""

        answer = await self._llm(EXAM_PROMPT, prompt, temperature=0.3)
        return {"grade": answer, "sources": self._format_sources(results)}
