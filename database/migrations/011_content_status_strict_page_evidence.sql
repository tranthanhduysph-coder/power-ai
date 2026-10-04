-- POWER AI v1.1.3 — strict per-unit content evidence reconciliation.
-- A curriculum unit is ingested only when its own mapped PDF range is explicit
-- AND at least one durable content chunk overlaps that range.
-- Do not treat NULL page mappings as wildcard matches, and do not infer all
-- units are ingested merely because the source row is marked ready.

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
      JOIN content_chunks cc ON cc.source_id = cus.source_id
      WHERE cus.curriculum_unit_id = cu.id
        AND cus.pdf_page_start IS NOT NULL
        AND cus.pdf_page_end IS NOT NULL
        AND cc.page_start IS NOT NULL
        AND cc.page_end IS NOT NULL
        AND cc.page_end >= cus.pdf_page_start
        AND cc.page_start <= cus.pdf_page_end
  );
