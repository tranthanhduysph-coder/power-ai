"""Security and consent checks; no production database or Firebase calls."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.api import research
from app.core import auth
from app.core.auth import CurrentUser


def actor():
    return CurrentUser(
        id=uuid4(), firebase_uid="firebase-staff-uid",
        email="ttduy@sgu.edu.vn", display_name="Researcher", role="student",
    )


def settings(auth_mode="firebase", uid="firebase-staff-uid"):
    return SimpleNamespace(
        auth_mode=auth_mode,
        research_admin_firebase_uid=uid,
        research_admin_email="ttduy@sgu.edu.vn",
        research_pseudonym_key="this-is-a-long-random-and-private-test-key",
    )


def test_admin_requires_verified_uid_email_and_production(monkeypatch):
    monkeypatch.setattr(research, "get_settings", lambda: settings())
    monkeypatch.setattr(
        research, "_claims_from_bearer",
        lambda _, **kwargs: {"uid": "firebase-staff-uid", "email": "ttduy@sgu.edu.vn",
                   "email_verified": True},
    )
    assert research.require_research_admin(actor(), "Bearer example").firebase_uid == "firebase-staff-uid"

    monkeypatch.setattr(research, "get_settings", lambda: settings(auth_mode="dev"))
    with pytest.raises(HTTPException) as denied:
        research.require_research_admin(actor(), "Bearer example")
    assert denied.value.status_code == 403


@pytest.mark.parametrize("claims", [
    {"uid": "another-user", "email": "ttduy@sgu.edu.vn", "email_verified": True},
    {"uid": "firebase-staff-uid", "email": "fake@sgu.edu.vn", "email_verified": True},
    {"uid": "firebase-staff-uid", "email": "ttduy@sgu.edu.vn", "email_verified": False},
])
def test_admin_rejects_mismatched_claims(monkeypatch, claims):
    monkeypatch.setattr(research, "get_settings", lambda: settings())
    monkeypatch.setattr(research, "_claims_from_bearer", lambda _, **kwargs: claims)
    with pytest.raises(HTTPException) as denied:
        research.require_research_admin(actor(), "Bearer example")
    assert denied.value.status_code == 403


def consent_data(**overrides):
    data = dict(
        email="learner@example.com", survey_response_ref="form:response-1",
        survey_version="V5", consented_at=datetime.now(timezone.utc) - timedelta(days=1),
        research_allowed=True, improvement_allowed=False,
        required_authorizations_verified=True,
    )
    data.update(overrides)
    return data


def test_research_consent_requires_approvals_and_timezone():
    with pytest.raises(ValidationError):
        research.ConsentRecord(**consent_data(required_authorizations_verified=False))
    with pytest.raises(ValidationError):
        research.ConsentRecord(**consent_data(consented_at=datetime(2026, 10, 17, 12)))


def test_historical_coverage_needs_explicit_attestation():
    earlier = datetime.now(timezone.utc) - timedelta(days=4)
    with pytest.raises(ValidationError):
        research.ConsentRecord(**consent_data(activity_scope_start_at=earlier))
    approved = research.ConsentRecord(**consent_data(
        activity_scope_start_at=earlier, historical_coverage_confirmed=True))
    assert approved.activity_scope_start_at == earlier


def test_csv_dangerous_prefix_and_pseudonym(monkeypatch):
    assert research._csv_cell("=HYPERLINK(1)") == "'=HYPERLINK(1)"
    assert research._csv_cell("+123") == "'+123"
    assert research._csv_cell("ABC") == "ABC"
    monkeypatch.setattr(research, "get_settings", lambda: settings())
    uid = uuid4()
    assert research._participant_id(uid) == research._participant_id(uid)
    assert str(uid) not in research._participant_id(uid)


@pytest.mark.parametrize("source", ["settings", "environment"])
def test_admin_rejects_authentication_emulator_before_token_check(monkeypatch, source):
    config = settings()
    monkeypatch.delenv("FIREBASE_AUTH_EMULATOR_HOST", raising=False)
    if source == "settings":
        config.firebase_auth_emulator_host = "127.0.0.1:9099"
    else:
        monkeypatch.setenv("FIREBASE_AUTH_EMULATOR_HOST", "127.0.0.1:9099")
    monkeypatch.setattr(research, "get_settings", lambda: config)

    def should_not_verify(*args, **kwargs):
        pytest.fail("Research must reject emulator mode before trusting its claims")

    monkeypatch.setattr(research, "_claims_from_bearer", should_not_verify)
    with pytest.raises(HTTPException) as denied:
        research.require_research_admin(actor(), "Bearer emulator-token")
    assert denied.value.status_code == 403


def test_research_admin_checks_token_revocation(monkeypatch):
    monkeypatch.setattr(research, "get_settings", lambda: settings())
    monkeypatch.delenv("FIREBASE_AUTH_EMULATOR_HOST", raising=False)
    monkeypatch.setattr(auth, "_init_firebase", lambda: None)
    checks = []

    def verify(token, *, check_revoked):
        assert token == "revoked-token"
        checks.append(check_revoked)
        raise auth.firebase_auth.RevokedIdTokenError("test-only revoked token")

    monkeypatch.setattr(auth.firebase_auth, "verify_id_token", verify)
    with pytest.raises(HTTPException) as denied:
        research.require_research_admin(actor(), "Bearer revoked-token")
    assert denied.value.status_code == 401
    assert denied.value.detail == "Invalid Firebase token"
    assert checks == [True]


def test_auth_default_keeps_existing_student_verification(monkeypatch):
    monkeypatch.setattr(auth, "_init_firebase", lambda: None)
    calls = []

    def verify(token, *, check_revoked):
        calls.append(check_revoked)
        return {"uid": "student-test"}

    monkeypatch.setattr(auth.firebase_auth, "verify_id_token", verify)
    assert auth._claims_from_bearer("Bearer example")["uid"] == "student-test"
    assert calls == [False]
