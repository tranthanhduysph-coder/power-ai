from typing import Any, Literal
from uuid import UUID
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, get_current_user
from app.db.session import get_db
from app.services.evaluate import summarize_evaluation
from app.services.mastery import update_mastery
from app.services.ai_practice import generate_ai_practice_items

router = APIRouter(tags=["practice"])


class GeneratePractice(BaseModel):
    mode: Literal["custom", "adaptive", "ai"] = "custom"
    unit_code: str = "B12_DNA_REPLICATION"
    difficulty: Literal["auto", "easy", "medium", "hard"] = "auto"
    question_types: list[Literal["mcq", "true_false", "short_answer"]] = Field(
        default_factory=lambda: ["mcq", "true_false", "short_answer"]
    )
    question_count: int = Field(default=6, ge=3, le=20)
    power_session_id: UUID | None = None
    purpose: Literal["standalone", "evaluate"] = "standalone"
    ai_instruction: str | None = Field(default=None, max_length=800)

    @model_validator(mode="after")
    def evaluate_requires_power_session(self):
        if self.purpose == "evaluate" and not self.power_session_id:
            raise ValueError("power_session_id is required for Evaluate practice")
        if self.purpose == "evaluate" and self.mode == "ai":
            raise ValueError("AI-generated questions are not allowed in POWER Evaluate")
        return self


class AnswerItem(BaseModel):
    question_id: UUID
    answer: Any
    response_time_ms: int | None = Field(default=None, ge=0)
    hint_used: bool = False


class SubmitPractice(BaseModel):
    answers: list[AnswerItem]

    @model_validator(mode="after")
    def answers_required(self):
        if not self.answers:
            raise ValueError("At least one answer is required")
        return self


def public_question(row: dict, options: list[dict]) -> dict:
    return {
        "id": str(row["id"]),
        "code": row["code"],
        "question_type": row["question_type"],
        "difficulty": row["difficulty"],
        "cognitive_level": row["cognitive_level"],
        "stem_vi": row["stem_vi"],
        "stem_en": row["stem_en"],
        "options": [
            {"key": o["option_key"], "text_vi": o["text_vi"], "text_en": o["text_en"]}
            for o in options
        ],
    }


def public_ai_question(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(item["id"]),
        "code": item["code"],
        "question_type": item["question_type"],
        "difficulty": item["difficulty"],
        "cognitive_level": item["cognitive_level"],
        "stem_vi": item["stem_vi"],
        "stem_en": item["stem_en"],
        "options": item.get("options") or [],
    }


def _recommended_unit(db: Session, user_id: UUID, fallback_code: str) -> dict[str, Any] | None:
    row = db.execute(
        text(
            """
            SELECT cu.id, cu.code,
                   COUNT(cm.concept_id) AS evidence_count,
                   AVG(COALESCE(cm.mastery_score, 0.50)) AS average_mastery
            FROM curriculum_units cu
            JOIN curriculum_concepts cc ON cc.curriculum_unit_id = cu.id
            LEFT JOIN concept_mastery cm
              ON cm.concept_id = cc.concept_id AND cm.user_id = :user_id
            WHERE cu.catalog_visible = true
              AND cu.is_power_ready = true
              AND cu.lesson_number IS NOT NULL
            GROUP BY cu.id, cu.code
            HAVING COUNT(cm.concept_id) > 0
            ORDER BY AVG(COALESCE(cm.mastery_score, 0.50)) ASC,
                     COUNT(cm.concept_id) DESC,
                     cu.code
            LIMIT 1
            """
        ),
        {"user_id": user_id},
    ).mappings().one_or_none()
    if row:
        return dict(row)
    fallback = db.execute(
        text("SELECT id, code FROM curriculum_units WHERE code = :code"),
        {"code": fallback_code},
    ).mappings().one_or_none()
    return dict(fallback) if fallback else None


def _validate_power_evaluate_context(
    db: Session,
    *,
    user_id: UUID,
    power_session_id: UUID,
    unit_id: UUID,
) -> None:
    row = db.execute(
        text("""
            SELECT ps.current_phase, ls.status, ls.curriculum_unit_id
            FROM power_sessions ps
            JOIN learning_sessions ls ON ls.id = ps.learning_session_id
            WHERE ps.id = :id AND ps.user_id = :user_id
        """),
        {"id": power_session_id, "user_id": user_id},
    ).mappings().one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="POWER session not found")
    if row["curriculum_unit_id"] != unit_id:
        raise HTTPException(status_code=422, detail="Practice unit does not match the POWER session")
    if row["status"] != "active" or row["current_phase"] != "EVALUATE":
        raise HTTPException(status_code=409, detail="POWER session is not currently in Evaluate")


@router.post("/practice/generate")
def generate_practice(
    payload: GeneratePractice,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    effective_difficulty = payload.difficulty
    effective_types = list(payload.question_types)
    effective_count = payload.question_count

    if payload.mode == "adaptive":
        effective_difficulty = "auto"
        effective_types = ["mcq", "true_false", "short_answer"]
        effective_count = 6
        unit_row = (
            _recommended_unit(db, user.id, payload.unit_code)
            if payload.purpose == "standalone"
            else db.execute(
                text("SELECT id, code FROM curriculum_units WHERE code = :code"),
                {"code": payload.unit_code},
            ).mappings().one_or_none()
        )
    else:
        unit_row = db.execute(
            text("SELECT id, code FROM curriculum_units WHERE code = :code"),
            {"code": payload.unit_code},
        ).mappings().one_or_none()

    if not unit_row:
        raise HTTPException(status_code=404, detail="Curriculum unit not found")

    unit = unit_row["id"]
    resolved_unit_code = str(unit_row["code"])

    if payload.purpose == "evaluate" and payload.power_session_id:
        _validate_power_evaluate_context(
            db,
            user_id=user.id,
            power_session_id=payload.power_session_id,
            unit_id=unit,
        )

    if payload.mode == "ai":
        if payload.purpose != "standalone":
            raise HTTPException(status_code=422, detail="AI-generated practice is standalone practice only")
        try:
            ai_model, ai_items, source_basis = generate_ai_practice_items(
                db,
                unit_id=unit,
                difficulty=effective_difficulty,
                question_types=effective_types,
                question_count=effective_count,
                instruction=payload.ai_instruction,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"AI practice generation failed: {exc}") from exc

        set_id = db.execute(
            text(
                """
                INSERT INTO practice_sets(
                    user_id, mode, curriculum_unit_id, requested_difficulty, requested_count,
                    power_session_id, purpose, generated_items
                )
                VALUES (:user_id, 'ai', :unit_id, :difficulty, :count, NULL, 'standalone', CAST(:items AS jsonb))
                RETURNING id
                """
            ),
            {
                "user_id": user.id,
                "unit_id": unit,
                "difficulty": effective_difficulty,
                "count": effective_count,
                "items": json.dumps(ai_items, ensure_ascii=False),
            },
        ).scalar_one()

        db.execute(
            text(
                """
                INSERT INTO usage_ledger(user_id, feature, quantity, model, metadata)
                VALUES (:user_id, 'ai_practice_openai', :quantity, :model, CAST(:metadata AS jsonb))
                """
            ),
            {
                "user_id": user.id,
                "quantity": len(ai_items),
                "model": ai_model,
                "metadata": json.dumps(
                    {
                        "unit_code": resolved_unit_code,
                        "difficulty": effective_difficulty,
                        "question_types": effective_types,
                        "instruction": (payload.ai_instruction or "")[:800],
                        "source_basis": source_basis,
                    },
                    ensure_ascii=False,
                ),
            },
        )
        db.execute(
            text(
                """
                INSERT INTO usage_ledger(user_id, feature, quantity, metadata)
                VALUES (:user_id, 'practice_set', 1, CAST(:metadata AS jsonb))
                """
            ),
            {
                "user_id": user.id,
                "metadata": json.dumps(
                    {"mode": "ai", "count": len(ai_items), "purpose": "standalone"}
                ),
            },
        )
        db.commit()
        return {
            "practice_set_id": str(set_id),
            "mode": "ai",
            "purpose": "standalone",
            "power_session_id": None,
            "unit_code": resolved_unit_code,
            "questions": [public_ai_question(item) for item in ai_items],
        }

    params: dict[str, Any] = {
        "unit_id": unit,
        "question_types": effective_types,
        "limit": effective_count,
        "user_id": user.id,
    }

    difficulty_clause = ""
    if effective_difficulty != "auto":
        difficulty_clause = "AND q.difficulty = :difficulty"
        params["difficulty"] = effective_difficulty

    if payload.mode == "adaptive":
        sql = f"""
            SELECT q.*, COALESCE(cm.mastery_score, 0.50) AS learner_mastery,
                   COALESCE(recent.seen_count, 0) AS seen_count
            FROM questions q
            JOIN question_concepts qc ON qc.question_id = q.id AND qc.is_primary = true
            JOIN curriculum_concepts cc ON cc.concept_id = qc.concept_id
            LEFT JOIN concept_mastery cm ON cm.concept_id = qc.concept_id AND cm.user_id = :user_id
            LEFT JOIN (
                SELECT qa.question_id, COUNT(*) AS seen_count
                FROM question_attempts qa
                JOIN practice_attempts pa ON pa.id = qa.practice_attempt_id
                WHERE pa.user_id = :user_id
                  AND qa.created_at > now() - interval '14 days'
                GROUP BY qa.question_id
            ) recent ON recent.question_id = q.id
            WHERE cc.curriculum_unit_id = :unit_id
              AND q.question_type = ANY(:question_types)
              AND q.review_status = 'approved'
              {difficulty_clause}
            ORDER BY learner_mastery ASC, seen_count ASC, random()
            LIMIT :limit
        """
    else:
        sql = f"""
            SELECT q.*, 0.50 AS learner_mastery, 0 AS seen_count
            FROM questions q
            JOIN question_concepts qc ON qc.question_id = q.id AND qc.is_primary = true
            JOIN curriculum_concepts cc ON cc.concept_id = qc.concept_id
            WHERE cc.curriculum_unit_id = :unit_id
              AND q.question_type = ANY(:question_types)
              AND q.review_status = 'approved'
              {difficulty_clause}
            ORDER BY random()
            LIMIT :limit
        """

    rows = db.execute(text(sql), params).mappings().all()
    if not rows:
        raise HTTPException(status_code=422, detail="No matching questions in the current bank")

    set_id = db.execute(
        text(
            """
            INSERT INTO practice_sets(
                user_id, mode, curriculum_unit_id, requested_difficulty, requested_count,
                power_session_id, purpose
            )
            VALUES (:user_id, :mode, :unit_id, :difficulty, :count, :power_session_id, :purpose)
            RETURNING id
            """
        ),
        {
            "user_id": user.id,
            "mode": payload.mode,
            "unit_id": unit,
            "difficulty": effective_difficulty,
            "count": effective_count,
            "power_session_id": payload.power_session_id,
            "purpose": payload.purpose,
        },
    ).scalar_one()

    questions = []
    for idx, row in enumerate(rows, start=1):
        db.execute(
            text(
                "INSERT INTO practice_set_items(practice_set_id, question_id, item_order) "
                "VALUES (:set_id, :qid, :ord)"
            ),
            {"set_id": set_id, "qid": row["id"], "ord": idx},
        )
        options = db.execute(
            text(
                "SELECT option_key, text_vi, text_en FROM question_options "
                "WHERE question_id = :qid ORDER BY option_key"
            ),
            {"qid": row["id"]},
        ).mappings().all()
        questions.append(public_question(row, list(options)))

    db.execute(
        text(
            "INSERT INTO usage_ledger(user_id, feature, quantity, metadata) "
            "VALUES (:user_id, 'practice_set', 1, CAST(:metadata AS jsonb))"
        ),
        {
            "user_id": user.id,
            "metadata": json.dumps(
                {"mode": payload.mode, "count": len(questions), "purpose": payload.purpose}
            ),
        },
    )
    db.commit()
    return {
        "practice_set_id": str(set_id),
        "mode": payload.mode,
        "purpose": payload.purpose,
        "power_session_id": str(payload.power_session_id) if payload.power_session_id else None,
        "unit_code": resolved_unit_code,
        "questions": questions,
    }


def normalize_answer(question_type: str, raw: Any):
    if question_type == "mcq":
        if isinstance(raw, dict):
            return str(raw.get("option", "")).strip().upper()
        return str(raw).strip().upper()
    if question_type == "true_false":
        if isinstance(raw, bool):
            return raw
        if isinstance(raw, dict):
            raw = raw.get("value")
        if isinstance(raw, str):
            return raw.strip().lower() in {"true", "1", "yes", "đúng", "dung"}
        return bool(raw)
    if isinstance(raw, dict):
        raw = raw.get("value", "")
    return str(raw).strip().replace(",", ".")


def _complete_power_evaluate(
    db: Session,
    *,
    user_id: UUID,
    power_session_id: UUID,
    evaluate_state: dict[str, Any],
) -> str:
    owned = db.execute(
        text("""
            SELECT ps.learning_session_id, ps.current_phase
            FROM power_sessions ps
            WHERE ps.id = :id AND ps.user_id = :user_id
        """),
        {"id": power_session_id, "user_id": user_id},
    ).mappings().one_or_none()
    if not owned:
        raise HTTPException(status_code=404, detail="POWER session not found")

    db.execute(
        text("""
            INSERT INTO power_phase_state(power_session_id, phase, state_json, completed_at)
            VALUES (:id, 'EVALUATE', CAST(:state AS jsonb), now())
            ON CONFLICT (power_session_id, phase) DO UPDATE
            SET state_json = EXCLUDED.state_json,
                completed_at = COALESCE(power_phase_state.completed_at, now()),
                updated_at = now()
        """),
        {"id": power_session_id, "state": json.dumps(evaluate_state, ensure_ascii=False)},
    )

    current_phase = owned["current_phase"]
    if current_phase == "EVALUATE":
        current_phase = "RETHINK"
        db.execute(
            text("UPDATE power_sessions SET current_phase = 'RETHINK', updated_at = now() WHERE id = :id"),
            {"id": power_session_id},
        )
        db.execute(
            text("UPDATE learning_sessions SET current_power_phase = 'RETHINK' WHERE id = :id"),
            {"id": owned["learning_session_id"]},
        )
        db.execute(
            text("""
                INSERT INTO power_phase_state(power_session_id, phase, state_json)
                VALUES (:id, 'RETHINK', '{}'::jsonb)
                ON CONFLICT (power_session_id, phase) DO NOTHING
            """),
            {"id": power_session_id},
        )

    db.execute(
        text("""
            INSERT INTO learning_events(user_id, learning_session_id, event_type, payload)
            VALUES (:user_id, :learning_session_id, 'evaluate_completed', CAST(:payload AS jsonb))
        """),
        {
            "user_id": user_id,
            "learning_session_id": owned["learning_session_id"],
            "payload": json.dumps(
                {
                    "accuracy": evaluate_state["accuracy"],
                    "correct": evaluate_state["correct"],
                    "total": evaluate_state["total"],
                    "weak_concepts": evaluate_state["weak_concepts"],
                    "practice_attempt_id": evaluate_state["practice_attempt_id"],
                },
                ensure_ascii=False,
            ),
        },
    )
    return current_phase


@router.post("/practice/{practice_set_id}/submit")
def submit_practice(
    practice_set_id: UUID,
    payload: SubmitPractice,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    practice_set = db.execute(
        text("""
            SELECT id, mode, power_session_id, purpose, generated_items
            FROM practice_sets
            WHERE id = :id AND user_id = :user_id
        """),
        {"id": practice_set_id, "user_id": user.id},
    ).mappings().one_or_none()
    if not practice_set:
        raise HTTPException(status_code=404, detail="Practice set not found")

    if practice_set["mode"] == "ai":
        generated_items = practice_set["generated_items"] or []
        if isinstance(generated_items, str):
            generated_items = json.loads(generated_items)
        item_by_id = {str(item.get("id")): item for item in generated_items}

        attempt_id = db.execute(
            text(
                """
                INSERT INTO practice_attempts(user_id, practice_set_id, started_at)
                VALUES (:user_id, :set_id, now()) RETURNING id
                """
            ),
            {"user_id": user.id, "set_id": practice_set_id},
        ).scalar_one()

        results = []
        correct_total = 0
        stored_answers = []
        for answer in payload.answers:
            item = item_by_id.get(str(answer.question_id))
            if not item:
                continue
            expected = normalize_answer(item["question_type"], item["answer_json"])
            received = normalize_answer(item["question_type"], answer.answer)
            is_correct = received == expected
            correct_total += int(is_correct)
            stored_answers.append(
                {
                    "question_id": str(answer.question_id),
                    "answer": answer.answer,
                    "is_correct": is_correct,
                    "response_time_ms": answer.response_time_ms,
                }
            )
            results.append(
                {
                    "question_id": str(answer.question_id),
                    "is_correct": is_correct,
                    "explanation_vi": item.get("explanation_vi", ""),
                    "explanation_en": item.get("explanation_en", ""),
                    "concept_code": item.get("concept_code"),
                    "concept_name_vi": item.get("concept_name_vi"),
                    "concept_name_en": item.get("concept_name_en"),
                    "mastery": None,
                }
            )

        total = len(results)
        accuracy = correct_total / total if total else 0.0
        db.execute(
            text(
                """
                UPDATE practice_attempts
                SET completed_at = now(), accuracy = :accuracy, response_json = CAST(:response AS jsonb)
                WHERE id = :id
                """
            ),
            {
                "accuracy": accuracy,
                "id": attempt_id,
                "response": json.dumps(
                    {"answers": stored_answers, "mastery_updated": False}, ensure_ascii=False
                ),
            },
        )
        db.execute(
            text(
                """
                INSERT INTO learning_events(user_id, learning_session_id, event_type, payload)
                VALUES (:user_id, NULL, 'practice_completed', CAST(:payload AS jsonb))
                """
            ),
            {
                "user_id": user.id,
                "payload": json.dumps(
                    {
                        "practice_set_id": str(practice_set_id),
                        "practice_attempt_id": str(attempt_id),
                        "accuracy": accuracy,
                        "purpose": "standalone",
                        "mode": "ai",
                        "mastery_updated": False,
                    }
                ),
            },
        )
        db.commit()
        return {
            "accuracy": accuracy,
            "correct": correct_total,
            "total": total,
            "results": results,
            "power": None,
            "mastery_updated": False,
        }

    if practice_set["purpose"] == "evaluate":
        completed_attempt = db.execute(
            text("""
                SELECT id FROM practice_attempts
                WHERE practice_set_id = :set_id AND user_id = :user_id AND completed_at IS NOT NULL
                ORDER BY completed_at DESC LIMIT 1
            """),
            {"set_id": practice_set_id, "user_id": user.id},
        ).scalar_one_or_none()
        if completed_attempt:
            raise HTTPException(status_code=409, detail="This Evaluate practice set has already been submitted")

    allowed = {
        str(x)
        for x in db.execute(
            text("SELECT question_id FROM practice_set_items WHERE practice_set_id = :id"),
            {"id": practice_set_id},
        ).scalars().all()
    }

    attempt_id = db.execute(
        text("""
            INSERT INTO practice_attempts(user_id, practice_set_id, started_at)
            VALUES (:user_id, :set_id, now()) RETURNING id
        """),
        {"user_id": user.id, "set_id": practice_set_id},
    ).scalar_one()

    results = []
    correct_total = 0
    for answer in payload.answers:
        if str(answer.question_id) not in allowed:
            continue

        q = db.execute(
            text("""
                SELECT q.id, q.question_type, q.difficulty, q.answer_json,
                       q.explanation_vi, q.explanation_en,
                       qc.concept_id, c.code AS concept_code,
                       c.name_vi AS concept_name_vi, c.name_en AS concept_name_en
                FROM questions q
                JOIN question_concepts qc ON qc.question_id = q.id AND qc.is_primary = true
                JOIN concepts c ON c.id = qc.concept_id
                WHERE q.id = :qid
            """),
            {"qid": answer.question_id},
        ).mappings().one()

        expected_json = q["answer_json"]
        if isinstance(expected_json, str):
            expected_json = json.loads(expected_json)
        expected = normalize_answer(q["question_type"], expected_json)
        received = normalize_answer(q["question_type"], answer.answer)
        is_correct = received == expected
        correct_total += int(is_correct)

        db.execute(
            text("""
                INSERT INTO question_attempts(
                    practice_attempt_id, question_id, concept_id, answer_json,
                    is_correct, response_time_ms, hint_used, attempt_number
                )
                VALUES (:attempt_id, :qid, :concept_id, CAST(:answer AS jsonb),
                        :correct, :response_time, :hint_used, 1)
            """),
            {
                "attempt_id": attempt_id,
                "qid": q["id"],
                "concept_id": q["concept_id"],
                "answer": json.dumps({"value": answer.answer}, ensure_ascii=False),
                "correct": is_correct,
                "response_time": answer.response_time_ms,
                "hint_used": answer.hint_used,
            },
        )

        mastery = update_mastery(
            db,
            user_id=user.id,
            concept_id=q["concept_id"],
            correct=is_correct,
            difficulty=q["difficulty"],
            hint_used=answer.hint_used,
        )
        results.append(
            {
                "question_id": str(q["id"]),
                "is_correct": is_correct,
                "explanation_vi": q["explanation_vi"],
                "explanation_en": q["explanation_en"],
                "concept_code": q["concept_code"],
                "concept_name_vi": q["concept_name_vi"],
                "concept_name_en": q["concept_name_en"],
                "mastery": mastery,
            }
        )

    total = len(results)
    accuracy = correct_total / total if total else 0.0
    db.execute(
        text("UPDATE practice_attempts SET completed_at = now(), accuracy = :accuracy WHERE id = :id"),
        {"accuracy": accuracy, "id": attempt_id},
    )

    power_payload = None
    learning_session_id = None
    if practice_set["purpose"] == "evaluate" and practice_set["power_session_id"]:
        evaluate_state = summarize_evaluation(
            results,
            practice_set_id=str(practice_set_id),
            practice_attempt_id=str(attempt_id),
        )
        current_phase = _complete_power_evaluate(
            db,
            user_id=user.id,
            power_session_id=practice_set["power_session_id"],
            evaluate_state=evaluate_state,
        )
        learning_session_id = db.execute(
            text("SELECT learning_session_id FROM power_sessions WHERE id = :id"),
            {"id": practice_set["power_session_id"]},
        ).scalar_one()
        power_payload = {
            "session_id": str(practice_set["power_session_id"]),
            "current_phase": current_phase,
            "evaluate": evaluate_state,
        }

    db.execute(
        text("""
            INSERT INTO learning_events(user_id, learning_session_id, event_type, payload)
            VALUES (:user_id, :learning_session_id, 'practice_completed', CAST(:payload AS jsonb))
        """),
        {
            "user_id": user.id,
            "learning_session_id": learning_session_id,
            "payload": json.dumps(
                {
                    "practice_set_id": str(practice_set_id),
                    "practice_attempt_id": str(attempt_id),
                    "accuracy": accuracy,
                    "purpose": practice_set["purpose"],
                }
            ),
        },
    )
    db.commit()
    return {
        "accuracy": accuracy,
        "correct": correct_total,
        "total": total,
        "results": results,
        "power": power_payload,
    }
