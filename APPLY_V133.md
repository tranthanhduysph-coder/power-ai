# POWER AI v1.3.3 — Primary Evaluate coverage hotfix

No database migration is required.

This hotfix makes primary-concept assessment an explicit quality requirement:
- generation prompt requires at least one Evaluate item to directly assess `policy.primary_concept_code`;
- QA now fails, instead of merely warning, when the primary concept is not directly assessed;
- if a generated question stem clearly names the primary concept but its `concept_code` was tagged to a neighboring concept, normalization repairs only that metadata;
- if no question clearly assesses the primary concept, the builder does not fabricate or relabel an unrelated question; QA fails so the unit can be regenerated;
- QA metrics include `primary_assessed_count`.

Existing drafts can be QA'd again. Some existing warnings will be repaired automatically when they were only metadata drift. Drafts that genuinely omitted primary-concept assessment must be regenerated.
