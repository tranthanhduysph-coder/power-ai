-- POWER v0.7: bind Practice/Evaluate evidence to a specific POWER learning cycle.
ALTER TABLE practice_sets
    ADD COLUMN IF NOT EXISTS power_session_id UUID REFERENCES power_sessions(id) ON DELETE SET NULL;

ALTER TABLE practice_sets
    ADD COLUMN IF NOT EXISTS purpose TEXT NOT NULL DEFAULT 'standalone';

ALTER TABLE practice_sets
    DROP CONSTRAINT IF EXISTS practice_sets_purpose_check;

ALTER TABLE practice_sets
    ADD CONSTRAINT practice_sets_purpose_check
    CHECK (purpose IN ('standalone', 'evaluate'));

CREATE INDEX IF NOT EXISTS idx_practice_sets_power_session
    ON practice_sets(power_session_id, created_at DESC);
