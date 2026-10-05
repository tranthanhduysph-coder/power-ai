-- POWER AI v1.1.2 — reconcile content status from durable unit↔source page mappings.
-- Do not rely on source_sections.code matching curriculum_units.code: section codes
-- can differ across historical ingestion runs. A unit is ingested when a mapped,
-- ready source contains at least one chunk overlapping that unit's mapped PDF range.

UPDATE curriculum_units cu
SET content_status = 'not_ingested',
    content_updated_at = NULL
WHERE cu.catalog_visible = true
  AND cu.lesson_number IS NOT NULL
  AND cu.unit_type IN ('lesson','practice','project');

UPDATE curriculum_units cu
SET content_status = 'ingested',
    content_updated_at = now()
WHERE cu.catalog_visible = true
  AND cu.lesson_number IS NOT NULL
  AND cu.unit_type IN ('lesson','practice','project')
  AND EXISTS (
      SELECT 1
      FROM curriculum_unit_sources cus
      JOIN sources s ON s.id = cus.source_id
      JOIN content_chunks cc ON cc.source_id = s.id
      WHERE cus.curriculum_unit_id = cu.id
        AND s.ingest_status = 'ready'
        AND (cus.pdf_page_start IS NULL OR cc.page_end >= cus.pdf_page_start)
        AND (cus.pdf_page_end IS NULL OR cc.page_start <= cus.pdf_page_end)
  );
