from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from math import prod
from typing import Any, Iterable


ERROR_CAUSES = {
    "knowledge_gap",
    "misconception",
    "careless",
    "strategy",
    "uncertain",
}


@dataclass(slots=True)
class RethinkValidation:
    understanding_gain: str
    error_cause: str
    corrected_explanation: str
    action_plan: str
    confidence_after_rethink: int
    confirmed_misconceptions: list[str]
    errors: list[str]


def aggregate_evidence_confidence(weights: Iterable[float]) -> float:
    """Combine independent weak signals without allowing confidence to reach 1.0."""
    clean = [min(max(float(weight), 0.0), 0.95) for weight in weights]
    if not clean:
        return 0.0
    return round(min(0.95, 1.0 - prod(1.0 - weight for weight in clean)), 4)


def build_candidate_misconceptions(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "code": "",
            "concept_code": "",
            "concept_name_vi": "",
            "concept_name_en": "",
            "statement_vi": "",
            "statement_en": "",
            "correction_vi": "",
            "correction_en": "",
            "weights": [],
            "question_codes": [],
        }
    )

    for row in rows:
        code = str(row.get("misconception_code") or "").strip()
        if not code:
            continue
        item = grouped[code]
        item["code"] = code
        item["concept_code"] = str(row.get("concept_code") or "")
        item["concept_name_vi"] = str(row.get("concept_name_vi") or item["concept_code"])
        item["concept_name_en"] = str(row.get("concept_name_en") or item["concept_code"])
        item["statement_vi"] = str(row.get("statement_vi") or "")
        item["statement_en"] = str(row.get("statement_en") or "")
        item["correction_vi"] = str(row.get("correction_vi") or "")
        item["correction_en"] = str(row.get("correction_en") or "")
        item["weights"].append(float(row.get("evidence_weight") or 0.0))
        question_code = str(row.get("question_code") or "")
        if question_code and question_code not in item["question_codes"]:
            item["question_codes"].append(question_code)

    result: list[dict[str, Any]] = []
    for item in grouped.values():
        confidence = aggregate_evidence_confidence(item.pop("weights"))
        result.append({**item, "confidence": confidence, "evidence_count": len(item["question_codes"])})
    result.sort(key=lambda item: (-float(item["confidence"]), item["code"]))
    return result


def validate_rethink_payload(
    *,
    understanding_gain: str,
    error_cause: str,
    corrected_explanation: str,
    action_plan: str,
    confidence_after_rethink: int,
    confirmed_misconceptions: Iterable[str],
    allowed_misconceptions: set[str],
    completed: bool,
) -> RethinkValidation:
    gain = understanding_gain.strip()
    cause = error_cause.strip()
    correction = corrected_explanation.strip()
    plan = action_plan.strip()
    confirmed = list(dict.fromkeys(code.strip() for code in confirmed_misconceptions if code.strip()))
    errors: list[str] = []

    if cause and cause not in ERROR_CAUSES:
        errors.append("Invalid error cause")
    unknown = [code for code in confirmed if code not in allowed_misconceptions]
    if unknown:
        errors.append("Unknown misconception confirmation")

    if completed:
        if len(gain) < 20:
            errors.append("Describe what became clearer in at least 20 characters")
        if cause not in ERROR_CAUSES:
            errors.append("Choose the main cause of error or uncertainty")
        if len(correction) < 40:
            errors.append("Rewrite the corrected idea in at least 40 characters")
        if len(plan) < 20:
            errors.append("State one concrete next-step action in at least 20 characters")
        if not 1 <= int(confidence_after_rethink) <= 5:
            errors.append("Confidence must be between 1 and 5")

    return RethinkValidation(
        understanding_gain=gain,
        error_cause=cause,
        corrected_explanation=correction,
        action_plan=plan,
        confidence_after_rethink=int(confidence_after_rethink),
        confirmed_misconceptions=confirmed,
        errors=errors,
    )


def recommend_next_action(
    *,
    accuracy: float,
    weak_concepts: Iterable[str],
    confirmed_misconceptions: Iterable[str],
    confidence_after_rethink: int,
    language: str,
    unit_code: str | None = None,
) -> dict[str, Any]:
    weak = list(dict.fromkeys(str(code) for code in weak_concepts if code))
    confirmed = list(dict.fromkeys(str(code) for code in confirmed_misconceptions if code))
    lang = "en" if language == "en" else "vi"

    if accuracy < 0.65 or len(weak) >= 3 or confirmed:
        kind = "review_and_retry"
        priority = 1
        title = "Ôn điểm yếu rồi chạy một chu trình POWER mới" if lang == "vi" else "Review weak points, then run another POWER cycle"
        reason = (
            "Kết quả Evaluate hoặc hiểu lầm đã xác nhận cho thấy bạn nên sửa một số khái niệm trước khi chuyển tiếp."
            if lang == "vi"
            else "Evaluate evidence or confirmed misconceptions suggest repairing a few concepts before moving on."
        )
        route = f"/learn/{unit_code}" if unit_code else "/learn"
    elif accuracy < 0.85 or confidence_after_rethink <= 3 or weak:
        kind = "targeted_practice"
        priority = 2
        title = "Luyện tập thích ứng tập trung vào khái niệm còn yếu" if lang == "vi" else "Do targeted adaptive practice on weaker concepts"
        reason = (
            "Bạn đã nắm phần lớn nội dung nhưng vẫn còn evidence cần củng cố trước khi coi là ổn định."
            if lang == "vi"
            else "You understand most of the unit, but some evidence still needs reinforcement before it is stable."
        )
        route = f"/practice?unitCode={unit_code}" if unit_code else "/practice"
    else:
        kind = "ready_to_continue"
        priority = 3
        title = "Sẵn sàng chuyển sang nội dung tiếp theo" if lang == "vi" else "Ready to continue to the next content"
        reason = (
            "Evaluate cho thấy mức hiểu khá vững; hãy duy trì bằng ôn cách quãng khi cần."
            if lang == "vi"
            else "Evaluate indicates relatively stable understanding; maintain it with spaced review when needed."
        )
        route = "/learn"

    return {
        "type": kind,
        "priority": priority,
        "title": title,
        "reason": reason,
        "route": route,
        "weak_concepts": weak,
        "confirmed_misconceptions": confirmed,
    }


def load_rethink_blueprint(db: Any, *, power_session_id: Any, user_id: Any, language: str) -> dict[str, Any]:
    """Load Evaluate evidence plus cautious misconception candidates for the Rethink phase."""
    from sqlalchemy import text

    owned = db.execute(
        text("""
            SELECT ps.id, ps.learning_session_id, ps.current_phase,
                   ls.status, ls.curriculum_unit_id, ls.language, cu.code AS unit_code,
                   prepare.state_json AS prepare_state,
                   work.state_json AS work_state,
                   evaluate.state_json AS evaluate_state,
                   evaluate.completed_at AS evaluate_completed_at,
                   rethink.state_json AS rethink_state,
                   rethink.completed_at AS rethink_completed_at
            FROM power_sessions ps
            JOIN learning_sessions ls ON ls.id = ps.learning_session_id
            JOIN curriculum_units cu ON cu.id = ls.curriculum_unit_id
            LEFT JOIN power_phase_state prepare ON prepare.power_session_id = ps.id AND prepare.phase = 'PREPARE'
            LEFT JOIN power_phase_state work ON work.power_session_id = ps.id AND work.phase = 'WORK'
            LEFT JOIN power_phase_state evaluate ON evaluate.power_session_id = ps.id AND evaluate.phase = 'EVALUATE'
            LEFT JOIN power_phase_state rethink ON rethink.power_session_id = ps.id AND rethink.phase = 'RETHINK'
            WHERE ps.id = :id AND ps.user_id = :user_id
        """),
        {"id": power_session_id, "user_id": user_id},
    ).mappings().one_or_none()
    if not owned:
        raise KeyError("POWER session not found")

    evaluate_state = owned["evaluate_state"] or {}
    prepare_state = owned["prepare_state"] or {}
    work_state = owned["work_state"] or {}
    rethink_state = owned["rethink_state"] or {}
    practice_attempt_id = evaluate_state.get("practice_attempt_id")

    candidate_rows: list[dict[str, Any]] = []
    if practice_attempt_id:
        candidate_rows = [
            dict(row)
            for row in db.execute(
                text("""
                    SELECT m.code AS misconception_code,
                           c.code AS concept_code,
                           c.name_vi AS concept_name_vi,
                           c.name_en AS concept_name_en,
                           m.statement_vi, m.statement_en,
                           m.correction_vi, m.correction_en,
                           qm.evidence_weight,
                           q.code AS question_code
                    FROM question_attempts qa
                    JOIN questions q ON q.id = qa.question_id
                    JOIN question_misconceptions qm ON qm.question_id = qa.question_id
                    JOIN misconceptions m ON m.id = qm.misconception_id
                    JOIN concepts c ON c.id = m.concept_id
                    WHERE qa.practice_attempt_id = :attempt_id
                      AND qa.is_correct = false
                    ORDER BY m.code, q.code
                """),
                {"attempt_id": practice_attempt_id},
            ).mappings().all()
        ]

    candidates = build_candidate_misconceptions(candidate_rows)
    weak_concepts = list(evaluate_state.get("weak_concepts") or [])
    current_confirmed = list(rethink_state.get("confirmed_misconceptions") or [])
    recommendation = recommend_next_action(
        accuracy=float(evaluate_state.get("accuracy") or 0.0),
        weak_concepts=weak_concepts,
        confirmed_misconceptions=current_confirmed,
        confidence_after_rethink=int(rethink_state.get("confidence_after_rethink") or work_state.get("confidence_after") or 3),
        language=language or owned["language"] or "vi",
        unit_code=owned.get("unit_code"),
    )

    return {
        "ready": bool(owned["evaluate_completed_at"] and evaluate_state.get("evidence_ready")),
        "current_phase": owned["current_phase"],
        "cycle_status": owned["status"],
        "evaluate": evaluate_state,
        "confidence_before": prepare_state.get("confidence"),
        "confidence_after_work": work_state.get("confidence_after"),
        "candidate_misconceptions": candidates,
        "saved": rethink_state,
        "completed_at": owned["rethink_completed_at"],
        "recommendation_preview": recommendation,
        "reflection_prompts": {
            "understanding_gain": "Điều gì đã trở nên rõ hơn?" if language != "en" else "What became clearer?",
            "corrected_explanation": "Hãy giải thích lại ý đúng bằng lời của bạn." if language != "en" else "Restate the corrected idea in your own words.",
            "action_plan": "Bạn sẽ làm gì khác đi ở lần học tiếp theo?" if language != "en" else "What will you do differently next time?",
        },
    }
