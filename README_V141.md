# POWER AI v1.4.1 — Full-grade safe runner

Runs the existing v1.4 `safe_power_batch.py` repeatedly for ONE grade.

It stops immediately on:
- generation error;
- QA failure;
- QA warning;
- traceback;
- activation/database error;
- no progress between batches.

It never intentionally continues past the first problematic batch.

## Apply

From repository root:

    tar -xf "%USERPROFILE%\Downloads\power-ai-v1.4.1-full-grade-safe-runner.zip" -C "C:\Users\Duy Tran\Downloads\power-ai-local"

No migration is required.

## Run Biology 10

    set PYTHONPATH=apps\api
    apps\api\.venv\Scripts\activate
    python scripts\content\run_power_grade.py --grade 10 --limit 5

Expected clean finish:

    POWER-ready: 26
    QA-passed awaiting activation: 0
    Validated awaiting QA: 0
    Draft needs regeneration/fix: 0
    Not started: 0

## Run Biology 11 only after Grade 10 finishes cleanly

    python scripts\content\run_power_grade.py --grade 11 --limit 5

Expected clean finish:

    POWER-ready: 29
    QA-passed awaiting activation: 0
    Validated awaiting QA: 0
    Draft needs regeneration/fix: 0
    Not started: 0
