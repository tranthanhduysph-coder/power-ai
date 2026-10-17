-- Research Analytics v1: keep identity separate from research exports.
-- Existing tables learning_events, power_sessions, mastery_snapshots stay unchanged.
CREATE TABLE IF NOT EXISTS research_consent (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    survey_response_ref TEXT NOT NULL,
    survey_version TEXT NOT NULL,
    consented_at TIMESTAMPTZ NOT NULL,
    activity_scope_start_at TIMESTAMPTZ NOT NULL,
    research_allowed BOOLEAN NOT NULL DEFAULT false,
    improvement_allowed BOOLEAN NOT NULL DEFAULT false,
    required_authorizations_verified BOOLEAN NOT NULL DEFAULT false,
    recorded_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (length(trim(survey_response_ref)) > 0),
    CHECK (length(trim(survey_version)) > 0),
    CHECK (activity_scope_start_at <= consented_at)
);
CREATE INDEX IF NOT EXISTS idx_research_consent_allowed
    ON research_consent (research_allowed, activity_scope_start_at);

CREATE TABLE IF NOT EXISTS research_consent_audit (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    survey_response_ref TEXT NOT NULL,
    survey_version TEXT NOT NULL,
    consented_at TIMESTAMPTZ NOT NULL,
    activity_scope_start_at TIMESTAMPTZ NOT NULL,
    research_allowed BOOLEAN NOT NULL,
    improvement_allowed BOOLEAN NOT NULL,
    required_authorizations_verified BOOLEAN NOT NULL,
    recorded_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_research_consent_audit_user
    ON research_consent_audit (user_id, recorded_at DESC);

CREATE TABLE IF NOT EXISTS research_export_audit (
    id BIGSERIAL PRIMARY KEY,
    actor_user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    dataset TEXT NOT NULL,
    rows_exported INTEGER NOT NULL,
    filters JSONB NOT NULL DEFAULT '{}'::jsonb,
    exported_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_research_export_audit_actor
    ON research_export_audit (actor_user_id, exported_at DESC);

CREATE INDEX IF NOT EXISTS idx_mastery_snapshots_user_time
    ON mastery_snapshots(user_id, captured_at DESC);
