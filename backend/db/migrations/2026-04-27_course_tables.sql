-- 1-hour compact L2~L8 course tables
-- 28 curated questions (4 per lecture × 7), 70% mandatory + 30% applied,
-- slides-only knowledge.

CREATE TABLE IF NOT EXISTS course_questions (
  id SERIAL PRIMARY KEY,
  lecture VARCHAR(10) NOT NULL,
  segment_position INT NOT NULL,
  kind VARCHAR(16) NOT NULL CHECK (kind IN ('mandatory', 'applied')),
  prompt_md TEXT NOT NULL,
  answer_md TEXT NOT NULL,
  rationale_md TEXT NOT NULL,
  slide_page INT,
  topic_tag TEXT,
  expected_time_s INT NOT NULL DEFAULT 90,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (lecture, segment_position)
);

CREATE INDEX IF NOT EXISTS idx_course_questions_lecture
  ON course_questions(lecture, segment_position);

CREATE TABLE IF NOT EXISTS course_runs (
  id SERIAL PRIMARY KEY,
  user_id INT NOT NULL,
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  current_question_id INT,
  current_index INT NOT NULL DEFAULT 0,
  correct_count INT NOT NULL DEFAULT 0,
  total_attempted INT NOT NULL DEFAULT 0,
  status VARCHAR(16) NOT NULL DEFAULT 'in_progress'
    CHECK (status IN ('in_progress', 'completed', 'abandoned')),
  total_time_s INT NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_course_runs_user
  ON course_runs(user_id, status);

CREATE TABLE IF NOT EXISTS course_responses (
  id SERIAL PRIMARY KEY,
  run_id INT NOT NULL REFERENCES course_runs(id) ON DELETE CASCADE,
  question_id INT NOT NULL REFERENCES course_questions(id),
  user_answer_md TEXT,
  correct BOOLEAN,
  time_spent_s INT NOT NULL DEFAULT 0,
  attempted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  attempt_num INT NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_course_responses_run
  ON course_responses(run_id, attempted_at);
