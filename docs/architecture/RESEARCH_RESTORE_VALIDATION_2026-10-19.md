# Isolated checkpoint validation — 19 October 2026

PR: https://github.com/tranthanhduysph-coder/power-ai/pull/2

Branch: `feature/research-analytics-consent-admin`.
Reviewed starting commit: `34b5348b563f5408307079a44199fd859eda65de`.

## Restore and data protection

- Source: the user-uploaded `2026-10-17T13_55Z.dir.tar.gz` checkpoint.
- SHA-256: `d94e3f71c14dc44e673f5bccaafae14366c1be132ea4692e779f104116f3de35`.
- Restored with `pg_restore --exit-on-error --no-owner --no-privileges` into a
  disposable local database, `research_restore`.
- PostgreSQL **16.15**, pgvector **0.8.7**; 42 original public tables.
- Image: `pgvector/pgvector:pg16`, digest
  `sha256:7b822b0aac60967beb1ea5e576b8602c94c300a157d187f385ae3e0da199b90a`.
- Container network disabled, no published ports, PostgreSQL TCP listening
  disabled, checkpoint mounted read-only; local access through a Unix socket.
- Checkpoint and private runtime output stayed outside the repository. No
  student rows, identities, raw exports, credentials or production endpoints
  are included in this report.
- Synthetic accounts were used for consent and export checks. Existing
  checkpoint accounts were never enrolled in research.
- Before/after SHA-256 fingerprints of sorted JSON row representations matched
  for **all 41 original application tables**. The separate migration ledger
  gained version 015 as expected. PostgreSQL sequences can advance during
  rolled-back tests; these tests do not assert identical sequence state.

## Results

| Check | Result |
| --- | --- |
| Checkpoint restore with stop-on-error | Passed |
| Actual application migrator on restored checkpoint | Applied only 015; existing versions skipped |
| Second application migration run | 015 skipped |
| Updated 015 SQL executed twice | Passed; includes audit source lookup index |
| Empty disposable migration smoke database | Passed; repeat DDL, duplicate response rejection, authorization constraint |
| Full migrations on empty pgvector database, then rerun | Passed |
| Integration tests on empty database | 14 passed |
| Complete backend test suite on restored checkpoint | 71 passed |
| Python application compilation | Passed |
| Web TypeScript `tsc --noEmit` | Passed |
| Original application table contents after tests | Unchanged |

Local backend tests ran on Python 3.14; CI is configured for Python 3.12.
The local test client emitted one dependency deprecation warning about httpx;
it did not affect test results.

## Confirmed defects and fixes

1. Missing HMAC configuration caused a 503 after consent and audit had already
   committed. Participant pseudonym validation now occurs before writes.
2. A decision with the same timestamp could reverse a withdrawal. Replacement
   decisions must now be strictly newer; real concurrent imports are serialized
   by source and learner so stale requests cannot overwrite later decisions.
3. A replaced Form response reference could be reassigned to another learner.
   Both the current registry and historical audit reserve the original link;
   concurrent source reuse returns 409.
4. Whitelisting JSON metric keys alone still allowed text under those keys into
   CSV. Metric cells now accept numeric text only; malformed learner text is
   blanked. Valid metric values remain available.

Regression coverage includes all five CSV datasets, consent scope boundaries,
explicit historical coverage, denied and absent consent, separate product
choice, withdrawal exclusion, export audit counts, date windows, paging,
UTF-8, spreadsheet formula escaping, HMAC pseudonyms, missing-key behavior,
admin restrictions, two-connection concurrency, and transactional mastery
snapshots. Tests never reconstruct historical mastery values.

CI now provisions pgvector, applies the complete schema twice and runs the
same synthetic integration tests. It does not upload or download this checkpoint.

## Deployment hold points remain

This validation does not exercise a real Firebase login, live Google Form
reconciliation, production configuration or a deployed browser session.
Firebase claims are stubbed only in tests. No production database, Render
configuration or service was changed, and this work does not authorize a merge.

Keep PR #2 in draft until independent review and the documented Firebase UID,
stable HMAC secret, consent evidence and deployment safeguards are satisfied.
