# POWER AI v1.1 — KNTT Content Build

v1.1 separates two states that were previously conflated:

- `content_status`: whether the textbook pages for a curriculum unit have been ingested into the knowledge base.
- `is_power_ready`: whether the unit has a reviewed POWER blueprint and is ready to run P–O–W–E–R.

A unit may therefore be `content_status=ingested` while `is_power_ready=false`.

## Verified PDF page mapping

The local source PDFs used for the POWER AI content build are image-only scans. The mapping between printed textbook pages and PDF indices was visually verified at the beginning and later pages of each book:

| Book | PDF pages | Mapping |
|---|---:|---|
| Biology 10 KNTT | 162 | `pdf_page = printed_page + 1` |
| Biology 11 KNTT | 190 | `pdf_page = printed_page + 1` |
| Biology 12 KNTT | 199 | `pdf_page = printed_page + 2` |

The build script refuses to ingest if the local PDF page count does not match the verified registry.

## Pipeline

```text
curriculum_units
      ↓
KNTT registry + verified page offset
      ↓
generated ingestion manifest
      ↓
PDF page render / vision extraction
      ↓
source_pages + source_sections
      ↓
content_chunks + embeddings
      ↓
curriculum_unit_sources
      ↓
content_status = ingested
```

Generated manifests and vision cache live under `storage/` and are not committed to Git. Original PDFs remain under `private_sources/` and are also excluded from Git.

## Commands

```bat
python scripts\content\build_kntt.py plan --grade 10
python scripts\content\build_kntt.py ingest --grade 10
python scripts\content\build_kntt.py verify --grade 10
```

Use `--all` only after each grade has been validated independently.
