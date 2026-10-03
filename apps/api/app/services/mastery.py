from decimal import Decimal
from sqlalchemy import text
from sqlalchemy.orm import Session


DIFFICULTY_WEIGHT = {
    "easy": Decimal("0.80"),
    "medium": Decimal("1.00"),
    "hard": Decimal("1.20"),
}


def update_mastery(
    db: Session,
    *,
    user_id,
    concept_id,
    correct: bool,
    difficulty: str,
    hint_used: bool,
) -> float:
    current = db.execute(
        text("""
            SELECT mastery_score, attempt_count, correct_count
            FROM concept_mastery
            WHERE user_id = :user_id AND concept_id = :concept_id
        """),
        {"user_id": user_id, "concept_id": concept_id},
    ).mappings().one_or_none()

    old = Decimal(str(current["mastery_score"])) if current else Decimal("0.50")
    weight = DIFFICULTY_WEIGHT.get(difficulty, Decimal("1.00"))
    if hint_used:
        weight *= Decimal("0.85")

    alpha = min(Decimal("0.18"), Decimal("0.12") * weight)
    target = Decimal("1") if correct else Decimal("0")
    new = old + alpha * (target - old)
    new = max(Decimal("0"), min(Decimal("1"), new))

    db.execute(
        text("""
            INSERT INTO concept_mastery(
                user_id, concept_id, mastery_score, confidence,
                attempt_count, correct_count, last_practiced_at, updated_at
            )
            VALUES (
                :user_id, :concept_id, :mastery, 0.50,
                1, :correct_count, now(), now()
            )
            ON CONFLICT (user_id, concept_id) DO UPDATE
            SET mastery_score = :mastery,
                attempt_count = concept_mastery.attempt_count + 1,
                correct_count = concept_mastery.correct_count + :correct_count,
                last_practiced_at = now(),
                updated_at = now()
        """),
        {
            "user_id": user_id,
            "concept_id": concept_id,
            "mastery": float(new),
            "correct_count": 1 if correct else 0,
        },
    )
    return float(new)
