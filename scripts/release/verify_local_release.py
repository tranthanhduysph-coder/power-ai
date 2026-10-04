from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API_DIR = ROOT / "apps" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from sqlalchemy import text  # noqa: E402

from app.core.release import REQUIRED_MIGRATIONS, REQUIRED_TABLES  # noqa: E402
from app.db.session import engine  # noqa: E402

EXPECTED_CATALOG_ITEMS = {10: 26, 11: 29, 12: 35}


def check(label: str, ok: bool, detail: str) -> bool:
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {label}: {detail}")
    return ok


def main() -> int:
    passed = True
    with engine.connect() as conn:
        vector = conn.execute(text("SELECT extversion FROM pg_extension WHERE extname='vector'")) .scalar_one_or_none()
        passed &= check("pgvector", bool(vector), vector or "missing")

        applied = set(conn.execute(text("SELECT version FROM schema_migrations")).scalars().all())
        missing_migrations = [m for m in REQUIRED_MIGRATIONS if m not in applied]
        passed &= check("migrations", not missing_migrations, "complete" if not missing_migrations else f"missing {missing_migrations}")

        tables = set(conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public'")).scalars().all())
        missing_tables = [t for t in REQUIRED_TABLES if t not in tables]
        passed &= check("tables", not missing_tables, "complete" if not missing_tables else f"missing {missing_tables}")

        lesson_rows = conn.execute(text("""
            SELECT g.level, count(*)
            FROM curriculum_units cu
            JOIN grades g ON g.id=cu.grade_id
            WHERE cu.catalog_visible=true
              AND cu.lesson_number IS NOT NULL
              AND cu.unit_type IN ('lesson','practice','project')
            GROUP BY g.level
            ORDER BY g.level
        """)).all()
        actual_lessons = {int(level): int(count) for level, count in lesson_rows}
        for grade, expected in EXPECTED_CATALOG_ITEMS.items():
            actual = actual_lessons.get(grade, 0)
            passed &= check(f"Biology {grade} catalog", actual == expected, f"{actual}/{expected} numbered units")

        ready = int(conn.execute(text("SELECT count(*) FROM curriculum_units WHERE catalog_visible=true AND is_power_ready=true")).scalar_one())
        passed &= check("POWER-ready units", ready >= 1, str(ready))

        dna_blueprint = int(conn.execute(text("""
            SELECT count(*) FROM power_unit_blueprints pub
            JOIN curriculum_units cu ON cu.id=pub.curriculum_unit_id
            WHERE cu.code='B12_DNA_REPLICATION'
        """)).scalar_one())
        passed &= check("DNA POWER blueprint", dna_blueprint == 1, str(dna_blueprint))

        orphan_eval = int(conn.execute(text("""
            SELECT count(*)
            FROM practice_sets ps
            WHERE ps.purpose='evaluate' AND ps.power_session_id IS NULL
        """)).scalar_one())
        passed &= check("Evaluate linkage", orphan_eval == 0, f"orphan sets={orphan_eval}")

        duplicate_active = int(conn.execute(text("""
            SELECT count(*) FROM (
              SELECT user_id, curriculum_unit_id
              FROM learning_sessions
              WHERE status='active'
              GROUP BY user_id, curriculum_unit_id
              HAVING count(*) > 1
            ) x
        """)).scalar_one())
        passed &= check("Active cycle uniqueness", duplicate_active == 0, f"duplicates={duplicate_active}")

    print("\nPOWER AI v1.0 local verification:", "READY" if passed else "NOT READY")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
