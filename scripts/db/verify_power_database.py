from sqlalchemy import text

from app.db.session import SessionLocal


def scalar(db, sql: str):
    return db.execute(text(sql)).scalar_one()


def main() -> None:
    db = SessionLocal()
    try:
        print("POWER AI database verification")
        print("------------------------------")
        print("users:", scalar(db, "SELECT count(*) FROM users"))
        print("power_sessions:", scalar(db, "SELECT count(*) FROM power_sessions"))
        print("practice_sets:", scalar(db, "SELECT count(*) FROM practice_sets"))
        print("practice_attempts:", scalar(db, "SELECT count(*) FROM practice_attempts"))
        print("question_attempts:", scalar(db, "SELECT count(*) FROM question_attempts"))
        print("concept_mastery:", scalar(db, "SELECT count(*) FROM concept_mastery"))
        print("source_pages:", scalar(db, "SELECT count(*) FROM source_pages"))
        print("content_chunks:", scalar(db, "SELECT count(*) FROM content_chunks"))
        print("evaluate_sets_linked:", scalar(db, "SELECT count(*) FROM practice_sets WHERE purpose='evaluate' AND power_session_id IS NOT NULL"))
        print("evaluate_phases_completed:", scalar(db, "SELECT count(*) FROM power_phase_state WHERE phase='EVALUATE' AND completed_at IS NOT NULL"))
        print("orphan_evaluate_sets:", scalar(db, "SELECT count(*) FROM practice_sets WHERE purpose='evaluate' AND power_session_id IS NULL"))
        print("rethink_phases_completed:", scalar(db, "SELECT count(*) FROM power_phase_state WHERE phase='RETHINK' AND completed_at IS NOT NULL"))
        print("learner_misconceptions_active:", scalar(db, "SELECT count(*) FROM learner_misconceptions WHERE status='active'"))
        print("misconception_evidence:", scalar(db, "SELECT count(*) FROM misconception_evidence"))
        print("pending_recommendations:", scalar(db, "SELECT count(*) FROM learning_recommendations WHERE status='pending'"))
        vector = db.execute(text("SELECT extversion FROM pg_extension WHERE extname='vector'")).scalar_one_or_none()
        print("pgvector:", vector or "missing")
        print("OK")
    finally:
        db.close()


if __name__ == "__main__":
    main()
