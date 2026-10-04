from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.services.curriculum import get_power_blueprint_record

_ACTION_VERBS_VI = (
    "mô tả",
    "giải thích",
    "phân biệt",
    "so sánh",
    "trình bày",
    "xác định",
    "vận dụng",
    "trả lời",
    "nêu",
)
_ACTION_VERBS_EN = (
    "describe",
    "explain",
    "distinguish",
    "compare",
    "identify",
    "apply",
    "answer",
    "state",
)


def _prepare_data(record: dict[str, Any]) -> dict[str, Any]:
    prepare = record.get("prepare") or {}
    if not prepare:
        raise KeyError(record.get("unit_code", ""))
    return prepare


def build_prepare_blueprint(unit_code: str, prepare: dict[str, Any], language: str = "vi") -> dict[str, Any]:
    lang = "en" if language == "en" else "vi"
    return {
        "unit_code": unit_code,
        "title": prepare.get(f"title_{lang}") or "",
        "outcomes": list(prepare.get(f"outcomes_{lang}") or []),
        "diagnostic_items": [
            {
                "code": item["code"],
                "concept_code": item["concept_code"],
                "question_type": item["question_type"],
                "prompt": item.get(f"prompt_{lang}") or "",
                "options": [
                    {
                        "key": option["key"],
                        "text": option.get(f"text_{lang}") or "",
                    }
                    for option in item.get("options", [])
                ],
            }
            for item in prepare.get("diagnostic_items", [])
        ],
    }


def get_prepare_blueprint(db: Session, unit_code: str, language: str = "vi") -> dict[str, Any]:
    record = get_power_blueprint_record(db, unit_code)
    return build_prepare_blueprint(unit_code, _prepare_data(record), language)


def analyze_goal_against_blueprint(
    goal: str,
    target_minutes: int,
    unit_code: str,
    language: str,
    prepare: dict[str, Any],
) -> dict[str, Any]:
    lang = "en" if language == "en" else "vi"
    normalized = " ".join(goal.strip().lower().split())
    verbs = _ACTION_VERBS_EN if lang == "en" else _ACTION_VERBS_VI
    keywords = [str(k).lower() for k in prepare.get("keywords", [])]

    relevant = any(keyword in normalized for keyword in keywords) if keywords else len(normalized) >= 20
    specific = relevant and len(normalized) >= 20
    measurable = any(verb in normalized for verb in verbs) or any(ch.isdigit() for ch in normalized)
    achievable = 10 <= target_minutes <= 90 and len(normalized) >= 10
    time_bound = target_minutes > 0

    checks = {
        "specific": specific,
        "measurable": measurable,
        "achievable": achievable,
        "relevant": relevant,
        "time_bound": time_bound,
    }
    score = sum(1 for value in checks.values() if value)

    title = prepare.get(f"title_{lang}") or unit_code
    if lang == "en":
        suggestions = []
        if not specific:
            suggestions.append(f"Name the exact idea in {title} that you want to understand.")
        if not measurable:
            suggestions.append("Use an observable verb such as explain, compare, identify or answer.")
        if not achievable:
            suggestions.append("Keep this session focused and use a realistic duration between 10 and 90 minutes.")
        if not relevant:
            suggestions.append(f"Link the goal directly to {title} or one of its core concepts.")
        if not time_bound:
            suggestions.append("Set a target duration for this learning session.")
        first_outcome = (prepare.get("outcomes_en") or [title])[0]
        example = f"Within {target_minutes} minutes, I can {first_outcome[:1].lower() + first_outcome[1:].rstrip('.')} and answer at least 4 out of 5 related questions correctly."
    else:
        suggestions = []
        if not specific:
            suggestions.append(f"Nêu rõ nội dung cụ thể của {title} mà bạn muốn hiểu.")
        if not measurable:
            suggestions.append("Dùng động từ có thể quan sát được như giải thích, so sánh, xác định hoặc trả lời.")
        if not achievable:
            suggestions.append("Giữ mục tiêu đủ tập trung và chọn thời lượng thực tế từ 10 đến 90 phút.")
        if not relevant:
            suggestions.append(f"Gắn mục tiêu trực tiếp với {title} hoặc một khái niệm cốt lõi của bài.")
        if not time_bound:
            suggestions.append("Đặt thời lượng mục tiêu cho phiên học.")
        first_outcome = (prepare.get("outcomes_vi") or [title])[0]
        example = f"Trong {target_minutes} phút, tôi có thể {first_outcome[:1].lower() + first_outcome[1:].rstrip('.')} và trả lời đúng ít nhất 4/5 câu hỏi liên quan."

    return {
        "score": score,
        "max_score": 5,
        "checks": checks,
        "suggestions": suggestions,
        "example": example,
    }


def analyze_goal(db: Session, goal: str, target_minutes: int, unit_code: str, language: str = "vi") -> dict[str, Any]:
    record = get_power_blueprint_record(db, unit_code)
    return analyze_goal_against_blueprint(goal, target_minutes, unit_code, language, _prepare_data(record))


def score_diagnostic_against_blueprint(prepare: dict[str, Any], answers: dict[str, Any]) -> dict[str, Any]:
    results = []
    correct = 0
    missing = []
    weak_concepts: set[str] = set()
    diagnostic_items = list(prepare.get("diagnostic_items") or [])

    for item in diagnostic_items:
        code = item["code"]
        if code not in answers:
            missing.append(code)
            continue

        received = answers[code]
        expected = item.get("expected")
        if item["question_type"] == "mcq":
            received = str(received).strip().upper()
        elif item["question_type"] == "true_false":
            if isinstance(received, str):
                received = received.strip().lower() in {"true", "1", "yes", "đúng", "dung"}
            else:
                received = bool(received)

        is_correct = received == expected
        correct += int(is_correct)
        if not is_correct:
            weak_concepts.add(item["concept_code"])
        results.append(
            {
                "code": code,
                "concept_code": item["concept_code"],
                "is_correct": is_correct,
            }
        )

    total = len(diagnostic_items)
    answered = total - len(missing)
    readiness = (correct / total) if total else 0.0
    return {
        "correct": correct,
        "total": total,
        "answered": answered,
        "readiness": round(readiness, 4),
        "missing": missing,
        "weak_concepts": sorted(weak_concepts),
        "results": results,
    }


def score_diagnostic(db: Session, unit_code: str, answers: dict[str, Any]) -> dict[str, Any]:
    record = get_power_blueprint_record(db, unit_code)
    return score_diagnostic_against_blueprint(_prepare_data(record), answers)
