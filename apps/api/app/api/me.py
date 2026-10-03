from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, get_current_user
from app.db.session import get_db

router = APIRouter(tags=["me"])


@router.get("/me")
def me(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.execute(
        text("""
            SELECT lp.preferred_language, lp.target_exam, lp.preferred_session_minutes,
                   g.level AS grade_level, s.code AS subject_code
            FROM learning_profiles lp
            LEFT JOIN grades g ON g.id = lp.grade_level_id
            LEFT JOIN subjects s ON s.id = g.subject_id
            WHERE lp.user_id = :user_id
        """),
        {"user_id": user.id},
    ).mappings().one_or_none()

    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
        "role": user.role,
        "profile": dict(profile) if profile else {},
    }
