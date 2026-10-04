import json
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, get_current_user
from app.db.session import get_db
from app.retrieval.search import search_chunks
from app.services.tutor import grounded_tutor_blocks

router = APIRouter(tags=["tutor"])


class TutorRequest(BaseModel):
    concept_code: str = "BIO.DNA.REPLICATION"
    message: str
    language: Literal["vi", "en"] = "vi"
    power_session_id: UUID | None = None
    phase: Literal["PREPARE", "ORGANIZE", "WORK", "EVALUATE", "RETHINK"] | None = None


@router.post("/tutor/respond")
def tutor_respond(
    payload: TutorRequest,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    phase = payload.phase or "WORK"
    learner_context: dict = {}
    learning_session_id = None

    if payload.power_session_id:
        row = db.execute(
            text("""
                SELECT ps.current_phase, ps.learning_session_id,
                       prepare_state.state_json AS prepare_state,
                       organize_state.state_json AS organize_state,
                       work_state.state_json AS work_state,
                       requested_state.state_json AS requested_phase_state
                FROM power_sessions ps
                LEFT JOIN power_phase_state prepare_state
                  ON prepare_state.power_session_id = ps.id AND prepare_state.phase = 'PREPARE'
                LEFT JOIN power_phase_state organize_state
                  ON organize_state.power_session_id = ps.id AND organize_state.phase = 'ORGANIZE'
                LEFT JOIN power_phase_state work_state
                  ON work_state.power_session_id = ps.id AND work_state.phase = 'WORK'
                LEFT JOIN power_phase_state requested_state
                  ON requested_state.power_session_id = ps.id AND requested_state.phase = :requested_phase
                WHERE ps.id = :id AND ps.user_id = :user_id
            """),
            {
                "id": payload.power_session_id,
                "user_id": user.id,
                "requested_phase": phase,
            },
        ).mappings().one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="POWER session not found")
        phase = payload.phase or row["current_phase"]
        learning_session_id = row["learning_session_id"]
        prepare_state = row["prepare_state"] or {}
        organize_state = row["organize_state"] or {}
        work_state = row["work_state"] or {}
        requested_phase_state = row["requested_phase_state"] or {}
        learner_context = {
            "goal": prepare_state.get("goal"),
            "confidence_before": prepare_state.get("confidence"),
            "readiness": (prepare_state.get("diagnostic") or {}).get("readiness"),
            "weak_concepts": (prepare_state.get("diagnostic") or {}).get("weak_concepts", []),
        }
        if organize_state:
            learner_context["organize_map"] = {
                "anchor_concepts": organize_state.get("anchor_concepts", []),
                "links": organize_state.get("links", []),
                "synthesis": organize_state.get("synthesis", ""),
                "coverage": organize_state.get("coverage"),
            }
        if phase == "WORK":
            learner_context["work_evidence"] = {
                "responses": work_state.get("responses", {}),
                "completed_tasks": work_state.get("completed_tasks", []),
                "confidence_after": work_state.get("confidence_after"),
                "completion_ratio": work_state.get("completion_ratio"),
            }
        elif requested_phase_state:
            learner_context["phase_state"] = requested_phase_state

    retrieved = search_chunks(
        db,
        payload.message,
        concept_code=payload.concept_code,
        language=payload.language,
        top_k=4,
    )
    provider, blocks = grounded_tutor_blocks(
        language=payload.language,
        message=payload.message,
        retrieved=retrieved,
        phase=phase,
        learner_context=learner_context,
    )
    db.execute(
        text("""
            INSERT INTO usage_ledger(user_id, feature, quantity, metadata)
            VALUES (:user_id, :feature, 1, CAST(:metadata AS jsonb))
        """),
        {
            "user_id": user.id,
            "feature": f"ai_tutor_{provider}",
            "metadata": json.dumps(
                {
                    "concept_code": payload.concept_code,
                    "retrieved_chunks": len(retrieved),
                    "power_phase": phase,
                }
            ),
        },
    )
    db.execute(
        text("""
            INSERT INTO learning_events(user_id, learning_session_id, event_type, payload)
            VALUES (:user_id, :learning_session_id, 'tutor_asked', CAST(:payload AS jsonb))
        """),
        {
            "user_id": user.id,
            "learning_session_id": learning_session_id,
            "payload": json.dumps(
                {
                    "phase": phase,
                    "concept_code": payload.concept_code,
                    "provider": provider,
                    "retrieved_chunks": len(retrieved),
                    "message": payload.message[:1000],
                },
                ensure_ascii=False,
            ),
        },
    )
    db.commit()
    return {
        "provider": provider,
        "phase": phase,
        "blocks": blocks,
        "retrieval": {
            "count": len(retrieved),
            "sources": [item.as_dict() for item in retrieved],
        },
    }
