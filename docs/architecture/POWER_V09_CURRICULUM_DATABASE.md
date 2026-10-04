# POWER AI v0.9 — Curriculum Database Generalization

## Goal
Remove the DNA-replication-only routing and move curriculum identity, source mapping, and POWER phase blueprints into PostgreSQL.

## What changes
- Biology 10, 11, and 12 KNTT catalog skeleton is stored in `curriculum_units`.
- Units are typed as `part`, `chapter`, `lesson`, `practice`, or `project`.
- Each lesson stores printed textbook page range and source mapping.
- `curriculum_unit_sources` links curriculum lessons to source documents without copying textbook content into Git.
- `power_unit_blueprints` stores Prepare and Work instructional blueprints as JSONB.
- Only `B12_DNA_REPLICATION` is `is_power_ready=true` in v0.9; all other lessons are visible in the catalog but explicitly marked as content pending.
- Frontend route becomes `/learn/[unitCode]`.
- `/learn` becomes the database-driven Biology 10–12 curriculum browser.
- Practice can receive `unitCode` and no longer has to be hard-coded to DNA replication.
- Tutor can derive the primary concept from the current POWER session when the client does not supply one.

## Database flow

```text
subjects
  -> grades
    -> curriculum_units
       -> curriculum_unit_sources -> sources -> source_pages/content_chunks
       -> curriculum_concepts -> concepts
       -> power_unit_blueprints
       -> learning_sessions -> power_sessions -> power_phase_state
```

## Content readiness contract
A catalog entry can exist before full POWER content is available.

- `catalog_visible=true`: show the lesson in the curriculum.
- `is_power_ready=true`: the lesson has concepts + POWER blueprint + question/content support and may start a POWER session.

This separates curriculum coverage from content production and prevents the app from pretending unsupported lessons are ready.

## Source-of-truth policy
The catalog seed records textbook structure and page ranges only. Private SGK PDFs remain under `private_sources/` and are never committed. Ingestion later fills `source_pages`, `content_chunks`, concepts, visuals, questions, and then flips a lesson to POWER-ready.
