# POWER AI v0.4 — POWER learning cycle foundation

v0.4 moves the product from a generic lesson/chat vertical slice toward the original POWER-Biology learning model.

## Product rule

POWER is not five tabs and not a chatbot wrapper. A learning cycle is stateful:

`PREPARE → ORGANIZE → WORK → EVALUATE → RETHINK → next cycle`

Each phase creates learner-owned evidence. The software persists that evidence, derives learner context from it, and changes Tutor behavior by phase.

## What v0.4 implements

### PREPARE (full first vertical slice)

- curriculum outcomes are visible before studying;
- learner writes their own goal;
- deterministic SMART feedback supports, but does not replace, the learner's goal;
- target session duration and pre-learning confidence are recorded;
- learner can state prior knowledge in their own words;
- a short prerequisite diagnostic captures readiness without counting as a graded practice set;
- diagnostic answers, SMART result, confidence, and readiness are stored in `power_phase_state.state_json`;
- events `prepare_saved` and `prepare_completed` are appended to `learning_events`.

### Session continuity

`POST /power/sessions` now resumes the latest active cycle for the same user/unit rather than creating duplicate active cycles.

The API also exposes the current phase plus persisted state for all phase records.

### Phase-aware Tutor

Tutor requests may include a POWER session. The server loads the current phase and Prepare context (goal, confidence, readiness, weak prerequisites) and changes tutoring behavior:

- PREPARE: clarify readiness and goals; do not teach the whole lesson;
- ORGANIZE: prioritize relationships and structure;
- WORK: explain and scaffold;
- EVALUATE: avoid simply revealing answers to active assessment;
- RETHINK: diagnose errors and prompt concrete adjustment.

### Cycle completion

Completing RETHINK marks the underlying `learning_sessions` record as completed. Reloading the lesson can then create a new cycle.

## Deliberate implementation choice

v0.4 uses the existing append-only `learning_events` plus `power_phase_state` JSONB instead of creating a separate table for every phase artifact. This keeps phase evidence flexible while the POWER interaction model is still stabilizing. Stable, repeatedly queried evidence can be normalized into dedicated tables later.

## Next milestone

v0.5 should make ORGANIZE a first-class activity (editable concept organization / relationship evidence) and connect EVALUATE completion to actual practice evidence rather than a confirmation button.
