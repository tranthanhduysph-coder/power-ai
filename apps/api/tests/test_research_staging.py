"""Startup guards must reject production before opening a connection."""
import pytest
from sqlalchemy.engine import make_url

from app.db.research_staging import staging_database_url, create_staging_app


@pytest.mark.parametrize("dsn,enabled", [
    ("postgresql://test:test@localhost/power_ai", "true"),
    ("postgresql://test:test@localhost/power_research_staging", "false"),
    ("postgresql://test:test@localhost/power_research_staging", ""),
    ("sqlite:///power_research_staging", "true"),
    ("postgresql://test:test@localhost/power_research_staging?hostaddr=192.0.2.1", "true"),
    ("postgresql://test:test@localhost/power_research_staging?service=production", "true"),
])
def test_staging_rejects_wrong_database_or_missing_opt_in(dsn, enabled):
    with pytest.raises(ValueError):
        staging_database_url(dsn, enabled)


def test_staging_uses_psycopg_and_preserves_encoded_credentials():
    result = make_url(staging_database_url(
        "postgresql://test:synthetic%40password@localhost/power_research_staging", "true"))
    assert result.drivername == "postgresql+psycopg"
    assert result.password == "synthetic@password"
    assert result.database == "power_research_staging"


def test_staging_denies_real_student_before_any_profile_write(monkeypatch):
    from fastapi import HTTPException
    from app.core import auth
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/power_research_staging")
    monkeypatch.setenv("RESEARCH_STAGING_ENABLED", "true")
    monkeypatch.setenv("RESEARCH_ADMIN_FIREBASE_UID", "test-admin")
    monkeypatch.setenv("RESEARCH_ADMIN_EMAIL", "admin@example.invalid")
    monkeypatch.delenv("FIREBASE_AUTH_EMULATOR_HOST", raising=False)
    checked = []

    def verify(*args, **kwargs):
        checked.append(kwargs["check_revoked"])
        return {"uid": "test-student", "email": "student@example.invalid", "email_verified": True}

    def forbidden_write(*args, **kwargs):
        pytest.fail("A real student must never be persisted in research staging")

    monkeypatch.setattr(auth, "_claims_from_bearer", verify)
    monkeypatch.setattr(auth, "_upsert_power_user", forbidden_write)
    app = create_staging_app()
    try:
        dependency = app.dependency_overrides[auth.get_current_user]
        with pytest.raises(HTTPException) as denied:
            dependency(authorization="Bearer test", db=object())
        assert denied.value.status_code == 403
        assert checked == [True]
    finally:
        app.dependency_overrides.pop(auth.get_current_user, None)
