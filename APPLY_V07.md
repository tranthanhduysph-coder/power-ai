# Apply POWER AI v0.7

1. Extract this patch over the current v0.6 repository.
2. Run `python -m app.db.migrate` from `apps/api` to apply migration `004_power_evaluate_link`.
3. Run `python -m pytest -q`.
4. Run `npm run build` from `apps/web`.
5. Restart FastAPI and Next.js.
6. Enter EVALUATE from the POWER lesson and use the new `Bắt đầu Evaluate` button.
7. Submit the practice set. POWER should automatically advance to RETHINK.
8. Run `python scripts/db/verify_power_database.py` from the repository root with `apps/api` on `PYTHONPATH`, or run the command shown in the chat instructions.
