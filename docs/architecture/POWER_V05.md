# POWER AI v0.5 — Organize as learner-owned knowledge construction

## Product intent

Organize is not a static explanation page and not a quiz. It is the phase in which the learner turns lesson content into an explicit structure that can be inspected, discussed, revised, and reused in later POWER phases.

The learner must own the map. POWER provides the curriculum concept bank, relationship vocabulary, persistence, and phase-aware Tutor scaffolding, but it does not silently construct the map on the learner's behalf.

## Vertical slice

For `B12_DNA_REPLICATION`, Organize now supports:

1. selecting at least three anchor concepts;
2. creating at least three learner-defined concept relationships;
3. previewing the emerging map;
4. explaining one relationship chain in the learner's own words;
5. saving partial work and resuming it later;
6. completing Organize only when minimum evidence exists;
7. passing the learner-built map into POWER Tutor context while in Organize;
8. transitioning to Work after completion.

## Evidence stored in power_phase_state

```json
{
  "anchor_concepts": ["BIO.DNA.STRUCTURE", "BIO.DNA.REPLICATION"],
  "links": [
    {
      "source": "BIO.DNA.STRUCTURE",
      "relation": "prerequisite",
      "target": "BIO.DNA.REPLICATION"
    }
  ],
  "synthesis": "...",
  "unique_concepts": ["..."],
  "coverage": 0.714
}
```

This state is learning evidence, not a canonical answer key. The canonical curriculum graph remains in `concept_relations` and can later be used for comparison, recommendation, misconception detection, or teacher analytics.

## API

- `GET /api/v1/power/organize/blueprint`
- `PUT /api/v1/power/sessions/{session_id}/organize`

## Completion rule

To complete Organize, the learner must provide:

- >= 3 valid anchor concepts;
- >= 3 valid, unique concept relationships;
- a synthesis of >= 20 characters.

Partial state can always be saved without satisfying completion requirements.

## POWER principle

The phase implements the POWER-Biology principle **AI-assisted but learner-owned**. The Tutor may ask the learner to justify or refine a relationship, but should not immediately replace the learner's construction with a finished expert map.
