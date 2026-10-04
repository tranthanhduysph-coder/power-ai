import json
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, get_current_user
from app.db.session import get_db
from app.services.organize import get_organize_blueprint, get_unit_concepts, validate_organize_payload
from app.services.prepare import analyze_goal, get_prepare_blueprint, score_diagnostic
from app.services.rethink import load_rethink_blueprint, recommend_next_action, validate_rethink_payload
from app.services.work import get_work_blueprint, validate_work_payload

router = APIRouter(tags=["power"])
PHASES = ["PREPARE", "ORGANIZE", "WORK", "EVALUATE", "RETHINK"]


class StartPowerSession(BaseModel):
    unit_code: str = "B12_DNA_REPLICATION"
    language: Literal["vi", "en"] = "vi"
    force_new: bool = False


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


class OrganizeLink(BaseModel):
    source: str
    relation: str
    target: str


class OrganizeUpdate(BaseModel):
    anchor_concepts: list[str] = Field(default_factory=list)
    links: list[OrganizeLink] = Field(default_factory=list)
    synthesis: str = Field(default="", max_length=5000)
    completed: bool = False


class WorkUpdate(BaseModel):
    responses: dict[str, str] = Field(default_factory=dict)
    confidence_after: int = Field(default=3, ge=1, le=5)
    completed: bool = False


class RethinkUpdate(BaseModel):
    understanding_gain: str = Field(default="", max_length=5000)
    error_cause: str = Field(default="", max_length=64)
    corrected_explanation: str = Field(default="", max_length=5000)
    action_plan: str = Field(default="", max_length=3000)
    confidence_after_rethink: int = Field(default=3, ge=1, le=5)
    confirmed_misconceptions: list[str] = Field(default_factory=list)
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
    db: Session = Depends(get_db),
):
    _ = user
    try:
        return get_prepare_blueprint(db, unit_code, language)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Prepare blueprint not found for this unit") from exc


@router.get("/power/organize/blueprint")
def organize_blueprint(
    unit_code: str = Query(default="B12_DNA_REPLICATION"),
    language: Literal["vi", "en"] = Query(default="vi"),
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return get_organize_blueprint(db, unit_code, user.id, language)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Organize blueprint not found for this unit") from exc


@router.get("/power/work/blueprint")
def work_blueprint(
    unit_code: str = Query(default="B12_DNA_REPLICATION"),
    language: Literal["vi", "en"] = Query(default="vi"),
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ = user
    try:
        return get_work_blueprint(db, unit_code, language)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Work blueprint not found for this unit") from exc


@router.post("/power/prepare/goal-feedback")
def prepare_goal_feedback(
    payload: GoalFeedbackRequest,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ = user
    try:
        return analyze_goal(db, payload.goal, payload.target_minutes, payload.unit_code, payload.language)
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


@router.get("/power/sessions/history")
def power_session_history(
    unit_code: str = Query(default="B12_DNA_REPLICATION"),
    limit: int = Query(default=10, ge=1, le=25),
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ids = db.execute(
        text("""
            SELECT ps.id
            FROM power_sessions ps
            JOIN learning_sessions ls ON ls.id = ps.learning_session_id
            JOIN curriculum_units cu ON cu.id = ls.curriculum_unit_id
            WHERE ps.user_id = :user_id
              AND cu.code = :unit_code
            ORDER BY COALESCE(ls.ended_at, ps.updated_at) DESC, ps.created_at DESC
            LIMIT :limit
        """),
        {"user_id": user.id, "unit_code": unit_code, "limit": limit},
    ).scalars().all()
    return {"sessions": [_session_payload(db, session_id, user.id) for session_id in ids]}


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
    unit = db.execute(
        text("SELECT id, is_power_ready FROM curriculum_units WHERE code = :code AND catalog_visible = true"),
        {"code": payload.unit_code},
    ).mappings().one_or_none()
    if not unit:
        raise HTTPException(status_code=404, detail="Curriculum unit not found")
    if not unit["is_power_ready"]:
        raise HTTPException(status_code=409, detail="POWER content is not ready for this curriculum unit yet")
    unit_id = unit["id"]

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

    if not payload.force_new:
        latest_completed_id = db.execute(
            text("""
                SELECT ps.id
                FROM power_sessions ps
                JOIN learning_sessions ls ON ls.id = ps.learning_session_id
                WHERE ps.user_id = :user_id
                  AND ls.curriculum_unit_id = :unit_id
                  AND ls.status = 'completed'
                ORDER BY COALESCE(ls.ended_at, ps.updated_at) DESC
                LIMIT 1
            """),
            {"user_id": user.id, "unit_id": unit_id},
        ).scalar_one_or_none()
        if latest_completed_id:
            return {
                **_session_payload(db, latest_completed_id, user.id),
                "resumed": True,
                "cycle_completed": True,
            }

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
            SELECT ps.learning_session_id, ps.current_phase, cu.code AS unit_code, ls.language
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
            db,
            payload.goal,
            payload.target_minutes,
            owned["unit_code"],
            owned["language"],
        )
        diagnostic = score_diagnostic(db, owned["unit_code"], payload.diagnostic_answers)
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

    current_phase = owned["current_phase"]
    if payload.completed and current_phase == "PREPARE":
        current_phase = "ORGANIZE"
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
        "current_phase": current_phase,
        "prepare": state,
        "session": _session_payload(db, session_id, user.id),
    }


@router.put("/power/sessions/{session_id}/organize")
def update_organize(
    session_id: UUID,
    payload: OrganizeUpdate,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    owned = db.execute(
        text("""
            SELECT ps.learning_session_id, ps.current_phase, cu.code AS unit_code, ls.language
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
        concepts = get_unit_concepts(db, owned["unit_code"], user.id, owned["language"])
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Organize blueprint not found for this unit") from exc

    validation = validate_organize_payload(
        allowed_concepts={item["code"] for item in concepts},
        anchors=payload.anchor_concepts,
        links=[item.model_dump() for item in payload.links],
        synthesis=payload.synthesis,
        completed=payload.completed,
    )
    if validation.errors:
        raise HTTPException(status_code=422, detail="; ".join(validation.errors))

    state = {
        "anchor_concepts": validation.anchors,
        "links": validation.links,
        "synthesis": validation.synthesis,
        "unique_concepts": validation.unique_concepts,
        "coverage": validation.coverage,
    }

    db.execute(
        text("""
            INSERT INTO power_phase_state(power_session_id, phase, state_json, completed_at)
            VALUES (:session_id, 'ORGANIZE', CAST(:state AS jsonb), CASE WHEN :completed THEN now() ELSE NULL END)
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

    current_phase = owned["current_phase"]
    if payload.completed and current_phase == "ORGANIZE":
        current_phase = "WORK"
        db.execute(
            text("UPDATE power_sessions SET current_phase = 'WORK', updated_at = now() WHERE id = :id"),
            {"id": session_id},
        )
        db.execute(
            text("UPDATE learning_sessions SET current_power_phase = 'WORK' WHERE id = :id"),
            {"id": owned["learning_session_id"]},
        )
        db.execute(
            text("""
                INSERT INTO power_phase_state(power_session_id, phase, state_json)
                VALUES (:id, 'WORK', '{}'::jsonb)
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
            "event_type": "organize_completed" if payload.completed else "organize_saved",
            "payload": json.dumps(
                {
                    "anchors": len(validation.anchors),
                    "links": len(validation.links),
                    "coverage": validation.coverage,
                    "completed": payload.completed,
                }
            ),
        },
    )
    db.commit()
    return {
        "current_phase": current_phase,
        "organize": state,
        "session": _session_payload(db, session_id, user.id),
    }


@router.put("/power/sessions/{session_id}/work")
def update_work(
    session_id: UUID,
    payload: WorkUpdate,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    owned = db.execute(
        text("""
            SELECT ps.learning_session_id, ps.current_phase, cu.code AS unit_code, ls.language
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
        validation = validate_work_payload(
            db=db,
            unit_code=owned["unit_code"],
            language=owned["language"],
            responses=payload.responses,
            confidence_after=payload.confidence_after,
            completed=payload.completed,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Work blueprint not found for this unit") from exc
    if validation.errors:
        raise HTTPException(status_code=422, detail="; ".join(validation.errors))

    state = {
        "responses": validation.responses,
        "completed_tasks": validation.completed_tasks,
        "confidence_after": validation.confidence_after,
        "evidence_chars": validation.evidence_chars,
        "completion_ratio": validation.completion_ratio,
    }

    db.execute(
        text("""
            INSERT INTO power_phase_state(power_session_id, phase, state_json, completed_at)
            VALUES (:session_id, 'WORK', CAST(:state AS jsonb), CASE WHEN :completed THEN now() ELSE NULL END)
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

    current_phase = owned["current_phase"]
    if payload.completed and current_phase == "WORK":
        current_phase = "EVALUATE"
        db.execute(
            text("UPDATE power_sessions SET current_phase = 'EVALUATE', updated_at = now() WHERE id = :id"),
            {"id": session_id},
        )
        db.execute(
            text("UPDATE learning_sessions SET current_power_phase = 'EVALUATE' WHERE id = :id"),
            {"id": owned["learning_session_id"]},
        )
        db.execute(
            text("""
                INSERT INTO power_phase_state(power_session_id, phase, state_json)
                VALUES (:id, 'EVALUATE', '{}'::jsonb)
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
            "event_type": "work_completed" if payload.completed else "work_saved",
            "payload": json.dumps(
                {
                    "completed_tasks": len(validation.completed_tasks),
                    "completion_ratio": validation.completion_ratio,
                    "evidence_chars": validation.evidence_chars,
                    "confidence_after": validation.confidence_after,
                    "completed": payload.completed,
                }
            ),
        },
    )
    db.commit()
    return {
        "current_phase": current_phase,
        "work": state,
        "session": _session_payload(db, session_id, user.id),
    }


@router.get("/power/sessions/{session_id}/rethink/blueprint")
def rethink_blueprint(
    session_id: UUID,
    language: Literal["vi", "en"] = Query(default="vi"),
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return load_rethink_blueprint(
            db,
            power_session_id=session_id,
            user_id=user.id,
            language=language,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="POWER session not found") from exc


@router.put("/power/sessions/{session_id}/rethink")
def update_rethink(
    session_id: UUID,
    payload: RethinkUpdate,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        blueprint = load_rethink_blueprint(
            db,
            power_session_id=session_id,
            user_id=user.id,
            language="vi",
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="POWER session not found") from exc

    if payload.completed and not blueprint["ready"]:
        raise HTTPException(status_code=409, detail="Evaluate evidence is required before completing Rethink")

    candidates = {item["code"]: item for item in blueprint["candidate_misconceptions"]}
    validation = validate_rethink_payload(
        understanding_gain=payload.understanding_gain,
        error_cause=payload.error_cause,
        corrected_explanation=payload.corrected_explanation,
        action_plan=payload.action_plan,
        confidence_after_rethink=payload.confidence_after_rethink,
        confirmed_misconceptions=payload.confirmed_misconceptions,
        allowed_misconceptions=set(candidates),
        completed=payload.completed,
    )
    if validation.errors:
        raise HTTPException(status_code=422, detail="; ".join(validation.errors))

    owned = db.execute(
        text("""
            SELECT ps.learning_session_id, ps.current_phase,
                   ls.curriculum_unit_id, ls.language, ls.status, cu.code AS unit_code
            FROM power_sessions ps
            JOIN learning_sessions ls ON ls.id = ps.learning_session_id
            JOIN curriculum_units cu ON cu.id = ls.curriculum_unit_id
            WHERE ps.id = :id AND ps.user_id = :user_id
        """),
        {"id": session_id, "user_id": user.id},
    ).mappings().one()

    evaluate = blueprint.get("evaluate") or {}
    recommendation = recommend_next_action(
        accuracy=float(evaluate.get("accuracy") or 0.0),
        weak_concepts=evaluate.get("weak_concepts") or [],
        confirmed_misconceptions=validation.confirmed_misconceptions,
        confidence_after_rethink=validation.confidence_after_rethink,
        language=owned["language"],
        unit_code=owned["unit_code"],
    )
    state = {
        "understanding_gain": validation.understanding_gain,
        "error_cause": validation.error_cause,
        "corrected_explanation": validation.corrected_explanation,
        "action_plan": validation.action_plan,
        "confidence_after_rethink": validation.confidence_after_rethink,
        "confirmed_misconceptions": validation.confirmed_misconceptions,
        "candidate_misconceptions": blueprint["candidate_misconceptions"],
        "evaluate_summary": {
            "accuracy": evaluate.get("accuracy"),
            "correct": evaluate.get("correct"),
            "total": evaluate.get("total"),
            "weak_concepts": evaluate.get("weak_concepts") or [],
            "practice_attempt_id": evaluate.get("practice_attempt_id"),
        },
        "recommendation": recommendation,
    }

    db.execute(
        text("""
            INSERT INTO power_phase_state(power_session_id, phase, state_json, completed_at)
            VALUES (:session_id, 'RETHINK', CAST(:state AS jsonb), CASE WHEN :completed THEN now() ELSE NULL END)
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
        for code in validation.confirmed_misconceptions:
            candidate = candidates[code]
            misconception = db.execute(
                text("""
                    SELECT m.id, m.concept_id
                    FROM misconceptions m
                    WHERE m.code = :code
                """),
                {"code": code},
            ).mappings().one()
            db.execute(
                text("""
                    INSERT INTO learner_misconceptions(
                        user_id, misconception_id, concept_id, confidence, status,
                        first_detected_at, last_detected_at
                    )
                    VALUES (:user_id, :misconception_id, :concept_id, :confidence, 'active', now(), now())
                    ON CONFLICT (user_id, misconception_id) DO UPDATE
                    SET confidence = GREATEST(learner_misconceptions.confidence, EXCLUDED.confidence),
                        status = 'active',
                        last_detected_at = now()
                """),
                {
                    "user_id": user.id,
                    "misconception_id": misconception["id"],
                    "concept_id": misconception["concept_id"],
                    "confidence": candidate["confidence"],
                },
            )
            db.execute(
                text("""
                    INSERT INTO misconception_evidence(
                        user_id, learning_session_id, misconception_id, concept_id,
                        evidence_type, evidence_object_id, confidence, details
                    )
                    VALUES (
                        :user_id, :learning_session_id, :misconception_id, :concept_id,
                        'evaluate_rethink_confirmation', :evidence_object_id, :confidence, CAST(:details AS jsonb)
                    )
                    ON CONFLICT (learning_session_id, misconception_id, evidence_type, evidence_object_id)
                    DO UPDATE SET confidence = EXCLUDED.confidence, details = EXCLUDED.details
                """),
                {
                    "user_id": user.id,
                    "learning_session_id": owned["learning_session_id"],
                    "misconception_id": misconception["id"],
                    "concept_id": misconception["concept_id"],
                    "evidence_object_id": str(evaluate.get("practice_attempt_id") or ""),
                    "confidence": candidate["confidence"],
                    "details": json.dumps(
                        {
                            "power_session_id": str(session_id),
                            "question_codes": candidate.get("question_codes", []),
                            "learner_confirmed": True,
                        },
                        ensure_ascii=False,
                    ),
                },
            )

        db.execute(
            text("""
                UPDATE learning_recommendations
                SET status = 'dismissed'
                WHERE learning_session_id = :learning_session_id AND status = 'pending'
            """),
            {"learning_session_id": owned["learning_session_id"]},
        )
        db.execute(
            text("""
                INSERT INTO learning_recommendations(
                    user_id, learning_session_id, curriculum_unit_id,
                    recommendation_type, priority, payload, status
                )
                VALUES (
                    :user_id, :learning_session_id, :curriculum_unit_id,
                    :recommendation_type, :priority, CAST(:payload AS jsonb), 'pending'
                )
            """),
            {
                "user_id": user.id,
                "learning_session_id": owned["learning_session_id"],
                "curriculum_unit_id": owned["curriculum_unit_id"],
                "recommendation_type": recommendation["type"],
                "priority": recommendation["priority"],
                "payload": json.dumps(recommendation, ensure_ascii=False),
            },
        )
        if owned["current_phase"] == "RETHINK":
            db.execute(
                text("UPDATE learning_sessions SET status = 'completed', ended_at = COALESCE(ended_at, now()) WHERE id = :id"),
                {"id": owned["learning_session_id"]},
            )

    db.execute(
        text("""
            INSERT INTO learning_events(user_id, learning_session_id, event_type, payload)
            VALUES (:user_id, :learning_session_id, :event_type, CAST(:payload AS jsonb))
        """),
        {
            "user_id": user.id,
            "learning_session_id": owned["learning_session_id"],
            "event_type": "rethink_completed" if payload.completed else "rethink_saved",
            "payload": json.dumps(
                {
                    "completed": payload.completed,
                    "error_cause": validation.error_cause,
                    "confirmed_misconceptions": validation.confirmed_misconceptions,
                    "recommendation_type": recommendation["type"],
                },
                ensure_ascii=False,
            ),
        },
    )
    db.commit()
    return {
        "current_phase": owned["current_phase"],
        "cycle_completed": bool(payload.completed and owned["current_phase"] == "RETHINK"),
        "rethink": state,
        "recommendation": recommendation,
        "session": _session_payload(db, session_id, user.id),
    }


@router.put("/power/sessions/{session_id}/phase")
def update_phase(
    session_id: UUID,
    payload: PhaseUpdate,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.phase == "RETHINK":
        raise HTTPException(status_code=409, detail="Use the dedicated Rethink endpoint so learner-model evidence is preserved")
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
