# POWER v1.3.3 — Primary concept coverage in Evaluate

Every POWER unit identifies a `policy.primary_concept_code`. Evaluate must collect direct evidence for that primary learning target, not only for neighboring concepts.

The builder therefore uses three layers:
1. **Generation contract:** at least one Evaluate question must have `concept_code == primary_concept_code` and genuinely assess that concept.
2. **Safe metadata repair:** if a question stem clearly names the primary concept but was tagged with a neighboring concept code, only the mapping metadata is corrected.
3. **Strict QA:** if direct primary coverage is still absent, QA fails. The system does not silently relabel an unrelated question or invent a new assessment item.

This keeps batch generation efficient while preserving the pedagogical meaning of Evaluate evidence.
