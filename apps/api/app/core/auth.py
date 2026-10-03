import os
from dataclasses import dataclass
from uuid import UUID

import firebase_admin
from fastapi import Depends, Header, HTTPException, status
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db

settings = get_settings()


@dataclass
class CurrentUser:
    id: UUID
    firebase_uid: str
    email: str | None
    display_name: str | None
    role: str


def _init_firebase() -> None:
    if firebase_admin._apps:
        return

    if settings.firebase_auth_emulator_host:
        os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = settings.firebase_auth_emulator_host

    # Application default is enough for Auth Emulator. In production,
    # configure GOOGLE_APPLICATION_CREDENTIALS or workload identity.
    try:
        firebase_admin.initialize_app(options={"projectId": settings.firebase_project_id})
    except ValueError:
        firebase_admin.initialize_app(credentials.ApplicationDefault(), {"projectId": settings.firebase_project_id})


def _claims_from_bearer(authorization: str | None) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Firebase bearer token")
    token = authorization.split(" ", 1)[1].strip()
    _init_firebase()
    try:
        return firebase_auth.verify_id_token(token, check_revoked=False)
    except Exception as exc:  # Firebase exceptions vary by credential/emulator mode.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Firebase token") from exc


def _upsert_power_user(db: Session, claims: dict) -> CurrentUser:
    uid = str(claims.get("uid") or claims.get("sub") or "")
    if not uid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has no uid")

    email = claims.get("email")
    name = claims.get("name") or claims.get("display_name")
    picture = claims.get("picture")

    row = db.execute(
        text("""
            INSERT INTO users(firebase_uid, email, display_name, photo_url, last_login_at)
            VALUES (:uid, :email, :name, :picture, now())
            ON CONFLICT (firebase_uid) DO UPDATE
            SET email = COALESCE(EXCLUDED.email, users.email),
                display_name = COALESCE(EXCLUDED.display_name, users.display_name),
                photo_url = COALESCE(EXCLUDED.photo_url, users.photo_url),
                last_login_at = now(),
                updated_at = now()
            RETURNING id, firebase_uid, email, display_name, role
        """),
        {"uid": uid, "email": email, "name": name, "picture": picture},
    ).mappings().one()

    db.execute(
        text("""
            INSERT INTO learning_profiles(user_id, preferred_language)
            VALUES (:user_id, 'vi')
            ON CONFLICT (user_id) DO NOTHING
        """),
        {"user_id": row["id"]},
    )
    db.commit()

    return CurrentUser(**row)


def get_current_user(
    authorization: str | None = Header(default=None),
    x_dev_user: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> CurrentUser:
    if settings.auth_mode.lower() == "dev":
        dev_uid = x_dev_user or "local-demo-student"
        claims = {
            "uid": dev_uid,
            "email": settings.dev_user_email,
            "name": settings.dev_user_name,
        }
        return _upsert_power_user(db, claims)

    claims = _claims_from_bearer(authorization)
    return _upsert_power_user(db, claims)
