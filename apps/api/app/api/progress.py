from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, get_current_user
from app.db.session import get_db

router = APIRouter(tags=["progress"])


@router.get("/progress")
def progress(
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        text("""
            SELECT c.code, c.name_vi, c.name_en,
                   cm.mastery_score, cm.confidence,
                   cm.attempt_count, cm.correct_count, cm.last_practiced_at
            FROM concept_mastery cm
            JOIN concepts c ON c.id = cm.concept_id
            WHERE cm.user_id = :user_id
            ORDER BY cm.mastery_score ASC, c.code
        """),
        {"user_id": user.id},
    ).mappings().all()

    practice = db.execute(
        text("""
            SELECT COUNT(*) AS completed_sets,
                   COALESCE(AVG(accuracy), 0) AS mean_accuracy,
                   MAX(completed_at) AS latest_completed_at
            FROM practice_attempts
            WHERE user_id = :user_id AND completed_at IS NOT NULL
        """),
        {"user_id": user.id},
    ).mappings().one()

    latest_accuracy = db.execute(
        text("""
            SELECT accuracy
            FROM practice_attempts
            WHERE user_id = :user_id AND completed_at IS NOT NULL
            ORDER BY completed_at DESC, id DESC
            LIMIT 1
        """),
        {"user_id": user.id},
    ).scalar_one_or_none()

    active_cycle = db.execute(
        text("""
            SELECT ps.id, ps.current_phase, cu.code AS unit_code,
                   cu.name_vi, cu.name_en, ps.updated_at
            FROM power_sessions ps
            JOIN learning_sessions ls ON ls.id = ps.learning_session_id
            JOIN curriculum_units cu ON cu.id = ls.curriculum_unit_id
            WHERE ps.user_id = :user_id AND ls.status = 'active'
            ORDER BY ps.updated_at DESC
            LIMIT 1
        """),
        {"user_id": user.id},
    ).mappings().one_or_none()

    return {
        "concepts": [dict(r) for r in rows],
        "summary": {
            "completed_sets": practice["completed_sets"],
            "mean_accuracy": float(practice["mean_accuracy"] or 0),
            "latest_accuracy": None if latest_accuracy is None else float(latest_accuracy),
            "latest_completed_at": practice["latest_completed_at"],
        },
        "active_cycle": None if not active_cycle else {
            "id": str(active_cycle["id"]),
            "current_phase": active_cycle["current_phase"],
            "unit_code": active_cycle["unit_code"],
            "name_vi": active_cycle["name_vi"],
            "name_en": active_cycle["name_en"],
            "updated_at": active_cycle["updated_at"],
        },
    }
