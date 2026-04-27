-- Migration 002: v0.5 schema additions
-- Consolidates Group A schema deltas from the v0.5 revised plan:
--   P0.8         users + mastery + sessions
--   P7.1         question_bank + question_review_log + lens_disagreement_log
--   P9.1         foundation_content
--   R1 figures   figures table (with bbox + dual-modal embeddings)
--   P10.5        analytics_events
--
-- Idempotent: every CREATE uses IF NOT EXISTS.
-- Apply with: psql -d bri610 -U tutor -f pipeline/migrations/002_v05_schema.sql

BEGIN;

-- ──────────────────────────────────────────────────────────────────
-- R3 — users + sessions + mastery
-- ──────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.users (
    id                SERIAL PRIMARY KEY,
    email             text UNIQUE NOT NULL,
    display_name      text,
    created_at        timestamptz DEFAULT now(),
    -- gamification (R3)
    streak_days       integer    DEFAULT 0,
    streak_last_date  date,
    xp                integer    DEFAULT 0,
    level             integer    DEFAULT 1,
    badges            jsonb      DEFAULT '[]'::jsonb,
    persona_voice     text       DEFAULT '뉴런쌤',
    daily_goal_min    integer    DEFAULT 20
);

-- Seed the single owner user (J) so foreign keys can resolve immediately
INSERT INTO public.users (email, display_name)
VALUES ('joonop99@snu.ac.kr', '준오')
ON CONFLICT (email) DO NOTHING;

CREATE TABLE IF NOT EXISTS public.sessions (
    id          SERIAL PRIMARY KEY,
    user_id     integer REFERENCES public.users(id) ON DELETE CASCADE,
    started_at  timestamptz DEFAULT now(),
    ended_at    timestamptz,
    strict_mode boolean DEFAULT false,    -- P4.8 mode lock
    metadata    jsonb DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_started
    ON public.sessions (user_id, started_at DESC);

CREATE TABLE IF NOT EXISTS public.mastery (
    user_id    integer NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    topic      text    NOT NULL,
    card_type  text    NOT NULL CHECK (card_type IN ('recall','concept','application','proof')),
    score      double precision NOT NULL DEFAULT 0,   -- 0..1, EMA over recent reviews
    reps       integer NOT NULL DEFAULT 0,
    lapses     integer NOT NULL DEFAULT 0,
    updated_at timestamptz DEFAULT now(),
    PRIMARY KEY (user_id, topic, card_type)
);

-- ──────────────────────────────────────────────────────────────────
-- R1 — figures (block-level extracted images with bbox + dual-modal embedding)
-- ──────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.figures (
    id                 SERIAL PRIMARY KEY,
    source             text NOT NULL CHECK (source IN ('slide','textbook','web','foundation')),
    lecture            text,                     -- e.g. 'L5'
    book               text,                     -- e.g. 'DA' or 'FN'
    page               integer,
    bbox               double precision[],       -- [x0,y0,x1,y1] in PDF points
    caption            text,
    caption_ko         text,
    img_path           text NOT NULL,            -- relative to data/figures/
    img_embedding      public.vector(2048),      -- Nemotron VL on the crop
    caption_embedding  public.vector(1024),      -- Qwen3 on the caption
    created_at         timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_figures_source_lecture
    ON public.figures (source, lecture, page);

-- HNSW index on caption embedding for fast semantic figure lookup
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_figures_caption_hnsw') THEN
        EXECUTE 'CREATE INDEX idx_figures_caption_hnsw
                 ON public.figures USING hnsw (caption_embedding public.vector_cosine_ops)';
    END IF;
EXCEPTION WHEN feature_not_supported THEN
    -- pgvector < 0.5 does not have HNSW; fall back to ivfflat
    NULL;
END $$;

-- ──────────────────────────────────────────────────────────────────
-- R2 / R4 — question_bank (4 card types, citation-grounded, priority/info-density)
-- ──────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.question_bank (
    id              SERIAL PRIMARY KEY,
    topic           text NOT NULL,
    card_type       text NOT NULL CHECK (card_type IN ('recall','concept','application','proof')),
    difficulty      integer NOT NULL CHECK (difficulty BETWEEN 1 AND 5),
    bloom           text CHECK (bloom IN ('Remember','Understand','Apply','Analyze','Evaluate','Create')),
    prompt_md       text NOT NULL,                -- KaTeX-ready markdown
    answer_md       text NOT NULL,
    rationale_md    text NOT NULL,                -- post-hoc explanation
    source_citation jsonb NOT NULL,               -- {kind:'textbook',book:'DA',ch:5,page:119}
    priority_score  double precision NOT NULL DEFAULT 0.5,
    info_density    double precision NOT NULL DEFAULT 0.5,
    is_prereq       boolean DEFAULT false,
    mastery_target  text,                         -- which concept-id this contributes mastery to
    status          text DEFAULT 'active' CHECK (status IN ('active','retired','manual_review','draft')),
    figure_id       integer REFERENCES public.figures(id),
    created_at      timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_qb_topic_type_status
    ON public.question_bank (topic, card_type, status);
CREATE INDEX IF NOT EXISTS idx_qb_priority
    ON public.question_bank (priority_score DESC);

-- SRS card layer (lives alongside the bank, but per-user)
CREATE TABLE IF NOT EXISTS public.srs_cards (
    id            SERIAL PRIMARY KEY,
    user_id       integer NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    bank_item_id  integer NOT NULL REFERENCES public.question_bank(id) ON DELETE CASCADE,
    -- FSRS-6 state
    state         text NOT NULL DEFAULT 'New' CHECK (state IN ('New','Learning','Review','Relearning')),
    stability     double precision DEFAULT 0,
    difficulty    double precision DEFAULT 0,
    due           timestamptz,
    last_review   timestamptz,
    reps          integer NOT NULL DEFAULT 0,
    lapses        integer NOT NULL DEFAULT 0,
    UNIQUE (user_id, bank_item_id)
);

CREATE INDEX IF NOT EXISTS idx_srs_user_due
    ON public.srs_cards (user_id, due ASC NULLS FIRST);

CREATE TABLE IF NOT EXISTS public.srs_reviews (
    id             SERIAL PRIMARY KEY,
    card_id        integer NOT NULL REFERENCES public.srs_cards(id) ON DELETE CASCADE,
    rating         integer NOT NULL CHECK (rating BETWEEN 1 AND 4),  -- 1=Again, 4=Easy
    elapsed_days   double precision,
    scheduled_days double precision,
    reviewed_at    timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_srs_reviews_card
    ON public.srs_reviews (card_id, reviewed_at DESC);

-- ──────────────────────────────────────────────────────────────────
-- Multi-Lens Review (P10.2)
-- ──────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.question_review_log (
    id             SERIAL PRIMARY KEY,
    artifact_kind  text NOT NULL CHECK (artifact_kind IN ('question','walkthrough_step','summary')),
    artifact_id    integer NOT NULL,
    round_num      integer NOT NULL CHECK (round_num BETWEEN 1 AND 5),
    lens           text NOT NULL CHECK (lens IN ('factual','pedagogical','korean','difficulty')),
    verdict        text NOT NULL CHECK (verdict IN ('pass','revise','reject')),
    reasoning      text,
    revised_text   text,
    reviewed_at    timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_qrl_artifact
    ON public.question_review_log (artifact_kind, artifact_id, round_num);

CREATE TABLE IF NOT EXISTS public.lens_disagreement_log (
    id             SERIAL PRIMARY KEY,
    artifact_id    integer,
    artifact_kind  text,
    round_num      integer,
    lenses_passing text[],
    lenses_failing text[],
    resolution     text CHECK (resolution IN ('converged','manual','rejected')),
    logged_at      timestamptz DEFAULT now()
);

-- ──────────────────────────────────────────────────────────────────
-- R5 — foundation_content (ODE / PDE / neuron anatomy from external sources)
-- ──────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.foundation_content (
    id              SERIAL PRIMARY KEY,
    source_kind     text NOT NULL CHECK (source_kind IN ('3b1b_diffeq','strogatz','kandel','ocw_mit','khan','wolfram_edu','web_other')),
    source_url      text,
    topic           text NOT NULL,                -- 'ODE_basic','PDE_basic','neuron_anatomy', ...
    title           text,
    body_md         text NOT NULL,
    body_ko         text,                         -- LLM-translated, lens-reviewed
    text_embedding  public.vector(1024),
    license         text NOT NULL DEFAULT 'unknown',  -- track for legal compliance
    ingested_at     timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_foundation_topic
    ON public.foundation_content (topic);

-- ──────────────────────────────────────────────────────────────────
-- P10.5 — analytics_events (telemetry)
-- ──────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.analytics_events (
    id          BIGSERIAL PRIMARY KEY,
    event_kind  text NOT NULL,
    user_id     integer REFERENCES public.users(id) ON DELETE SET NULL,
    session_id  text,
    agent       text,
    ms          integer,                          -- latency
    tokens_in   integer,
    tokens_out  integer,
    llm_route   text,                             -- e.g. 'openrouter:qwen', 'ollama:qwen3-30b-a3b'
    payload     jsonb,
    created_at  timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_analytics_kind_time
    ON public.analytics_events (event_kind, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analytics_user_time
    ON public.analytics_events (user_id, created_at DESC);

-- pgvector dual-column extension (P2.1) was here originally; split out into
-- 003_v05_dual_embedding.sql since slides/textbook_pages are owned by `joonoh`
-- and need to be ALTERed by that role, not by `tutor`.

COMMIT;
