from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.release import (
    LOCAL_RELEASE_VERSION,
    REQUIRED_TABLES,
    ReadinessReport,
    migration_gaps,
    readiness_ok,
)
from app.db.session import get_db

router = APIRouter(tags=["health"])


@router.get("/health/live")
def liveness():
    return {"status": "ok", "version": LOCAL_RELEASE_VERSION}


@router.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    vector = db.execute(
        text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
    ).scalar_one_or_none()
    return {
        "status": "ok",
        "version": LOCAL_RELEASE_VERSION,
        "database": "ok",
        "pgvector": vector or "missing",
    }


@router.get("/health/ready")
def readiness(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        vector = db.execute(
            text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
        ).scalar_one_or_none()

        migration_table = db.execute(
            text("SELECT to_regclass('public.schema_migrations')")
        ).scalar_one_or_none()
        applied: list[str] = []
        latest: str | None = None
        if migration_table:
            applied = list(
                db.execute(
                    text("SELECT version FROM schema_migrations ORDER BY version")
                ).scalars().all()
            )
            latest = applied[-1] if applied else None

        existing_tables = set(
            db.execute(
                text(
                    """
                    SELECT tablename
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    """
                )
            ).scalars().all()
        )
        missing_tables = tuple(name for name in REQUIRED_TABLES if name not in existing_tables)
        missing_migrations = migration_gaps(applied)

        ready_units = 0
        if "curriculum_units" in existing_tables:
            ready_units = int(
                db.execute(
                    text(
                        """
                        SELECT count(*)
                        FROM curriculum_units
                        WHERE catalog_visible = true
                          AND is_power_ready = true
                        """
                    )
                ).scalar_one()
            )

        ok = readiness_ok(
            database_ok=True,
            pgvector_present=bool(vector),
            missing_migrations=missing_migrations,
            missing_tables=missing_tables,
            power_ready_units=ready_units,
        )
        report = ReadinessReport(
            ok=ok,
            database="ok",
            pgvector=vector or "missing",
            latest_migration=latest,
            missing_migrations=missing_migrations,
            missing_tables=missing_tables,
            power_ready_units=ready_units,
        )
        if not ok:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=report.as_dict(),
            )
        return report.as_dict()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "version": LOCAL_RELEASE_VERSION,
                "database": "unavailable",
                "reason": str(exc),
            },
        ) from exc
