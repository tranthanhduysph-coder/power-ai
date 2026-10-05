# POWER AI v1.3 — Batch POWER Package QA

1. Apply patch at repo root.
2. Run `python -m app.db.migrate` from `apps/api`.
3. Run backend tests.
4. From repo root with `PYTHONPATH=apps/api`, use:
   - `python scripts/content/build_power.py status --grade 12`
   - `python scripts/content/build_power.py qa --unit B12_L02_GENE_EXPRESSION_GENOME`
   - `python scripts/content/build_power.py generate --grade 12 --limit 3`
   - `python scripts/content/build_power.py qa --grade 12 --limit 3`
   - `python scripts/content/build_power.py activate-batch --grade 12 --limit 3 --confirm ACTIVATE-QA-PASSED`

Batch activation is intentionally gated by deterministic QA and an explicit confirmation token.
