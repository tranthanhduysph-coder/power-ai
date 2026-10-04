# Apply POWER AI v1.0.1 database integrity hotfix

From repository root:

```bat
cd "C:\Users\Duy Tran\Downloads\power-ai-local"
tar -xf "%USERPROFILE%\Downloads\power-ai-v1.0.1-database-integrity-hotfix.zip" -C "C:\Users\Duy Tran\Downloads\power-ai-local"
```

Then migrate and test:

```bat
cd apps\api
.venv\Scripts\activate
python -m app.db.migrate
python -m pytest -q
python -m compileall app
```

Return to repo root and verify:

```bat
cd ..\..
set PYTHONPATH=apps\api
python scripts\release\verify_local_release.py
```

Expected catalog checks:

```text
[PASS] Biology 10 catalog: 26/26 numbered units
[PASS] Biology 11 catalog: 29/29 numbered units
[PASS] Biology 12 catalog: 35/35 numbered units
[PASS] Active cycle uniqueness: duplicates=0

POWER AI v1.0 local verification: READY
```
