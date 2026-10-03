from typing import Any, Literal
from uuid import UUID
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, get_current_user
from app.db.session import get_db
from app.services.mastery import update_mastery

router = APIRouter(tags=["practice"])


class GeneratePractice(BaseModel):
    mode: Literal["custom", "adaptive"] = "custom"
    unit_code: str = "B10_DNA_REPLICATION"
    difficulty: Literal["auto", "easy", "medium", "hard"] = "auto"
    question_types: list[Literal["mcq", "true_false", "short_answer"]] = Field(
        default_factory=lambda: ["mcq", "true_false", "short_answer"]
    )
    question_count: int = Field(default=6, ge=3, le=20)


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


@router.post("/practice/generate")
def generate_practice(
    payload: GeneratePractice,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    unit = db.execute(
        text("SELECT id FROM curriculum_units WHERE code = :code"), {"code": payload.unit_code}
    ).scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=404, detail="Curriculum unit not found")

    params: dict[str, Any] = {
        "unit_id": unit,
        "question_types": payload.question_types,
        "limit": payload.question_count,
        "user_id": user.id,
    }

    difficulty_clause = ""
    if payload.difficulty != "auto":
        difficulty_clause = "AND q.difficulty = :difficulty"
        params["difficulty"] = payload.difficulty

    if payload.mode == "adaptive":
        # Prefer questions mapped to the learner's weakest concepts. Recent exposure is penalized.
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
        text("""
            INSERT INTO practice_sets(user_id, mode, curriculum_unit_id, requested_difficulty, requested_count)
            VALUES (:user_id, :mode, :unit_id, :difficulty, :count)
            RETURNING id
        """),
        {
            "user_id": user.id,
            "mode": payload.mode,
            "unit_id": unit,
            "difficulty": payload.difficulty,
            "count": payload.question_count,
        },
    ).scalar_one()

    questions = []
    for idx, row in enumerate(rows, start=1):
        db.execute(
            text("INSERT INTO practice_set_items(practice_set_id, question_id, item_order) VALUES (:set_id, :qid, :ord)"),
            {"set_id": set_id, "qid": row["id"], "ord": idx},
        )
        options = db.execute(
            text("SELECT option_key, text_vi, text_en FROM question_options WHERE question_id = :qid ORDER BY option_key"),
            {"qid": row["id"]},
        ).mappings().all()
        questions.append(public_question(row, list(options)))

    db.execute(
        text("INSERT INTO usage_ledger(user_id, feature, quantity, metadata) VALUES (:user_id, 'practice_set', 1, CAST(:metadata AS jsonb))"),
        {
            "user_id": user.id,
            "metadata": json.dumps({"mode": payload.mode, "count": len(questions)}),
        },
    )
    db.commit()
    return {"practice_set_id": str(set_id), "mode": payload.mode, "questions": questions}


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


@router.post("/practice/{practice_set_id}/submit")
def submit_practice(
    practice_set_id: UUID,
    payload: SubmitPractice,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    owned = db.execute(
        text("SELECT id FROM practice_sets WHERE id = :id AND user_id = :user_id"),
        {"id": practice_set_id, "user_id": user.id},
    ).scalar_one_or_none()
    if not owned:
        raise HTTPException(status_code=404, detail="Practice set not found")

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
                       qc.concept_id
                FROM questions q
                JOIN question_concepts qc ON qc.question_id = q.id AND qc.is_primary = true
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
                "mastery": mastery,
            }
        )

    total = len(results)
    accuracy = correct_total / total if total else 0.0
    db.execute(
        text("UPDATE practice_attempts SET completed_at = now(), accuracy = :accuracy WHERE id = :id"),
        {"accuracy": accuracy, "id": attempt_id},
    )
    db.execute(
        text("""
            INSERT INTO learning_events(user_id, event_type, payload)
            VALUES (:user_id, 'practice_completed', CAST(:payload AS jsonb))
        """),
        {
            "user_id": user.id,
            "payload": json.dumps({"practice_set_id": str(practice_set_id), "accuracy": accuracy}),
        },
    )
    db.commit()
    return {"accuracy": accuracy, "correct": correct_total, "total": total, "results": results}
