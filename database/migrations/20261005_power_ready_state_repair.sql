-- POWER-AI-WEB v1.7.1
-- One-time production state repair after legacy seed reset is_power_ready.
-- This migration does NOT modify curriculum content, blueprints, questions,
-- concepts, sources, learner data, or authentication data.

UPDATE curriculum_units AS cu
SET is_power_ready = TRUE
WHERE cu.catalog_visible = TRUE
  AND cu.lesson_number IS NOT NULL
  AND cu.power_status = 'ready'
  AND cu.is_power_ready IS DISTINCT FROM TRUE
  AND EXISTS (
      SELECT 1
      FROM power_unit_blueprints AS pub
      WHERE pub.curriculum_unit_id = cu.id
  );
