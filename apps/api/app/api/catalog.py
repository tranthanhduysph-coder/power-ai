from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, get_current_user
from app.db.session import get_db

router = APIRouter(tags=["catalog"])


@router.get("/catalog")
def catalog(
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        text("""
            SELECT cu.code, cu.name_vi, cu.name_en, cu.sort_order,
                   g.level AS grade, s.code AS subject_code,
                   s.name_vi AS subject_vi, s.name_en AS subject_en
            FROM curriculum_units cu
            JOIN grades g ON g.id = cu.grade_id
            JOIN subjects s ON s.id = cu.subject_id
            WHERE cu.parent_id IS NOT NULL
            ORDER BY g.level, cu.sort_order
        """)
    ).mappings().all()
    return {"items": [dict(r) for r in rows]}


@router.get("/catalog/{unit_code}/concepts")
def unit_concepts(
    unit_code: str,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        text("""
            SELECT c.code, c.name_vi, c.name_en,
                   COALESCE(cm.mastery_score, 0.50) AS mastery_score
            FROM curriculum_units cu
            JOIN curriculum_concepts cc ON cc.curriculum_unit_id = cu.id
            JOIN concepts c ON c.id = cc.concept_id
            LEFT JOIN concept_mastery cm ON cm.concept_id = c.id AND cm.user_id = :user_id
            WHERE cu.code = :unit_code
            ORDER BY cc.is_core DESC, c.code
        """),
        {"unit_code": unit_code, "user_id": user.id},
    ).mappings().all()
    return {"items": [dict(r) for r in rows]}
