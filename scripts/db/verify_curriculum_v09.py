from sqlalchemy import text

from app.db.session import SessionLocal


def main() -> None:
    db = SessionLocal()
    try:
        rows = db.execute(
            text("""
                SELECT g.level AS grade,
                       count(*) FILTER (WHERE cu.unit_type IN ('lesson','practice','project') AND cu.catalog_visible) AS lessons,
                       count(*) FILTER (WHERE cu.is_power_ready AND cu.catalog_visible) AS power_ready
                FROM grades g
                LEFT JOIN curriculum_units cu ON cu.grade_id = g.id
                JOIN subjects s ON s.id = g.subject_id
                WHERE s.code = 'BIOLOGY' AND g.level IN (10,11,12)
                GROUP BY g.level
                ORDER BY g.level
            """)
        ).mappings().all()
        print("POWER AI v0.9 curriculum verification")
        print("----------------------------------")
        for row in rows:
            print(f"Biology {row['grade']}: lessons={row['lessons']} power_ready={row['power_ready']}")

        blueprint = db.execute(
            text("""
                SELECT cu.code, cu.is_power_ready, pub.version,
                       jsonb_array_length(pub.prepare_json->'diagnostic_items') AS diagnostic_items,
                       jsonb_array_length(pub.work_json->'vi'->'tasks') AS work_tasks
                FROM curriculum_units cu
                LEFT JOIN power_unit_blueprints pub ON pub.curriculum_unit_id = cu.id
                WHERE cu.code='B12_DNA_REPLICATION'
            """)
        ).mappings().one_or_none()
        print("DNA blueprint:", dict(blueprint) if blueprint else None)

        source_map = db.execute(
            text("""
                SELECT s.code, cus.printed_page_start, cus.printed_page_end,
                       cus.pdf_page_start, cus.pdf_page_end
                FROM curriculum_unit_sources cus
                JOIN curriculum_units cu ON cu.id = cus.curriculum_unit_id
                JOIN sources s ON s.id = cus.source_id
                WHERE cu.code='B12_DNA_REPLICATION'
                ORDER BY cus.source_role
            """)
        ).mappings().all()
        print("DNA source mapping:", [dict(r) for r in source_map])

        hidden_legacy = db.execute(
            text("SELECT count(*) FROM curriculum_units WHERE code IN ('B10_NUCLEIC_ACIDS','B10_DNA_REPLICATION') AND catalog_visible=false")
        ).scalar_one()
        print("legacy_demo_units_hidden:", hidden_legacy)

        expected = {10: 26, 11: 29, 12: 35}
        actual = {int(r['grade']): int(r['lessons']) for r in rows}
        problems = [f"Biology {grade}: expected {count}, got {actual.get(grade)}" for grade, count in expected.items() if actual.get(grade) != count]
        if not blueprint or not blueprint['is_power_ready'] or blueprint['version'] is None:
            problems.append('B12_DNA_REPLICATION blueprint missing or not POWER-ready')
        if not source_map:
            problems.append('B12_DNA_REPLICATION source mapping missing')
        if problems:
            print("FAILED")
            for problem in problems:
                print("-", problem)
            raise SystemExit(1)
        print("OK")
    finally:
        db.close()


if __name__ == '__main__':
    main()
