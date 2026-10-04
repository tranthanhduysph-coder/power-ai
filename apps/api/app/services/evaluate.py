from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable


def summarize_evaluation(
    rows: Iterable[dict[str, Any]],
    *,
    practice_set_id: str,
    practice_attempt_id: str,
) -> dict[str, Any]:
    """Build stable POWER Evaluate evidence from question-level results."""
    items = list(rows)
    total = len(items)
    correct = sum(1 for item in items if bool(item.get("is_correct")))
    accuracy = correct / total if total else 0.0

    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "concept_code": "",
            "name_vi": "",
            "name_en": "",
            "correct": 0,
            "total": 0,
            "mastery": 0.0,
        }
    )

    for item in items:
        code = str(item.get("concept_code") or "UNKNOWN")
        bucket = grouped[code]
        bucket["concept_code"] = code
        bucket["name_vi"] = str(item.get("concept_name_vi") or code)
        bucket["name_en"] = str(item.get("concept_name_en") or code)
        bucket["total"] += 1
        bucket["correct"] += int(bool(item.get("is_correct")))
        mastery = item.get("mastery") or {}
        if isinstance(mastery, dict):
            bucket["mastery"] = float(mastery.get("mastery_score", bucket["mastery"]) or 0.0)

    concepts: list[dict[str, Any]] = []
    for bucket in grouped.values():
        concept_accuracy = bucket["correct"] / bucket["total"] if bucket["total"] else 0.0
        concepts.append({**bucket, "accuracy": round(concept_accuracy, 4)})

    concepts.sort(key=lambda item: (item["accuracy"], item["mastery"], item["concept_code"]))
    weak_concepts = [
        item["concept_code"]
        for item in concepts
        if item["accuracy"] < 0.6 or item["mastery"] < 0.6
    ]

    return {
        "practice_set_id": practice_set_id,
        "practice_attempt_id": practice_attempt_id,
        "accuracy": round(accuracy, 5),
        "correct": correct,
        "total": total,
        "concepts": concepts,
        "weak_concepts": weak_concepts,
        "evidence_ready": total > 0,
    }
