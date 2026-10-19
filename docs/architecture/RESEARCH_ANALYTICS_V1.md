# POWER-AI-WEB — Learning behavior exports

## Current behavior (19 October 2026)

The Research Admin exports all recorded learning behavior in a selected time
window, including historical records. Google Form responses and the legacy
consent registry are **not** eligibility filters. This applies whether a legacy
record is absent, allowed or denied. The owner explicitly requested this change.
No acceptance/consent record is fabricated and no historical source records are
rewritten. The existing consent tables and deprecated POST endpoint remain for
compatibility and audit history only; the consent entry UI has been removed.

The public `/legal#learning-data` notice and the Terms modal describe collection
of learning activity solely for educational research and product improvement,
including stored history. Login and registration show a short notice linking to
the full text. This is disclosure text; it is not an acceptance-tracking system.

## Data scope

- `events`: existing learning events and numeric metric fields only; no raw JSON,
  chat content, free-text answers, names or email.
- `cycles`: POWER phase timestamps, progress and Evaluate accuracy.
- `assessments`: Practice/Evaluate attempts, results and duration.
- `mastery`: recorded mastery snapshots, never reconstructed historical scores.
- `linkage`: participant ID and email only, for users with any of the four
  activity sources in the selected window. Users with no activity are excluded.
  Source Form references and consent metadata are no longer exported.

Regular analytic files use a stable HMAC participant ID. Store linkage separately
and never publish identifiable learner data. A mastery score is a product
indicator, not an IRT ability estimate. Counts are engagement indicators, not
competency measures. Associations do not establish educational causality.

## Using the admin page

1. Sign in as the pinned, verified Firebase Research Admin and open `/research`.
2. Select a dataset and a date range no longer than 366 days. Start is inclusive;
   end is exclusive. The browser interprets dates in the local timezone.
3. Download CSV. One click includes all matching learners, with at most 10,000
   data rows. If full, repeat at offsets 10,000, 20,000, etc. The API supports a
   maximum page size of 20,000. For longer history, use adjacent time windows.
4. Use the same window for the separate linkage file if identity matching is
   needed. Its scope is the union of activity sources, independent of account
   creation date and Google Form response date.

## Security and operations

- All research routes require the configured exact Firebase UID and verified
  email. Dev auth, authentication emulators and revoked/disabled tokens are
  rejected. Ordinary learners cannot export.
- Preserve `RESEARCH_ADMIN_FIREBASE_UID`, `RESEARCH_ADMIN_EMAIL`,
  `RESEARCH_PSEUDONYM_KEY` (at least 32 secret characters) and `AUTH_MODE=firebase`.
  Rotating the HMAC key changes participant codes.
- Missing configuration fails closed. CSV formula prefixes are escaped and
  JSON metrics accept numeric values only. Downloads use `Cache-Control: no-store`.
- Each download records actor, dataset, row count, window, pagination and
  `scope=all_recorded_activity` in `research_export_audit`.
- Migration 015 and the existing three research tables remain unchanged. This
  update requires no new migration, production data backfill or secret change.
- Render auto-deploys `main`. Verify CI and deployment status when releasing.

## Validation

Use only a fresh disposable local PostgreSQL16/pgvector database with the full
schema. Never use a production database or real learner data for these tests.

```bash
cd apps/api
python -m pytest -q tests --ignore=tests/test_research_integration.py
RESEARCH_TEST_DATABASE_URL=<local-disposable-dsn> python -m pytest -q tests/test_research_integration.py
```

Tests cover all datasets regardless of old Form decisions; inclusive/exclusive
window boundaries; pre-decision activity; stable pagination; each linkage source;
absence of chat, raw answers and identifying UUIDs; CSV/UTF-8 handling; export
audits; admin authorization; and preservation of legacy audit behavior.

From `apps/web`, run TypeScript checking, the staging build guard test and a
production build. The isolated staging Blueprint remains optional; it uses only
synthetic fixtures and must never be populated with student data.

The earlier restore and preflight documents describe the previous consent-gated
release, retained as historical verification records. This document supersedes
those documents for current export eligibility and operator workflow.
