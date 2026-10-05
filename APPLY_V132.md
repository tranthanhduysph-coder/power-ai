# POWER AI v1.3.2 — Core concept normalization hotfix

No database migration is required.

This hotfix repairs harmless model drift in `is_core` flags before validation/QA:
- the primary concept is always core when it exists in the returned concept set;
- fewer than 3 core concepts are promoted deterministically in source order;
- more than 6 core concepts are trimmed deterministically to 6 while preserving the primary concept;
- the concept set and semantic relations are not changed.

After applying the patch, rerun `pytest`, then rerun QA on the existing failed drafts. Regeneration is not required for drafts that failed only because of the 3–6 core-concept rule.
