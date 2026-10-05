from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API_DIR = ROOT / "apps" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from sqlalchemy import text  # noqa: E402

from app.content.power_builder import (  # noqa: E402
    activate_latest_draft,
    generate_power_draft,
    latest_draft,
    load_unit_source_context,
    qa_latest_draft,
    save_draft,
    validate_power_draft,
)
from app.db.session import SessionLocal  # noqa: E402


def _eligible_units(db, *, grade: int | None = None, unit_code: str | None = None) -> list[dict]:
    clauses = [
        "cu.catalog_visible=true",
        "cu.lesson_number IS NOT NULL",
        "cu.unit_type IN ('lesson','practice','project')",
        "cu.content_status='ingested'",
    ]
    params: dict[str, object] = {}
    if grade is not None:
        clauses.append("g.level=:grade")
        params["grade"] = grade
    if unit_code:
        clauses.append("cu.code=:unit_code")
        params["unit_code"] = unit_code
    return [dict(r) for r in db.execute(
        text(
            f"""
            SELECT cu.code,cu.name_vi,cu.name_en,cu.unit_type,cu.lesson_number,
                   cu.content_status,cu.power_status,cu.is_power_ready,g.level AS grade,
                   latest.status AS draft_status, latest.qa_status, latest.version AS draft_version
            FROM curriculum_units cu JOIN grades g ON g.id=cu.grade_id
            LEFT JOIN LATERAL (
                SELECT pbd.status, pbd.qa_status, pbd.version
                FROM power_blueprint_drafts pbd
                WHERE pbd.curriculum_unit_id=cu.id
                ORDER BY pbd.version DESC LIMIT 1
            ) latest ON true
            WHERE {' AND '.join(clauses)}
            ORDER BY g.level,cu.lesson_number
            """
        ),
        params,
    ).mappings().all()]


def _draft_path(unit_code: str) -> Path:
    p = ROOT / "storage" / "generated-power-blueprints" / f"{unit_code}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def cmd_plan(args) -> int:
    db = SessionLocal()
    try:
        rows = _eligible_units(db, grade=args.grade, unit_code=args.unit)
        ready = sum(1 for r in rows if r["is_power_ready"])
        draftish = sum(1 for r in rows if r["power_status"] in {"draft", "validated"})
        print(f"Eligible ingested units: {len(rows)}")
        print(f"Already POWER-ready: {ready}")
        print(f"Draft/validated: {draftish}")
        for row in rows[: args.limit or len(rows)]:
            print(f"- {row['code']} | {row['name_vi']} | content={row['content_status']} | power={row['power_status']} | draft={row.get('draft_status') or '-'} | qa={row.get('qa_status') or '-'}")
        return 0
    finally:
        db.close()


def cmd_generate(args) -> int:
    db = SessionLocal()
    try:
        rows = _eligible_units(db, grade=args.grade, unit_code=args.unit)
    finally:
        db.close()
    if args.force:
        rows = rows
    else:
        rows = [
            r for r in rows
            if not r["is_power_ready"] and (r.get("draft_status") not in {"validated", "activated"})
        ]
    if args.limit:
        rows = rows[: args.limit]
    if not rows:
        print("No eligible units to generate.")
        return 0

    failures = 0
    for row in rows:
        print(f"\n=== {row['code']} · {row['name_vi']} ===")
        db = SessionLocal()
        try:
            context = load_unit_source_context(db, row["code"])
            model, payload = generate_power_draft(context)
            saved = save_draft(
                db,
                unit_code=row["code"],
                model=model,
                payload=payload,
                fingerprint=context.fingerprint,
            )
            db.commit()
            _draft_path(row["code"]).write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            print(f"draft v{saved['version']} status={saved['status']} model={model}")
            if saved["validation"]["errors"]:
                failures += 1
                for err in saved["validation"]["errors"]:
                    print(f"  [ERROR] {err}")
            else:
                print(f"  concepts={len(payload.get('concepts') or [])} questions={len(payload.get('questions') or [])}")
                print(f"  review file: {_draft_path(row['code'])}")
        except Exception as exc:
            db.rollback()
            failures += 1
            print(f"[FAIL] {exc}")
        finally:
            db.close()
    return 1 if failures else 0


def cmd_validate(args) -> int:
    db = SessionLocal()
    try:
        draft = latest_draft(db, args.unit)
        result = validate_power_draft(draft["payload_json"])
        db.execute(
            text(
                """
                UPDATE power_blueprint_drafts SET status=:status,
                    validation_json=CAST(:validation AS jsonb),updated_at=now()
                WHERE id=CAST(:id AS uuid)
                """
            ),
            {
                "id": draft["id"],
                "status": "validated" if result["valid"] else "draft",
                "validation": json.dumps(result, ensure_ascii=False),
            },
        )
        if not draft["is_power_ready"]:
            db.execute(
                text("UPDATE curriculum_units SET power_status=:status WHERE code=:code"),
                {"status": "validated" if result["valid"] else "draft", "code": args.unit},
            )
        db.commit()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["valid"] else 1
    finally:
        db.close()


def cmd_show(args) -> int:
    db = SessionLocal()
    try:
        draft = latest_draft(db, args.unit)
    finally:
        db.close()
    payload = draft["payload_json"]
    print(f"{args.unit} · draft v{draft['version']} · {draft['status']} · model={draft['model']}")
    print(f"concepts={len(payload.get('concepts') or [])} questions={len(payload.get('questions') or [])}")
    print(f"primary={((payload.get('policy') or {}).get('primary_concept_code'))}")
    print(f"validation={json.dumps(draft['validation_json'], ensure_ascii=False)}")
    path = _draft_path(args.unit)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"review file: {path}")
    return 0


def _qa_targets(db, *, grade: int | None = None, unit_code: str | None = None) -> list[dict]:
    rows = _eligible_units(db, grade=grade, unit_code=unit_code)
    return [r for r in rows if r.get("draft_version") is not None and not r["is_power_ready"]]


def cmd_qa(args) -> int:
    db = SessionLocal()
    try:
        rows = _qa_targets(db, grade=args.grade, unit_code=args.unit)
    finally:
        db.close()
    if args.limit:
        rows = rows[: args.limit]
    if not rows:
        print("No generated drafts eligible for QA.")
        return 0
    failed = 0
    for row in rows:
        db = SessionLocal()
        try:
            result = qa_latest_draft(db, row["code"])
            db.commit()
            mark = "PASS" if result["passed"] else "FAIL"
            print(f"[{mark}] {row['code']} · draft v{result['draft_version']} · qa={result['qa_status']}")
            for err in result["errors"]:
                print(f"  [ERROR] {err}")
            for warning in result["warnings"]:
                print(f"  [WARN] {warning}")
            if not result["passed"]:
                failed += 1
        except Exception as exc:
            db.rollback()
            failed += 1
            print(f"[FAIL] {row['code']}: {exc}")
        finally:
            db.close()
    return 1 if failed else 0


def cmd_status(args) -> int:
    db = SessionLocal()
    try:
        rows = _eligible_units(db, grade=args.grade, unit_code=None)
    finally:
        db.close()
    total = len(rows)
    ready = sum(bool(r["is_power_ready"]) for r in rows)
    qa_passed = sum(r.get("qa_status") == "passed" and not r["is_power_ready"] for r in rows)
    validated = sum(r.get("draft_status") == "validated" and r.get("qa_status") != "passed" and not r["is_power_ready"] for r in rows)
    draft = sum(r.get("draft_status") == "draft" and not r["is_power_ready"] for r in rows)
    not_started = sum(r.get("draft_version") is None and not r["is_power_ready"] for r in rows)
    print(f"Eligible ingested units: {total}")
    print(f"POWER-ready: {ready}")
    print(f"QA-passed awaiting activation: {qa_passed}")
    print(f"Validated awaiting QA: {validated}")
    print(f"Draft needs regeneration/fix: {draft}")
    print(f"Not started: {not_started}")
    return 0


def cmd_activate_batch(args) -> int:
    if args.confirm != "ACTIVATE-QA-PASSED":
        print("Refusing batch activation. Re-run with --confirm ACTIVATE-QA-PASSED")
        return 2
    db = SessionLocal()
    try:
        rows = _eligible_units(db, grade=args.grade, unit_code=None)
    finally:
        db.close()
    rows = [r for r in rows if not r["is_power_ready"] and r.get("qa_status") == "passed"]
    if args.limit:
        rows = rows[: args.limit]
    if not rows:
        print("No QA-passed units awaiting activation.")
        return 0
    failed = 0
    for row in rows:
        db = SessionLocal()
        try:
            result = activate_latest_draft(db, row["code"], force=False)
            db.commit()
            print(f"[ACTIVATED] {row['code']} · concepts={result['concepts']} · questions={result['questions']}")
        except Exception as exc:
            db.rollback()
            failed += 1
            print(f"[FAIL] {row['code']}: {exc}")
        finally:
            db.close()
    return 1 if failed else 0


def cmd_activate(args) -> int:
    db = SessionLocal()
    try:
        result = activate_latest_draft(db, args.unit, force=args.force)
        db.commit()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="POWER AI v1.2 source-grounded POWER package builder")
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan")
    plan.add_argument("--grade", type=int, choices=(10, 11, 12))
    plan.add_argument("--unit")
    plan.add_argument("--limit", type=int)
    plan.set_defaults(func=cmd_plan)

    generate = sub.add_parser("generate")
    group = generate.add_mutually_exclusive_group(required=True)
    group.add_argument("--grade", type=int, choices=(10, 11, 12))
    group.add_argument("--unit")
    generate.add_argument("--limit", type=int)
    generate.add_argument("--force", action="store_true")
    generate.set_defaults(func=cmd_generate)

    validate = sub.add_parser("validate")
    validate.add_argument("--unit", required=True)
    validate.set_defaults(func=cmd_validate)

    show = sub.add_parser("show")
    show.add_argument("--unit", required=True)
    show.set_defaults(func=cmd_show)

    qa = sub.add_parser("qa", help="Run deterministic source/currentness QA on generated drafts")
    qgroup = qa.add_mutually_exclusive_group(required=True)
    qgroup.add_argument("--grade", type=int, choices=(10, 11, 12))
    qgroup.add_argument("--unit")
    qa.add_argument("--limit", type=int)
    qa.set_defaults(func=cmd_qa)

    status = sub.add_parser("status", help="Summarize POWER package build state")
    status.add_argument("--grade", type=int, choices=(10, 11, 12))
    status.set_defaults(func=cmd_status)

    batch_activate = sub.add_parser("activate-batch", help="Activate only drafts that passed v1.3 QA")
    batch_activate.add_argument("--grade", type=int, choices=(10, 11, 12), required=True)
    batch_activate.add_argument("--limit", type=int)
    batch_activate.add_argument("--confirm")
    batch_activate.set_defaults(func=cmd_activate_batch)

    activate = sub.add_parser("activate")
    activate.add_argument("--unit", required=True)
    activate.add_argument("--force", action="store_true")
    activate.set_defaults(func=cmd_activate)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
