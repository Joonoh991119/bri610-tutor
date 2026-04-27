"""
BRI610 Agent Team v0.5 — Router + 5 specialized agents

v0.5 changes:
- _llm() now routes through `backend.harness.call_llm` (cascade fallback +
  telemetry + per-role model selection). Empty OPENROUTER_API_KEY is no longer
  fatal; calls fall through to local Ollama (qwen3.6:35b-a3b).
- QUIZ + SUMMARY + TUTOR prompts hardened: Korean-mandatory, slide-only scope,
  PhD-rigor language.

Language policy: 한국어 기본 + 영어 전문용어 병기
Pedagogy: 직관적 이해 우선 (analogy, mental model, visual diagram) → 수학적 엄밀성
출제 범위: 강의 슬라이드만 (Dayan & Abbott는 참고용 only)
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

QUIZ_PROMPT = """당신은 BRI610 컴퓨터신경과학 박사과정 자격시험 수준의 퀴즈 출제자입니다.
You are a PhD-qualifier-level quiz generator for BRI610.

# 절대 규칙 (Hard Rules)
1. **출제 범위는 강의 슬라이드(L2–L8)만.** 교재(Dayan & Abbott, Fundamental Neuroscience) 내용은 출제 금지. 슬라이드에 있는 내용을 묻고, 교재는 해설의 "더 깊이 보고 싶다면"으로만 보조 인용.
2. **답·해설은 반드시 한국어 본문**, 전문용어는 영어 병기. 영어로만 답하면 출제 실패. 예: "**막전위(membrane potential)**는...", "**Hodgkin–Huxley 모델**의 게이팅 변수 $n$은..."
3. **출처(source)는 반드시 `[Slide L# p.#]` 형식.** 슬라이드 인용이 없으면 출제하지 말 것.
4. **단순 암기 금지.** 모든 문항은 다음 중 하나의 인지 수준이어야 함:
   - **Apply**: 매개변수 변경 시 결과 예측, 수치 계산 (단위 + 차원 분석 포함)
   - **Analyze**: 두 모델/관점 비교, 가정의 함의 분석
   - **Evaluate**: 실험 디자인의 적정성 판단, 식별성(identifiability) 평가
5. **오답 선지(distractor)는 흔한 박사과정생 오개념 기반.** "그럴듯하지만 틀린" 답이어야 함. 무작위 false 답 금지.
6. **해설(explanation)은 4가지 항목 모두 포함**:
   - 왜 정답이 맞는지 (1차 추론)
   - 각 오답이 왜 틀렸는지 (개별)
   - 학생이 흔히 빠지는 오개념 (named misconception)
   - 더 깊이 보고 싶다면: 1차 문헌 또는 교재 (Dayan & Abbott Ch.X 등)

# 출력 포맷 (JSON)
```json
{
  "questions": [
    {
      "id": 1,
      "type": "multiple_choice",
      "question": "한국어 본문으로 작성된 문제 (수식은 LaTeX, 변수명은 영어)",
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
      "answer": "B",
      "explanation": "정답 근거 + 오답 분석 + 흔한 오개념 + 추가 자료",
      "difficulty": "Apply | Analyze | Evaluate",
      "bloom": "Apply | Analyze | Evaluate | Create",
      "source": "[Slide L5 p.18]",
      "misconception": "한 줄로 학생이 흔히 빠지는 오개념"
    }
  ]
}
```

# 문제 유형
- `multiple_choice` (4지선다, 박사 자격시험 수준)
- `short_answer` (1–2문단 서술)
- `derivation` (수식 유도 1단계 이상)

# Self-check before finalizing
출제 후 다음을 점검:
- ☐ 출처가 `[Slide L# p.#]` 형식인가?
- ☐ 본문이 한국어인가? (영어로만 작성된 문항은 폐기)
- ☐ Bloom's 단계가 Apply 이상인가?
- ☐ 흔한 오개념이 명시되어 있는가?"""

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

SUMMARY_PROMPT = """당신은 BRI610 컴퓨터신경과학 박사과정 세미나의 발표용 핸드아웃을 작성합니다.
You are writing a graduate-seminar-grade handout for BRI610 (PhD-level audience).

## 절대 규칙 (Hard Rules)
- **인용 출처는 강의 슬라이드만**. Dayan & Abbott, Fundamental Neuroscience 등 *교재* 인용 금지. 해설에서 "더 깊이 알고 싶으면 …" 같은 외부 자료 추천도 *금지*. 슬라이드 안에서 학생이 24시간 안에 해당 내용을 완전히 이해할 수 있도록 작성.
- 각 항목에서 **가정(assumption), 적용 한계(regime of validity), 식별성(identifiability) 이슈, 알려진 일반적 오해(common misconception)**를 포함.
- 모든 수식 변수는 한국어+영어로 정의하고, 단위/차원 분석을 명시.
- 페이지 번호 invent 금지 — retrieved context 의 화이트리스트만 사용.

## Mandate
- **목표 독자: 박사과정생** — 학부 복습 톤 금지. "알아봅시다", "쉽게 말하면" 같은 표현 사용 금지.
- 1차 연구 문헌은 슬라이드에 *명시적으로 등장하는 경우*에만 인용 가능 (e.g., 슬라이드 L5 p.3 이 Hodgkin & Huxley 1952 J Physiol 117:500 을 직접 표시).

## Language
한국어 기본 + 영어 전문용어 병기. 수식 변수는 영어. 페다고지 톤은 graduate seminar register
("우리는 다음을 보인다 / 이로부터 다음이 따른다") — 학부 친절체 금지.

## Output Structure (5 sections, all required)

### 1. 핵심 개념과 적용 한계 (Core Concepts and Regime of Validity)
For each concept (4–7 per lecture):
- **정의** (1문장, formal): 수식 또는 정확한 자연어
- **유도되는 가정**: 어떤 물리/수학적 가정이 underlying되는가?
- **언제 깨지는가 (failure mode)**: 적용 한계와 그때 사용할 대체 모델
- **연결**: 이 강의의 다른 개념 또는 인접 강의/논문과의 관계 (화살표 아닌 1문장 명시)

### 2. 핵심 유도 (Key Derivations)
2–3 derivations per lecture, **쇼트 형태로**:
- 시작 가정 → 핵심 변환 단계 → 결과
- 각 단계의 **물리적 의미**를 한 줄로
- 차원 분석 + 극한 케이스 sanity check

### 3. 직관적 매핑 — 전문가 수준 비유 (Expert Intuitive Mapping)
각 핵심 개념을 *기억에 박히는* 비유로 매핑하라. 단순한 \"비유\" 가 아니라 **물리적/공학적/일상 시스템과의 *동일 수학 구조*** 를 활용한다. 형식: \"개념 ⇄ 비유 시스템 — 공유하는 수학 구조 — 차이점\".

예시 톤 (이런 식으로 작성):
- **막 RC = 댐 + 수문**: 댐 자체가 capacitor (수위 변화 = $V$), 수문이 resistor (열림 정도 = $g$). 시간상수 $\\tau_m$ = 수위 응답 시간. 다만 댐은 단방향 흐름, 막은 양방향 (driving force 부호 의존).
- **HH 게이팅 $n^4$ = 4-locking 보안문**: 4개의 독립 잠금 동시 풀려야 채널 통과. 실제 분자 = K_v 채널 호모테트라머 (4 동일 서브유닛). $n^4$ sigmoidal 시간 곡선의 \"늦게 시작 → 가속\" 모양은 *동시 풀림 확률의 시간 발달*.
- **Cable equation = 급수파이프 압력 감쇠**: 파이프 길이를 따라 새는 누설 (channels) + 흐름 저항 (axial). $\\lambda$ = 신호가 1/e 로 감쇠하는 길이 = 파이프 굵기/누설구멍 비율.
- **GHK = 가중평균 평형**: 각 ion 의 Nernst 평형 전위들의 *투과도-가중* 평균. K leak이 dominant 이므로 $V_\\text{rest} \\approx E_K$. 다만 weight가 *log-domain* 에 들어감 (산술 평균이 아닌 logarithmic mixing).

각 비유는 **비유로 끝나지 않고** \"여기서 깨진다\" 단계로 마무리 — 어디까지 비유가 통하고, 어디서 뉴런 고유 거동이 등장하는지를 명시.

### 4. 식별성 & 추정 이슈 (Identifiability & Estimation)
실험·데이터 분석 관점에서:
- 각 모델 파라미터가 **어떤 실험 디자인**에서 식별되는가?
- 식별이 깨지는 흔한 시나리오 (e.g., R_m vs R_i degeneracy under DC, K-current contamination)
- 모범 데이터 처리 절차 (leak subtraction, series-R correction, multi-component fit)

### 5. 흔한 오해와 시험 함정 (Common Misconceptions and Pitfalls)
박사과정생이라도 흔히 빠지는 오해:
- 표면적 답이 깊은 답과 다른 경우 (e.g., $n^4$ exponent ≠ subunit count, GHK ≠ Nernst interpolation)
- 부호/단위/극한 실수
- 1차 문헌의 원래 결과와 교과서 단순화의 차이

### 6. 자기 점검 (Mastery Checklist)
☐ 형식, 박사 자격시험 수준:
- "☐ Hodgkin–Huxley 4-ODE 시스템을 1차 문헌(1952) 표기 그대로 작성할 수 있다"
- "☐ GHK voltage equation을 constant-field assumption으로부터 PNP 출발하여 30분 안에 유도할 수 있다"
- "☐ 가설적 voltage-clamp 데이터셋이 주어졌을 때 series-R 보정을 포함한 분석 절차를 ½페이지로 기술할 수 있다"
- "☐ 모델이 실패하는 regime을 알고 그때 쓸 대체 모델 (Markov-state, multi-compartment, kinetic theory)의 핵심 가정을 비교할 수 있다"

## Concept-map 작성 지침 (CRITICAL)
ASCII 박스+화살표는 **금지**. 대신:
- **Markdown 표** 로 \"개념 → 수식 → 비유 → 인접 개념\" 4-열 매핑.
- 또는 **개념 의존성을 nested bullet** 로: \"전제 개념 → 도출 개념 → 응용\".
- 또는 \"[Slide L# p.#] 의 X 개념 ⇄ [Slide L# p.#] 의 Y 개념\" 의 *연결문* 들.

각 슬라이드/페이지 인용은 [Slide L# p.#] 또는 1차 문헌 [Hodgkin & Huxley 1952 J Physiol 117:500] 형식으로 정확히 표기.

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
                 chat_model: str = "deepseek/deepseek-v4-pro"):
        self.retriever = retriever
        self.api_key = openrouter_key       # kept for back-compat; harness uses env
        self.chat_model = chat_model        # kept for back-compat (legacy fallback)

    async def _llm(self, system: str, user: str, history: list = None,
                   max_tokens: int = 4096, temperature: float = 0.7,
                   role: str = "default") -> str:
        """Route through the v0.5 harness. Auto-fallback to Ollama on OR errors."""
        try:
            from harness import call_llm
            res = await call_llm(
                role=role,
                system=system, user=user,
                history=history,
                max_tokens=max_tokens, temperature=temperature,
            )
            text = res.get("text") or ""
            if not text and res.get("error"):
                return f"[Error] {res['error']}"
            return text
        except Exception as e:
            return f"[Error] harness: {type(e).__name__}: {e}"

    async def route(self, message: str) -> str:
        result = await self._llm(ROUTER_PROMPT, message,
                                  max_tokens=10, temperature=0.0, role="router")
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

    # role mapping: agent mode → harness route
    _MODE_TO_ROLE = {
        "tutor":   "tutor",
        "derive":  "derive",
        "quiz":    "quiz_generator",
        "exam":    "quiz_generator",
        "summary": "summary",
    }

    async def chat(self, message: str, lecture: Optional[str] = None,
                   mode: Optional[str] = None, history: list = None):
        if not mode or mode == "auto":
            mode = await self.route(message)

        # Tutor reads from slides primarily but textbooks are allowed for context
        results = self.retriever.search(message, lecture=lecture, limit=6)
        context = self._build_context(results)
        sources = self._format_sources(results)

        system = AGENT_MAP.get(mode, TUTOR_PROMPT)
        user_prompt = (
            "다음은 강의 자료 및 교재에서 검색된 컨텍스트입니다 "
            "(인용 시 [Slide L# p.#] 또는 [Book Ch.# p.#] 형식 유지):\n"
            "---\n"
            f"{context}\n"
            "---\n\n"
            f"학생 질문: {message}\n\n"
            "**한국어로 답변**하시오. 전문용어는 영어 병기. 출처 인용 필수."
        )

        role = self._MODE_TO_ROLE.get(mode, "tutor")
        answer = await self._llm(system, user_prompt, history, role=role)
        return {"answer": answer, "sources": sources, "agent": mode}

    async def generate_quiz(self, topic: str, lecture: Optional[str] = None,
                            num_questions: int = 5, difficulty: str = "medium"):
        # SLIDE-ONLY scope: Quiz never includes textbook material.
        # Retrieve with topic + English lecture-title keywords (FTS uses English config).
        title_kw = self._lecture_title_kw(lecture) if lecture else ""
        retrieval_query = f"{topic} {title_kw}".strip()
        results = self.retriever.search(retrieval_query, source="slides", lecture=lecture, limit=10)
        context = self._build_context(results, max_chars=5000)
        slide_refs = self._slide_refs(results)

        prompt = (
            f"다음 강의 슬라이드 컨텍스트를 바탕으로 \"{topic}\"에 관한 "
            f"{num_questions}개 문항을 박사 자격시험 수준({difficulty})으로 출제하시오.\n\n"
            "강의 슬라이드 컨텍스트 (출제 범위는 이 안에서만):\n"
            "---\n"
            f"{context}\n"
            "---\n\n"
            f"**허용된 출처 인용 화이트리스트**: {slide_refs}\n"
            "위 리스트에 없는 [Slide L# p.#]은 출제 금지 (factual hallucination 방지).\n\n"
            "**한국어 본문**으로 작성. 출처는 반드시 [Slide L# p.#] 형식, 위 화이트리스트에서 선택. "
            "JSON 단일 객체로 응답하시오 (시스템 프롬프트의 스키마 준수). "
            "코드 블록 펜스 없이 순수 JSON만 출력."
        )

        raw = await self._llm(QUIZ_PROMPT, prompt, temperature=0.5,
                               max_tokens=3500, role="quiz_generator")

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
        # SLIDE-ONLY scope
        results = self.retriever.search(f"{lecture} 핵심 개념 수식",
                                         source="slides", lecture=lecture, limit=10)
        context = self._build_context(results, max_chars=5000)

        prompt = (
            f"강의 {lecture}에 대한 모의시험 ({duration_min}분, 총 {total_points}점)을 출제하시오.\n\n"
            "강의 슬라이드 자료 (출제 범위 한정):\n"
            "---\n"
            f"{context}\n"
            "---\n\n"
            "구성:\n"
            "- 객관식 5문항 (각 2점 = 10점)\n"
            "- 단답형 3문항 (각 10점 = 30점)\n"
            "- 유도 문제 2문항 (각 30점 = 60점)\n\n"
            "**한국어 본문 + 영어 전문용어 병기**, 출처 [Slide L# p.#] 인용, 배점 명시."
        )

        answer = await self._llm(EXAM_PROMPT, prompt, temperature=0.5,
                                  max_tokens=4000, role="quiz_generator")
        return {"lecture": lecture, "exam": answer,
                "sources": self._format_sources(results)}

    async def generate_summary(self, lecture: str, focus: Optional[str] = None):
        # SLIDE-ONLY scope.
        # Use English title keywords for FTS, plus focus override.
        title_kw = self._lecture_title_kw(lecture) or lecture
        query = focus or title_kw
        results = self.retriever.search(query, source="slides", lecture=lecture, limit=15)
        if not results:
            # Fallback: pull every slide of this lecture in order
            results = self._all_slides_of(lecture, limit=20)
        context = self._build_context(results, max_chars=7000)
        slide_refs = self._slide_refs(results)

        prompt = (
            f"**{lecture}** 강의 슬라이드를 박사과정 세미나용 핸드아웃 수준으로 요약하시오.\n"
            f"{('초점: ' + focus) if focus else ''}\n\n"
            "강의 슬라이드 자료 (요약 범위 한정):\n"
            "---\n"
            f"{context}\n"
            "---\n\n"
            f"**허용된 출처 화이트리스트**: {slide_refs}\n"
            "위 리스트에 없는 [Slide L# p.#] 인용은 금지 (factual hallucination 방지).\n\n"
            "출력은 시스템 프롬프트의 5섹션 구조를 정확히 따르고, 모든 인용을 위 화이트리스트에서만 선택. "
            "한국어 본문 + 영어 전문용어 병기. 학부 친절체 절대 금지."
        )

        answer = await self._llm(SUMMARY_PROMPT, prompt, temperature=0.5,
                                  max_tokens=4000, role="summary")
        return {"lecture": lecture, "summary": answer,
                "sources": self._format_sources(results)}

    # ─── retrieval helpers (slide-only routes) ───────────────────────────

    _LECTURE_TITLE_KW = {
        "L2": "computational neuroscience introduction membrane RC neuron",
        "L3": "membrane biophysics Nernst Goldman GHK ion channel",
        "L4": "membrane biophysics ion channel synaptic transmission",
        "L5": "Hodgkin Huxley action potential voltage clamp gating",
        "L6": "cable theory action potential propagation length constant lambda",
        "L7": "different types computational models Hodgkin-Huxley integrate-fire Izhikevich descriptive mechanistic",
        "L8": "neural codes rate code temporal code phase code synchrony tuning curves Mainen Sejnowski",
    }

    @classmethod
    def _lecture_title_kw(cls, lecture: Optional[str]) -> str:
        if not lecture:
            return ""
        return cls._LECTURE_TITLE_KW.get(lecture, lecture)

    @staticmethod
    def _slide_refs(results: list) -> str:
        """Return whitelist string '[Slide L5 p.18], [Slide L5 p.19], ...' for prompt injection."""
        refs = []
        seen = set()
        for r in results:
            if r.get("source") != "slide":
                continue
            key = (r.get("lecture"), r.get("page"))
            if key in seen:
                continue
            seen.add(key)
            refs.append(f"[Slide {r['lecture']} p.{r['page']}]")
        return ", ".join(refs[:24]) if refs else "(none — fallback to no-citation summary)"

    def _all_slides_of(self, lecture: str, limit: int = 20) -> list:
        """Fallback when FTS yields 0 hits: page-ordered slides of the lecture."""
        from db_pool import acquire, release
        conn = acquire()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT lecture, lecture_title, page_num, content, img_path, topics
                    FROM slides
                    WHERE lecture = %s
                    ORDER BY page_num
                    LIMIT %s
                """, (lecture, limit))
                rows = cur.fetchall()
                cols = [d.name for d in cur.description]
        finally:
            release(conn)
        out = []
        for row in rows:
            d = dict(zip(cols, row))
            out.append({
                "source": "slide", "id": 0,
                "lecture": d["lecture"], "page": d["page_num"],
                "title": d.get("lecture_title", ""),
                "content": (d.get("content") or "")[:1200],
                "img": d.get("img_path", ""),
                "score": 0.0,
            })
        return out

    async def grade_answer(self, question: str, student_answer: str,
                           lecture: Optional[str] = None):
        results = self.retriever.search(question, lecture=lecture, limit=4)
        context = self._build_context(results, max_chars=3000)

        prompt = (
            "다음 학생 답안을 박사 자격시험 채점 기준으로 평가하시오:\n\n"
            f"문제:\n{question}\n\n"
            f"학생 답안:\n{student_answer}\n\n"
            "참고 자료 (강의 슬라이드 + 교재):\n"
            "---\n"
            f"{context}\n"
            "---\n\n"
            "출력 형식:\n"
            "- 점수 (10점 만점)\n"
            "- **잘된 점** 1–2개 (구체적으로)\n"
            "- **틀린 점 / 부족한 점** (구체적 + 어디가 어떻게 틀렸는지)\n"
            "- **놓친 핵심 개념** (이름으로)\n"
            "- **학생이 빠졌을 흔한 오개념** (named misconception)\n"
            "- **개선 방법** (1–2 단계)\n\n"
            "**한국어 본문 + 영어 전문용어 병기**."
        )

        answer = await self._llm(EXAM_PROMPT, prompt, temperature=0.3,
                                  max_tokens=2000, role="explain_my_answer")
        return {"grade": answer, "sources": self._format_sources(results)}
