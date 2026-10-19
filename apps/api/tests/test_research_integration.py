"""Real PostgreSQL tests with synthetic learners; never connect to production.

Set RESEARCH_TEST_DATABASE_URL to a disposable local database after migrations.
Each test rolls back even when the endpoint commits its own transaction.
"""
import csv
import io
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.api import health, research
from app.core.auth import CurrentUser, get_current_user
from app.db.session import get_db
from app.services.mastery import update_mastery
from app.db.research_staging import assert_synthetic_database, seed_synthetic_activity


T0 = datetime(2026, 10, 10, tzinfo=timezone.utc)


@pytest.fixture
def local_engine():
    dsn = os.environ.get("RESEARCH_TEST_DATABASE_URL")
    if not dsn:
        pytest.skip("requires an explicitly configured disposable local PostgreSQL")
    url = make_url(dsn)
    host = url.query.get("host") or url.host or ""
    if (url.get_backend_name() != "postgresql"
            or not (host in ("localhost", "127.0.0.1", "::1") or host.startswith("/"))
            or url.query.get("hostaddr") or url.query.get("service")
            or url.database not in ("research_restore", "research_integration_test")):
        pytest.fail("Refusing tests outside a named disposable local database")
    engine = create_engine(url)
    yield engine
    engine.dispose()


@pytest.fixture
def case(monkeypatch, local_engine):
    engine = local_engine
    with engine.connect() as conn:
        tx = conn.begin()
        db = Session(bind=conn, join_transaction_mode="create_savepoint")
        # Existing checkpoint accounts must never become eligible for a test export.
        assert db.scalar(text("SELECT count(*) FROM research_consent")) == 0
        ids = [uuid4() for _ in range(4)]
        for i, uid in enumerate(ids):
            db.execute(text("INSERT INTO users(id,firebase_uid,email) VALUES (:id,:uid,:email)"),
                       {"id": uid, "uid": f"research-test-{uid}", "email": f"test-{i}@example.invalid"})
        concept = db.scalar(text("""INSERT INTO concepts(code,name_vi,name_en)
            VALUES (:code,'Khái niệm thử','Test concept') RETURNING id"""), {"code": f"research-test-{uuid4()}"})
        admin = CurrentUser(ids[0], "test-admin-uid", "ttduy@sgu.edu.vn", "Test", "admin")
        settings = SimpleNamespace(auth_mode="firebase", research_admin_firebase_uid=admin.firebase_uid,
                                   research_admin_email=admin.email, research_pseudonym_key="a" * 40)
        monkeypatch.setattr(research, "get_settings", lambda: settings)
        monkeypatch.setattr(research, "_claims_from_bearer", lambda _, **kwargs: {
            "uid": admin.firebase_uid, "email": admin.email, "email_verified": True})
        app = FastAPI()
        app.include_router(research.router)
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: admin
        with TestClient(app, raise_server_exceptions=False) as client:
            yield SimpleNamespace(db=db, client=client, ids=ids, admin=admin, settings=settings, concept=concept)
        db.close()
        tx.rollback()


def consent(case, who=1, when=T0, **overrides):
    payload = dict(email=f"test-{who}@example.invalid", survey_response_ref=f"test-response-{who}",
                   survey_version="test-v1", consented_at=when.isoformat(), research_allowed=True,
                   required_authorizations_verified=True)
    payload.update(overrides)
    return case.client.post("/research/consents", json=payload)


def exported(case, dataset, **overrides):
    params = dict(start_at=(T0 - timedelta(days=1)).isoformat(),
                  end_at=(T0 + timedelta(days=2)).isoformat(), limit=100, offset=0)
    params.update(overrides)
    return case.client.get(f"/research/exports/{dataset}", params=params)


def records(response):
    assert response.status_code == 200
    return list(csv.DictReader(io.StringIO(response.content.decode("utf-8-sig"))))


def seed_activity(case):
    db = case.db
    concept = case.concept
    for who in (1, 2, 3):
        uid = case.ids[who]
        # One event before consent, one exactly at consent, one at the end boundary.
        for when in (T0 - timedelta(seconds=1), T0, T0 + timedelta(days=2)):
            db.execute(text("""INSERT INTO learning_events(user_id,event_type,payload,created_at)
                VALUES (:uid,'test_event',CAST(:payload AS jsonb),:when)"""),
                {"uid": uid, "when": when,
                 "payload": '{"smart_score":0.8,"readiness":"PRIVATE-SENTINEL",'
                            '"answer":"PRIVATE-SENTINEL","email":"PRIVATE-SENTINEL"}'})
        ls = db.scalar(text("INSERT INTO learning_sessions(user_id,started_at) VALUES (:uid,:t) RETURNING id"), {"uid": uid, "t": T0})
        ps = db.scalar(text("INSERT INTO power_sessions(user_id,learning_session_id) VALUES (:uid,:ls) RETURNING id"), {"uid": uid, "ls": ls})
        practice = db.scalar(text("""INSERT INTO practice_sets(user_id,mode,power_session_id)
            VALUES (:uid,'custom',:ps) RETURNING id"""), {"uid": uid, "ps": ps})
        db.execute(text("""INSERT INTO practice_attempts(user_id,practice_set_id,started_at,accuracy)
            VALUES (:uid,:practice,:t,0.75)"""), {"uid": uid, "practice": practice, "t": T0})
        db.execute(text("""INSERT INTO mastery_snapshots(user_id,concept_id,mastery_score,captured_at)
            VALUES (:uid,:concept,0.6,:t)"""), {"uid": uid, "concept": concept, "t": T0})
    return concept


@pytest.mark.parametrize("dataset", research.DATASETS)
def test_all_datasets_consent_scope_withdrawal_and_audit(case, dataset):
    seed_activity(case)
    assert consent(case).status_code == 200
    assert consent(case, who=2, research_allowed=False, improvement_allowed=True).status_code == 200
    # who=3 has no decision. Neither product consent nor login permits research.
    response = exported(case, dataset)
    rows = records(response)
    assert len(rows) == 1
    assert rows[0]["participant_id"] == research._participant_id(case.ids[1])
    assert response.headers["cache-control"] == "no-store"
    if dataset != "linkage":
        assert "email" not in rows[0]
        assert all(str(uid) not in response.text for uid in case.ids)
        assert "PRIVATE-SENTINEL" not in response.text
        if dataset == "events":
            assert rows[0]["smart_score"] == "0.8"
            assert rows[0]["readiness"] == ""
    else:
        assert rows[0]["email"] == "test-1@example.invalid"
    audit = case.db.execute(text("SELECT dataset,rows_exported FROM research_export_audit")).one()
    assert tuple(audit) == (dataset, 1)
    assert consent(case, when=T0 + timedelta(hours=1), research_allowed=False).status_code == 200
    assert records(exported(case, dataset)) == []
    assert case.db.scalar(text("SELECT count(*) FROM research_consent_audit WHERE user_id=:uid"), {"uid": case.ids[1]}) == 2


def test_missing_key_does_not_commit_consent(case):
    case.settings.research_pseudonym_key = ""
    assert consent(case).status_code == 503
    assert case.db.scalar(text("SELECT count(*) FROM research_consent")) == 0
    assert case.db.scalar(text("SELECT count(*) FROM research_consent_audit")) == 0
    assert exported(case, "events").status_code == 503
    assert case.db.scalar(text("SELECT count(*) FROM research_export_audit")) == 0


def test_withdrawal_cannot_be_replayed_at_same_or_older_timestamp(case):
    assert consent(case).status_code == 200
    withdrawn = T0 + timedelta(hours=1)
    assert consent(case, when=withdrawn, research_allowed=False).status_code == 200
    assert consent(case, when=T0).status_code == 409
    assert consent(case, when=withdrawn).status_code == 409
    assert case.db.scalar(text("SELECT research_allowed FROM research_consent WHERE user_id=:uid"), {"uid": case.ids[1]}) is False


def test_source_reference_is_reserved_in_audit_history(case):
    assert consent(case, survey_response_ref="original-response").status_code == 200
    assert consent(case, when=T0 + timedelta(hours=1), survey_response_ref="withdrawal-response", research_allowed=False).status_code == 200
    assert consent(case, who=2, survey_response_ref="original-response").status_code == 409


def test_duplicate_email_source_and_unverified_authorizations(case):
    assert consent(case, required_authorizations_verified=False).status_code == 422
    assert consent(case, email="missing@example.invalid").status_code == 404
    assert consent(case).status_code == 200
    assert consent(case, who=2, survey_response_ref="test-response-1").status_code == 409
    case.db.execute(text("UPDATE users SET email=' TEST-1@example.invalid ' WHERE id=:id"), {"id": case.ids[2]})
    assert consent(case).status_code == 409


def test_export_paging_window_and_admin_boundary(case):
    seed_activity(case)
    assert consent(case).status_code == 200
    assert len(records(exported(case, "events", limit=1))) == 1
    assert records(exported(case, "events", limit=1, offset=1)) == []
    for params in ({"limit": 20001}, {"offset": -1}, {"start_at": "2026-10-10T00:00:00"},
                   {"end_at": T0.isoformat(), "start_at": T0.isoformat()},
                   {"end_at": (T0 + timedelta(days=400)).isoformat()}):
        assert exported(case, "events", **params).status_code == 422
    for mode, uid in (("dev", "test-admin-uid"), ("firebase", ""), ("firebase", "different")):
        case.settings.auth_mode = mode
        case.settings.research_admin_firebase_uid = uid
        assert exported(case, "events").status_code == 403
        assert consent(case).status_code == 403
        assert case.client.get("/research/status").status_code == 403


def test_mastery_snapshot_uses_same_transaction(case):
    concept = case.concept
    uid = case.ids[1]
    with case.db.begin_nested() as savepoint:
        score = update_mastery(case.db, user_id=uid, concept_id=concept, correct=True, difficulty="medium", hint_used=False)
        assert score == pytest.approx(0.56)
        assert float(case.db.scalar(text("SELECT mastery_score FROM mastery_snapshots WHERE user_id=:uid"), {"uid": uid})) == pytest.approx(score)
        savepoint.rollback()
    assert case.db.scalar(text("SELECT count(*) FROM mastery_snapshots WHERE user_id=:uid"), {"uid": uid}) == 0
    assert case.db.scalar(text("SELECT count(*) FROM concept_mastery WHERE user_id=:uid"), {"uid": uid}) == 0


def test_readiness_detects_missing_research_migration_and_table(case):
    case.db.execute(text("DELETE FROM schema_migrations WHERE version='015_research_analytics'"))
    case.db.execute(text("DROP TABLE research_export_audit"))
    with pytest.raises(research.HTTPException) as unavailable:
        health.readiness(case.db)
    assert unavailable.value.status_code == 503
    assert "015_research_analytics" in unavailable.value.detail["missing_migrations"]
    assert "research_export_audit" in unavailable.value.detail["missing_tables"]


def test_staging_fixtures_are_idempotent_and_never_grant_consent(local_engine):
    with local_engine.connect() as conn:
        transaction = conn.begin()
        try:
            if conn.scalar(text("SELECT count(*) FROM users")):
                pytest.skip("Fixture initialization is tested only on a fresh synthetic database")
            assert_synthetic_database(conn, "")
            seed_synthetic_activity(conn)
            seed_synthetic_activity(conn)
            assert_synthetic_database(conn, "")
            assert conn.scalar(text("SELECT count(*) FROM users WHERE firebase_uid LIKE 'staging-fixture-%'")) == 3
            assert conn.scalar(text("SELECT count(*) FROM learning_events WHERE event_type='staging_fixture'")) == 3
            assert conn.scalar(text("SELECT count(*) FROM research_consent")) == 0
            assert conn.scalar(text("SELECT count(*) FROM research_consent_audit")) == 0
        finally:
            transaction.rollback()


def test_staging_rejects_database_with_other_learner_accounts(case):
    with pytest.raises(ValueError, match="non-fixture learner accounts"):
        assert_synthetic_database(case.db, case.admin.firebase_uid)


def test_historical_scope_and_linkage_formula_utf8(case):
    seed_activity(case)
    assert consent(case, activity_scope_start_at=(T0 - timedelta(days=1)).isoformat()).status_code == 422
    assert consent(case, activity_scope_start_at=(T0 - timedelta(days=1)).isoformat(),
                   historical_coverage_confirmed=True, survey_response_ref="=FORM-TEST",
                   survey_version="Đợt thử nghiệm").status_code == 200
    assert len(records(exported(case, "events"))) == 2
    row = records(exported(case, "linkage"))[0]
    assert row["survey_response_ref"] == "'=FORM-TEST"
    assert row["survey_version"] == "Đợt thử nghiệm"


@pytest.mark.parametrize("shared_source", [False, True])
def test_concurrent_consent_imports(local_engine, monkeypatch, shared_source):
    """Independent connections exercise actual PostgreSQL locking and commits."""
    ids = [uuid4() for _ in range(3)]
    prefix = f"concurrency-{uuid4()}"
    admin = CurrentUser(ids[0], "test-admin", "ttduy@sgu.edu.vn", "Test", "admin")
    monkeypatch.setattr(research, "get_settings", lambda: SimpleNamespace(research_pseudonym_key="a" * 40))
    try:
        with local_engine.begin() as conn:
            for i, uid in enumerate(ids):
                conn.execute(text("INSERT INTO users(id,firebase_uid,email) VALUES (:id,:uid,:email)"),
                             {"id": uid, "uid": f"{prefix}-{i}", "email": f"{prefix}-{i}@example.invalid"})

        def submit(i):
            who = 1 + i if shared_source else 1
            payload = research.ConsentRecord(
                email=f"{prefix}-{who}@example.invalid",
                survey_response_ref=prefix if shared_source else f"{prefix}-{i}", survey_version="test",
                consented_at=T0 + timedelta(seconds=i), research_allowed=(i == 0),
                required_authorizations_verified=True)
            with Session(local_engine) as db:
                try:
                    research.record_verified_form_consent(payload, admin, db)
                    return 200
                except research.HTTPException as exc:
                    return exc.status_code

        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses = list(pool.map(submit, (0, 1)))
        with local_engine.connect() as conn:
            if shared_source:
                assert sorted(statuses) == [200, 409]
                assert conn.scalar(text("SELECT count(*) FROM research_consent WHERE survey_response_ref=:ref"), {"ref": prefix}) == 1
            else:
                assert statuses[1] == 200
                assert statuses[0] in (200, 409)
                row = conn.execute(text("SELECT research_allowed,consented_at FROM research_consent WHERE user_id=:uid"), {"uid": ids[1]}).one()
                assert row.research_allowed is False
                assert row.consented_at == T0 + timedelta(seconds=1)
    finally:
        # Only remove this test's synthetic accounts and their consent records.
        with local_engine.begin() as conn:
            for uid in ids[1:]:
                conn.execute(text("DELETE FROM research_consent_audit WHERE user_id=:uid"), {"uid": uid})
                conn.execute(text("DELETE FROM research_consent WHERE user_id=:uid"), {"uid": uid})
            for uid in ids:
                conn.execute(text("DELETE FROM users WHERE id=:uid"), {"uid": uid})
