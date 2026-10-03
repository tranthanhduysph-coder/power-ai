import json
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, get_current_user
from app.db.session import get_db
from app.services.prepare import analyze_goal, get_prepare_blueprint, score_diagnostic

router = APIRouter(tags=["power"])
PHASES = ["PREPARE", "ORGANIZE", "WORK", "EVALUATE", "RETHINK"]


class StartPowerSession(BaseModel):
    unit_code: str = "B12_DNA_REPLICATION"
    language: Literal["vi", "en"] = "vi"


class PhaseUpdate(BaseModel):
    phase: Literal["PREPARE", "ORGANIZE", "WORK", "EVALUATE", "RETHINK"]
    state: dict[str, Any] = Field(default_factory=dict)
    completed: bool = False


class GoalFeedbackRequest(BaseModel):
    unit_code: str = "B12_DNA_REPLICATION"
    language: Literal["vi", "en"] = "vi"
    goal: str = Field(min_length=1, max_length=1000)
    target_minutes: int = Field(default=30, ge=5, le=180)


class PrepareUpdate(BaseModel):
    goal: str = Field(min_length=1, max_length=1000)
    target_minutes: int = Field(default=30, ge=5, le=180)
    confidence: int = Field(default=3, ge=1, le=5)
    prior_knowledge: str = Field(default="", max_length=3000)
    diagnostic_answers: dict[str, Any] = Field(default_factory=dict)
    completed: bool = False


def _phase_rows(db: Session, power_session_id: UUID) -> dict[str, dict[str, Any]]:
    rows = db.execute(
        text("""
            SELECT phase, state_json, started_at, completed_at, updated_at
            FROM power_phase_state
            WHERE power_session_id = :id
            ORDER BY started_at
        """),
        {"id": power_session_id},
    ).mappings().all()
    return {
        row["phase"]: {
            "state": row["state_json"] or {},
            "started_at": row["started_at"],
            "completed_at": row["completed_at"],
            "updated_at": row["updated_at"],
        }
        for row in rows
    }


def _session_payload(db: Session, power_session_id: UUID, user_id: UUID) -> dict[str, Any]:
    row = db.execute(
        text("""
            SELECT ps.id, ps.current_phase, ps.created_at, ps.updated_at,
                   ls.id AS learning_session_id, ls.language, ls.status,
                   cu.code AS unit_code, cu.name_vi, cu.name_en
            FROM power_sessions ps
            JOIN learning_sessions ls ON ls.id = ps.learning_session_id
            JOIN curriculum_units cu ON cu.id = ls.curriculum_unit_id
            WHERE ps.id = :id AND ps.user_id = :user_id
        """),
        {"id": power_session_id, "user_id": user_id},
    ).mappings().one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="POWER session not found")
    return {
        "id": str(row["id"]),
        "learning_session_id": str(row["learning_session_id"]),
        "current_phase": row["current_phase"],
        "language": row["language"],
        "status": row["status"],
        "unit": {
            "code": row["unit_code"],
            "name_vi": row["name_vi"],
            "name_en": row["name_en"],
        },
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "phases": _phase_rows(db, row["id"]),
    }


@router.get("/power/prepare/blueprint")
def prepare_blueprint(
    unit_code: str = Query(default="B12_DNA_REPLICATION"),
    language: Literal["vi", "en"] = Query(default="vi"),
    user: CurrentUser = Depends(get_current_user),
):
    _ = user
    try:
        return get_prepare_blueprint(unit_code, language)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Prepare blueprint not found for this unit") from exc


@router.post("/power/prepare/goal-feedback")
def prepare_goal_feedback(
    payload: GoalFeedbackRequest,
    user: CurrentUser = Depends(get_current_user),
):
    _ = user
    try:
        return analyze_goal(payload.goal, payload.target_minutes, payload.unit_code, payload.language)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Prepare blueprint not found for this unit") from exc


@router.get("/power/sessions/active")
def active_power_session(
    unit_code: str = Query(default="B12_DNA_REPLICATION"),
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session_id = db.execute(
        text("""
            SELECT ps.id
            FROM power_sessions ps
            JOIN learning_sessions ls ON ls.id = ps.learning_session_id
            JOIN curriculum_units cu ON cu.id = ls.curriculum_unit_id
            WHERE ps.user_id = :user_id
              AND cu.code = :unit_code
              AND ls.status = 'active'
            ORDER BY ps.updated_at DESC
            LIMIT 1
        """),
        {"user_id": user.id, "unit_code": unit_code},
    ).scalar_one_or_none()
    if not session_id:
        return {"session": None}
    return {"session": _session_payload(db, session_id, user.id)}


@router.get("/power/sessions/{session_id}")
def get_power_session(
    session_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _session_payload(db, session_id, user.id)


@router.post("/power/sessions")
def start_power_session(
    payload: StartPowerSession,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    unit_id = db.execute(
        text("SELECT id FROM curriculum_units WHERE code = :code"), {"code": payload.unit_code}
    ).scalar_one_or_none()
    if not unit_id:
        raise HTTPException(status_code=404, detail="Curriculum unit not found")

    existing_id = db.execute(
        text("""
            SELECT ps.id
            FROM power_sessions ps
            JOIN learning_sessions ls ON ls.id = ps.learning_session_id
            WHERE ps.user_id = :user_id
              AND ls.curriculum_unit_id = :unit_id
              AND ls.status = 'active'
            ORDER BY ps.updated_at DESC
            LIMIT 1
        """),
        {"user_id": user.id, "unit_id": unit_id},
    ).scalar_one_or_none()
    if existing_id:
        return {**_session_payload(db, existing_id, user.id), "resumed": True}

    learning_session_id = db.execute(
        text("""
            INSERT INTO learning_sessions(user_id, curriculum_unit_id, current_power_phase, language, status)
            VALUES (:user_id, :unit_id, 'PREPARE', :language, 'active')
            RETURNING id
        """),
        {"user_id": user.id, "unit_id": unit_id, "language": payload.language},
    ).scalar_one()

    power_session_id = db.execute(
        text("""
            INSERT INTO power_sessions(user_id, learning_session_id, current_phase)
            VALUES (:user_id, :learning_session_id, 'PREPARE')
            RETURNING id
        """),
        {"user_id": user.id, "learning_session_id": learning_session_id},
    ).scalar_one()

    db.execute(
        text("""
            INSERT INTO power_phase_state(power_session_id, phase, state_json)
            VALUES (:id, 'PREPARE', '{}'::jsonb)
        """),
        {"id": power_session_id},
    )
    db.execute(
        text("""
            INSERT INTO learning_events(user_id, learning_session_id, event_type, payload)
            VALUES (:user_id, :learning_session_id, 'power_cycle_started', CAST(:payload AS jsonb))
        """),
        {
            "user_id": user.id,
            "learning_session_id": learning_session_id,
            "payload": json.dumps({"unit_code": payload.unit_code, "phase": "PREPARE"}),
        },
    )
    db.commit()
    return {**_session_payload(db, power_session_id, user.id), "resumed": False}


@router.put("/power/sessions/{session_id}/prepare")
def update_prepare(
    session_id: UUID,
    payload: PrepareUpdate,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    owned = db.execute(
        text("""
            SELECT ps.learning_session_id, cu.code AS unit_code, ls.language
            FROM power_sessions ps
            JOIN learning_sessions ls ON ls.id = ps.learning_session_id
            JOIN curriculum_units cu ON cu.id = ls.curriculum_unit_id
            WHERE ps.id = :id AND ps.user_id = :user_id
        """),
        {"id": session_id, "user_id": user.id},
    ).mappings().one_or_none()
    if not owned:
        raise HTTPException(status_code=404, detail="POWER session not found")

    try:
        goal_feedback = analyze_goal(
            payload.goal,
            payload.target_minutes,
            owned["unit_code"],
            owned["language"],
        )
        diagnostic = score_diagnostic(owned["unit_code"], payload.diagnostic_answers)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Prepare blueprint not found for this unit") from exc

    if payload.completed and diagnostic["missing"]:
        raise HTTPException(status_code=422, detail="Complete all prerequisite diagnostic items before finishing Prepare")

    state = {
        "goal": payload.goal.strip(),
        "target_minutes": payload.target_minutes,
        "confidence": payload.confidence,
        "prior_knowledge": payload.prior_knowledge.strip(),
        "goal_feedback": goal_feedback,
        "diagnostic_answers": payload.diagnostic_answers,
        "diagnostic": diagnostic,
    }

    db.execute(
        text("""
            INSERT INTO power_phase_state(power_session_id, phase, state_json, completed_at)
            VALUES (:session_id, 'PREPARE', CAST(:state AS jsonb), CASE WHEN :completed THEN now() ELSE NULL END)
            ON CONFLICT (power_session_id, phase) DO UPDATE
            SET state_json = EXCLUDED.state_json,
                completed_at = CASE WHEN :completed THEN COALESCE(power_phase_state.completed_at, now()) ELSE power_phase_state.completed_at END,
                updated_at = now()
        """),
        {
            "session_id": session_id,
            "state": json.dumps(state, ensure_ascii=False),
            "completed": payload.completed,
        },
    )

    if payload.completed:
        db.execute(
            text("UPDATE power_sessions SET current_phase = 'ORGANIZE', updated_at = now() WHERE id = :id"),
            {"id": session_id},
        )
        db.execute(
            text("UPDATE learning_sessions SET current_power_phase = 'ORGANIZE' WHERE id = :id"),
            {"id": owned["learning_session_id"]},
        )
        db.execute(
            text("""
                INSERT INTO power_phase_state(power_session_id, phase, state_json)
                VALUES (:id, 'ORGANIZE', '{}'::jsonb)
                ON CONFLICT (power_session_id, phase) DO NOTHING
            """),
            {"id": session_id},
        )

    db.execute(
        text("""
            INSERT INTO learning_events(user_id, learning_session_id, event_type, payload)
            VALUES (:user_id, :learning_session_id, :event_type, CAST(:payload AS jsonb))
        """),
        {
            "user_id": user.id,
            "learning_session_id": owned["learning_session_id"],
            "event_type": "prepare_completed" if payload.completed else "prepare_saved",
            "payload": json.dumps(
                {
                    "smart_score": goal_feedback["score"],
                    "readiness": diagnostic["readiness"],
                    "confidence": payload.confidence,
                    "completed": payload.completed,
                }
            ),
        },
    )
    db.commit()
    return {
        "current_phase": "ORGANIZE" if payload.completed else "PREPARE",
        "prepare": state,
        "session": _session_payload(db, session_id, user.id),
    }


@router.put("/power/sessions/{session_id}/phase")
def update_phase(
    session_id: UUID,
    payload: PhaseUpdate,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    owned = db.execute(
        text("SELECT learning_session_id FROM power_sessions WHERE id = :id AND user_id = :user_id"),
        {"id": session_id, "user_id": user.id},
    ).scalar_one_or_none()
    if not owned:
        raise HTTPException(status_code=404, detail="POWER session not found")

    db.execute(
        text("""
            INSERT INTO power_phase_state(power_session_id, phase, state_json, completed_at)
            VALUES (:session_id, :phase, CAST(:state AS jsonb), CASE WHEN :completed THEN now() ELSE NULL END)
            ON CONFLICT (power_session_id, phase) DO UPDATE
            SET state_json = EXCLUDED.state_json,
                completed_at = CASE WHEN :completed THEN COALESCE(power_phase_state.completed_at, now()) ELSE power_phase_state.completed_at END,
                updated_at = now()
        """),
        {
            "session_id": session_id,
            "phase": payload.phase,
            "state": json.dumps(payload.state, ensure_ascii=False),
            "completed": payload.completed,
        },
    )

    idx = PHASES.index(payload.phase)
    next_phase = PHASES[min(idx + 1, len(PHASES) - 1)] if payload.completed else payload.phase
    db.execute(
        text("UPDATE power_sessions SET current_phase = :phase, updated_at = now() WHERE id = :id"),
        {"phase": next_phase, "id": session_id},
    )
    db.execute(
        text("UPDATE learning_sessions SET current_power_phase = :phase WHERE id = :id"),
        {"phase": next_phase, "id": owned},
    )
    if payload.completed and payload.phase != "RETHINK":
        db.execute(
            text("""
                INSERT INTO power_phase_state(power_session_id, phase, state_json)
                VALUES (:id, :phase, '{}'::jsonb)
                ON CONFLICT (power_session_id, phase) DO NOTHING
            """),
            {"id": session_id, "phase": next_phase},
        )
    elif payload.completed and payload.phase == "RETHINK":
        db.execute(
            text("UPDATE learning_sessions SET status = 'completed', ended_at = now() WHERE id = :id"),
            {"id": owned},
        )

    db.execute(
        text("""
            INSERT INTO learning_events(user_id, learning_session_id, event_type, payload)
            VALUES (:user_id, :learning_session_id, 'power_phase_updated', CAST(:payload AS jsonb))
        """),
        {
            "user_id": user.id,
            "learning_session_id": owned,
            "payload": json.dumps({"phase": payload.phase, "completed": payload.completed}),
        },
    )
    db.commit()
    return {
        "current_phase": next_phase,
        "cycle_completed": bool(payload.completed and payload.phase == "RETHINK"),
        "session": _session_payload(db, session_id, user.id),
    }
