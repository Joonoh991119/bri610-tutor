-- v0.7.6 — Make srs_cards polymorphic (legacy question_bank OR new quiz_items)

-- Step 1: relax bank_item_id to be nullable + add source-aware columns
ALTER TABLE srs_cards
    ALTER COLUMN bank_item_id DROP NOT NULL;

ALTER TABLE srs_cards
    ADD COLUMN IF NOT EXISTS quiz_item_id INTEGER REFERENCES quiz_items(id) ON DELETE CASCADE,
    ADD COLUMN IF NOT EXISTS source_kind  TEXT NOT NULL DEFAULT 'legacy_bank'
        CHECK (source_kind IN ('legacy_bank', 'quiz_item'));

-- Step 2: Exactly one of (bank_item_id, quiz_item_id) must be set
ALTER TABLE srs_cards
    DROP CONSTRAINT IF EXISTS srs_cards_one_source_check;
ALTER TABLE srs_cards
    ADD  CONSTRAINT srs_cards_one_source_check CHECK (
        (bank_item_id IS NOT NULL AND quiz_item_id IS NULL)
     OR (bank_item_id IS NULL     AND quiz_item_id IS NOT NULL)
    );

-- Step 3: Unique constraint per source — drop old (user_id, bank_item_id) UNIQUE and add two partial uniques
ALTER TABLE srs_cards
    DROP CONSTRAINT IF EXISTS srs_cards_user_id_bank_item_id_key;

CREATE UNIQUE INDEX IF NOT EXISTS srs_cards_user_legacy_uidx
    ON srs_cards(user_id, bank_item_id) WHERE bank_item_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS srs_cards_user_quiz_uidx
    ON srs_cards(user_id, quiz_item_id) WHERE quiz_item_id IS NOT NULL;

-- Step 4: Auto-populate srs_cards from quiz_items for default user (id=1) — initial seed
INSERT INTO srs_cards (user_id, quiz_item_id, source_kind, state, due)
SELECT 1, q.id, 'quiz_item', 'New', now()
FROM quiz_items q
WHERE NOT EXISTS (
    SELECT 1 FROM srs_cards s
    WHERE s.user_id = 1 AND s.quiz_item_id = q.id
);

COMMENT ON COLUMN srs_cards.source_kind IS 'Polymorphic: ''legacy_bank'' (question_bank) or ''quiz_item'' (quiz_items)';
COMMENT ON COLUMN srs_cards.quiz_item_id IS 'FK to quiz_items.id when source_kind=quiz_item';
