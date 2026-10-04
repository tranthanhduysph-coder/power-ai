-- POWER AI v0.8 — durable Rethink evidence, misconception signals, and next-action recommendations.

CREATE TABLE IF NOT EXISTS question_misconceptions (
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    misconception_id UUID NOT NULL REFERENCES misconceptions(id) ON DELETE CASCADE,
    evidence_weight NUMERIC(5,4) NOT NULL DEFAULT 0.5000 CHECK (evidence_weight > 0 AND evidence_weight <= 0.9500),
    PRIMARY KEY(question_id, misconception_id)
);

CREATE TABLE IF NOT EXISTS misconception_evidence (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    learning_session_id UUID REFERENCES learning_sessions(id) ON DELETE SET NULL,
    misconception_id UUID NOT NULL REFERENCES misconceptions(id) ON DELETE CASCADE,
    concept_id UUID NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    evidence_type TEXT NOT NULL,
    evidence_object_id TEXT,
    confidence NUMERIC(5,4) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_misconception_evidence_user_time
    ON misconception_evidence(user_id, created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS uq_misconception_evidence_session_signal
    ON misconception_evidence(learning_session_id, misconception_id, evidence_type, evidence_object_id);

CREATE TABLE IF NOT EXISTS learning_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    learning_session_id UUID REFERENCES learning_sessions(id) ON DELETE SET NULL,
    curriculum_unit_id UUID REFERENCES curriculum_units(id) ON DELETE SET NULL,
    recommendation_type TEXT NOT NULL,
    priority INTEGER NOT NULL DEFAULT 3,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'acted', 'dismissed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    acted_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_learning_recommendations_user_status
    ON learning_recommendations(user_id, status, created_at DESC);
