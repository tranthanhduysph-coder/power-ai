-- POWER AI v1.1 — content-build state separated from POWER-ready state.

ALTER TABLE curriculum_units
    ADD COLUMN IF NOT EXISTS content_status TEXT NOT NULL DEFAULT 'not_ingested',
    ADD COLUMN IF NOT EXISTS content_updated_at TIMESTAMPTZ;

ALTER TABLE curriculum_units
    DROP CONSTRAINT IF EXISTS curriculum_units_content_status_check;
ALTER TABLE curriculum_units
    ADD CONSTRAINT curriculum_units_content_status_check
    CHECK (content_status IN ('not_ingested', 'planned', 'ingested', 'failed'));

CREATE INDEX IF NOT EXISTS idx_curriculum_units_content_status
    ON curriculum_units(grade_id, content_status)
    WHERE catalog_visible = true;

-- Preserve already-ingested pilot units (for example B12_DNA_REPLICATION).
UPDATE curriculum_units cu
SET content_status = 'ingested',
    content_updated_at = COALESCE(content_updated_at, now())
WHERE EXISTS (
    SELECT 1
    FROM curriculum_unit_sources cus
    JOIN sources s ON s.id = cus.source_id
    WHERE cus.curriculum_unit_id = cu.id
      AND s.ingest_status = 'ready'
);
