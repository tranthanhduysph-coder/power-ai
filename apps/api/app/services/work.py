from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.services.curriculum import get_power_blueprint_record


@dataclass(frozen=True)
class WorkValidation:
    responses: dict[str, str]
    completed_tasks: list[str]
    confidence_after: int
    evidence_chars: int
    completion_ratio: float
    errors: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "responses": self.responses,
            "completed_tasks": self.completed_tasks,
            "confidence_after": self.confidence_after,
            "evidence_chars": self.evidence_chars,
            "completion_ratio": self.completion_ratio,
            "errors": self.errors,
        }


def build_work_blueprint(unit_code: str, work: dict[str, Any], language: str = "vi") -> dict[str, Any]:
    lang = "en" if language == "en" else "vi"
    raw = work.get(lang)
    if not raw:
        raise KeyError(unit_code)
    return {
        "unit_code": unit_code,
        "title": raw.get("title", ""),
        "intro": raw.get("intro", ""),
        "tasks": list(raw.get("tasks") or []),
        "self_check_prompt": raw.get("self_check_prompt", ""),
    }


def get_work_blueprint(db: Session, unit_code: str, language: str = "vi") -> dict[str, Any]:
    record = get_power_blueprint_record(db, unit_code)
    return build_work_blueprint(unit_code, record.get("work") or {}, language)


def validate_work_against_blueprint(
    *,
    blueprint: dict[str, Any],
    responses: dict[str, str],
    confidence_after: int,
    completed: bool,
) -> WorkValidation:
    clean_responses = {str(k): str(v).strip() for k, v in responses.items() if str(v).strip()}
    allowed_codes = {task["code"] for task in blueprint.get("tasks", [])}
    clean_responses = {k: v for k, v in clean_responses.items() if k in allowed_codes}

    errors: list[str] = []
    completed_tasks: list[str] = []
    for task in blueprint.get("tasks", []):
        value = clean_responses.get(task["code"], "")
        if len(value) >= int(task["minimum_chars"]):
            completed_tasks.append(task["code"])
        elif completed:
            errors.append(
                f"{task['code']} requires at least {task['minimum_chars']} characters of learner evidence"
            )

    if not 1 <= confidence_after <= 5:
        errors.append("confidence_after must be between 1 and 5")

    evidence_chars = sum(len(value) for value in clean_responses.values())
    total = len(blueprint.get("tasks", []))
    completion_ratio = round(len(completed_tasks) / max(total, 1), 3)

    return WorkValidation(
        responses=clean_responses,
        completed_tasks=completed_tasks,
        confidence_after=confidence_after,
        evidence_chars=evidence_chars,
        completion_ratio=completion_ratio,
        errors=errors,
    )


def validate_work_payload(
    *,
    db: Session,
    unit_code: str,
    language: str,
    responses: dict[str, str],
    confidence_after: int,
    completed: bool,
) -> WorkValidation:
    blueprint = get_work_blueprint(db, unit_code, language)
    return validate_work_against_blueprint(
        blueprint=blueprint,
        responses=responses,
        confidence_after=confidence_after,
        completed=completed,
    )
