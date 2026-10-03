from pathlib import Path

from app.db.session import engine
from app.db.sql_utils import split_sql_statements


def seed_dir() -> Path:
    container = Path("/app/database/seeds")
    if container.exists():
        return container
    return Path(__file__).resolve().parents[4] / "database" / "seeds"


def main() -> None:
    seeds = sorted(seed_dir().glob("*.sql"))
    if not seeds:
        print("no seed files")
        return

    for path in seeds:
        sql = path.read_text(encoding="utf-8")
        with engine.begin() as conn:
            for statement in split_sql_statements(sql):
                conn.exec_driver_sql(statement)
        print(f"applied seed {path.stem}")


if __name__ == "__main__":
    main()
