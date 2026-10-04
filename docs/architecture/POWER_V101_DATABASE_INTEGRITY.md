# POWER AI v1.0.1 — Database integrity hotfix

This hotfix addresses two release-verifier findings from the v1.0 local baseline.

## 1. Curriculum catalog counting

The v0.9 curriculum seed is complete: the numbered KNTT catalog contains 26 items for Biology 10, 29 for Biology 11, and 35 for Biology 12.

The v1.0 verifier incorrectly counted only rows with `unit_type='lesson'`, excluding numbered `practice` and `project` entries. The corrected release check counts visible numbered curriculum entries with unit types `lesson`, `practice`, or `project`.

Expected totals:

- Biology 10: 19 lessons + 7 practices = 26 numbered units
- Biology 11: 21 lessons + 8 practices = 29 numbered units
- Biology 12: 28 lessons + 6 practices + 1 project = 35 numbered units

## 2. Duplicate active POWER cycles

Historical local data may contain more than one active `learning_session` for the same `(user_id, curriculum_unit_id)` from earlier development builds.

Migration `007_active_cycle_integrity`:

1. preserves the most recently updated active session;
2. marks older duplicates as `abandoned` and sets `ended_at`;
3. does not delete POWER phase evidence;
4. creates a partial unique index so only one active session can exist per learner and curriculum unit.

Abandoned historical cycles remain visible through POWER cycle history.

## Release version

Local readiness version becomes `1.0.1-local` and now requires migration `007_active_cycle_integrity`.
