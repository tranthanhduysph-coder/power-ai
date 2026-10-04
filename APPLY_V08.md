# Apply POWER AI v0.8

1. Apply the patch on top of v0.7.
2. Run `python -m app.db.migrate` (migration 005).
3. Run `python -m app.db.seed` (seed 004).
4. Run `python -m pytest -q` and `python -m compileall app`.
5. Run `npm run build` in `apps/web`.
6. Start API + web + Firebase and complete a fresh POWER cycle through Evaluate and Rethink.
7. Run `set PYTHONPATH=apps\api` then `python scripts\db\verify_power_database.py` from repo root.
