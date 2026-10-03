from pathlib import Path

from sqlalchemy import text

from app.db.session import engine
from app.db.sql_utils import split_sql_statements


def migration_dir() -> Path:
    container = Path("/app/database/migrations")
    if container.exists():
        return container
    return Path(__file__).resolve().parents[4] / "database" / "migrations"


def main() -> None:
    migrations = sorted(migration_dir().glob("*.sql"))
    if not migrations:
        raise RuntimeError("No database migrations found")

    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """))

    for path in migrations:
        version = path.stem
        with engine.begin() as conn:
            applied = conn.execute(
                text("SELECT 1 FROM schema_migrations WHERE version = :version"),
                {"version": version},
            ).scalar_one_or_none()
            if applied:
                print(f"skip migration {version}")
                continue

            sql = path.read_text(encoding="utf-8")
            for statement in split_sql_statements(sql):
                conn.exec_driver_sql(statement)
            conn.execute(
                text("INSERT INTO schema_migrations(version) VALUES (:version)"),
                {"version": version},
            )
            print(f"applied migration {version}")


if __name__ == "__main__":
    main()
