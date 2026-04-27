-- Migration 003: v0.5 dual-column embedding (P2.1)
-- Why: Adds text_embedding_v2 (1024-dim) to slides + textbook_pages so we can
-- A/B Qwen3-Embedding-8B (Korean+English STEM #1 on MMTEB) against the existing
-- 2048-dim Nemotron VL column.
--
-- IMPORTANT: This migration must be applied BY THE TABLE OWNER. On this Mac
-- the legacy v0.4 tables are owned by `joonoh`, so:
--    psql -d bri610 -U joonoh -f pipeline/migrations/003_v05_dual_embedding.sql
--
-- Idempotent.

DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'textbook_pages' AND column_name = 'text_embedding_v2'
    ) THEN
        ALTER TABLE public.textbook_pages
            ADD COLUMN text_embedding_v2 public.vector(1024);
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'slides' AND column_name = 'text_embedding_v2'
    ) THEN
        ALTER TABLE public.slides
            ADD COLUMN text_embedding_v2 public.vector(1024);
    END IF;
END $$;
