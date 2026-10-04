# Apply v1.1.2

1. Extract patch at repository root.
2. `cd apps/api && .venv\\Scripts\\activate`
3. `python -m app.db.migrate`
4. `cd ../..`
5. `set PYTHONPATH=apps\\api`
6. `python scripts\\content\\build_kntt.py reconcile --grade 10`
7. `python scripts\\content\\build_kntt.py verify --grade 10`
