from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, get_current_user
from app.db.session import get_db
from app.services.curriculum import build_catalog_tree, get_unit_record

router = APIRouter(tags=["catalog"])


@router.get("/catalog")
def catalog(
    grade: int | None = Query(default=None, ge=10, le=12),
    ready_only: bool = Query(default=False),
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ = user
    clauses = ["cu.catalog_visible = true", "cu.unit_type IN ('lesson','practice','project')"]
    params: dict[str, object] = {}
    if grade is not None:
        clauses.append("g.level = :grade")
        params["grade"] = grade
    if ready_only:
        clauses.append("cu.is_power_ready = true")

    rows = db.execute(
        text(
            f"""
            SELECT cu.code, cu.name_vi, cu.name_en, cu.sort_order, cu.unit_type,
                   cu.lesson_number, cu.printed_page_start, cu.printed_page_end,
                   cu.is_power_ready, cu.metadata_json,
                   g.level AS grade, s.code AS subject_code,
                   s.name_vi AS subject_vi, s.name_en AS subject_en,
                   p.code AS parent_code, p.name_vi AS parent_vi, p.name_en AS parent_en
            FROM curriculum_units cu
            JOIN grades g ON g.id = cu.grade_id
            JOIN subjects s ON s.id = cu.subject_id
            LEFT JOIN curriculum_units p ON p.id = cu.parent_id
            WHERE {' AND '.join(clauses)}
            ORDER BY g.level, p.sort_order, cu.sort_order, cu.lesson_number NULLS LAST, cu.code
            """
        ),
        params,
    ).mappings().all()
    return {"items": [dict(r) for r in rows]}


@router.get("/catalog/tree")
def catalog_tree(
    grade: int | None = Query(default=None, ge=10, le=12),
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ = user
    params: dict[str, object] = {}
    grade_clause = ""
    if grade is not None:
        grade_clause = "AND g.level = :grade"
        params["grade"] = grade
    rows = db.execute(
        text(
            f"""
            SELECT cu.code, cu.name_vi, cu.name_en, cu.sort_order, cu.unit_type,
                   cu.lesson_number, cu.printed_page_start, cu.printed_page_end,
                   cu.is_power_ready, cu.metadata_json,
                   g.level AS grade, p.code AS parent_code
            FROM curriculum_units cu
            JOIN grades g ON g.id = cu.grade_id
            LEFT JOIN curriculum_units p ON p.id = cu.parent_id
            WHERE cu.catalog_visible = true {grade_clause}
            ORDER BY g.level, cu.sort_order, cu.lesson_number NULLS LAST, cu.code
            """
        ),
        params,
    ).mappings().all()
    return {"grades": build_catalog_tree([dict(r) for r in rows])}


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


@router.get("/catalog/{unit_code}")
def unit_detail(
    unit_code: str,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ = user
    try:
        unit = get_unit_record(db, unit_code)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Curriculum unit not found") from exc

    sources = db.execute(
        text(
            """
            SELECT s.code, s.title, s.language, cus.source_role,
                   cus.printed_page_start, cus.printed_page_end,
                   cus.pdf_page_start, cus.pdf_page_end, cus.metadata_json
            FROM curriculum_unit_sources cus
            JOIN sources s ON s.id = cus.source_id
            JOIN curriculum_units cu ON cu.id = cus.curriculum_unit_id
            WHERE cu.code = :unit_code
            ORDER BY CASE cus.source_role WHEN 'primary' THEN 0 WHEN 'reference' THEN 1 ELSE 2 END, s.code
            """
        ),
        {"unit_code": unit_code},
    ).mappings().all()
    concepts = db.execute(
        text(
            """
            SELECT c.code, c.name_vi, c.name_en, cc.is_core
            FROM curriculum_units cu
            JOIN curriculum_concepts cc ON cc.curriculum_unit_id = cu.id
            JOIN concepts c ON c.id = cc.concept_id
            WHERE cu.code = :unit_code
            ORDER BY cc.is_core DESC, c.code
            """
        ),
        {"unit_code": unit_code},
    ).mappings().all()
    metadata = unit.get("metadata_json") or {}
    return {
        **unit,
        "primary_concept_code": metadata.get("primary_concept_code") or (concepts[0]["code"] if concepts else None),
        "sources": [dict(r) for r in sources],
        "concepts": [dict(r) for r in concepts],
    }
