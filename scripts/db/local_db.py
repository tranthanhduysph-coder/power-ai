from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API_DIR = ROOT / "apps" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from sqlalchemy import text  # noqa: E402

from app.db.migrate import main as migrate_main  # noqa: E402
from app.db.seed import main as seed_main  # noqa: E402
from app.db.session import engine  # noqa: E402

BACKUP_DIR = ROOT / "local_backups"
DB_NAME = os.getenv("POSTGRES_DB", "power_ai")
DB_USER = os.getenv("POSTGRES_USER", "power_ai")


def _compose(*args: str, input_bytes: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["docker", "compose", *args],
        cwd=ROOT,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def status() -> int:
    proc = _compose("ps")
    sys.stdout.buffer.write(proc.stdout)
    if proc.returncode != 0:
        sys.stderr.buffer.write(proc.stderr)
        return proc.returncode

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            users = conn.execute(text("SELECT count(*) FROM users")).scalar_one()
            sessions = conn.execute(text("SELECT count(*) FROM learning_sessions")).scalar_one()
            ready = conn.execute(
                text("SELECT count(*) FROM curriculum_units WHERE catalog_visible = true AND is_power_ready = true")
            ).scalar_one()
        print(f"database: ok | users={users} | learning_sessions={sessions} | power_ready_units={ready}")
        return 0
    except Exception as exc:
        print(f"database: unavailable | {exc}", file=sys.stderr)
        return 2


def backup(output: Path | None = None) -> int:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    if output is None:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output = BACKUP_DIR / f"power_ai-{stamp}.dump"
    else:
        output = output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)

    proc = _compose("exec", "-T", "db", "pg_dump", "-U", DB_USER, "-d", DB_NAME, "-Fc")
    if proc.returncode != 0:
        sys.stderr.buffer.write(proc.stderr)
        return proc.returncode
    output.write_bytes(proc.stdout)
    print(f"backup: {output}")
    return 0


def reset(confirm: str) -> int:
    if confirm != "RESET-LOCAL":
        print("Refusing destructive reset. Re-run with --confirm RESET-LOCAL", file=sys.stderr)
        return 2

    with engine.begin() as conn:
        conn.exec_driver_sql("DROP EXTENSION IF EXISTS vector CASCADE")
        conn.exec_driver_sql("DROP EXTENSION IF EXISTS pgcrypto CASCADE")
        conn.exec_driver_sql("DROP SCHEMA public CASCADE")
        conn.exec_driver_sql("CREATE SCHEMA public")
        conn.exec_driver_sql("GRANT ALL ON SCHEMA public TO public")

    print("database schema reset")
    migrate_main()
    seed_main()
    print("database reset complete")
    return 0


def restore(path: Path, confirm: str) -> int:
    if confirm != "RESTORE-LOCAL":
        print("Refusing destructive restore. Re-run with --confirm RESTORE-LOCAL", file=sys.stderr)
        return 2
    path = path.resolve()
    if not path.exists():
        print(f"Backup not found: {path}", file=sys.stderr)
        return 2

    payload = path.read_bytes()
    proc = _compose(
        "exec",
        "-T",
        "db",
        "pg_restore",
        "--clean",
        "--if-exists",
        "--no-owner",
        "-U",
        DB_USER,
        "-d",
        DB_NAME,
        input_bytes=payload,
    )
    if proc.returncode != 0:
        sys.stderr.buffer.write(proc.stderr)
        return proc.returncode
    print(f"restored: {path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="POWER AI local PostgreSQL maintenance")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status")

    p_backup = sub.add_parser("backup")
    p_backup.add_argument("--output", type=Path)

    p_reset = sub.add_parser("reset")
    p_reset.add_argument("--confirm", default="")

    p_restore = sub.add_parser("restore")
    p_restore.add_argument("path", type=Path)
    p_restore.add_argument("--confirm", default="")

    args = parser.parse_args()
    if args.command == "status":
        return status()
    if args.command == "backup":
        return backup(args.output)
    if args.command == "reset":
        return reset(args.confirm)
    if args.command == "restore":
        return restore(args.path, args.confirm)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
