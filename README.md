# POWER AI — v1.0 Local Baseline

Greenfield commercial web application foundation for the **POWER learning process in Biology**.

This repository is intentionally independent from the earlier GOFAI research project.

## What is already wired

- Next.js + TypeScript student web app
- FastAPI backend
- PostgreSQL + pgvector schema
- Firebase Authentication integration
  - Google sign-in
  - email/password registration
  - Firebase Auth Emulator support for local development
- Bilingual UI/content foundation: Vietnamese / English
- POWER state persistence: Prepare → Organize → Work → Evaluate → Rethink
- Practice engine with three required item formats:
  - multiple choice
  - true/false
  - short answer
- Custom and adaptive practice modes
- Learner event log, question attempts, concept mastery, misconception-ready schema
- Product / plan / entitlement / usage-ledger foundation for future paid access
- RAG-ready content schema for Biology 10–12 KNTT + Campbell Biology
- Mock structured POWER Tutor response so the complete app can run before an AI provider is connected

## Local vertical slice

The local release now has a database-driven Biology 10–12 curriculum catalog. The currently POWER-ready content remains intentionally small:

`Biology 10 → Nucleic acids → DNA replication`

Concepts include DNA structure, DNA polymerase, leading strand, lagging strand and Okazaki fragments. The seed bank contains all three practice item formats.

---

## 1. Requirements

Recommended:

- Node.js 20+
- npm 10+
- Python 3.11+
- Docker Desktop / Docker Engine with Compose
- Firebase CLI (`npm install -g firebase-tools`) if using the Firebase Auth Emulator

## 2. Start PostgreSQL

Copy the environment file:

```bash
cp .env.example .env
cp apps/web/.env.local.example apps/web/.env.local
```

Start only the database:

```bash
docker compose up -d db
```

The image already includes `pgvector`.

## 3. Start the API

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate       # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Run migrations and seed data from repo root paths
python -m app.db.migrate
python -m app.db.seed

uvicorn app.main:app --reload --port 8000
```

API docs:

- http://localhost:8000/docs
- health: http://localhost:8000/api/v1/health

## 4. Start Firebase Auth Emulator

From the repository root:

```bash
firebase emulators:start --only auth
```

- Auth emulator: http://127.0.0.1:9099
- Emulator UI: http://127.0.0.1:4000

The local Firebase project id is `demo-power-ai`; no production credentials are needed for emulator development.

> Google sign-in uses the Firebase Auth Emulator in local mode. Email/password is also supported.

## 5. Start the web app

```bash
cd apps/web
npm install
npm run dev
```

Open:

- http://localhost:3000

## Optional: API dev-auth fallback

If Firebase CLI is temporarily unavailable, set:

```env
AUTH_MODE=dev
NEXT_PUBLIC_AUTH_MODE=dev
```

The web app will use a local development identity and the API will accept `X-Dev-User`. This mode exists only for smoke testing and must never be enabled in production.

---

## Core runtime flow

```text
Firebase Auth
    ↓
Next.js
    ↓ Firebase ID token
FastAPI
    ↓
POWER internal user UUID
    ↓
PostgreSQL
    ├── POWER session state
    ├── learning events
    ├── practice attempts
    ├── concept mastery
    └── usage ledger
```

## Knowledge architecture

The production knowledge base is intentionally constrained to:

1. Biology 10 KNTT
2. Biology 11 KNTT
3. Biology 12 KNTT
4. Campbell Biology

The books are **sources**, not the center of the database. The center is the shared concept layer:

```text
Source → Section → Chunk → Concept ← Curriculum unit
                              ↓
                         Visual / Question
```

PDF files themselves should remain in private object storage and should not be committed to Git.

## Next milestones

1. Validate this vertical slice locally.
2. Add private object storage configuration.
3. Build the ingestion worker for the four approved knowledge sources.
4. Add concept mapping + embeddings.
5. Replace the mock Tutor provider with the selected production AI provider.
6. Expand Biology 10, then Biology 11 and 12.
7. Add billing provider integration after entitlement logic is tested.

See `docs/architecture/FOUNDATION.md` for architecture decisions.

## v0.2 — Knowledge ingestion smoke test

After applying migration `002_knowledge_ingestion.sql` and installing the updated API requirements, ingest the POWER-owned demo source from the repository root:

```bat
python scripts\ingest\ingest_source.py --manifest content\sources\demo_dna_replication\manifest.json
```

Then test authenticated retrieval at `POST /api/v1/retrieval/search` in Swagger (`http://localhost:8000/docs`). The v0.2 default embedding provider is `local_hash`: a zero-cost local development embedding used to verify pgvector plumbing. It will be replaced by a production semantic embedding provider later without changing the database contract.

See `docs/architecture/KNOWLEDGE_INGESTION_V02.md` for the full workflow and private-PDF rules.



## v1.0 local release checks

With the API virtual environment active and local services running:

```bat
python scripts\release\check_local.py
```

Database maintenance:

```bat
python scripts\db\local_db.py status
python scripts\db\local_db.py backup
```

Destructive reset and restore require explicit confirmation. See `docs/architecture/POWER_V10_LOCAL_RELEASE.md`.

Health endpoints:

- `GET /api/v1/health/live`
- `GET /api/v1/health`
- `GET /api/v1/health/ready`

## v1.1 content build

The curriculum catalog is separate from textbook ingestion. Use `scripts/content/build_kntt.py` to plan, ingest and verify the KNTT Biology 10–12 scanned PDFs. `content_status` tracks textbook ingestion; `is_power_ready` remains reserved for reviewed POWER learning blueprints.


## Copyright and licensing

Copyright © 2026 Trần Thanh Duy. Unless explicitly stated otherwise, original POWER-AI-WEB code, product design, documentation, database design, and project-created educational materials are proprietary and all rights are reserved.

Public visibility of this repository does not mean the entire project is open source. Third-party components remain governed by their own licenses. See `LICENSE.md`, `THIRD_PARTY_NOTICES.md`, and `docs/LEGAL_COMPLIANCE.md`.

Textbooks, publisher figures, Campbell Biology materials, private PDFs, user data, production databases, API keys, and other third-party/private materials are not licensed for public reuse by this repository.

Important: the current PDF ingestion pipeline uses PyMuPDF/MuPDF. Before a proprietary commercial deployment, resolve its AGPL/commercial licensing requirements as described in `THIRD_PARTY_NOTICES.md`.
