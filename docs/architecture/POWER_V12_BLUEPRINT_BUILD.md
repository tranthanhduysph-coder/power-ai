# POWER AI v1.2 — Source-grounded POWER package build

v1.2 converts an **ingested curriculum unit** into a reviewable POWER package. It does not mark units POWER-ready merely because an LLM produced JSON.

Pipeline:

`ingested SGK chunks → draft concepts/relations → Prepare/Work draft → Evaluate question draft → deterministic validation → explicit activation → POWER-ready`

## Product rule

POWER remains learner-owned. Generated Work tasks must make the learner explain, compare, interpret, analyze, or apply source-supported ideas. The AI may scaffold; it must not replace learner evidence.

## Safety/quality gates

- Generation uses only the unit's mapped SGK chunks.
- Drafts are stored separately in `power_blueprint_drafts`.
- `is_power_ready` remains false until explicit `activate`.
- Activation requires a valid draft and ingested source evidence.
- Activation creates concept mappings, the POWER blueprint, and a minimum approved Evaluate question bank.
- Existing POWER-ready units are protected unless `--force` is explicitly used.

## Commands

```bat
python scripts\content\build_power.py plan --grade 12
python scripts\content\build_power.py generate --unit B12_L02_GENE_EXPRESSION_GENOME
python scripts\content\build_power.py show --unit B12_L02_GENE_EXPRESSION_GENOME
python scripts\content\build_power.py validate --unit B12_L02_GENE_EXPRESSION_GENOME
python scripts\content\build_power.py activate --unit B12_L02_GENE_EXPRESSION_GENOME
```
