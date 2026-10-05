from __future__ import annotations

from dataclasses import dataclass

LATEST_MIGRATION = "012_power_blueprint_drafts"
REQUIRED_MIGRATIONS = (
    "001_initial",
    "002_knowledge_ingestion",
    "003_direct_pdf_vision",
    "004_power_evaluate_link",
    "005_rethink_learning_model",
    "006_curriculum_generalization",
    "007_active_cycle_integrity",
    "008_content_build_status",
    "009_content_status_reconciliation",
    "010_content_status_mapping_reconciliation",
    "011_content_status_strict_page_evidence",
    "012_power_blueprint_drafts",
)
REQUIRED_TABLES = (
    "users",
    "curriculum_units",
    "power_sessions",
    "power_phase_state",
    "practice_sets",
    "practice_attempts",
    "question_attempts",
    "concept_mastery",
    "learning_recommendations",
    "source_pages",
    "content_chunks",
    "power_unit_blueprints",
    "power_blueprint_drafts",
)
LOCAL_RELEASE_VERSION = "1.2.0-content-local"


@dataclass(frozen=True)
class ReadinessReport:
    ok: bool
    database: str
    pgvector: str
    latest_migration: str | None
    missing_migrations: tuple[str, ...]
    missing_tables: tuple[str, ...]
    power_ready_units: int

    def as_dict(self) -> dict[str, object]:
        return {
            "status": "ready" if self.ok else "not_ready",
            "version": LOCAL_RELEASE_VERSION,
            "database": self.database,
            "pgvector": self.pgvector,
            "latest_migration": self.latest_migration,
            "missing_migrations": list(self.missing_migrations),
            "missing_tables": list(self.missing_tables),
            "power_ready_units": self.power_ready_units,
        }


def migration_gaps(applied: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    applied_set = set(applied)
    return tuple(version for version in REQUIRED_MIGRATIONS if version not in applied_set)


def readiness_ok(
    *,
    database_ok: bool,
    pgvector_present: bool,
    missing_migrations: tuple[str, ...],
    missing_tables: tuple[str, ...],
    power_ready_units: int,
) -> bool:
    return (
        database_ok
        and pgvector_present
        and not missing_migrations
        and not missing_tables
        and power_ready_units > 0
    )
