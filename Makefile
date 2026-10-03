.PHONY: db db-down migrate seed api web firebase

db:
	docker compose up -d db

db-down:
	docker compose down

migrate:
	cd apps/api && python -m app.db.migrate

seed:
	cd apps/api && python -m app.db.seed

api:
	cd apps/api && uvicorn app.main:app --reload --port 8000

web:
	cd apps/web && npm run dev

firebase:
	firebase emulators:start --only auth
