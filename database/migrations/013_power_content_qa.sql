-- POWER AI v1.3 — batch content QA/review workflow for generated POWER packages.

ALTER TABLE power_blueprint_drafts
    ADD COLUMN IF NOT EXISTS qa_status TEXT NOT NULL DEFAULT 'pending',
    ADD COLUMN IF NOT EXISTS qa_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS qa_checked_at TIMESTAMPTZ;

ALTER TABLE power_blueprint_drafts
    DROP CONSTRAINT IF EXISTS power_blueprint_drafts_qa_status_check;
ALTER TABLE power_blueprint_drafts
    ADD CONSTRAINT power_blueprint_drafts_qa_status_check
    CHECK (qa_status IN ('pending','passed','failed'));

CREATE INDEX IF NOT EXISTS idx_power_blueprint_drafts_qa
    ON power_blueprint_drafts(qa_status, curriculum_unit_id, version DESC);
