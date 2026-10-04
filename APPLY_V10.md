# Apply POWER AI v1.0 Local Hardening

1. Apply this patch over committed v0.9.
2. Activate `apps\api\.venv`.
3. No new SQL migration is required in v1.0 hardening.
4. Run backend tests and compile.
5. Run `npm run build` in `apps\web`.
6. Start PostgreSQL, Firebase Auth Emulator, FastAPI and Next.js.
7. Run `python scripts\release\check_local.py` from repository root.
8. Before any destructive DB test, run `python scripts\db\local_db.py backup`.

See `docs/architecture/POWER_V10_LOCAL_RELEASE.md`.
