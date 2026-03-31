"""
RAG Engine — Retrieval-Augmented Generation for BRI610 Tutor
Uses Ollama for local LLM inference
"""
import httpx
import json
from typing import Optional

SYSTEM_PROMPT = """You are an expert AI tutor for BRI610 Computational Neuroscience at Seoul National University.
Your knowledge base includes:
- Lecture slides from Prof. Jeehyun Kwag (L2-L6: Intro CompNeuro, Membrane Biophysics I&II, Action Potential & HH Model, Cable Theory)
- "Theoretical Neuroscience" by Dayan & Abbott (textbook)

Rules:
- Answer in the SAME LANGUAGE as the student's question (Korean or English).
- Always cite your sources: [Slide L3 p.15] or [Dayan&Abbott Ch.5 §5.6 p.177]
- For math/equations: use clear notation, show step-by-step derivations.
- If referencing a slide diagram, mention the slide number so the student can view it.
- Be pedagogical: explain concepts from first principles when needed.
- Encourage active learning: ask follow-up questions when appropriate.
"""

QUIZ_PROMPT = """You are a quiz generator for BRI610 Computational Neuroscience.
Generate {num} {difficulty}-level questions about "{topic}".

Format each question as JSON:
{{
  "questions": [
    {{
      "id": 1,
      "type": "multiple_choice" | "short_answer" | "derivation",
      "question": "...",
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."],  // only for multiple_choice
      "answer": "...",
      "explanation": "...",
      "source": "Slide L3 p.29" or "Dayan&Abbott Ch.5 §5.2"
    }}
  ]
}}

Answer ONLY with valid JSON. No markdown fences."""

SUMMARY_PROMPT = """Summarize the key concepts from the following lecture content for exam preparation.
Structure your summary as:
1. **Core Concepts** — main ideas and definitions
2. **Key Equations** — all important formulas with variable definitions
3. **Key Figures/Diagrams** — reference slide numbers for important visuals
4. **Common Exam Topics** — likely exam questions based on the material
5. **Connections** — how this material connects to other lectures

Answer in the same language as the content (Korean if Korean, English if English)."""


class RAGEngine:
    def __init__(self, db, ollama_base: str = "http://localhost:11434", model: str = "llama3.1:8b"):
        self.db = db
        self.ollama_base = ollama_base.rstrip("/")
        self.model = model

    def search(self, query: str, source: str = "all", lecture: Optional[str] = None, limit: int = 8):
        if source == "slides":
            return self.db.search_slides(query, lecture, limit)
        elif source == "textbook":
            return self.db.search_textbook(query, limit)
        else:
            return self.db.search_all(query, lecture, limit)

    def _build_context(self, results: list, max_chars: int = 6000) -> str:
        """Build context string from search results, truncated to max_chars"""
        parts = []
        total = 0
        for r in results:
            if r["source"] == "slide":
                header = f"[Slide {r['lecture']} p.{r['page']}] {r['title']}"
            else:
                header = f"[{r['book']} Ch.{r['chapter']} §{r['section']}] {r['section_title']} (pp.{r['pages']})"
            content = r["content"][:1500]
            block = f"{header}\n{content}\n"
            if total + len(block) > max_chars:
                break
            parts.append(block)
            total += len(block)
        return "\n---\n".join(parts)

    async def _ollama_generate(self, system: str, user: str, history: list = None) -> str:
        messages = [{"role": "system", "content": system}]
        if history:
            messages.extend(history[-6:])  # keep last 3 turns
        messages.append({"role": "user", "content": user})

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                resp = await client.post(
                    f"{self.ollama_base}/api/chat",
                    json={"model": self.model, "messages": messages, "stream": False},
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("message", {}).get("content", "")
            except httpx.ConnectError:
                return "[Error] Ollama is not running. Start it with: ollama serve"
            except httpx.HTTPStatusError as e:
                return f"[Error] Ollama returned {e.response.status_code}: {e.response.text[:200]}"
            except Exception as e:
                return f"[Error] {type(e).__name__}: {str(e)}"

    async def chat(self, message: str, lecture: Optional[str] = None,
                   mode: str = "tutor", history: list = None):
        # Retrieve relevant content
        results = self.search(message, source="all", lecture=lecture, limit=6)
        context = self._build_context(results)

        # Build user prompt with context
        user_prompt = f"""Context from lecture materials and textbook:
---
{context}
---

Student's question: {message}"""

        system = SYSTEM_PROMPT
        if mode == "derive":
            system += "\nFocus on step-by-step mathematical derivation. Show every step clearly."

        answer = await self._ollama_generate(system, user_prompt, history)

        # Return answer + sources
        sources = []
        for r in results:
            if r["source"] == "slide":
                sources.append({"type": "slide", "lecture": r["lecture"], "page": r["page"],
                                "title": r["title"]})
            else:
                sources.append({"type": "textbook", "book": r["book"], "chapter": r["chapter"],
                                "section": r["section"], "title": r["section_title"],
                                "pages": r["pages"]})

        return {"answer": answer, "sources": sources}

    async def generate_quiz(self, topic: str, lecture: Optional[str] = None,
                            num_questions: int = 5, difficulty: str = "medium"):
        results = self.search(topic, source="all", lecture=lecture, limit=8)
        context = self._build_context(results, max_chars=4000)

        prompt = QUIZ_PROMPT.format(num=num_questions, difficulty=difficulty, topic=topic)
        user_msg = f"""Based on this material:
---
{context}
---

{prompt}"""

        raw = await self._ollama_generate(SYSTEM_PROMPT, user_msg)

        # Try to parse JSON from response
        try:
            # Find JSON in response
            start = raw.find('{')
            end = raw.rfind('}') + 1
            if start >= 0 and end > start:
                parsed = json.loads(raw[start:end])
                return parsed
        except json.JSONDecodeError:
            pass

        return {"raw_response": raw, "parse_error": True}

    async def generate_summary(self, lecture: str, focus: Optional[str] = None):
        # Get all slides for this lecture
        slides = self.db.get_slides_range(lecture, 1, 100)
        if not slides:
            return {"error": f"No slides found for {lecture}"}

        # Also search textbook for related content
        lecture_title = slides[0]["lecture_title"] if slides else lecture
        tb_results = self.db.search_textbook(lecture_title, limit=4)

        # Build context from slides
        slide_context = ""
        for s in slides:
            if len(s["content"]) > 30:  # skip near-empty
                slide_context += f"[p.{s['page_num']}] {s['content'][:300]}\n"

        tb_context = self._build_context(tb_results, max_chars=2000) if tb_results else ""

        user_msg = f"""Lecture: {lecture} — {lecture_title}

Slide content:
{slide_context[:5000]}

Related textbook sections:
{tb_context}

{f'Focus area: {focus}' if focus else ''}

{SUMMARY_PROMPT}"""

        answer = await self._ollama_generate(SYSTEM_PROMPT, user_msg)
        return {"lecture": lecture, "title": lecture_title, "summary": answer,
                "slide_count": len(slides), "textbook_refs": len(tb_results)}
