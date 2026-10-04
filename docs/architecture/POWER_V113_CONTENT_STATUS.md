# POWER AI v1.1.3 — Strict content-status evidence

`content_status='ingested'` is now derived per curriculum unit from durable evidence:

1. the unit has a `curriculum_unit_sources` mapping;
2. both `pdf_page_start` and `pdf_page_end` are explicit;
3. at least one `content_chunks` row from the same source overlaps that range.

A NULL unit page range is never treated as a wildcard. Source-level `ingest_status` is not sufficient to mark every unit in a book as ingested.

Expected current state after reconciliation:

- Biology 10: 26 ingested units (full book already ingested)
- Biology 11: 0 ingested units (not ingested yet)
- Biology 12: 1 ingested unit (DNA replication pilot only)
