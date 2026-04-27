-- v0.7 — Pre-built quiz bank + take-home exam separation
-- Course (lecture summary + narration + quiz) inheritance pattern: course view
-- selects from lecture_summaries + lecture_narrations + quiz_items per lecture.

-- Quiz items: MCQ + short-answer (auto-gradeable, fast feedback)
CREATE TABLE IF NOT EXISTS quiz_items (
    id              SERIAL PRIMARY KEY,
    lecture         VARCHAR(10) NOT NULL,        -- L2..L8
    position        INTEGER NOT NULL,            -- ordering within lecture
    kind            VARCHAR(16) NOT NULL CHECK (kind IN ('mcq', 'short_answer')),
    prompt_md       TEXT NOT NULL,               -- question stem (markdown + KaTeX OK)
    choices_json    JSONB,                       -- NULL for short_answer; for mcq: [{"key":"A","text":"...","correct":false}, ...]
    correct_key     VARCHAR(8),                  -- NULL for short_answer; for mcq: "A"|"B"|...
    correct_text    TEXT,                        -- canonical short answer (for short_answer kind)
    accept_patterns JSONB,                       -- for short_answer: list of regex/synonym patterns
    rationale_md    TEXT NOT NULL,               -- why this is correct + common pitfalls
    slide_ref       TEXT,                        -- "[Slide L3 p.27]"
    difficulty      INTEGER NOT NULL CHECK (difficulty BETWEEN 1 AND 5),
    bloom           VARCHAR(16) CHECK (bloom IN ('Remember','Understand','Apply','Analyze','Evaluate','Create')),
    topic_tag       TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(lecture, position)
);
CREATE INDEX IF NOT EXISTS idx_quiz_items_lecture ON quiz_items(lecture, position);
CREATE INDEX IF NOT EXISTS idx_quiz_items_difficulty ON quiz_items(difficulty);

-- Take-home exam: formula derivations + essay questions (manual grading, deeper)
CREATE TABLE IF NOT EXISTS take_home_exam (
    id              SERIAL PRIMARY KEY,
    lecture         VARCHAR(10) NOT NULL,
    position        INTEGER NOT NULL,
    kind            VARCHAR(16) NOT NULL CHECK (kind IN ('derivation', 'essay', 'numerical', 'proof')),
    prompt_md       TEXT NOT NULL,
    model_answer_md TEXT NOT NULL,               -- worked solution
    rubric_md       TEXT NOT NULL,               -- grading rubric (points per part)
    max_points      INTEGER NOT NULL DEFAULT 10,
    expected_time_min INTEGER NOT NULL DEFAULT 15,
    slide_ref       TEXT,
    topic_tag       TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(lecture, position)
);
CREATE INDEX IF NOT EXISTS idx_take_home_lecture ON take_home_exam(lecture, position);

-- Course view: union of summary + narration + quiz item-counts for a compact study guide
CREATE OR REPLACE VIEW course_view AS
SELECT
    s.lecture,
    LEFT(s.summary, 200)        AS summary_preview,
    LENGTH(s.summary)           AS summary_chars,
    (SELECT COUNT(*) FROM lecture_narrations n WHERE n.lecture = s.lecture)  AS narration_steps,
    (SELECT COUNT(*) FROM quiz_items q WHERE q.lecture = s.lecture)          AS quiz_n,
    (SELECT COUNT(*) FROM take_home_exam t WHERE t.lecture = s.lecture)      AS take_home_n,
    s.generated_at              AS summary_generated_at
FROM lecture_summaries s
ORDER BY s.lecture;

COMMENT ON TABLE quiz_items IS 'Auto-gradeable MCQ + short-answer for spaced retrieval. Pre-built per lecture.';
COMMENT ON TABLE take_home_exam IS 'Manual-graded derivations + essays. Separate from quiz to keep quick-check loop fast.';
COMMENT ON VIEW course_view IS 'Course = summary + narration + quiz; one row per lecture for compact study guide.';
