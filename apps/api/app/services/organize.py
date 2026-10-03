from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


RELATION_OPTIONS: tuple[dict[str, str], ...] = (
    {"code": "prerequisite", "vi": "là kiến thức nền cho", "en": "is a prerequisite for"},
    {"code": "causes", "vi": "dẫn đến", "en": "leads to"},
    {"code": "explains", "vi": "giải thích", "en": "explains"},
    {"code": "part_of", "vi": "là một phần của", "en": "is part of"},
    {"code": "related", "vi": "có liên quan với", "en": "is related to"},
    {"code": "contrasts_with", "vi": "đối lập/so sánh với", "en": "contrasts with"},
)

_ALLOWED_RELATIONS = {item["code"] for item in RELATION_OPTIONS}


@dataclass(frozen=True)
class OrganizeValidation:
    anchors: list[str]
    links: list[dict[str, str]]
    synthesis: str
    unique_concepts: list[str]
    coverage: float
    errors: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "anchors": self.anchors,
            "links": self.links,
            "synthesis": self.synthesis,
            "unique_concepts": self.unique_concepts,
            "coverage": self.coverage,
            "errors": self.errors,
        }


def get_unit_concepts(db: Session, unit_code: str, user_id: Any, language: str) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            SELECT c.code, c.name_vi, c.name_en, c.description_vi, c.description_en,
                   cc.is_core, COALESCE(cm.mastery_score, 0.50) AS mastery_score
            FROM curriculum_units cu
            JOIN curriculum_concepts cc ON cc.curriculum_unit_id = cu.id
            JOIN concepts c ON c.id = cc.concept_id
            LEFT JOIN concept_mastery cm ON cm.concept_id = c.id AND cm.user_id = :user_id
            WHERE cu.code = :unit_code
            ORDER BY cc.is_core DESC, c.code
            """
        ),
        {"unit_code": unit_code, "user_id": user_id},
    ).mappings().all()
    if not rows:
        raise KeyError(unit_code)

    suffix = "en" if language == "en" else "vi"
    return [
        {
            "code": row["code"],
            "name": row[f"name_{suffix}"],
            "description": row[f"description_{suffix}"] or "",
            "is_core": bool(row["is_core"]),
            "mastery_score": float(row["mastery_score"]),
        }
        for row in rows
    ]


def get_organize_blueprint(db: Session, unit_code: str, user_id: Any, language: str) -> dict[str, Any]:
    concepts = get_unit_concepts(db, unit_code, user_id, language)
    is_en = language == "en"
    return {
        "unit_code": unit_code,
        "concepts": concepts,
        "relation_options": [
            {"code": item["code"], "label": item["en"] if is_en else item["vi"]}
            for item in RELATION_OPTIONS
        ],
        "minimum_anchor_concepts": 3,
        "minimum_links": 3,
        "synthesis_prompt": (
            "Explain one chain of relationships in your own words. What makes the links meaningful?"
            if is_en
            else "Hãy giải thích một chuỗi quan hệ bằng lời của bạn. Vì sao các mắt xích đó có ý nghĩa?"
        ),
    }


def validate_organize_payload(
    *,
    allowed_concepts: set[str],
    anchors: list[str],
    links: list[dict[str, str]],
    synthesis: str,
    completed: bool,
) -> OrganizeValidation:
    errors: list[str] = []

    clean_anchors: list[str] = []
    for code in anchors:
        code = str(code).strip()
        if code and code not in clean_anchors:
            clean_anchors.append(code)

    clean_links: list[dict[str, str]] = []
    seen_links: set[tuple[str, str, str]] = set()
    for raw in links:
        source = str(raw.get("source", "")).strip()
        relation = str(raw.get("relation", "")).strip()
        target = str(raw.get("target", "")).strip()
        if not source and not relation and not target:
            continue
        if source not in allowed_concepts:
            errors.append(f"Unknown source concept: {source}")
            continue
        if target not in allowed_concepts:
            errors.append(f"Unknown target concept: {target}")
            continue
        if source == target:
            errors.append("A concept cannot be linked to itself")
            continue
        if relation not in _ALLOWED_RELATIONS:
            errors.append(f"Unsupported relation: {relation}")
            continue
        key = (source, relation, target)
        if key in seen_links:
            continue
        seen_links.add(key)
        clean_links.append({"source": source, "relation": relation, "target": target})

    for code in clean_anchors:
        if code not in allowed_concepts:
            errors.append(f"Unknown anchor concept: {code}")

    clean_anchors = [code for code in clean_anchors if code in allowed_concepts]
    clean_synthesis = synthesis.strip()

    used = set(clean_anchors)
    for link in clean_links:
        used.add(link["source"])
        used.add(link["target"])
    coverage = round(len(used) / max(len(allowed_concepts), 1), 3)

    if completed:
        if len(clean_anchors) < 3:
            errors.append("Choose at least 3 anchor concepts before completing Organize")
        if len(clean_links) < 3:
            errors.append("Create at least 3 concept relationships before completing Organize")
        if len(clean_synthesis) < 20:
            errors.append("Write a synthesis of at least 20 characters before completing Organize")

    return OrganizeValidation(
        anchors=clean_anchors,
        links=clean_links,
        synthesis=clean_synthesis,
        unique_concepts=sorted(used),
        coverage=coverage,
        errors=errors,
    )
