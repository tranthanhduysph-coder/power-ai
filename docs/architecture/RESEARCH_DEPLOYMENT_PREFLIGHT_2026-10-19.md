# Research deployment preflight — 19 October 2026

This follows the isolated checkpoint validation. It does not deploy the branch
or record real participant consent.

## Code protections added

- Research administration rejects `FIREBASE_AUTH_EMULATOR_HOST`, whether read
  through application settings or the process environment. The Firebase Admin
  SDK accepts unsigned emulator tokens when this setting is enabled, so a
  pinned UID/email alone does not establish a production identity in that mode.
- Research endpoints explicitly use `check_revoked=True`. Firebase must accept
  the ID token and confirm that its account/session has not been disabled or
  revoked. Existing ordinary student-token verification keeps its prior
  behavior. An authentication failure denies research access.
- The application's schema readiness manifest now requires migrations 013,
  014 and 015 and all three research tables. A real PostgreSQL regression test
  removes 015 and one research table inside a rolled-back test transaction and
  confirms that readiness reports them missing.
- API CI runs the complete non-database test suite; the PostgreSQL job continues
  to run the integration suite with synthetic learners.

References: [Firebase emulator behavior](https://firebase.google.com/docs/emulator-suite/connect_auth),
[Firebase revoked token checks](https://firebase.google.com/docs/auth/admin/manage-sessions).

## Verification

The initial regression tests reproduced missing emulator rejection, missing
revocation checking and the incomplete readiness manifest. After the fixes,
**77 backend tests passed** against a fresh isolated PostgreSQL 16/pgvector
database containing synthetic test data only. Python compilation passed.
No checkpoint restore was needed again for these authentication/readiness
changes. The earlier checkpoint validation remains documented separately.

## Read-only production observations

- The user confirmed the intended Render workspace, **My Workspace**.
- Both `power-ai` and `power-ai-web` still run main commit
  `9e455f4f300b07826892056bae548200582b627f`, with automatic deployment enabled.
- Migration 015 and the research tables were absent during the read-only check.
- After the user's login, exactly one POWER account matched the designated
  administrator email. Its UID was retained privately for configuration and is
  intentionally omitted here. This account lookup does not replace checking a
  verified Firebase ID token at runtime.
- The backend has a Firebase service-account secret file configured. Its
  contents were not read or exported.
- Dashboard inspection found no research environment keys, no auth emulator
  key and no linked environment groups. Existing secret values stayed hidden.

## Prepared next action

After the tested branch and exact administrator identity are reviewed, add
`RESEARCH_ADMIN_FIREBASE_UID`, `RESEARCH_ADMIN_EMAIL` and a newly generated,
stable 32+ character `RESEARCH_PSEUDONYM_KEY` to **power-ai** only, preserving
all existing keys. Prefer saving configuration without deploying while the
application remains on main. Never print the HMAC secret or put it in Git.

Before release, verify a real administrator login, revoked/disabled account
denial, ordinary student denial, and the server's Firebase Auth read permission.
Keep the consent registry empty until independently documented participant and
applicable guardian/institutional authorizations have been checked. An operator
must approve any deployment or merge separately from this read-only preflight.
