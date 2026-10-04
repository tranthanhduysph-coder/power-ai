-- POWER AI v1.1.1 — reconcile per-unit content state with actually ingested source sections.
-- v1.1 migration 008 treated any unit mapped to a ready source as ingested.
-- v0.9 had pre-created source mappings for the full textbook catalog, so that rule
-- could mark untouched units as ingested. Recompute from section/chunk evidence.

UPDATE curriculum_units cu
SET content_status = 'not_ingested',
    content_updated_at = NULL
WHERE cu.catalog_visible = true
  AND cu.unit_type IN ('lesson','practice','project');

UPDATE curriculum_units cu
SET content_status = 'ingested',
    content_updated_at = now()
WHERE cu.catalog_visible = true
  AND cu.unit_type IN ('lesson','practice','project')
  AND EXISTS (
      SELECT 1
      FROM source_sections ss
      JOIN sources s ON s.id = ss.source_id
      WHERE ss.code = cu.code
        AND s.ingest_status = 'ready'
        AND EXISTS (
            SELECT 1 FROM content_chunks cc
            WHERE cc.section_id = ss.id
        )
  );
