# Apply POWER AI v1.2

1. `python -m app.db.migrate` from `apps\api`.
2. `python -m pytest -q`.
3. From repo root, set `PYTHONPATH=apps\api` and run `build_power.py plan`.
4. Generate ONE pilot draft first. Review the JSON under `storage\generated-power-blueprints`.
5. Validate, then explicitly activate that unit.
6. Only after the pilot works end-to-end should you batch-generate more units.
