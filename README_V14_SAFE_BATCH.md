# POWER AI v1.4 — Safe batch runner

This helper does not replace `build_power.py`. It wraps the existing stable builder
conservatively so Biology 10/11 do not repeat the failure pattern seen during
Biology 12.

Safety rules:
- generate first;
- stop on any `[ERROR]`, traceback, or non-zero exit code;
- QA next;
- stop on any `[FAIL]` or `[WARN]`;
- activate only when the whole QA batch is clean;
- print status before and after;
- never activates a mixed PASS/FAIL batch.

Usage from repository root:

    set PYTHONPATH=apps\api
    apps\api\.venv\Scripts\activate

Status only:

    python scripts\content\safe_power_batch.py --grade 10 --status-only
    python scripts\content\safe_power_batch.py --grade 11 --status-only

One safe batch:

    python scripts\content\safe_power_batch.py --grade 10 --limit 5
    python scripts\content\safe_power_batch.py --grade 11 --limit 5

Repeat one batch at a time until the grade reports all units POWER-ready.

This wrapper assumes the current `build_power.py` already contains the stabilized
v1.2.x/v1.3.x normalizers and activation fixes that produced Biology 12 at 35/35.
