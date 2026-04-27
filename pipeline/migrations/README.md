# Migrations — bri610-tutor

Migrations are applied in numeric order. Each is idempotent (`IF NOT EXISTS` everywhere) so re-applying is safe.

| # | File | Purpose |
|---|---|---|
| 001 | `001_lecture_summaries.sql` | Adds the `lecture_summaries` table that v0.4 referenced but never declared in `pipeline/schema.sql`. |
| 002 | `002_v05_schema.sql` | v0.5 schema delta: `users`, `sessions`, `mastery`, `figures`, `question_bank`, `srs_cards`, `srs_reviews`, `question_review_log`, `lens_disagreement_log`, `foundation_content`, `analytics_events`, plus `text_embedding_v2 vector(1024)` on `slides` and `textbook_pages`. |

## Apply

```bash
# Existing v0.4 DB upgrade to v0.5
for f in pipeline/migrations/00*.sql; do
  echo "→ applying $f"
  psql -d bri610 -U tutor -f "$f"
done
```

## Fresh setup

```bash
# 1. base v0.4 schema
psql -d bri610 -U tutor -f pipeline/schema.sql
# 2. then all migrations
for f in pipeline/migrations/00*.sql; do
  psql -d bri610 -U tutor -f "$f"
done
```

## Convention

- Filename: `NNN_short_description.sql`, zero-padded 3 digits.
- Wrap in `BEGIN; … COMMIT;` so partial failures roll back.
- Use `IF NOT EXISTS` on every CREATE; use a `DO $$ … $$` guard for ALTER COLUMN.
- Document the WHY in a comment header (which v0.5 phase + which atomic step ID).
