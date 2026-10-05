# POWER AI v1.3.1 — generated relation repair

Generated POWER drafts may contain harmless relation-graph defects even when the concept set itself is valid. The normalizer now repairs only deterministic structural defects before strict validation:

- canonicalize concept identifiers;
- discard self-links;
- discard relations whose endpoints are not part of the draft concept set;
- remove exact duplicate relations.

Unsupported relation types remain untouched and are still rejected by validation. The change therefore repairs model formatting/graph noise without silently inventing conceptual meaning.
