from app.core.release import (
    REQUIRED_MIGRATIONS,
    REQUIRED_TABLES,
    ReadinessReport,
    migration_gaps,
    readiness_ok,
)


def test_migration_gaps_reports_only_missing_versions():
    applied = list(REQUIRED_MIGRATIONS[:-1])
    assert migration_gaps(applied) == (REQUIRED_MIGRATIONS[-1],)


def test_readiness_requires_research_schema_before_release():
    before_research = tuple(v for v in REQUIRED_MIGRATIONS if v != "015_research_analytics")
    assert migration_gaps(before_research) == ("015_research_analytics",)
    assert {"research_consent", "research_consent_audit", "research_export_audit"} <= set(REQUIRED_TABLES)


def test_readiness_requires_database_vector_schema_and_ready_unit():
    assert readiness_ok(
        database_ok=True,
        pgvector_present=True,
        missing_migrations=(),
        missing_tables=(),
        power_ready_units=1,
    )
    assert not readiness_ok(
        database_ok=True,
        pgvector_present=True,
        missing_migrations=(),
        missing_tables=(),
        power_ready_units=0,
    )


def test_readiness_report_serializes_stable_contract():
    report = ReadinessReport(
        ok=False,
        database="ok",
        pgvector="0.8.0",
        latest_migration="006_curriculum_generalization",
        missing_migrations=("007_active_cycle_integrity",),
        missing_tables=("power_unit_blueprints",),
        power_ready_units=0,
    ).as_dict()
    assert report["status"] == "not_ready"
    assert report["missing_migrations"] == ["007_active_cycle_integrity"]
    assert report["missing_tables"] == ["power_unit_blueprints"]
