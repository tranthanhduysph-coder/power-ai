from __future__ import annotations

from collections import defaultdict
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def get_unit_record(db: Session, unit_code: str) -> dict[str, Any]:
    row = db.execute(
        text(
            """
            SELECT cu.id, cu.code, cu.name_vi, cu.name_en, cu.unit_type, cu.lesson_number,
                   cu.printed_page_start, cu.printed_page_end, cu.is_power_ready,
                   cu.catalog_visible, cu.metadata_json,
                   g.level AS grade, g.name_vi AS grade_name_vi, g.name_en AS grade_name_en,
                   s.code AS subject_code, s.name_vi AS subject_name_vi, s.name_en AS subject_name_en,
                   p.code AS parent_code, p.name_vi AS parent_name_vi, p.name_en AS parent_name_en
            FROM curriculum_units cu
            JOIN grades g ON g.id = cu.grade_id
            JOIN subjects s ON s.id = cu.subject_id
            LEFT JOIN curriculum_units p ON p.id = cu.parent_id
            WHERE cu.code = :unit_code AND cu.catalog_visible = true
            """
        ),
        {"unit_code": unit_code},
    ).mappings().one_or_none()
    if not row:
        raise KeyError(unit_code)
    result = dict(row)
    result["metadata_json"] = result.get("metadata_json") or {}
    return result


def get_power_blueprint_record(db: Session, unit_code: str) -> dict[str, Any]:
    row = db.execute(
        text(
            """
            SELECT cu.code AS unit_code, cu.name_vi, cu.name_en, cu.is_power_ready, cu.metadata_json,
                   pub.version, pub.prepare_json, pub.work_json, pub.policy_json
            FROM curriculum_units cu
            LEFT JOIN power_unit_blueprints pub ON pub.curriculum_unit_id = cu.id
            WHERE cu.code = :unit_code AND cu.catalog_visible = true
            """
        ),
        {"unit_code": unit_code},
    ).mappings().one_or_none()
    if not row or not row["is_power_ready"] or row["version"] is None:
        raise KeyError(unit_code)
    return {
        "unit_code": row["unit_code"],
        "name_vi": row["name_vi"],
        "name_en": row["name_en"],
        "metadata": row["metadata_json"] or {},
        "version": row["version"],
        "prepare": row["prepare_json"] or {},
        "work": row["work_json"] or {},
        "policy": row["policy_json"] or {},
    }


def build_catalog_tree(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_grade: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for raw in rows:
        row = dict(raw)
        by_grade[int(row["grade"])].append(row)

    output: list[dict[str, Any]] = []
    for grade in sorted(by_grade):
        grade_rows = by_grade[grade]
        nodes = {r["code"]: {**r, "children": []} for r in grade_rows}
        roots: list[dict[str, Any]] = []
        for row in grade_rows:
            node = nodes[row["code"]]
            parent_code = row.get("parent_code")
            if parent_code and parent_code in nodes:
                nodes[parent_code]["children"].append(node)
            else:
                roots.append(node)

        def sort_node(node: dict[str, Any]) -> None:
            node["children"].sort(key=lambda x: (int(x.get("sort_order") or 0), x["code"]))
            for child in node["children"]:
                sort_node(child)

        roots.sort(key=lambda x: (int(x.get("sort_order") or 0), x["code"]))
        for root in roots:
            sort_node(root)
        output.append({"grade": grade, "items": roots})
    return output
