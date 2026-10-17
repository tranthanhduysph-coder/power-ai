"""Smoke-test migration 015 in a temporary PostgreSQL 16 database only.

Run with DATABASE_URL pointing to an EMPTY disposable database. NEVER production.
"""
from pathlib import Path
import os
import psycopg

dsn = os.environ.get("RESEARCH_TEST_DATABASE_URL")
if not dsn or "localhost" not in dsn and "127.0.0.1" not in dsn:
    raise SystemExit("Refusing migration test unless RESEARCH_TEST_DATABASE_URL points to localhost")

migration = Path(__file__).resolve().parents[3] / "database/migrations/015_research_analytics.sql"
with psycopg.connect(dsn, autocommit=True) as conn:
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
        cur.execute("CREATE TABLE users (id uuid PRIMARY KEY)")
        cur.execute("CREATE TABLE mastery_snapshots (id bigserial PRIMARY KEY, user_id uuid REFERENCES users(id), captured_at timestamptz NOT NULL)")
        for attempt in range(2):
            # DDL is rerunnable thanks to IF NOT EXISTS; production migrator records version once.
            cur.execute(migration.read_text(encoding="utf-8"))
        cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE 'research_%'")
        assert cur.fetchone()[0] == 3, "Research tables not created"
        cur.execute("INSERT INTO users(id) VALUES (gen_random_uuid()), (gen_random_uuid()) RETURNING id")
        u1, u2 = [r[0] for r in cur.fetchall()]
        cur.execute("""
            INSERT INTO research_consent
              (user_id,survey_response_ref,survey_version,consented_at,activity_scope_start_at,
               research_allowed,required_authorizations_verified,recorded_by)
            VALUES (%s,'response-1','V5',now(),now(),true,true,%s)
        """, (u1,u1))
        cur.execute("SELECT research_allowed FROM research_consent WHERE user_id=%s", (u1,))
        assert cur.fetchone()[0] is True
        # Duplicate source reference cannot be silently assigned to a different learner.
        try:
            cur.execute("""
                INSERT INTO research_consent
                  (user_id,survey_response_ref,survey_version,consented_at,activity_scope_start_at,
                   research_allowed,required_authorizations_verified,recorded_by)
                VALUES (%s,'response-1','V5',now(),now(),true,true,%s)
            """, (u2,u2))
        except psycopg.errors.UniqueViolation:
            pass
        else:
            raise AssertionError("Duplicate survey response accepted")
        # No research consent without verified authorizations.
        try:
            cur.execute("""
                INSERT INTO research_consent
                  (user_id,survey_response_ref,survey_version,consented_at,activity_scope_start_at,
                   research_allowed,required_authorizations_verified,recorded_by)
                VALUES (%s,'response-2','V5',now(),now(),true,false,%s)
            """, (u2,u2))
        except psycopg.errors.CheckViolation:
            pass
        else:
            raise AssertionError("Unverified consent accepted")
        cur.execute("SELECT COUNT(*) FROM research_consent")
        assert cur.fetchone()[0] == 1
        print("PASS: migration repeated, constraints enforced, original schema untouched")
