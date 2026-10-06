import json
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, get_current_user
from app.db.session import get_db
from app.retrieval.search import search_chunks
from app.services.tutor import generate_grounded_image, grounded_tutor_blocks

router = APIRouter(tags=["tutor"])


class TutorRequest(BaseModel):
    concept_code: str | None = None
    message: str
    language: Literal["vi", "en"] = "vi"
    power_session_id: UUID | None = None
    phase: Literal["PREPARE", "ORGANIZE", "WORK", "EVALUATE", "RETHINK"] | None = None
    image_data_url: str | None = Field(default=None, max_length=7_100_000)


class TutorImageRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=1200)
    concept_code: str | None = None
    language: Literal["vi", "en"] = "vi"
    power_session_id: UUID | None = None
    phase: Literal["PREPARE", "ORGANIZE", "WORK", "EVALUATE", "RETHINK"] | None = None


def _validate_image_data_url(image_data_url: str | None) -> None:
    if not image_data_url:
        return
    allowed = (
        "data:image/png;base64,",
        "data:image/jpeg;base64,",
        "data:image/webp;base64,",
    )
    if not image_data_url.startswith(allowed):
        raise HTTPException(status_code=422, detail="Only PNG, JPEG, and WebP tutor images are supported")


@router.post("/tutor/respond")
def tutor_respond(
    payload: TutorRequest,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    phase = payload.phase or "WORK"
    _validate_image_data_url(payload.image_data_url)
    learner_context: dict = {}
    learning_session_id = None
    concept_code = payload.concept_code

    if payload.power_session_id:
        row = db.execute(
            text("""
                SELECT ps.current_phase, ps.learning_session_id,
                       ls.curriculum_unit_id, cu.metadata_json AS unit_metadata,
                       prepare_state.state_json AS prepare_state,
                       organize_state.state_json AS organize_state,
                       work_state.state_json AS work_state,
                       evaluate_state.state_json AS evaluate_state,
                       rethink_state.state_json AS rethink_state,
                       requested_state.state_json AS requested_phase_state
                FROM power_sessions ps
                JOIN learning_sessions ls ON ls.id = ps.learning_session_id
                JOIN curriculum_units cu ON cu.id = ls.curriculum_unit_id
                LEFT JOIN power_phase_state prepare_state
                  ON prepare_state.power_session_id = ps.id AND prepare_state.phase = 'PREPARE'
                LEFT JOIN power_phase_state organize_state
                  ON organize_state.power_session_id = ps.id AND organize_state.phase = 'ORGANIZE'
                LEFT JOIN power_phase_state work_state
                  ON work_state.power_session_id = ps.id AND work_state.phase = 'WORK'
                LEFT JOIN power_phase_state evaluate_state
                  ON evaluate_state.power_session_id = ps.id AND evaluate_state.phase = 'EVALUATE'
                LEFT JOIN power_phase_state rethink_state
                  ON rethink_state.power_session_id = ps.id AND rethink_state.phase = 'RETHINK'
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
        if not concept_code:
            metadata = row["unit_metadata"] or {}
            concept_code = metadata.get("primary_concept_code")
            if not concept_code:
                concept_code = db.execute(
                    text("""
                        SELECT c.code
                        FROM curriculum_concepts cc
                        JOIN concepts c ON c.id = cc.concept_id
                        WHERE cc.curriculum_unit_id = :unit_id
                        ORDER BY cc.is_core DESC, c.code
                        LIMIT 1
                    """),
                    {"unit_id": row["curriculum_unit_id"]},
                ).scalar_one_or_none()
        prepare_state = row["prepare_state"] or {}
        organize_state = row["organize_state"] or {}
        work_state = row["work_state"] or {}
        evaluate_state = row["evaluate_state"] or {}
        rethink_state = row["rethink_state"] or {}
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
        elif phase == "RETHINK":
            learner_context["evaluate_evidence"] = {
                "accuracy": evaluate_state.get("accuracy"),
                "correct": evaluate_state.get("correct"),
                "total": evaluate_state.get("total"),
                "weak_concepts": evaluate_state.get("weak_concepts", []),
                "concepts": evaluate_state.get("concepts", []),
            }
            learner_context["rethink_evidence"] = rethink_state
        elif requested_phase_state:
            learner_context["phase_state"] = requested_phase_state

    search_message = payload.message.strip() or (
        "Phân tích hình ảnh Sinh học này" if payload.language == "vi" else "Analyze this Biology image"
    )
    retrieved = search_chunks(
        db,
        search_message,
        concept_code=concept_code,
        language=payload.language,
        top_k=4,
    )
    provider, blocks = grounded_tutor_blocks(
        language=payload.language,
        message=payload.message,
        retrieved=retrieved,
        phase=phase,
        learner_context=learner_context,
        image_data_url=payload.image_data_url,
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
                    "concept_code": concept_code,
                    "retrieved_chunks": len(retrieved),
                    "power_phase": phase,
                    "has_image": bool(payload.image_data_url),
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
                    "concept_code": concept_code,
                    "provider": provider,
                    "retrieved_chunks": len(retrieved),
                    "message": payload.message[:1000],
                    "has_image": bool(payload.image_data_url),
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

@router.post("/tutor/generate-image")
def tutor_generate_image(
    payload: TutorImageRequest,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    phase = payload.phase or "WORK"
    concept_code = payload.concept_code
    learning_session_id = None

    if payload.power_session_id:
        row = db.execute(
            text(
                """
                SELECT ps.current_phase, ps.learning_session_id, ls.curriculum_unit_id,
                       cu.metadata_json AS unit_metadata
                FROM power_sessions ps
                JOIN learning_sessions ls ON ls.id = ps.learning_session_id
                JOIN curriculum_units cu ON cu.id = ls.curriculum_unit_id
                WHERE ps.id = :id AND ps.user_id = :user_id
                """
            ),
            {"id": payload.power_session_id, "user_id": user.id},
        ).mappings().one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="POWER session not found")
        phase = payload.phase or row["current_phase"]
        learning_session_id = row["learning_session_id"]
        if not concept_code:
            metadata = row["unit_metadata"] or {}
            concept_code = metadata.get("primary_concept_code")
            if not concept_code:
                concept_code = db.execute(
                    text(
                        """
                        SELECT c.code
                        FROM curriculum_concepts cc
                        JOIN concepts c ON c.id = cc.concept_id
                        WHERE cc.curriculum_unit_id = :unit_id
                        ORDER BY cc.is_core DESC, c.code
                        LIMIT 1
                        """
                    ),
                    {"unit_id": row["curriculum_unit_id"]},
                ).scalar_one_or_none()

    retrieved = search_chunks(
        db,
        payload.prompt,
        concept_code=concept_code,
        language=payload.language,
        top_k=4,
    )
    if not retrieved:
        raise HTTPException(status_code=422, detail="No grounded source context is available for image generation")

    try:
        model, image_data_url = generate_grounded_image(
            language=payload.language,
            prompt=payload.prompt,
            retrieved=retrieved,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Image generation failed: {exc}") from exc

    db.execute(
        text(
            """
            INSERT INTO usage_ledger(user_id, feature, quantity, model, metadata)
            VALUES (:user_id, 'ai_image_openai', 1, :model, CAST(:metadata AS jsonb))
            """
        ),
        {
            "user_id": user.id,
            "model": model,
            "metadata": json.dumps(
                {
                    "concept_code": concept_code,
                    "retrieved_chunks": len(retrieved),
                    "power_phase": phase,
                    "prompt": payload.prompt[:1000],
                },
                ensure_ascii=False,
            ),
        },
    )
    db.execute(
        text(
            """
            INSERT INTO learning_events(user_id, learning_session_id, event_type, payload)
            VALUES (:user_id, :learning_session_id, 'tutor_image_generated', CAST(:payload AS jsonb))
            """
        ),
        {
            "user_id": user.id,
            "learning_session_id": learning_session_id,
            "payload": json.dumps(
                {
                    "phase": phase,
                    "concept_code": concept_code,
                    "model": model,
                    "retrieved_chunks": len(retrieved),
                    "prompt": payload.prompt[:1000],
                },
                ensure_ascii=False,
            ),
        },
    )
    db.commit()
    return {
        "provider": "openai",
        "model": model,
        "phase": phase,
        "image_data_url": image_data_url,
        "retrieval": {
            "count": len(retrieved),
            "sources": [item.as_dict() for item in retrieved],
        },
    }

