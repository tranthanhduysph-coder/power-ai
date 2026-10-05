from __future__ import annotations

import importlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
API_ROOT = ROOT / "apps" / "api"
WEB_ROOT = ROOT / "apps" / "web"
AUDIT = ROOT / "scripts" / "content" / "audit_power_curriculum.py"
REPORT_DIR = ROOT / "storage" / "release-reports"
REPORT_JSON = REPORT_DIR / "power_ai_local_release_v1_7.json"
COMPLETE_FLAG = ROOT / "LOCAL_BUILD_COMPLETE.txt"

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

report: dict[str, Any] = {
    "release": "POWER AI local v1.7",
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "repo_root": str(ROOT),
    "checks": {},
    "warnings": [],
    "errors": [],
}

CORE_TABLES = [
    "curriculum_units",
    "learning_sessions",
    "learning_events",
    "power_phase_state",
    "practice_sets",
    "practice_attempts",
    "question_attempts",
    "concept_mastery",
    "learner_misconceptions",
    "misconception_evidence",
]


def log(s: str = "") -> None:
    print(s, flush=True)


def err(s: str) -> None:
    report["errors"].append(s)
    log(f"[ERROR] {s}")


def warn(s: str) -> None:
    report["warnings"].append(s)
    log(f"[WARN] {s}")


def env_utf8() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = "apps\\api" if os.name == "nt" else "apps/api"
    return env


def run(args: list[str], *, cwd: Path = ROOT) -> tuple[int, str]:
    p = subprocess.run(
        args,
        cwd=cwd,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        env=env_utf8(),
    )
    out = (p.stdout or "") + (p.stderr or "")
    if out:
        print(out, end="" if out.endswith("\n") else "\n", flush=True)
    return p.returncode, out


def open_db_session():
    from sqlalchemy.orm import Session
    from sqlalchemy.engine import Engine

    modules = (
        "app.db.session",
        "app.db.database",
        "app.database",
        "app.core.database",
        "app.core.db",
        "app.db",
    )
    factories = ("SessionLocal", "SessionFactory", "SessionMaker", "session_factory")
    engines = ("engine", "sync_engine", "db_engine")

    for module_name in modules:
        try:
            mod = importlib.import_module(module_name)
        except Exception:
            continue
        for name in factories:
            obj = getattr(mod, name, None)
            if callable(obj):
                try:
                    db = obj()
                    if hasattr(db, "execute") and hasattr(db, "close"):
                        return db
                except Exception:
                    pass
        for name in engines:
            obj = getattr(mod, name, None)
            if isinstance(obj, Engine):
                return Session(obj)

    from app.core.config import get_settings
    from sqlalchemy import create_engine

    settings = get_settings()
    values = settings.model_dump() if hasattr(settings, "model_dump") else vars(settings)
    url = None
    for key in (
        "database_url", "db_url", "sqlalchemy_database_uri",
        "postgres_url", "postgresql_url",
    ):
        if values.get(key):
            url = values[key]
            break
    if url is None:
        for key, value in values.items():
            k = str(key).lower()
            if value and ("database" in k or "postgres" in k) and ("url" in k or "uri" in k):
                url = value
                break
    if url is None:
        raise RuntimeError("Could not discover database connection.")
    return Session(create_engine(str(url)))


def inspect_routes() -> dict[str, Any]:
    from app.main import app

    spec = app.openapi()
    operations = []
    for path, item in (spec.get("paths") or {}).items():
        if not isinstance(item, dict):
            continue
        for method, op in item.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                continue
            if not isinstance(op, dict):
                continue
            operations.append({
                "method": method.upper(),
                "path": path,
                "operation_id": str(op.get("operationId") or ""),
                "summary": str(op.get("summary") or ""),
                "tags": [str(x) for x in (op.get("tags") or [])],
            })

    def hay(op):
        return " ".join([
            op["path"], op["operation_id"], op["summary"], " ".join(op["tags"])
        ]).lower()

    direct = {
        phase: [op for op in operations if phase in hay(op)]
        for phase in ("prepare", "organize", "work", "rethink")
    }

    # Evaluate is intentionally practice-backed in the current architecture.
    evaluate_service = False
    practice_module = False
    practice_write_routes = []
    try:
        importlib.import_module("app.services.evaluate")
        evaluate_service = True
    except Exception:
        pass
    try:
        mod = importlib.import_module("app.api.practice")
        practice_module = True
        router = getattr(mod, "router", None)
        for route in getattr(router, "routes", []) if router else []:
            for method in sorted(getattr(route, "methods", set()) or set()):
                if method.upper() in {"POST", "PUT", "PATCH"}:
                    practice_write_routes.append({
                        "method": method.upper(),
                        "path": str(getattr(route, "path", "") or ""),
                        "name": str(getattr(route, "name", "") or ""),
                    })
    except Exception:
        pass

    return {
        "operation_count": len(operations),
        "direct_phase_routes": direct,
        "evaluate_service_importable": evaluate_service,
        "practice_module_importable": practice_module,
        "practice_write_routes": practice_write_routes,
    }


def inspect_db() -> dict[str, Any]:
    from sqlalchemy import inspect, text

    db = open_db_session()
    result: dict[str, Any] = {"tables": {}, "foreign_key_orphans": []}
    try:
        insp = inspect(db.get_bind())
        tables = set(insp.get_table_names())

        for table in CORE_TABLES:
            if table not in tables:
                err(f"Missing required table: {table}")
                continue
            cols = [c["name"] for c in insp.get_columns(table)]
            count = int(db.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar_one())
            result["tables"][table] = {"columns": cols, "row_count": count}

        # All learnable Biology units must be ready.
        if "curriculum_units" in tables:
            ready = db.execute(text("""
                SELECT
                    COUNT(*) FILTER (WHERE lesson_number IS NOT NULL) AS learnable,
                    COUNT(*) FILTER (
                        WHERE lesson_number IS NOT NULL
                          AND is_power_ready=true
                          AND power_status='ready'
                    ) AS ready
                FROM curriculum_units
                WHERE catalog_visible=true
            """)).mappings().one()
            result["curriculum_readiness"] = {
                "learnable": int(ready["learnable"] or 0),
                "ready": int(ready["ready"] or 0),
            }
            if int(ready["learnable"] or 0) != 90 or int(ready["ready"] or 0) != 90:
                err(
                    f"Curriculum DB readiness mismatch: "
                    f"{ready['ready']}/{ready['learnable']} ready, expected 90/90"
                )

        # Generic orphan check on learner-state tables.
        learner_tables = [t for t in CORE_TABLES if t in tables and t != "curriculum_units"]
        for table in learner_tables:
            for fk in insp.get_foreign_keys(table):
                cc = fk.get("constrained_columns") or []
                rc = fk.get("referred_columns") or []
                rt = fk.get("referred_table")
                if len(cc) != 1 or len(rc) != 1 or not rt:
                    continue
                col, rcol = cc[0], rc[0]
                n = int(db.execute(text(
                    f'SELECT COUNT(*) FROM "{table}" c '
                    f'LEFT JOIN "{rt}" p ON c."{col}"=p."{rcol}" '
                    f'WHERE c."{col}" IS NOT NULL AND p."{rcol}" IS NULL'
                )).scalar_one())
                result["foreign_key_orphans"].append({
                    "table": table,
                    "column": col,
                    "referred_table": rt,
                    "orphans": n,
                })
                if n:
                    err(f"{table}.{col} has {n} orphan row(s)")

        # Duplicate phase-state guard.
        if "power_phase_state" in tables:
            cols = {c["name"] for c in insp.get_columns("power_phase_state")}
            session_col = next((c for c in ("learning_session_id", "session_id") if c in cols), None)
            phase_col = next((c for c in ("phase", "phase_code") if c in cols), None)
            if session_col and phase_col:
                dup = int(db.execute(text(
                    f'SELECT COUNT(*) FROM ('
                    f'SELECT "{session_col}", "{phase_col}", COUNT(*) '
                    f'FROM "power_phase_state" '
                    f'GROUP BY "{session_col}", "{phase_col}" '
                    f'HAVING COUNT(*)>1'
                    f') x'
                )).scalar_one())
                result["duplicate_phase_state_groups"] = dup
                if dup:
                    err(f"power_phase_state has {dup} duplicate session+phase group(s)")

        # Append-only trigger is hardening, not a release blocker.
        if "learning_events" in tables:
            try:
                triggers = list(db.execute(text("""
                    SELECT tgname
                    FROM pg_trigger
                    WHERE tgrelid='learning_events'::regclass
                      AND NOT tgisinternal
                    ORDER BY tgname
                """)).scalars().all())
                result["learning_events_custom_triggers"] = triggers
                if not triggers:
                    warn(
                        "learning_events has no custom append-only DB trigger; "
                        "retain this as post-v1.7 hardening if application permissions are the current guard."
                    )
            except Exception as ex:
                warn(f"Could not inspect learning_events triggers: {ex}")

        return result
    finally:
        db.close()


def save_report() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def main() -> int:
    log("=== POWER AI v1.7 LOCAL RELEASE FINALIZER ===")
    log("No content regeneration. No learner-data mutation.\n")

    # 1. Content audit: blocking failures only.
    log("=== 1. CURRICULUM 90/90 ===")
    rc, out = run([sys.executable, str(AUDIT), "--grade", "all"])
    ok = rc == 0 and "PASS=90 FAIL=0" in out and "[FAIL]" not in out
    report["checks"]["curriculum_audit"] = {"passed": ok, "returncode": rc}
    if not ok:
        err("Curriculum is not 90/90 PASS.")

    # Strict warnings remain visible, but are not falsely converted into blocking content failures.
    log("\n=== 2. STRICT WARNING REVIEW ===")
    rc, out = run([sys.executable, str(AUDIT), "--grade", "all", "--strict-warnings"])
    m = re.findall(r"warning-units=(\d+)", out)
    warning_units = int(m[-1]) if m else None
    report["checks"]["strict_warning_review"] = {
        "returncode": rc,
        "warning_units": warning_units,
    }
    if warning_units:
        warn(f"Curriculum has {warning_units} warning-unit(s); 90/90 blocking audit still passes.")

    # 3. Full API tests.
    log("\n=== 3. FULL BACKEND TESTS ===")
    rc, out = run([sys.executable, "-m", "pytest", "apps/api/tests", "-q"])
    report["checks"]["backend_tests"] = {"passed": rc == 0, "returncode": rc}
    if rc != 0:
        err("Backend test suite failed.")

    # 4. Import/openapi + POWER capabilities.
    log("\n=== 4. POWER API CONTRACT ===")
    try:
        routes = inspect_routes()
        report["checks"]["routes"] = routes
        log(f"FastAPI operations: {routes['operation_count']}")
        for phase in ("prepare", "organize", "work", "rethink"):
            n = len(routes["direct_phase_routes"][phase])
            log(f"  {phase}: {n} direct route(s)")
            if n == 0:
                err(f"Missing POWER {phase} route.")

        eval_ok = (
            routes["evaluate_service_importable"]
            and routes["practice_module_importable"]
            and len(routes["practice_write_routes"]) > 0
        )
        log(
            "  evaluate: practice-backed "
            f"(service={routes['evaluate_service_importable']}, "
            f"practice={routes['practice_module_importable']}, "
            f"write_routes={len(routes['practice_write_routes'])})"
        )
        if not eval_ok:
            err("Practice-backed Evaluate capability is incomplete.")
    except Exception as ex:
        err(f"API contract inspection failed: {ex}")

    # 5. DB integrity/readiness.
    log("\n=== 5. DATABASE RELEASE INTEGRITY ===")
    try:
        dbinfo = inspect_db()
        report["checks"]["database"] = dbinfo
        for table, meta in dbinfo["tables"].items():
            log(f"  {table}: rows={meta['row_count']}")
        readiness = dbinfo.get("curriculum_readiness") or {}
        if readiness:
            log(f"  curriculum ready: {readiness.get('ready')}/{readiness.get('learnable')}")
        orphan_total = sum(x["orphans"] for x in dbinfo["foreign_key_orphans"])
        log(f"  FK orphan rows: {orphan_total}")
    except Exception as ex:
        err(f"Database release integrity check failed: {ex}")

    # 6. Frontend production build.
    log("\n=== 6. NEXT.JS PRODUCTION BUILD ===")
    npm = "npm.cmd" if os.name == "nt" else "npm"
    rc, out = run([npm, "run", "build"], cwd=WEB_ROOT)
    report["checks"]["frontend_build"] = {"passed": rc == 0, "returncode": rc}
    if rc != 0:
        err("Next.js production build failed.")

    # 7. Final artifact state.
    save_report()

    log("\n=== v1.7 RELEASE SUMMARY ===")
    log(f"Errors  : {len(report['errors'])}")
    log(f"Warnings: {len(report['warnings'])}")
    log(f"Report  : {REPORT_JSON}")

    if report["errors"]:
        if COMPLETE_FLAG.exists():
            COMPLETE_FLAG.unlink()
        log("\nBlocking errors:")
        for item in report["errors"]:
            log(f"  - {item}")
        log("\n[STOP] Local build is NOT release-complete.")
        return 1

    COMPLETE_FLAG.write_text(
        "\n".join([
            "POWER AI LOCAL BUILD COMPLETE",
            "Release: v1.7",
            f"Completed UTC: {datetime.now(timezone.utc).isoformat()}",
            "Curriculum: 90/90 PASS",
            "Backend tests: PASS",
            "POWER API contract: PASS",
            "Database release integrity: PASS",
            "Next.js production build: PASS",
            f"Advisory warnings: {len(report['warnings'])}",
            f"Report: {REPORT_JSON}",
            "",
        ]),
        encoding="utf-8",
    )

    if report["warnings"]:
        log("\nAdvisory only:")
        for item in report["warnings"]:
            log(f"  - {item}")

    log("\n[DONE] POWER AI local build is release-complete.")
    log(f"[FLAG] {COMPLETE_FLAG}")
    log("[NEXT] Freeze local v1.7; then run live browser/auth E2E as a separate release-validation stage.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
