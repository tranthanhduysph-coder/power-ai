-- POWER AI v1.2 — source-grounded POWER blueprint drafts and readiness workflow.

ALTER TABLE curriculum_units
    ADD COLUMN IF NOT EXISTS power_status TEXT NOT NULL DEFAULT 'not_started';

ALTER TABLE curriculum_units
    DROP CONSTRAINT IF EXISTS curriculum_units_power_status_check;
ALTER TABLE curriculum_units
    ADD CONSTRAINT curriculum_units_power_status_check
    CHECK (power_status IN ('not_started','draft','validated','ready','failed'));

UPDATE curriculum_units
SET power_status = CASE WHEN is_power_ready THEN 'ready' ELSE power_status END;

ALTER TABLE power_unit_blueprints
    ADD COLUMN IF NOT EXISTS generation_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS validation_json JSONB NOT NULL DEFAULT '{}'::jsonb;

CREATE TABLE IF NOT EXISTS power_blueprint_drafts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    curriculum_unit_id UUID NOT NULL REFERENCES curriculum_units(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','validated','activated','failed')),
    payload_json JSONB NOT NULL,
    validation_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    source_fingerprint TEXT NOT NULL,
    model TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    activated_at TIMESTAMPTZ,
    UNIQUE(curriculum_unit_id, version)
);
CREATE INDEX IF NOT EXISTS idx_power_blueprint_drafts_unit_status
    ON power_blueprint_drafts(curriculum_unit_id, status, version DESC);
