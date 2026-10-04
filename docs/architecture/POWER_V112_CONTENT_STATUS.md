# POWER AI v1.1.2 — Content status reconciliation

A curriculum unit is considered ingested only when:

1. it has a `curriculum_unit_sources` mapping;
2. the mapped source is `ready`; and
3. at least one persisted `content_chunks` row overlaps the unit's mapped PDF page range.

This replaces fragile reconciliation based on `source_sections.code = curriculum_units.code`, which can fail for historical ingestion runs even when sections/chunks and unit-source mappings are valid.
