# POWER AI v1.4.3 — Status parser hotfix

Problem:
- `safe_power_batch.py` prints status both before and after a batch.
- `run_power_grade.py` parsed the FIRST `POWER-ready:` line in the combined output.
- After a successful 0 -> 5 batch it still read 0 and incorrectly stopped with:
  `[STOP] No increase in POWER-ready count`.

Fix:
- status parsing now uses the LAST occurrence of each status field.

No database migration.
No regeneration of completed units.
The first 5 Biology 10 units already activated remain valid.

Apply from repository root:

    tar -xf "%USERPROFILE%\Downloads\power-ai-v1.4.3-status-parser-hotfix.zip" -C "C:\Users\Duy Tran\Downloads\power-ai-local"
    python hotfix_v143\apply_v143.py

Then:

    set PYTHONUTF8=1
    set PYTHONIOENCODING=utf-8
    set PYTHONPATH=apps\api
    apps\api\.venv\Scripts\activate
    python scripts\content\run_power_grade.py --grade 10 --limit 5

Expected resume point:
    POWER-ready: 5
    Not started: 21
