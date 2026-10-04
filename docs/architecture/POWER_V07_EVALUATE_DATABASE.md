# POWER AI v0.7 — Database-backed Evaluate

## Product intent

Evaluate must be evidence-driven. A learner cannot complete E by clicking a self-report button. A real Practice attempt is linked to the current POWER cycle and becomes the persisted evidence for E.

## Data flow

```text
POWER session (EVALUATE)
        ↓
practice_sets.power_session_id + purpose='evaluate'
        ↓
practice_attempts
        ↓
question_attempts
        ↓
concept_mastery
        ↓
POWER EVALUATE state_json
        ↓
RETHINK
```

## Database linkage added in v0.7

`practice_sets` receives:

- `power_session_id UUID NULL REFERENCES power_sessions(id)`
- `purpose TEXT NOT NULL DEFAULT 'standalone'`

Standalone practice remains supported. Only an Evaluate set is required to belong to a POWER cycle.

## Completion rule

On submission of an Evaluate set:

1. answers are scored;
2. `question_attempts` are stored;
3. `concept_mastery` is updated;
4. concept-level evidence is summarized;
5. `power_phase_state(EVALUATE)` is completed;
6. the POWER cycle advances to `RETHINK`;
7. a `evaluate_completed` learning event is written.

The previous manual "I completed practice" action is removed.

## Local database status

The local build already uses PostgreSQL + pgvector. v0.7 does not introduce a new database product; it completes an important relationship between Practice and the POWER learner-state database.

A later milestone will generalize curriculum/content beyond the current DNA vertical slice and populate the complete Biology 10–12 content packages.
