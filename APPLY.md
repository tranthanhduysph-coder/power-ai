# Apply POWER AI v0.6

This patch assumes v0.5.1 phase review is already applied.

From repo root on Windows CMD:

```bat
cd "C:\Users\Duy Tran\Downloads\power-ai-local"
tar -xf "%USERPROFILE%\Downloads\power-ai-v0.6-work-rich-tutor-patch.zip" -C "C:\Users\Duy Tran\Downloads\power-ai-local"
```

Backend:

```bat
cd apps\api
.venv\Scripts\activate
python -m pytest -q
python -m compileall app
```

Expected test count after v0.5.1 + v0.6: 15 passed.

Frontend:

```bat
cd ..\web
npm run build
```

No database migration or seed is required for v0.6.
