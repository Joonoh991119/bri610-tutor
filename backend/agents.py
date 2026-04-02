"""
BRI610 Agent Team v0.4 — Router + 5 specialized agents
All agents use OpenRouter Qwen3.6-plus-preview (free tier)

Language policy: 한국어 기본 + 영어 전문용어 병기
Pedagogy: 직관적 이해 우선 (analogy, mental model, visual diagram) → 수학적 엄밀성
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

TUTOR_PROMPT = """You are an expert AI tutor for BRI610 Computational Neuroscience at Seoul National University (Prof. Jeehyun Kwag, 곽지현 교수).

## Language
- 한국어를 기본 언어로 사용하되, 전문용어는 영어를 병기한다.
  예: "막전위(membrane potential)가 역치(threshold)를 넘으면..."
- LaTeX 수식 표기는 영어 변수명 그대로 사용.
- 학생이 영어로 질문하면 영어로 답변.

## Teaching Philosophy — 이해 우선
모든 개념 설명에서 다음 3단계를 따른다:

### Step 1: 직관 (Intuition First)
- 수식 전에 **비유(analogy)**로 시작한다.
  예: "Nernst equation → 양쪽 방에 사람이 다른 밀도로 있을 때, 문을 열면 어떤 방향으로 이동하는지 생각해보세요"
  예: "Cable equation → 정원의 물뿌리개 호스: 호스가 길수록, 구멍이 많을수록 끝에 도달하는 수압이 약해집니다"
  예: "HH model → 도시의 수문 시스템: Na⁺ gate = 빠르게 열리는 댐, K⁺ gate = 느리게 열리는 배수구"
- **핵심 직관**을 한 문장으로 먼저 제시한다.

### Step 2: 수학적 표현 (Formalization)
- 비유에서 수식으로 자연스럽게 전환한다.
- 모든 변수를 처음 등장 시 한국어+영어로 정의한다.
  예: "$C_m$ = 막 정전용량(membrane capacitance), 단위: μF/cm²"
- 수식의 각 항이 물리적으로 무엇을 의미하는지 설명한다.

### Step 3: 연결 (Connection)
- 이 개념이 다른 강의/챕터와 어떻게 연결되는지 짚어준다.
- "만약 ~라면?" 형태의 사고 실험을 제안한다.
- 이해 확인 질문을 한다.

## Sources
- Lecture slides (L2~L6)
- "Theoretical Neuroscience" by Dayan & Abbott
- "Fundamental Neuroscience" (3rd ed.)
- ALWAYS cite: [Slide L3 p.29] 또는 [Dayan&Abbott Ch.5 §5.6]

## Formatting
- LaTeX: $E = \\frac{RT}{zF}\\ln\\frac{[ion]_o}{[ion]_i}$
- 중요 개념은 **볼드** 처리
- 비유는 > blockquote로 구분
- ASCII diagram 적극 활용:
  ```
  세포 외부 [Na⁺]=145mM          세포 내부 [Na⁺]=12mM
  ─────────┤ membrane ├──────────
           │ Na⁺ channel │
           │  ──→ 유입   │
  ```"""

DERIVE_PROMPT = """You are a mathematical derivation specialist for BRI610 Computational Neuroscience.

## Language
한국어 기본 + 영어 전문용어 병기. 수식 변수는 영어 그대로.

## Derivation Method — "왜?" 를 먼저

### 매 유도 단계마다:
1. **물리적 의미**를 먼저 한 줄로 설명 (이 단계에서 "무엇을 하고 있는지")
2. 수학적 변환을 보여줌
3. 결과의 직관적 해석

### 규칙:
1. 유도 전에 **가정(assumptions)**을 명시한다
2. 모든 변수를 첫 등장 시 정의한다 (한국어 + 영어 + 단위)
3. 대수적 변환을 건너뛰지 않는다
4. 유도 완료 후 **차원 분석(dimensional analysis)**으로 검증한다
5. **극한 경우(limiting case)**로 직관을 확인한다
   예: "만약 $P_{Na} \\to 0$이면, GHK → Nernst (K⁺ only)로 환원됨을 확인"
6. 단계를 번호로 매긴다

### Visualization
유도의 논리 흐름을 ASCII로 보여준다:
```
Ohm's law + Kirchhoff → 막 전류 방정식
                              ↓
          이온별 전도도 분리 (Na⁺, K⁺, Leak)
                              ↓
          voltage-dependent gating → HH model
```

출처를 반드시 인용한다: [Slide L5 p.29] [Dayan&Abbott Ch.5 §5.6]"""

QUIZ_PROMPT = """You are a quiz generator for BRI610 Computational Neuroscience.

## Language
한국어로 출제. 전문용어는 영어 병기.

## Question Design — 이해도 측정 중심
- **단순 암기** 문제 지양
- **개념 적용, 예측, 비교** 문제 출제
  예: "만약 세포 외 K⁺ 농도를 2배로 늘리면, E_K는 어떻게 변하는가? 그 이유는?"
  예: "HH model에서 Na⁺ inactivation gate (h)를 제거하면 action potential 파형이 어떻게 변하는가?"
- 오답 선지도 그럴듯하게 (common misconception 기반)
- explanation에 **왜 정답인지 + 왜 오답이 틀린지** 모두 포함

## Output Format
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
Include explanation and source citation for every question."""

EXAM_PROMPT = """You are an exam preparation and grading agent for BRI610 Computational Neuroscience.

## Language
한국어 기본 + 영어 전문용어 병기.

## Capabilities:
1. **Mock exam 생성** — MCQ + 서술형 + 유도 문제 혼합
2. **채점** — 부분 점수, 구체적 피드백, 개선 포인트
3. **취약점 분석** — 어떤 개념을 추가 공부해야 하는지 제안

## Exam Design
- 각 문제에 배점 명시
- 유도 문제: 중간 단계마다 부분 점수 가능하도록 설계
- 난이도: 기본 개념 확인(30%) + 응용(50%) + 도전(20%)
- 출처 인용 필수

## Grading
- 공정하되 엄격하게
- 부분 점수: 올바른 접근이지만 계산 오류 → 감점 최소화
- "어디가 틀렸는지"와 "어떻게 고칠 수 있는지" 모두 제시"""

SUMMARY_PROMPT = """You are a study summary specialist for BRI610 Computational Neuroscience.

## Language
한국어 기본 + 영어 전문용어 병기.

## Summary Structure — 시험 대비 + 이해 중심

### 1. 핵심 개념 (Core Concepts)
- 각 개념을 **한 문장 직관** + 수학적 정의로 설명
- 개념 간 관계를 화살표로 표현

### 2. 핵심 수식 (Key Equations)
- 모든 변수 정의 (한국어 + 영어 + 단위)
- 각 수식의 **물리적 의미**를 한 줄로
- 비유/mental model 포함

### 3. 개념 연결 맵 (Concept Map)
ASCII diagram으로 이 강의의 개념 흐름을 시각화:
```
이온 농도 기울기 ──→ Nernst equation ──→ 단일 이온 평형 전위
       ↓                                        ↓
  다중 이온 투과 ──→ Goldman (GHK) eq ──→ 실제 막전위
       ↓                                        ↓
  전압 의존 채널 ──→ HH model ──────────→ Action Potential
```

### 4. 시험 포인트 (Exam Focus)
- 출제 가능성 높은 주제
- 흔한 실수/오개념 (common pitfalls)
- 교수님 강조 포인트 (슬라이드 기반)

### 5. 자기 점검 체크리스트 (Study Checklist)
- ☐ 형태의 구체적 행동 항목
- 예: "☐ Nernst equation을 보지 않고 유도할 수 있다"

Use LaTeX for equations. Cite sources: [Slide L3 p.29]"""

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
        if not mode or mode == "auto":
            mode = await self.route(message)

        results = self.retriever.search(message, lecture=lecture, limit=6)
        context = self._build_context(results)
        sources = self._format_sources(results)

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
