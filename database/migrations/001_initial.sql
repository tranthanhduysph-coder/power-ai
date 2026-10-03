CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    firebase_uid TEXT NOT NULL UNIQUE,
    email TEXT,
    display_name TEXT,
    photo_url TEXT,
    role TEXT NOT NULL DEFAULT 'student' CHECK (role IN ('student', 'teacher', 'admin', 'parent')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_login_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT NOT NULL UNIQUE,
    name_vi TEXT NOT NULL,
    name_en TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS grades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    level INTEGER NOT NULL,
    name_vi TEXT NOT NULL,
    name_en TEXT NOT NULL,
    UNIQUE(subject_id, level)
);

CREATE TABLE IF NOT EXISTS learning_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    grade_level_id UUID REFERENCES grades(id) ON DELETE SET NULL,
    preferred_language TEXT NOT NULL DEFAULT 'vi' CHECK (preferred_language IN ('vi', 'en')),
    target_exam TEXT,
    preferred_session_minutes INTEGER DEFAULT 30,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS curriculum_units (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    grade_id UUID NOT NULL REFERENCES grades(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES curriculum_units(id) ON DELETE CASCADE,
    code TEXT NOT NULL UNIQUE,
    name_vi TEXT NOT NULL,
    name_en TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS concepts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT NOT NULL UNIQUE,
    parent_id UUID REFERENCES concepts(id) ON DELETE SET NULL,
    name_vi TEXT NOT NULL,
    name_en TEXT NOT NULL,
    description_vi TEXT,
    description_en TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS concept_relations (
    source_concept_id UUID NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    target_concept_id UUID NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    relation_type TEXT NOT NULL CHECK (relation_type IN ('prerequisite', 'related', 'part_of', 'contrasts_with', 'applied_in')),
    PRIMARY KEY(source_concept_id, target_concept_id, relation_type)
);

CREATE TABLE IF NOT EXISTS curriculum_concepts (
    curriculum_unit_id UUID NOT NULL REFERENCES curriculum_units(id) ON DELETE CASCADE,
    concept_id UUID NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    is_core BOOLEAN NOT NULL DEFAULT true,
    PRIMARY KEY(curriculum_unit_id, concept_id)
);

CREATE TABLE IF NOT EXISTS sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    language TEXT NOT NULL,
    grade_level INTEGER,
    edition TEXT,
    publisher TEXT,
    source_role TEXT NOT NULL CHECK (source_role IN ('curriculum', 'reference')),
    license_status TEXT NOT NULL DEFAULT 'review_required',
    storage_key TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS source_sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES source_sections(id) ON DELETE CASCADE,
    code TEXT,
    title TEXT NOT NULL,
    page_start INTEGER,
    page_end INTEGER,
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS content_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    section_id UUID REFERENCES source_sections(id) ON DELETE SET NULL,
    concept_id UUID REFERENCES concepts(id) ON DELETE SET NULL,
    language TEXT NOT NULL,
    page_start INTEGER,
    page_end INTEGER,
    text_content TEXT NOT NULL,
    token_count INTEGER,
    embedding vector(1536),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_content_chunks_concept ON content_chunks(concept_id);

CREATE TABLE IF NOT EXISTS visual_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT NOT NULL UNIQUE,
    concept_id UUID REFERENCES concepts(id) ON DELETE SET NULL,
    asset_type TEXT NOT NULL CHECK (asset_type IN ('image', 'svg', 'diagram', 'chart', 'table', 'animation', 'interactive')),
    storage_key TEXT,
    title_vi TEXT,
    title_en TEXT,
    caption_vi TEXT,
    caption_en TEXT,
    alt_text_vi TEXT,
    alt_text_en TEXT,
    source_type TEXT NOT NULL DEFAULT 'power',
    source_reference TEXT,
    license_type TEXT,
    is_ai_generated BOOLEAN NOT NULL DEFAULT false,
    is_reviewed BOOLEAN NOT NULL DEFAULT false,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT NOT NULL UNIQUE,
    question_type TEXT NOT NULL CHECK (question_type IN ('mcq', 'true_false', 'short_answer')),
    difficulty TEXT NOT NULL CHECK (difficulty IN ('easy', 'medium', 'hard')),
    cognitive_level TEXT NOT NULL CHECK (cognitive_level IN ('remember', 'understand', 'apply', 'high_apply')),
    stem_vi TEXT NOT NULL,
    stem_en TEXT NOT NULL,
    answer_json JSONB NOT NULL,
    explanation_vi TEXT,
    explanation_en TEXT,
    source_basis TEXT,
    is_ai_generated BOOLEAN NOT NULL DEFAULT false,
    review_status TEXT NOT NULL DEFAULT 'draft' CHECK (review_status IN ('draft', 'approved', 'retired')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS question_options (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    option_key TEXT NOT NULL,
    text_vi TEXT NOT NULL,
    text_en TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL DEFAULT false,
    UNIQUE(question_id, option_key)
);

CREATE TABLE IF NOT EXISTS question_concepts (
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    concept_id UUID NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    is_primary BOOLEAN NOT NULL DEFAULT false,
    PRIMARY KEY(question_id, concept_id)
);

CREATE TABLE IF NOT EXISTS misconceptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT NOT NULL UNIQUE,
    concept_id UUID NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    statement_vi TEXT NOT NULL,
    statement_en TEXT NOT NULL,
    correction_vi TEXT,
    correction_en TEXT
);

CREATE TABLE IF NOT EXISTS learner_misconceptions (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    misconception_id UUID NOT NULL REFERENCES misconceptions(id) ON DELETE CASCADE,
    concept_id UUID NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    confidence NUMERIC(5,4) NOT NULL DEFAULT 0.5000,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'resolved')),
    first_detected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_detected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY(user_id, misconception_id)
);

CREATE TABLE IF NOT EXISTS learning_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    curriculum_unit_id UUID REFERENCES curriculum_units(id) ON DELETE SET NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at TIMESTAMPTZ,
    current_power_phase TEXT NOT NULL DEFAULT 'PREPARE',
    language TEXT NOT NULL DEFAULT 'vi',
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'abandoned'))
);

CREATE TABLE IF NOT EXISTS learning_events (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    learning_session_id UUID REFERENCES learning_sessions(id) ON DELETE SET NULL,
    event_type TEXT NOT NULL,
    concept_id UUID REFERENCES concepts(id) ON DELETE SET NULL,
    object_id TEXT,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_learning_events_user_time ON learning_events(user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS power_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    learning_session_id UUID NOT NULL UNIQUE REFERENCES learning_sessions(id) ON DELETE CASCADE,
    current_phase TEXT NOT NULL DEFAULT 'PREPARE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS power_phase_state (
    power_session_id UUID NOT NULL REFERENCES power_sessions(id) ON DELETE CASCADE,
    phase TEXT NOT NULL CHECK (phase IN ('PREPARE', 'ORGANIZE', 'WORK', 'EVALUATE', 'RETHINK')),
    state_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY(power_session_id, phase)
);

CREATE TABLE IF NOT EXISTS practice_sets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    mode TEXT NOT NULL CHECK (mode IN ('custom', 'adaptive')),
    curriculum_unit_id UUID REFERENCES curriculum_units(id) ON DELETE SET NULL,
    requested_difficulty TEXT NOT NULL DEFAULT 'auto',
    requested_count INTEGER NOT NULL DEFAULT 10,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS practice_set_items (
    practice_set_id UUID NOT NULL REFERENCES practice_sets(id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    item_order INTEGER NOT NULL,
    PRIMARY KEY(practice_set_id, question_id)
);

CREATE TABLE IF NOT EXISTS practice_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    practice_set_id UUID NOT NULL REFERENCES practice_sets(id) ON DELETE CASCADE,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    accuracy NUMERIC(6,5),
    duration_seconds INTEGER
);

CREATE TABLE IF NOT EXISTS question_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    practice_attempt_id UUID NOT NULL REFERENCES practice_attempts(id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    concept_id UUID REFERENCES concepts(id) ON DELETE SET NULL,
    answer_json JSONB NOT NULL,
    is_correct BOOLEAN NOT NULL,
    response_time_ms INTEGER,
    hint_used BOOLEAN NOT NULL DEFAULT false,
    attempt_number INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_question_attempts_question_time ON question_attempts(question_id, created_at DESC);

CREATE TABLE IF NOT EXISTS concept_mastery (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    concept_id UUID NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    mastery_score NUMERIC(5,4) NOT NULL DEFAULT 0.5000 CHECK (mastery_score >= 0 AND mastery_score <= 1),
    confidence NUMERIC(5,4) NOT NULL DEFAULT 0.5000 CHECK (confidence >= 0 AND confidence <= 1),
    attempt_count INTEGER NOT NULL DEFAULT 0,
    correct_count INTEGER NOT NULL DEFAULT 0,
    last_practiced_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY(user_id, concept_id)
);

CREATE TABLE IF NOT EXISTS mastery_snapshots (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    concept_id UUID NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    mastery_score NUMERIC(5,4) NOT NULL,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT NOT NULL UNIQUE,
    name_vi TEXT NOT NULL,
    name_en TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    code TEXT NOT NULL UNIQUE,
    name_vi TEXT NOT NULL,
    name_en TEXT NOT NULL,
    billing_period TEXT NOT NULL DEFAULT 'free',
    price_amount NUMERIC(14,2) NOT NULL DEFAULT 0,
    currency TEXT NOT NULL DEFAULT 'VND',
    is_active BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS plan_entitlements (
    plan_id UUID NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
    feature_code TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT true,
    limit_value INTEGER,
    PRIMARY KEY(plan_id, feature_code)
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_id UUID NOT NULL REFERENCES plans(id) ON DELETE RESTRICT,
    status TEXT NOT NULL CHECK (status IN ('active', 'expired', 'cancelled', 'pending')),
    starts_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS usage_ledger (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    feature TEXT NOT NULL,
    quantity NUMERIC(12,3) NOT NULL DEFAULT 1,
    model TEXT,
    estimated_cost NUMERIC(14,6),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_usage_ledger_user_time ON usage_ledger(user_id, created_at DESC);
