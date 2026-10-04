# POWER AI v1.0 Local Release

v1.0-local is the first local baseline where the full POWER workflow is treated as one application rather than a sequence of technical prototypes.

## Product invariant

A POWER learning cycle remains:

`Prepare → Organize → Work → Evaluate → Rethink`

The learner may review completed phases without moving progression backwards. Evidence from each phase persists in PostgreSQL and feeds later phases. AI supports the learner but does not own the learner's products or reflection.

## v1.0 hardening scope

- FastAPI liveness and readiness endpoints.
- Database schema/migration/readiness verification.
- Safe local PostgreSQL backup, restore and destructive reset commands.
- One-command local release checker.
- Clear UI states when Firebase Auth, FastAPI or the database are unavailable.
- Global Next.js error and not-found screens.
- Dashboard retry instead of silent console-only failures.
- Responsive navigation and single-column learning/Tutor layout on smaller screens.
- Stable local version identifier: `1.0.0-local`.

## Health contract

- `GET /api/v1/health/live`: process is alive; does not depend on PostgreSQL.
- `GET /api/v1/health`: basic database and pgvector connection.
- `GET /api/v1/health/ready`: release readiness. It checks required migrations, critical tables, pgvector and at least one POWER-ready curriculum unit.

A 503 from `/health/ready` means the API process exists but the local stack is not yet ready for learning traffic.

## Database operations

From repository root with the API virtual environment active:

```bat
python scripts\db\local_db.py status
python scripts\db\local_db.py backup
python scripts\db\local_db.py reset --confirm RESET-LOCAL
python scripts\db\local_db.py restore local_backups\<backup>.dump --confirm RESTORE-LOCAL
```

`reset` and `restore` are intentionally confirmation-gated because both are destructive.

## Release verification

With PostgreSQL, Firebase, FastAPI and Next.js running:

```bat
python scripts\release\check_local.py
```

It runs Python compilation, backend tests, the Next.js production build, database verification and API smoke tests.

Use `--skip-smoke` when the API is not running, or `--skip-db --skip-smoke` for code-only verification.

## Local release is not production

v1.0-local does not include production hosting, payment gateways, production Firebase configuration, managed secrets, managed object storage, observability service integration, or the full ingestion of every Biology 10–12 textbook lesson. The curriculum catalog is generalized, but only content marked `is_power_ready=true` should be offered as a complete POWER lesson.
