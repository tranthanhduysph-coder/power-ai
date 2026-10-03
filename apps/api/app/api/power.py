from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, get_current_user
from app.db.session import get_db

router = APIRouter(tags=["power"])
PHASES = ["PREPARE", "ORGANIZE", "WORK", "EVALUATE", "RETHINK"]


class StartPowerSession(BaseModel):
    unit_code: str = "B10_DNA_REPLICATION"
    language: Literal["vi", "en"] = "vi"


class PhaseUpdate(BaseModel):
    phase: Literal["PREPARE", "ORGANIZE", "WORK", "EVALUATE", "RETHINK"]
    state: dict[str, Any] = Field(default_factory=dict)
    completed: bool = False


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
    db.commit()
    return {"id": str(power_session_id), "current_phase": "PREPARE"}


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
                completed_at = CASE WHEN :completed THEN now() ELSE power_phase_state.completed_at END,
                updated_at = now()
        """),
        {
            "session_id": session_id,
            "phase": payload.phase,
            "state": __import__("json").dumps(payload.state, ensure_ascii=False),
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
    db.execute(
        text("""
            INSERT INTO learning_events(user_id, learning_session_id, event_type, payload)
            VALUES (:user_id, :learning_session_id, 'power_phase_updated', CAST(:payload AS jsonb))
        """),
        {
            "user_id": user.id,
            "learning_session_id": owned,
            "payload": __import__("json").dumps({"phase": payload.phase, "completed": payload.completed}),
        },
    )
    db.commit()
    return {"current_phase": next_phase}
