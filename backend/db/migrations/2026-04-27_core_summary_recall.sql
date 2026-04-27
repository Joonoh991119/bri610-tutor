-- v0.7.7 — Core summary (1-page condensed) + recall-style repeated quiz

-- Final exam-ready 핵심요약본: ~1 page per lecture, must-memorize only
CREATE TABLE IF NOT EXISTS core_summaries (
    id              SERIAL PRIMARY KEY,
    lecture         VARCHAR(10) NOT NULL UNIQUE,
    title           TEXT NOT NULL,
    summary_md      TEXT NOT NULL,        -- KaTeX-ready, ~1500-2500 chars
    must_memorize   JSONB NOT NULL,       -- list of {fact, hint, slide_ref}
    one_line        TEXT NOT NULL,        -- single-sentence essence
    generated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Recall-style repeated quiz — short stem, 1-line answer, fast cycling
-- Different from quiz_items in that:
--  - All short_answer (no MCQ)
--  - Same fact may appear N times across lectures (cross-cut reinforcement)
--  - Designed for daily SRS-style repetition until 100% recall
CREATE TABLE IF NOT EXISTS recall_quiz (
    id              SERIAL PRIMARY KEY,
    lecture         VARCHAR(10) NOT NULL,
    position        INTEGER NOT NULL,
    fact_tag        TEXT NOT NULL,        -- canonical key for cross-cut grouping (e.g., 'C_m_value')
    prompt          TEXT NOT NULL,        -- short stem
    answer          TEXT NOT NULL,        -- canonical 1-liner answer
    accept_patterns JSONB NOT NULL,       -- regex patterns for grading
    slide_ref       TEXT,
    difficulty      INTEGER CHECK (difficulty BETWEEN 1 AND 3),  -- recall is mostly D1
    UNIQUE(lecture, position)
);
CREATE INDEX IF NOT EXISTS idx_recall_lecture ON recall_quiz(lecture, position);
CREATE INDEX IF NOT EXISTS idx_recall_tag ON recall_quiz(fact_tag);

COMMENT ON TABLE core_summaries IS 'Compressed 1-page exam-ready cores per lecture (must-memorize facts).';
COMMENT ON TABLE recall_quiz IS 'Short-answer repeated-question pool for must-memorize facts; cycle until 100%.';
