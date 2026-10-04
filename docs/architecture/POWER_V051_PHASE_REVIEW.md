# POWER AI v0.5.1 — Phase Review & Cycle History

## Why this hotfix exists
POWER is a regulated learning cycle, not a one-way wizard. Completing a phase records evidence and advances the current progression, but it must not make earlier learning evidence inaccessible. Learners need to revisit Prepare and Organize during Work/Evaluate/Rethink, and they must be able to inspect a completed cycle before starting another one.

## Product behavior
- `current_phase` remains the learner's progression position.
- `view_phase` is client-side navigation only; reviewing an earlier phase never moves progress backward.
- Completed phase cards remain clickable.
- Prepare and Organize can be edited after completion without clearing `completed_at` and without regressing `current_phase`.
- A completed POWER cycle remains reviewable after reload.
- The learner explicitly starts a new cycle rather than the application silently replacing a completed cycle.
- Recent cycles are available from a cycle selector, including a previously completed cycle when an active cycle already exists.

## API changes
- `POST /power/sessions` accepts `force_new` (default `false`).
- With no active cycle and `force_new=false`, the latest completed cycle is returned for review.
- `GET /power/sessions/history` returns recent cycles for the selected curriculum unit.
- Updating completed Prepare/Organize evidence preserves the actual current progression phase.

## POWER semantics
Completion means "evidence collected for this phase", not "locked forever". Review and revision are part of self-regulated learning, especially during Rethink. A new cycle is a separate learning attempt and is created explicitly.
