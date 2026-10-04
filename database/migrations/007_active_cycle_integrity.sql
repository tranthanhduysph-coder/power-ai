-- POWER AI v1.0.1
-- Repair historical duplicate active learning cycles and prevent recurrence.
--
-- A learner may have only one active learning_session for the same curriculum unit.
-- Older duplicate sessions are preserved as abandoned, not deleted, so their POWER
-- phase evidence remains available in cycle history.

WITH ranked AS (
    SELECT
        ls.id,
        ROW_NUMBER() OVER (
            PARTITION BY ls.user_id, ls.curriculum_unit_id
            ORDER BY
                COALESCE(ps.updated_at, ls.started_at) DESC,
                ls.started_at DESC,
                ls.id DESC
        ) AS rn
    FROM learning_sessions ls
    LEFT JOIN power_sessions ps ON ps.learning_session_id = ls.id
    WHERE ls.status = 'active'
      AND ls.curriculum_unit_id IS NOT NULL
)
UPDATE learning_sessions ls
SET status = 'abandoned',
    ended_at = COALESCE(ls.ended_at, now())
FROM ranked r
WHERE ls.id = r.id
  AND r.rn > 1;

CREATE UNIQUE INDEX IF NOT EXISTS uq_learning_sessions_one_active_per_user_unit
ON learning_sessions(user_id, curriculum_unit_id)
WHERE status = 'active' AND curriculum_unit_id IS NOT NULL;
