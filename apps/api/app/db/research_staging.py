"""Opt-in startup for a disposable, synthetic-only research staging database."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

DATABASE_NAME = "power_research_staging"
FIXTURE_PREFIX = "staging-fixture-"


def staging_database_url(value: str, enabled: str) -> str:
    if enabled != "true":
        raise ValueError("Research staging startup requires explicit opt-in")
    url = make_url(value)
    if (url.drivername not in ("postgres", "postgresql", "postgresql+psycopg")
            or url.database != DATABASE_NAME
            or not (url.host or url.query.get("host"))
            or any(k in url.query for k in ("hostaddr", "service", "options"))):
        raise ValueError("Refusing startup outside the disposable research staging database")
    return url.set(drivername="postgresql+psycopg").render_as_string(hide_password=False)


def assert_synthetic_database(conn, admin_uid: str) -> None:
    if not conn.scalar(text("SELECT to_regclass('public.users')")):
        return
    unexpected = conn.scalar(text("""
        SELECT EXISTS(SELECT 1 FROM users
          WHERE left(firebase_uid, :prefix_length) <> :prefix AND firebase_uid <> :admin)
    """), {"prefix": FIXTURE_PREFIX, "prefix_length": len(FIXTURE_PREFIX), "admin": admin_uid})
    if unexpected:
        raise ValueError("Refusing staging startup: database contains non-fixture learner accounts")


def is_staging_admin(claims: dict, uid: str, email: str) -> bool:
    return bool(uid and email
                and str(claims.get("uid") or claims.get("sub") or "") == uid
                and str(claims.get("email") or "").strip().casefold() == email.strip().casefold()
                and claims.get("email_verified") is True)


def create_staging_app():
    # Validate again in the actual server process, before importing its DB engine.
    staging_database_url(os.environ.get("DATABASE_URL", ""),
                         os.environ.get("RESEARCH_STAGING_ENABLED", ""))
    from fastapi import Depends, Header, HTTPException
    from app.core import auth
    from app.db.session import get_db
    from app.main import app

    def only_staging_admin(authorization: str | None = Header(default=None), db=Depends(get_db)):
        if os.environ.get("FIREBASE_AUTH_EMULATOR_HOST"):
            raise HTTPException(403, "Authentication emulator is forbidden in research staging")
        claims = auth._claims_from_bearer(authorization, check_revoked=True)
        if not is_staging_admin(claims, os.environ.get("RESEARCH_ADMIN_FIREBASE_UID", ""),
                                os.environ.get("RESEARCH_ADMIN_EMAIL", "ttduy@sgu.edu.vn")):
            # Deny before the ordinary auth dependency can persist a student profile.
            raise HTTPException(403, "Research staging is restricted to its verified administrator")
        return auth._upsert_power_user(db, claims)

    app.dependency_overrides[auth.get_current_user] = only_staging_admin
    return app


def seed_synthetic_activity(conn) -> None:
    """Idempotent fixtures, with no consent decisions and no real learner data."""
    def fixture_id(label):
        return uuid5(NAMESPACE_URL, "power-research-staging:" + label)

    concept = fixture_id("concept")
    when = datetime(2026, 10, 19, tzinfo=timezone.utc)
    conn.execute(text("""INSERT INTO concepts(id,code,name_vi,name_en)
        VALUES (:id,'SYNTHETIC_RESEARCH_TEST','Khái niệm giả để thử nghiệm','Synthetic test concept')
        ON CONFLICT (id) DO NOTHING"""), {"id": concept})
    for label in ("allow", "deny", "absent"):
        uid, session, cycle, practice, attempt = [fixture_id(f"{label}-{kind}") for kind in
                                                 ("user", "session", "cycle", "practice", "attempt")]
        p = {"uid": uid, "session": session, "cycle": cycle, "practice": practice,
             "attempt": attempt, "concept": concept, "when": when,
             "payload": '{"smart_score":4,"readiness":0.75}',
             "firebase": FIXTURE_PREFIX + label, "email": f"research-{label}@example.invalid"}
        conn.execute(text("""INSERT INTO users(id,firebase_uid,email,display_name)
            VALUES (:uid,:firebase,:email,'SYNTHETIC TEST ACCOUNT') ON CONFLICT (id) DO NOTHING"""), p)
        conn.execute(text("""INSERT INTO learning_sessions(id,user_id,started_at)
            VALUES (:session,:uid,:when) ON CONFLICT (id) DO NOTHING"""), p)
        conn.execute(text("""INSERT INTO power_sessions(id,user_id,learning_session_id)
            VALUES (:cycle,:uid,:session) ON CONFLICT (id) DO NOTHING"""), p)
        conn.execute(text("""INSERT INTO practice_sets(id,user_id,mode,power_session_id,purpose)
            VALUES (:practice,:uid,'custom',:cycle,'evaluate') ON CONFLICT (id) DO NOTHING"""), p)
        conn.execute(text("""INSERT INTO practice_attempts(id,user_id,practice_set_id,started_at,accuracy)
            VALUES (:attempt,:uid,:practice,:when,0.75) ON CONFLICT (id) DO NOTHING"""), p)
        conn.execute(text("""INSERT INTO learning_events(user_id,learning_session_id,event_type,payload,created_at)
            SELECT :uid,:session,'staging_fixture',CAST(:payload AS jsonb),:when
            WHERE NOT EXISTS (SELECT 1 FROM learning_events WHERE user_id=:uid AND event_type='staging_fixture')"""), p)
        conn.execute(text("""INSERT INTO mastery_snapshots(user_id,concept_id,mastery_score,captured_at)
            SELECT :uid,:concept,0.6,:when
            WHERE NOT EXISTS (SELECT 1 FROM mastery_snapshots WHERE user_id=:uid AND concept_id=:concept)"""), p)


def main() -> None:
    dsn = staging_database_url(os.environ.get("DATABASE_URL", ""),
                               os.environ.get("RESEARCH_STAGING_ENABLED", ""))
    os.environ["DATABASE_URL"] = dsn
    # Check existing accounts before applying any migration or fixture writes.
    probe = create_engine(dsn)
    try:
        with probe.connect() as conn:
            assert_synthetic_database(conn, os.environ.get("RESEARCH_ADMIN_FIREBASE_UID", ""))
    finally:
        probe.dispose()
    # These imports must follow URL validation; application settings cache the DSN.
    from app.db.migrate import main as migrate
    from app.db.session import engine

    migrate()
    with engine.begin() as conn:
        seed_synthetic_activity(conn)
    print("Research staging initialized: synthetic fixtures only; no consent auto-created.")
    os.execvp("uvicorn", ["uvicorn", "app.db.research_staging:create_staging_app", "--factory", "--host", "0.0.0.0",
                          "--port", os.environ.get("PORT", "8000")])


if __name__ == "__main__":
    main()
