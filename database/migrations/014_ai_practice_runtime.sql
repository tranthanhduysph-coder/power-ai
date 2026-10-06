-- POWER-AI-WEB: isolate on-demand AI practice from the validated question bank.
-- No existing questions, content, blueprints, or learner mastery rows are modified.

ALTER TABLE practice_sets
    DROP CONSTRAINT IF EXISTS practice_sets_mode_check;

ALTER TABLE practice_sets
    ADD CONSTRAINT practice_sets_mode_check
    CHECK (mode IN ('custom', 'adaptive', 'ai'));

ALTER TABLE practice_sets
    ADD COLUMN IF NOT EXISTS generated_items JSONB NOT NULL DEFAULT '[]'::jsonb;

ALTER TABLE practice_attempts
    ADD COLUMN IF NOT EXISTS response_json JSONB NOT NULL DEFAULT '{}'::jsonb;
