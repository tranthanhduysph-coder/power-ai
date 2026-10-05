# POWER AI v1.3 — Batch POWER Package QA

v1.3 adds a deterministic QA gate between generated POWER drafts and activation.

## Workflow

`ingested textbook unit -> generate draft -> schema validation -> QA -> explicit batch activation -> POWER-ready`

QA checks:
- strict v1.2 package schema;
- source fingerprint freshness;
- duplicate Evaluate stems;
- duplicate Work prompts;
- concept/question coverage metrics;
- question-type, difficulty and cognitive-level distributions;
- source context size warning.

A QA pass does **not** claim pedagogical perfection. It establishes a repeatable machine gate before activation. Human review remains appropriate for high-stakes or public release content.

## Safe batch commands

- `build_power.py status --grade 12`
- `build_power.py generate --grade 12 --limit 5`
- `build_power.py qa --grade 12 --limit 5`
- `build_power.py activate-batch --grade 12 --limit 5 --confirm ACTIVATE-QA-PASSED`

Generation skips already validated/activated drafts unless `--force` is used. Batch activation only accepts QA-passed drafts and requires an explicit confirmation token.
