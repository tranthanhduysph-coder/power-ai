# POWER AI v0.9 — Curriculum Database Generalization

## Goal
Replace the DNA-only hard-coded learning route with a database-driven Biology 10–12 curriculum catalog. Only units with a POWER blueprint are launchable; the full catalog is visible and can be progressively activated as content is ingested.

## 1. Create branch
From `C:\Users\Duy Tran\Downloads\power-ai-local`:

```bat
git status
git checkout -b feature/power-v09-curriculum-db
```

If the branch already exists:

```bat
git checkout feature/power-v09-curriculum-db
```

## 2. Apply patch

```bat
tar -xf "%USERPROFILE%\Downloads\power-ai-v0.9-curriculum-database-patch.zip" -C "C:\Users\Duy Tran\Downloads\power-ai-local"
```

## 3. Migrate and seed

```bat
cd "C:\Users\Duy Tran\Downloads\power-ai-local\apps\api"
.venv\Scripts\activate
python -m app.db.migrate
python -m app.db.seed
```

Expected new entries:
- migration `006_curriculum_generalization`
- seed `005_curriculum_catalog`

## 4. Backend tests

```bat
python -m pytest -q
python -m compileall app
```

Expected: `21 passed` and no compile errors.

## 5. Frontend production build

```bat
cd "C:\Users\Duy Tran\Downloads\power-ai-local\apps\web"
npm run build
```

Fix any TypeScript error before continuing.

## 6. Verify curriculum database

```bat
cd "C:\Users\Duy Tran\Downloads\power-ai-local"
set PYTHONPATH=apps\api
python scripts\db\verify_curriculum_v09.py
```

Expected essentials:
- Biology 10 lessons = 26
- Biology 11 lessons = 29
- Biology 12 lessons = 35
- `B12_DNA_REPLICATION` is POWER-ready
- DNA POWER blueprint exists
- DNA source mapping exists
- legacy demo units are hidden
- final status `OK`

## 7. Restart local services

FastAPI:

```bat
cd "C:\Users\Duy Tran\Downloads\power-ai-local\apps\api"
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

Next.js in another CMD:

```bat
cd "C:\Users\Duy Tran\Downloads\power-ai-local\apps\web"
npm run dev
```

Keep Firebase Auth Emulator running as before.

## 8. Manual acceptance tests

1. Open `http://localhost:3000/learn`.
2. Verify tabs Biology 10, Biology 11, Biology 12.
3. Verify the database catalog shows all lessons and textbook printed page ranges.
4. Verify only `DNA và cơ chế tái bản DNA` is currently marked ready for POWER.
5. Click it and verify route becomes `/learn/B12_DNA_REPLICATION`.
6. Verify `/learn/dna-replication` redirects to `/learn/B12_DNA_REPLICATION`.
7. Run Prepare → Organize → Work and verify the dynamic route behaves like the prior DNA page.
8. Verify Dashboard Continue points to `/learn/<unit_code>`.
9. Open Practice and verify the unit selector is loaded from the database.
10. In Evaluate mode, verify the unit is locked to the POWER cycle unit.

## 9. Git checks and commit

```bat
cd "C:\Users\Duy Tran\Downloads\power-ai-local"
git diff --check
git add .
git diff --cached --check
git status --short
git commit -m "feat: generalize POWER curriculum and database-driven lessons"
git push -u origin feature/power-v09-curriculum-db
```

Do not merge to `main` until the v0.9 manual acceptance tests pass.
