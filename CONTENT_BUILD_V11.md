# Apply POWER AI v1.1 content build

1. Run migration 008.
2. Put the original PDFs in `private_sources/` with the exact names from `content/sources/kntt_books.json`.
3. Run `plan` for Biology 10 first.
4. Ingest Biology 10 and verify it before moving to 11 and 12.

The build is resumable at the expensive vision step because extracted pages are cached by PDF SHA256 under `storage/ingestion-cache/`.
