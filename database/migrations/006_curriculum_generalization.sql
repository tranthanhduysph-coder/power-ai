-- POWER AI v0.9 — database-driven curriculum catalog and POWER unit blueprints.

ALTER TABLE curriculum_units
    ADD COLUMN IF NOT EXISTS unit_type TEXT NOT NULL DEFAULT 'lesson',
    ADD COLUMN IF NOT EXISTS lesson_number INTEGER,
    ADD COLUMN IF NOT EXISTS printed_page_start INTEGER,
    ADD COLUMN IF NOT EXISTS printed_page_end INTEGER,
    ADD COLUMN IF NOT EXISTS is_power_ready BOOLEAN NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS catalog_visible BOOLEAN NOT NULL DEFAULT true,
    ADD COLUMN IF NOT EXISTS metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb;

ALTER TABLE curriculum_units
    DROP CONSTRAINT IF EXISTS curriculum_units_unit_type_check;
ALTER TABLE curriculum_units
    ADD CONSTRAINT curriculum_units_unit_type_check
    CHECK (unit_type IN ('part', 'chapter', 'lesson', 'practice', 'project', 'legacy'));

CREATE INDEX IF NOT EXISTS idx_curriculum_units_catalog
    ON curriculum_units(grade_id, parent_id, sort_order)
    WHERE catalog_visible = true;
CREATE INDEX IF NOT EXISTS idx_curriculum_units_power_ready
    ON curriculum_units(is_power_ready, grade_id)
    WHERE catalog_visible = true;

CREATE TABLE IF NOT EXISTS curriculum_unit_sources (
    curriculum_unit_id UUID NOT NULL REFERENCES curriculum_units(id) ON DELETE CASCADE,
    source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    source_role TEXT NOT NULL DEFAULT 'primary' CHECK (source_role IN ('primary', 'reference', 'supplemental')),
    printed_page_start INTEGER,
    printed_page_end INTEGER,
    pdf_page_start INTEGER,
    pdf_page_end INTEGER,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY(curriculum_unit_id, source_id, source_role)
);
CREATE INDEX IF NOT EXISTS idx_curriculum_unit_sources_source
    ON curriculum_unit_sources(source_id, curriculum_unit_id);

CREATE TABLE IF NOT EXISTS power_unit_blueprints (
    curriculum_unit_id UUID PRIMARY KEY REFERENCES curriculum_units(id) ON DELETE CASCADE,
    version INTEGER NOT NULL DEFAULT 1,
    prepare_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    work_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    policy_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
