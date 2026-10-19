# Disposable research staging

The stack in `infra/render.research-staging.yaml` creates **new** resources only:

| Resource | Purpose | Requested compute plan |
| --- | --- | --- |
| power-research-staging-db | PostgreSQL 16, synthetic records only | Free |
| power-research-staging-api | Feature-branch backend | Free |
| power-research-staging-web | Feature-branch Next.js interface | Free |

Region: Singapore. Automatic deploys and automatic previews are off. The
database denies external connections. No production resource is referenced.
The backend uses a new generated HMAC key; production pseudonyms and secrets
are not copied. AI uses mock/local providers and requires no OpenAI API key.

## Protection against production data

The staging entrypoint requires `RESEARCH_STAGING_ENABLED=true` and the exact
database name `power_research_staging` before opening a connection. It converts
Render's `postgresql://` URL to the installed psycopg driver without logging the
URL. Existing non-fixture learner accounts cause startup to abort before DDL.

All authenticated application routes are restricted to the exact verified
administrator before the ordinary auth dependency can persist a user profile.
Emulator tokens are forbidden and token revocation is checked. Ordinary student
logins must return 403 without adding the student to this database.

Fixtures contain three fictional accounts: `research-allow@example.invalid`,
`research-deny@example.invalid`, `research-absent@example.invalid`. Their events,
cycles, assessments and mastery values are explicitly synthetic, dated
2026-10-19T00:00:00Z. Startup is idempotent and creates **no** research consent.
It does not infer or reconstruct any real student's historical mastery.

The frontend staging build refuses to target the production API or any hostname
outside the `power-research-staging-api` Render subdomain family.

## Costs and limits to review before creation

Free plans have no base compute subscription, but they consume the workspace's
shared Free instance hours, build minutes and bandwidth. Exceeding included
build/bandwidth usage can incur charges when billing is enabled. Exhausting the
750-hour monthly Free pool suspends all Free web services in the workspace,
including existing Free applications. Free Postgres is limited to one active
instance per workspace, expires after 30 days and has no backups.

Inspect the Dashboard's current usage/spend limit and the final Blueprint
estimate before applying. Do not substitute a paid plan if Free is unavailable
without approval. Tear down the disposable stack after testing; do not retain
real student data or live research consent in it.

References: [Free plan constraints](https://render.com/docs/free),
[Blueprint syntax](https://render.com/docs/blueprint-spec).

## Configuration and deployment

1. Select **My Workspace**, repository `tranthanhduysph-coder/power-ai`, branch
   `feature/research-analytics-consent-admin`, and Blueprint path
   `infra/render.research-staging.yaml`. The file must be pushed first; it does
   not need to be merged to main.
2. Review the three **new** resource names and Free compute plans. Stop if the
   preview includes either production service or the production database.
3. Supply the exact administrator UID and Firebase project ID privately, plus
   the Firebase web application's public API key, auth domain and app ID.
   These `sync: false` fields are requested during initial Blueprint creation.
4. Use a dedicated Firebase service-account credential with only the required
   Firebase Auth user-status read permission. Upload it directly to the new
   staging API as secret file `research-staging-firebase.json`; do not paste it
   into chat, commit it, or export the production service-account secret.
5. Check that the staging web hostname is an authorized domain in Firebase Auth
   before attempting browser sign-in. Any Firebase permission/domain change
   needs review; do not enable broad wildcard access.
6. Apply only after the resource/quota and credential-access changes have been
   approved. Monitor the exact deploy IDs until live. `/api/v1/health` checks
   database and pgvector; the curriculum readiness endpoint intentionally has
   no real curriculum to mark ready in this fixture stack.

If credentials are absent or invalid, research login must fail closed. A green
health check alone does not verify a real Firebase administrator session.

## Browser acceptance checks

- Sign in as the designated verified administrator and open `/research`.
- Confirm the registry begins with zero research consents.
- Register the allow fixture with synthetic evidence, survey version
  `STAGING-SYNTHETIC`, decision time `2026-10-18T00:00:00Z`, research true and
  approval verification true. These flags describe a fictional test only.
- Register the deny fixture with research false and product improvement true;
  leave the absent fixture unregistered.
- Export all five datasets for 18–21 October 2026. Each should contain only
  the allow fixture; linkage alone includes its fictional email. Check audits,
  UTF-8, paging and stable participant IDs.
- Record a later withdrawal for the allow fixture. All five datasets must then
  exclude it. Replay an older or equal-time grant and expect 409.
- Verify ordinary student denial, an unverified administrator email, and a
  revoked/disabled test session. Do not disable the real production admin or
  revoke their production sessions merely to perform this test.
- Confirm both production deploy IDs and migration ledger are unchanged.

The schema validator, Python/Node unit tests and PostgreSQL integration tests
validate preparation. Actual Render service creation, a real Firebase session,
and these browser acceptance checks must be recorded separately as they occur.
