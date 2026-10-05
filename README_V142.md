POWER AI v1.4.2 - Windows UTF-8 hotfix

Fixes UnicodeEncodeError/charmap codec crashes on Windows CMD.

Changes:
- forces UTF-8 for child Python processes;
- prints captured output safely even on cp1252 consoles;
- replaces decorative Unicode separators in runner-owned messages with ASCII.

No DB migration.

After applying, first run status because the failed display step may have occurred
after some drafts were already generated.

Commands:
  set PYTHONUTF8=1
  set PYTHONIOENCODING=utf-8
  set PYTHONPATH=apps\api
  apps\api\.venv\Scripts\activate
  python scripts\content\safe_power_batch.py --grade 10 --status-only
  python scripts\content\run_power_grade.py --grade 10 --limit 5
