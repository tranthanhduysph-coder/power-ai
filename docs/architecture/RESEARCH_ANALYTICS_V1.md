# POWER-AI-WEB — Research Analytics v1 (review branch)

## Scope and data provenance

The application already stores `users`, `learning_events`, `learning_sessions`,
`power_sessions`, `power_phase_state`, `practice_attempts`, `concept_mastery`
and `mastery_snapshots`. This change **reuses** these tables, adds consent/export
audit tables in migration 015, and records future mastery updates in
`mastery_snapshots` in the same transaction as the mastery calculation.

**Do not backfill historical mastery values as if they were observed.** The
snapshot table was empty at the October 17 pre-change review. A mastery score
is a product indicator, not an IRT ability estimate.

## Deployment safeguards

1. Production Render services `power-ai` (FastAPI) and `power-ai-web` (Next.js)
   auto-deploy **main**, so this branch must stay unmerged until reviewed.
2. Confirm `power-ai-db` status **Available** (upgraded from Free) and preserve
   an independently stored, restorable Postgres backup/checkpoint.
3. Run migrations on a **non-production copy** first. Migration
   `015_research_analytics.sql` adds only tables/indexes.
4. In the Render **power-ai** backend environment, set:
   - `RESEARCH_ADMIN_FIREBASE_UID`: exact UID of the verified Firebase
     account `ttduy@sgu.edu.vn`, copied from Firebase Console > Authentication.
     **Never** use the email address as a UID.
   - `RESEARCH_ADMIN_EMAIL=ttduy@sgu.edu.vn`
   - `RESEARCH_PSEUDONYM_KEY`: at least 32 random, secret characters. Keep
     it stable across exports; rotating it changes all participant codes.
     Store in Render secret environment variables, never in GitHub.
   - `AUTH_MODE=firebase`. Research routes explicitly reject dev auth.
   - Ensure `FIREBASE_AUTH_EMULATOR_HOST` is unset. Research administration
     rejects emulator configuration even when `AUTH_MODE=firebase`.
5. Configure production Firebase credentials and allowed CORS origin.
   Research requests check revoked/disabled administrator tokens through the
   Firebase Admin SDK. Credentials must permit reading Firebase Auth user
   status; a missing permission or failed verification denies the request.
   See [Firebase session verification](https://firebase.google.com/docs/auth/admin/manage-sessions).
6. Verify `GET /api/v1/research/status` returns 403 for any ordinary student
   and for dev mode, and succeeds only for the exact verified Firebase UID.
7. Create a verified Google Form response with **separately recorded** research
   and product-improvement choices. **Do not** infer consent from a login,
   an existing account, or earlier Form responses without the required text.
8. Register each verified consent in the Research Data screen; guardian and
   institutional ethics authorization (where required) must be verified.
   For older log data, mark historical coverage **only if explicitly disclosed
   and consented**. Otherwise data from before the response is excluded.
9. Check that denied/withdrawn students never appear in any dataset. Test
   start/end filters, 10,000-row paging, UTF-8 CSV and export audit trail.
10. Merge only after independent review. Production deploy may restart the API
    while the database migration runs; monitor the Render deploy and app health.

## Workflow in the Research Data UI

1. Sign in to POWER with the **verified** Firebase account
   `ttduy@sgu.edu.vn`.
2. Visit `/research`. The sidebar displays “Dữ liệu nghiên cứu” for this
   email only; backend authorization is the actual security boundary.
3. From the original Google Form / response Sheet, verify the respondent's
   POWER login email, consent decision, survey version, exact response time,
   and unique Form response reference. Record consent in the admin panel.
4. A respondent who declines research must be recorded as `research_allowed=false`.
   To process a withdrawal, enter a new documented decision with a later time
   and `research_allowed=false`. Future exports then exclude this learner.
   Existing downloaded exports must be handled under the withdrawal protocol.
   Every replacement must have a strictly later decision time; equal-time
   imports are rejected with 409 to prevent replay from reversing a withdrawal.
   A response reference remains reserved to its original learner in audit
   history even after a later response replaces it. Concurrent imports are
   serialized by source reference and learner.
5. Export `linkage` to a separately secured file to map the Form's email to a
   stable `participant_id`. Do not add names/emails to other analytic files.
6. Export `events`, `cycles`, `assessments`, `mastery` for the same time
   window. Merge datasets using `participant_id`. Do not interpret the absence
   of pre-instrumentation events as absent behavior.
7. Use `offset=10000`, `20000`, etc. if an export reaches 10,000 rows.
   The backend enforces max 20,000 rows per request.

## Endpoint permissions

All paths below require a Firebase ID token from exactly the pinned UID and
verified email. Unconfigured admin UID or missing pseudonym key **fails closed**.

- `GET /api/v1/research/status`: aggregate counts only.
- `POST /api/v1/research/consents`: manually record an independently verified
  Google Form choice. Include source ref, version, timestamps, separate
  research/product selections and required approval verification.
- `GET /api/v1/research/exports/{events|cycles|assessments|mastery|linkage}`:
  CSV with `start_at` (inclusive), `end_at` (exclusive), `limit` and
  `offset`. All exports are audited.
- `linkage` contains email and must be stored separately; other exports
  intentionally exclude names, emails, raw prompts and learner answers.

### Consent example (test data only)

```json
{
  "email": "learner@example.com",
  "survey_response_ref": "form-id:response-id",
  "survey_version": "POWER-AI-WEB V5",
  "consented_at": "2026-10-17T20:00:00+07:00",
  "research_allowed": true,
  "improvement_allowed": false,
  "required_authorizations_verified": true,
  "activity_scope_start_at": null,
  "historical_coverage_confirmed": false
}
```

## Research and ethics limitations

- The current Google Form is a **separate system**. Consent is manually
  reconciled; there is no automatic Google Sheets ingest in this version.
  A first survey email can be mismatched; ambiguous or nonexistent POWER
  accounts are rejected rather than guessed by name.
- The 30 POWER–UTAUT items remain unchanged. The email in General Information
  is a **linkage variable**, not an indicator in the SEM model.
- Do not use logs to infer performance quality without a defined behavioral
  rubric. Counts of interactions are engagement indicators, not competencies.
- Evaluate outcomes are not automatically equivalent across arbitrary topics
  or question difficulties. Mastery is not IRT.
- An observational link between reported POWER and mastery **does not**
  establish causal educational effectiveness.
- Review the participant information sheet, privacy notice, institutional
  approvals, appropriate guardian authorization, retention/deletion rules,
  and the legal basis for product improvement before using real learner data.
- Production database external allowlist was `0.0.0.0/0` at pre-change
  inspection. Evaluate restriction to Render private-network access **after**
  verifying all legitimate backend and maintenance connections.

## Minimal checks

From the repository on the development machine:

```bash
cd apps/api
python -m pip install -r requirements.txt
python -m pytest -q tests/test_research_admin.py
python -m compileall -q app
```

From `apps/web`:

```bash
npm ci
npm run build
```

For database tests, use a temporary clone **not** production. Confirm the
migration applies once and is skipped on the second run. Check the export
audit row count and test a consenting and a withdrawing test learner.

The PostgreSQL CI job now runs the full schema with pgvector and
`tests/test_research_integration.py` using synthetic accounts only. For a local
run, explicitly set `RESEARCH_TEST_DATABASE_URL` to a local disposable database
named `research_integration_test` (empty schema after migrations), or
`research_restore` (private restored checkpoint after migrations), then run:

```bash
python -m pytest -q tests/test_research_admin.py tests/test_research_integration.py
```

Integration fixtures use rollback or delete only their generated synthetic
accounts; no existing learner is granted consent. The standalone migration
smoke script requires a separate empty local database named
`research_migration_test`, using a psycopg DSN in the same environment variable.
Do not set the test variable to a production database or commit a checkpoint.
JSON metric fields are type-filtered before CSV output; malformed text values
are exported as empty cells rather than exposing learner content.

See [isolated checkpoint validation](RESEARCH_RESTORE_VALIDATION_2026-10-19.md)
for the restore evidence and remaining deployment hold points.

## Post-review work (not included here)

- Automate the secure Google Form consent import after checking the Form
  permissions and ethics-approved source of truth.
- Assess whether more events are needed to validate P/O/W/E/R quality; add
  targeted server-side instrumentation only after agreeing on the rubric.
- Introduce independent privacy-review and multi-school release criteria.
