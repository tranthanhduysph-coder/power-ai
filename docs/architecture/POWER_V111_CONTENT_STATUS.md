# POWER AI v1.1.1 — Content status reconciliation

`content_status` is per curriculum unit and must reflect actual ingested evidence, not merely a source mapping.

A unit is `ingested` only when a ready source contains a `source_sections.code` equal to the unit code and that section has at least one `content_chunks` row.

This fixes the v1.1 migration rule that could mark all units mapped to a ready textbook source as ingested even when only a pilot section had actually been processed.

Use:

```bat
python scripts\content\build_kntt.py reconcile --grade 10
python scripts\content\build_kntt.py verify --grade 10
```
