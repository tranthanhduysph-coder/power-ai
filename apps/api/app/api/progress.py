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
                   COALESCE(AVG(accuracy), 0) AS mean_accuracy
            FROM practice_attempts
            WHERE user_id = :user_id AND completed_at IS NOT NULL
        """),
        {"user_id": user.id},
    ).mappings().one()

    return {
        "concepts": [dict(r) for r in rows],
        "summary": {
            "completed_sets": practice["completed_sets"],
            "mean_accuracy": float(practice["mean_accuracy"] or 0),
        },
    }
