# POWER AI v1.2.2 — Concept code normalization

Overlay on top of v1.2.1. No database migration is required.

This hotfix canonicalizes harmless concept-code separator drift from the content model:
`BIO_GENE` -> `BIO.GENE`, `BIO_RNA_TYPES` -> `BIO.RNA.TYPES`, etc., and rewrites all references consistently before strict validation and storage.

Existing drafts are normalized when they are validated or activated, so regeneration is not required solely for this error.
