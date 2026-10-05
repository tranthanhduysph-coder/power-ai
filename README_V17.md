# POWER AI v1.7 — Local Release Finalizer

This is the final non-destructive local-build gate.

It does NOT generate or replace curriculum content and does NOT write learner
data. It verifies the finished local build using the real repo:

- ordinary curriculum audit = 90/90 PASS;
- strict warning review (advisory, not falsely classified as content failure);
- full backend pytest suite;
- FastAPI POWER contract for Prepare / Organize / Work / Rethink;
- practice-backed Evaluate capability;
- DB table readiness, 90/90 POWER-ready state, FK orphan integrity, duplicate
  phase-state guard;
- Next.js production build.

When every blocking check passes it creates:

    LOCAL_BUILD_COMPLETE.txt
    storage\release-reports\power_ai_local_release_v1_7.json

Run from repo root after extracting:

    scripts\release\finish_local_build.cmd

or:

    set PYTHONUTF8=1
    set PYTHONIOENCODING=utf-8
    set PYTHONPATH=apps\api
    apps\api\.venv\Scripts\activate
    python scripts\release\finalize_local_v17.py

Success:

    [DONE] POWER AI local build is release-complete.

The next stage is deliberately separate: live browser + Firebase-auth E2E.
Keeping it separate prevents an unavailable emulator/browser from being
misreported as a defect in an otherwise clean application build.
