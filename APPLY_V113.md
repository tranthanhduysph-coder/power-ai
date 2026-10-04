# Apply v1.1.3

1. Extract patch at repository root.
2. `cd apps/api && .venv\\Scripts\\activate`
3. `python -m app.db.migrate`
4. `python -m pytest -q`
5. `cd ../..`
6. `set PYTHONPATH=apps\\api`
7. `python scripts\\content\\build_kntt.py reconcile --grade 10`
8. `python scripts\\content\\build_kntt.py reconcile --grade 12`
9. Verify status counts for grades 10, 11 and 12.
