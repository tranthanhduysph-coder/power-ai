"""Consent-gated, audited research exports. No unrestricted learner-data endpoint."""
from __future__ import annotations

import csv
import hashlib
import hmac
import io
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, _claims_from_bearer, get_current_user
from app.core.config import get_settings
from app.db.session import get_db

router = APIRouter(prefix="/research", tags=["research"])
DATASETS = ("events", "cycles", "assessments", "mastery", "linkage")
FORMULA_PREFIXES = ("=", "+", "-", "@")
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
NUMERIC_PATTERN = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?")
JSON_METRIC_FIELDS = frozenset({
    "smart_score", "readiness", "organization_coverage", "work_completion_ratio",
    "completed_tasks_count", "evidence_length", "evaluate_accuracy",
    "evaluate_correct", "evaluate_total",
})


def require_research_admin(
    user: CurrentUser = Depends(get_current_user),
    authorization: str | None = Header(default=None),
) -> CurrentUser:
    """Require verified Firebase token AND a pinned UID and verified email."""
    settings = get_settings()
    if settings.auth_mode.lower() != "firebase" or not settings.research_admin_firebase_uid:
        raise HTTPException(403, "Research administration is disabled")
    claims = _claims_from_bearer(authorization)
    claimed_uid = str(claims.get("uid") or claims.get("sub") or "")
    claimed_email = str(claims.get("email") or "").strip().casefold()
    if (
        claimed_uid != settings.research_admin_firebase_uid
        or claimed_uid != user.firebase_uid
        or claimed_email != settings.research_admin_email.strip().casefold()
        or claims.get("email_verified") is not True
    ):
        raise HTTPException(403, "Research administrator permission required")
    return user


class ConsentRecord(BaseModel):
    email: str = Field(min_length=5, max_length=320)
    survey_response_ref: str = Field(min_length=1, max_length=300)
    survey_version: str = Field(min_length=1, max_length=100)
    consented_at: datetime
    research_allowed: bool
    improvement_allowed: bool = False
    required_authorizations_verified: bool = False
    activity_scope_start_at: datetime | None = None
    historical_coverage_confirmed: bool = False

    @model_validator(mode="after")
    def validate_consent(self):
        self.email = self.email.strip().casefold()
        self.survey_response_ref = self.survey_response_ref.strip()
        self.survey_version = self.survey_version.strip()
        if not EMAIL_PATTERN.fullmatch(self.email):
            raise ValueError("Enter the exact valid POWER login email")
        if not self.survey_response_ref or not self.survey_version:
            raise ValueError("Source reference and survey version cannot be blank")
        if self.consented_at.tzinfo is None:
            raise ValueError("consented_at must include a timezone offset")
        if self.consented_at > datetime.now(timezone.utc) + timedelta(minutes=5):
            raise ValueError("Consent date cannot be in the future")
        if self.research_allowed and not self.required_authorizations_verified:
            raise ValueError("Required participant/guardian approvals have not been verified")
        if self.activity_scope_start_at:
            if self.activity_scope_start_at.tzinfo is None:
                raise ValueError("activity_scope_start_at must include a timezone offset")
            if self.activity_scope_start_at > self.consented_at:
                raise ValueError("Activity window cannot start after the consent")
            if (self.activity_scope_start_at < self.consented_at
                    and not self.historical_coverage_confirmed):
                raise ValueError("Explicit historical activity consent evidence required")
        return self


def _participant_id(user_id: object) -> str:
    key = get_settings().research_pseudonym_key
    if not key or len(key) < 32:
        raise HTTPException(503, "Research pseudonym key is not configured")
    digest = hmac.new(key.encode(), str(user_id).encode(), hashlib.sha256).hexdigest()
    return "P" + digest[:24]


def _csv_cell(value: object) -> str:
    if value is None:
        return ""
    value = str(value)
    # Avoid CSV formula injection when data are opened in spreadsheet tools.
    if value.lstrip().startswith(FORMULA_PREFIXES):
        return "'" + value
    return value


def _export_cell(field: str, value: object) -> str:
    # JSON keys are not a type boundary: legacy/malformed payloads can contain
    # learner text even under a metric name. Export numeric metric values only.
    if field in JSON_METRIC_FIELDS and value is not None:
        metric = str(value)
        if len(metric) > 64 or not NUMERIC_PATTERN.fullmatch(metric):
            return ""
    return _csv_cell(value)


@router.get("/status")
def research_status(
    admin: CurrentUser = Depends(require_research_admin),
    db: Session = Depends(get_db),
):
    counts = db.execute(text("""
        SELECT
          (SELECT count(*) FROM users) AS users_total,
          (SELECT count(*) FROM learning_events) AS event_count,
          (SELECT count(*) FROM power_sessions) AS cycle_count,
          (SELECT count(*) FROM mastery_snapshots) AS mastery_snapshot_count,
          (SELECT count(*) FROM research_consent WHERE research_allowed) AS consented_students
    """)).mappings().one()
    return {"access": "research_admin", "datasets": list(DATASETS), "counts": dict(counts)}


@router.post("/consents")
def record_verified_form_consent(
    payload: ConsentRecord,
    admin: CurrentUser = Depends(require_research_admin),
    db: Session = Depends(get_db),
):
    """Manual import from a verified Google Form response; never infer consent from login."""
    matching_users = db.execute(text("""
        SELECT id FROM users WHERE lower(btrim(email)) = :email LIMIT 2
    """), {"email": payload.email}).scalars().all()
    if not matching_users:
        raise HTTPException(404, "POWER user email not found; do not match by name")
    if len(matching_users) != 1:
        raise HTTPException(409, "Ambiguous POWER email; resolve before linking")
    user_id = matching_users[0]
    # Validate configuration before any consent/audit write can be committed.
    participant_id = _participant_id(user_id)
    # Serialize imports of the same source and the same learner. Otherwise a
    # stale concurrent request could re-enable consent after a withdrawal.
    db.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:ref, 0))"),
               {"ref": "research-consent:" + payload.survey_response_ref})
    db.execute(text("SELECT id FROM users WHERE id = :uid FOR UPDATE"), {"uid": user_id})
    reused = db.execute(text("""
        SELECT 1 FROM research_consent
        WHERE survey_response_ref = :ref AND user_id <> :uid
        UNION ALL
        SELECT 1 FROM research_consent_audit
        WHERE survey_response_ref = :ref AND user_id <> :uid
        LIMIT 1
    """), {"ref": payload.survey_response_ref, "uid": user_id}).scalar_one_or_none()
    if reused:
        raise HTTPException(409, "Survey response reference is already linked to another learner")
    previous = db.execute(text("""
        SELECT consented_at FROM research_consent WHERE user_id = :uid
    """), {"uid": user_id}).scalar_one_or_none()
    if previous and payload.consented_at <= previous:
        raise HTTPException(409, "Consent must be newer than the recorded decision")

    scope_start = payload.activity_scope_start_at or payload.consented_at
    params = {
        "uid": user_id, "ref": payload.survey_response_ref, "version": payload.survey_version,
        "consented_at": payload.consented_at, "scope": scope_start,
        "research": payload.research_allowed, "improvement": payload.improvement_allowed,
        "approvals": payload.required_authorizations_verified,
        "actor": admin.id,
    }
    db.execute(text("""
        INSERT INTO research_consent (
            user_id, survey_response_ref, survey_version, consented_at,
            activity_scope_start_at, research_allowed, improvement_allowed,
            required_authorizations_verified, recorded_by
        ) VALUES (:uid, :ref, :version, :consented_at, :scope, :research, :improvement, :approvals, :actor)
        ON CONFLICT (user_id) DO UPDATE SET
            survey_response_ref = EXCLUDED.survey_response_ref,
            survey_version = EXCLUDED.survey_version,
            consented_at = EXCLUDED.consented_at,
            activity_scope_start_at = EXCLUDED.activity_scope_start_at,
            research_allowed = EXCLUDED.research_allowed,
            improvement_allowed = EXCLUDED.improvement_allowed,
            required_authorizations_verified = EXCLUDED.required_authorizations_verified,
            recorded_by = EXCLUDED.recorded_by,
            updated_at = now()
    """), params)
    db.execute(text("""
        INSERT INTO research_consent_audit (
            user_id, survey_response_ref, survey_version, consented_at,
            activity_scope_start_at, research_allowed, improvement_allowed,
            required_authorizations_verified, recorded_by
        ) VALUES (:uid, :ref, :version, :consented_at, :scope, :research, :improvement, :approvals, :actor)
    """), params)
    db.commit()
    return {"participant_id": participant_id,
            "research_allowed": payload.research_allowed,
            "activity_scope_start_at": scope_start.isoformat()}


DATASET_QUERIES = {
    "events": """
        SELECT le.user_id, le.id AS event_id, le.learning_session_id,
               ps.id AS power_session_id, cu.code AS unit_code,
               le.event_type, le.concept_id, le.created_at AS recorded_at,
               le.payload ->> 'smart_score' AS smart_score,
               le.payload ->> 'readiness' AS readiness,
               le.payload ->> 'coverage' AS organization_coverage,
               le.payload ->> 'completion_ratio' AS work_completion_ratio,
               le.payload ->> 'completed_tasks' AS completed_tasks_count,
               le.payload ->> 'evidence_chars' AS evidence_length,
               le.payload ->> 'accuracy' AS evaluate_accuracy,
               le.payload ->> 'correct' AS evaluate_correct,
               le.payload ->> 'total' AS evaluate_total
        FROM learning_events le
        JOIN research_consent rc ON rc.user_id = le.user_id AND rc.research_allowed
             AND le.created_at >= rc.activity_scope_start_at
        LEFT JOIN learning_sessions ls ON ls.id = le.learning_session_id
        LEFT JOIN power_sessions ps ON ps.learning_session_id = ls.id
        LEFT JOIN curriculum_units cu ON cu.id = ls.curriculum_unit_id
        WHERE le.created_at >= :start_at AND le.created_at < :end_at
        ORDER BY le.created_at, le.id
        LIMIT :limit OFFSET :offset
    """,
    "cycles": """
        SELECT ps.user_id, ps.id AS power_session_id, ls.id AS learning_session_id,
               cu.code AS unit_code, ls.status AS session_status,
               ps.current_phase, ls.started_at, ls.ended_at,
               prep.completed_at AS prepare_completed_at,
               org.completed_at AS organize_completed_at,
               work.completed_at AS work_completed_at,
               eval.completed_at AS evaluate_completed_at,
               rethink.completed_at AS rethink_completed_at,
               eval.state_json ->> 'accuracy' AS evaluate_accuracy
        FROM power_sessions ps
        JOIN learning_sessions ls ON ls.id = ps.learning_session_id
        JOIN research_consent rc ON rc.user_id = ps.user_id AND rc.research_allowed
             AND ls.started_at >= rc.activity_scope_start_at
        LEFT JOIN curriculum_units cu ON cu.id = ls.curriculum_unit_id
        LEFT JOIN power_phase_state prep ON prep.power_session_id = ps.id AND prep.phase = 'PREPARE'
        LEFT JOIN power_phase_state org ON org.power_session_id = ps.id AND org.phase = 'ORGANIZE'
        LEFT JOIN power_phase_state work ON work.power_session_id = ps.id AND work.phase = 'WORK'
        LEFT JOIN power_phase_state eval ON eval.power_session_id = ps.id AND eval.phase = 'EVALUATE'
        LEFT JOIN power_phase_state rethink ON rethink.power_session_id = ps.id AND rethink.phase = 'RETHINK'
        WHERE ls.started_at >= :start_at AND ls.started_at < :end_at
        ORDER BY ls.started_at, ps.id
        LIMIT :limit OFFSET :offset
    """,
    "assessments": """
        SELECT pa.user_id, pa.id AS practice_attempt_id, ps.power_session_id,
               cu.code AS unit_code, ps.mode, ps.purpose,
               pa.started_at, pa.completed_at, pa.accuracy, pa.duration_seconds
        FROM practice_attempts pa
        JOIN practice_sets ps ON ps.id = pa.practice_set_id
        JOIN research_consent rc ON rc.user_id = pa.user_id AND rc.research_allowed
             AND pa.started_at >= rc.activity_scope_start_at
        LEFT JOIN curriculum_units cu ON cu.id = ps.curriculum_unit_id
        WHERE pa.started_at >= :start_at AND pa.started_at < :end_at
        ORDER BY pa.started_at, pa.id
        LIMIT :limit OFFSET :offset
    """,
    "mastery": """
        SELECT ms.user_id, ms.id AS snapshot_id, c.code AS concept_code,
               ms.mastery_score, ms.captured_at
        FROM mastery_snapshots ms
        JOIN research_consent rc ON rc.user_id = ms.user_id AND rc.research_allowed
             AND ms.captured_at >= rc.activity_scope_start_at
        JOIN concepts c ON c.id = ms.concept_id
        WHERE ms.captured_at >= :start_at AND ms.captured_at < :end_at
        ORDER BY ms.captured_at, ms.id
        LIMIT :limit OFFSET :offset
    """,
    "linkage": """
        SELECT rc.user_id, u.email, rc.survey_response_ref, rc.survey_version,
               rc.consented_at, rc.activity_scope_start_at
        FROM research_consent rc
        JOIN users u ON u.id = rc.user_id
        WHERE rc.research_allowed AND rc.consented_at >= :start_at
              AND rc.consented_at < :end_at
        ORDER BY rc.consented_at, rc.user_id
        LIMIT :limit OFFSET :offset
    """,
}


@router.get("/exports/{dataset}")
def export_research_csv(
    dataset: Literal["events", "cycles", "assessments", "mastery", "linkage"],
    start_at: datetime = Query(..., description="Inclusive start, ISO timestamp with timezone"),
    end_at: datetime = Query(..., description="Exclusive end, ISO timestamp with timezone"),
    limit: int = Query(10000, ge=1, le=20000),
    offset: int = Query(0, ge=0),
    admin: CurrentUser = Depends(require_research_admin),
    db: Session = Depends(get_db),
):
    # Refuse any export, even an empty one, until stable pseudonymization is configured.
    if len(get_settings().research_pseudonym_key) < 32:
        raise HTTPException(503, "Research pseudonym key is not configured")
    if start_at.tzinfo is None or end_at.tzinfo is None:
        raise HTTPException(422, "Export timestamps must include timezone offsets")
    if start_at >= end_at or end_at - start_at > timedelta(days=366):
        raise HTTPException(422, "Select a valid time range no longer than 366 days")
    # Never expose raw event payloads, student answers, prompt text or names.
    rows = db.execute(text(DATASET_QUERIES[dataset]), {
        "start_at": start_at, "end_at": end_at, "limit": limit, "offset": offset,
    }).mappings().all()
    fieldnames = [k for k in db.execute(text(DATASET_QUERIES[dataset]), {
        "start_at": start_at, "end_at": end_at, "limit": 0, "offset": 0,
    }).keys() if k != "user_id"]
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["participant_id", *fieldnames])
    for row in rows:
        writer.writerow([_participant_id(row["user_id"]), *[_export_cell(k, row[k]) for k in fieldnames]])
    db.execute(text("""
        INSERT INTO research_export_audit(actor_user_id, dataset, rows_exported, filters)
        VALUES (:actor, :dataset, :rows, CAST(:filters AS jsonb))
    """), {
        "actor": admin.id, "dataset": dataset, "rows": len(rows),
        "filters": json.dumps({
            "start_at": start_at.isoformat(), "end_at": end_at.isoformat(),
            "limit": limit, "offset": offset,
        }),
    })
    db.commit()
    return Response(
        content="\ufeff" + out.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="power_research_{dataset}.csv"',
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )
