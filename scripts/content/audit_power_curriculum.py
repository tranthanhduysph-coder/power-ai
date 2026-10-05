from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from sqlalchemy import inspect, text
from sqlalchemy.exc import SAWarning
import warnings
from app.db.session import SessionLocal

REPO_ROOT = Path(__file__).resolve().parents[2]
BLUEPRINT_DIR = REPO_ROOT / "storage" / "generated-power-blueprints"
REPORT_DIR = REPO_ROOT / "storage" / "audit-reports"
EXPECTED_GRADE_TOTALS = {10: 26, 11: 29, 12: 35}


def norm_code(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().upper().replace("_", ".")


def boolish(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        s = value.strip().lower()
        if s in {"true", "1", "yes", "y", "đúng", "dung"}:
            return True
        if s in {"false", "0", "no", "n", "sai"}:
            return False
    return None


def get_tables_and_columns(db):
    insp = inspect(db.bind)
    tables = set(insp.get_table_names())

    # pgvector columns can trigger a harmless SQLAlchemy reflection warning.
    # The audit only needs column names, so suppress that warning here.
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="Did not recognize type 'vector'.*",
            category=SAWarning,
        )
        columns = {
            table: {c["name"] for c in insp.get_columns(table)}
            for table in tables
        }
    return tables, columns


def first_existing(cols: set[str], candidates: list[str]) -> str | None:
    for name in candidates:
        if name in cols:
            return name
    return None


def find_nested(obj: Any, key: str) -> Any:
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for value in obj.values():
            found = find_nested(value, key)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = find_nested(value, key)
            if found is not None:
                return found
    return None


def pick_payload(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {}
    candidates = [raw]
    for key in ("payload", "payload_json", "blueprint", "draft", "content", "data"):
        value = raw.get(key)
        if isinstance(value, dict):
            candidates.append(value)
    best = {}
    best_score = -1
    markers = {
        "concepts", "relations", "questions", "evaluate_questions",
        "work_tasks", "work", "prepare", "organize", "primary_concept_code"
    }
    for c in candidates:
        score = len(markers.intersection(c.keys()))
        if score > best_score:
            best = c
            best_score = score
    return best


def get_list(payload: dict[str, Any], *names: str) -> list[Any]:
    for name in names:
        value = payload.get(name)
        if isinstance(value, list):
            return value
    for name in names:
        value = find_nested(payload, name)
        if isinstance(value, list):
            return value
    return []


def get_primary(payload: dict[str, Any], metadata: dict[str, Any]) -> str:
    for obj in (payload, metadata):
        for key in ("primary_concept_code", "primary_concept", "primaryConceptCode"):
            value = obj.get(key) if isinstance(obj, dict) else None
            if isinstance(value, str) and value.strip():
                return norm_code(value)
    nested = find_nested(payload, "primary_concept_code")
    if isinstance(nested, str):
        return norm_code(nested)
    return ""


def concept_code(item: Any) -> str:
    if isinstance(item, str):
        return norm_code(item)
    if not isinstance(item, dict):
        return ""
    for key in ("code", "concept_code", "id"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return norm_code(value)
    return ""


def is_core(item: Any) -> bool:
    if not isinstance(item, dict):
        return False
    for key in ("is_core", "core"):
        b = boolish(item.get(key))
        if b is not None:
            return b
    return False


def relation_endpoints(rel: Any) -> tuple[str, str]:
    if not isinstance(rel, dict):
        return "", ""
    src = ""
    dst = ""
    for key in ("source", "source_code", "from", "from_code", "concept_a"):
        if rel.get(key):
            src = norm_code(rel.get(key))
            break
    for key in ("target", "target_code", "to", "to_code", "concept_b"):
        if rel.get(key):
            dst = norm_code(rel.get(key))
            break
    return src, dst


def question_text(q: dict[str, Any]) -> str:
    for key in ("text_vi", "prompt_vi", "question_vi", "prompt", "text", "stem"):
        v = q.get(key)
        if isinstance(v, str) and v.strip():
            return re.sub(r"\s+", " ", v.strip()).lower()
    return ""


def question_type(q: dict[str, Any]) -> str:
    for key in ("type", "question_type", "item_type"):
        v = q.get(key)
        if isinstance(v, str):
            return v.strip().lower()
    return ""


def question_concept(q: dict[str, Any]) -> str:
    for key in ("concept_code", "primary_concept_code", "assesses_concept"):
        v = q.get(key)
        if isinstance(v, str) and v.strip():
            return norm_code(v)
    values = q.get("concept_codes")
    if isinstance(values, list) and values:
        return norm_code(values[0])
    return ""


def extract_answer_values(answer: Any) -> set[str]:
    vals: list[Any] = []

    def walk(x: Any):
        if isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
        elif x is not None:
            vals.append(x)

    walk(answer)
    return {str(v).strip() for v in vals if isinstance(v, (str, int, float, bool))}


def audit_mcq(q: dict[str, Any]) -> list[str]:
    errs = []
    qtype = question_type(q)
    if "mcq" not in qtype and "multiple" not in qtype:
        return errs

    options = q.get("options")
    if not isinstance(options, list):
        errs.append("MCQ options missing")
        return errs
    if len(options) != 4:
        errs.append(f"MCQ option count={len(options)} (expected 4)")

    correct = []
    for opt in options:
        if isinstance(opt, dict):
            b = boolish(opt.get("is_correct"))
            if b is True:
                correct.append(opt)

    answer_vals = extract_answer_values(q.get("answer_json"))

    if any(isinstance(o, dict) and "is_correct" in o for o in options):
        if len(correct) != 1:
            errs.append(f"MCQ correct-option count={len(correct)} (expected 1)")
        elif answer_vals:
            opt = correct[0]
            candidates = {
                str(opt.get("key", "")).strip(),
                str(opt.get("text_vi", "")).strip(),
                str(opt.get("text_en", "")).strip(),
            }
            candidates.discard("")
            if candidates.isdisjoint(answer_vals):
                errs.append("MCQ answer_json does not match correct option")
    else:
        if not answer_vals:
            errs.append("MCQ has no is_correct and empty answer_json")
        else:
            matches = 0
            for opt in options:
                if not isinstance(opt, dict):
                    continue
                candidates = {
                    str(opt.get("key", "")).strip(),
                    str(opt.get("text_vi", "")).strip(),
                    str(opt.get("text_en", "")).strip(),
                }
                candidates.discard("")
                if not candidates.isdisjoint(answer_vals):
                    matches += 1
            if matches != 1:
                errs.append(f"MCQ answer_json matches {matches} options (expected 1)")
    return errs


def audit_blueprint(path: Path, metadata: dict[str, Any]) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []
    metrics: dict[str, Any] = {}

    if not path.exists():
        return [f"missing blueprint file: {path.name}"], [], metrics

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"invalid blueprint JSON: {exc}"], [], metrics

    payload = pick_payload(raw)
    if not payload:
        return ["could not locate POWER payload in blueprint JSON"], [], metrics

    concepts = get_list(payload, "concepts")
    relations = get_list(payload, "relations", "concept_relations")
    questions = get_list(payload, "questions", "evaluate_questions", "evaluation_questions")
    # V155_WORK_SCHEMA
    work_obj = payload.get("work") or {}
    work_vi = []
    work_en = []
    if isinstance(work_obj, dict):
        vi_obj = work_obj.get("vi") or {}
        en_obj = work_obj.get("en") or {}
        if isinstance(vi_obj, dict) and isinstance(vi_obj.get("tasks"), list):
            work_vi = vi_obj["tasks"]
        if isinstance(en_obj, dict) and isinstance(en_obj.get("tasks"), list):
            work_en = en_obj["tasks"]
        if not work_vi and isinstance(work_obj.get("tasks"), list):
            work_vi = work_obj["tasks"]
    work_tasks = work_vi
    codes = [concept_code(c) for c in concepts]
    codes = [c for c in codes if c]
    code_set = set(codes)
    core_codes = [concept_code(c) for c in concepts if is_core(c)]
    primary = get_primary(payload, metadata)

    metrics["concepts"] = len(codes)
    metrics["core_concepts"] = len(core_codes)
    metrics["relations"] = len(relations)
    metrics["questions"] = len(questions)
    metrics["work_tasks"] = len(work_vi)
    metrics["work_tasks_en"] = len(work_en)
    metrics["primary"] = primary

    if len(codes) < 3:
        errors.append(f"concept count={len(codes)} (<3)")
    if len(codes) != len(code_set):
        errors.append("duplicate concept codes")
    if not (3 <= len(core_codes) <= 6):
        errors.append(f"core concept count={len(core_codes)} (expected 3-6)")
    if not primary:
        errors.append("primary_concept_code missing")
    elif primary not in code_set:
        errors.append(f"primary concept {primary} not in concept list")
    elif primary not in set(core_codes):
        errors.append(f"primary concept {primary} is not marked core")

    seen_rel = set()
    for idx, rel in enumerate(relations):
        src, dst = relation_endpoints(rel)
        if not src or not dst:
            errors.append(f"relation[{idx}] missing source/target")
            continue
        if src == dst:
            errors.append(f"relation[{idx}] self-link {src}")
        if src not in code_set or dst not in code_set:
            errors.append(f"relation[{idx}] references unknown concept")
        rel_key = (src, dst, str(rel.get("type", rel.get("relation_type", ""))) if isinstance(rel, dict) else "")
        if rel_key in seen_rel:
            warnings.append(f"duplicate relation[{idx}]")
        seen_rel.add(rel_key)
    if len(work_vi) != 3:
        errors.append(f"work.vi task count={len(work_vi)} (expected exactly 3)")
    if work_en and len(work_en) != 3:
        errors.append(f"work.en task count={len(work_en)} (expected exactly 3)")
    if not (8 <= len(questions) <= 10):
        errors.append(f"Evaluate question count={len(questions)} (expected 8-10)")

    qtexts = []
    primary_hits = 0
    qtypes = Counter()
    difficulties = Counter()
    cognitive = Counter()

    for idx, q in enumerate(questions):
        if not isinstance(q, dict):
            errors.append(f"question[{idx}] is not an object")
            continue

        txt = question_text(q)
        if txt:
            qtexts.append(txt)

        qt = question_type(q)
        if qt:
            qtypes[qt] += 1

        diff = q.get("difficulty")
        if isinstance(diff, str) and diff.strip():
            difficulties[diff.strip().lower()] += 1

        cog = q.get("cognitive_level") or q.get("cognitive")
        if isinstance(cog, str) and cog.strip():
            cognitive[cog.strip().lower()] += 1

        qc = question_concept(q)
        if primary and qc == primary:
            primary_hits += 1

        for err in audit_mcq(q):
            errors.append(f"question[{idx}] {err}")

    if len(qtexts) != len(set(qtexts)):
        errors.append("duplicate Evaluate question text")

    if primary and primary_hits == 0:
        errors.append("primary concept is not directly assessed by any Evaluate question")

    metrics["primary_evaluate_hits"] = primary_hits
    metrics["question_types"] = dict(qtypes)
    metrics["difficulty_mix"] = dict(difficulties)
    metrics["cognitive_mix"] = dict(cognitive)

    if len(qtypes) < 2:
        warnings.append("Evaluate question type mix has <2 types")
    if difficulties and len(difficulties) < 2:
        warnings.append("Evaluate difficulty mix has <2 levels")
    if cognitive and len(cognitive) < 2:
        warnings.append("Evaluate cognitive mix has <2 levels")

    source_fp = (
        payload.get("source_fingerprint")
        or raw.get("source_fingerprint")
        or find_nested(raw, "source_fingerprint")
    )
    if not source_fp:
        pass  # v1.5.5: fingerprint is not required in review JSON

    return errors, warnings, metrics


def load_units(db, grade: int | None):
    insp = inspect(db.bind)
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="Did not recognize type 'vector'.*",
            category=SAWarning,
        )
        unit_cols = {c["name"] for c in insp.get_columns("curriculum_units")}

    grade_col = first_existing(
        unit_cols,
        ["grade_level", "level", "grade", "class_level"],
    )

    required = [
        "id", "code", "content_status", "power_status",
        "is_power_ready", "metadata_json",
    ]
    missing = [name for name in required if name not in unit_cols]
    if missing:
        raise RuntimeError(
            "curriculum_units is missing required audit columns: "
            + ", ".join(missing)
        )

    # Direct grade column (older/local schemas).
    if grade_col:
        filters = []
        params = {}
        if grade is not None:
            filters.append(f"CAST({grade_col} AS text)=:grade")
            params["grade"] = str(grade)

        # Audit only numbered learnable units, matching POWER status/build.
        if "lesson_number" in unit_cols:
            filters.append("lesson_number IS NOT NULL")

        where = ("WHERE " + " AND ".join(filters)) if filters else ""

        rows = db.execute(
            text(
                f"""
                SELECT id, code, {grade_col} AS grade_level,
                       content_status, power_status,
                       is_power_ready, metadata_json
                FROM curriculum_units
                {where}
                ORDER BY {grade_col}, lesson_number NULLS LAST, code
                """
            ),
            params,
        ).mappings().all()
        return [dict(r) for r in rows]

    # Current schema: curriculum_units stores grade_id instead of a numeric grade column.
    if "grade_id" not in unit_cols:
        raise RuntimeError(
            "Could not find a direct grade column or grade_id in curriculum_units. "
            f"Available columns: {sorted(unit_cols)}"
        )

    fks = insp.get_foreign_keys("curriculum_units")
    grade_fk = next(
        (
            fk for fk in fks
            if "grade_id" in (fk.get("constrained_columns") or [])
            and fk.get("referred_table")
        ),
        None,
    )

    grade_table = grade_fk.get("referred_table") if grade_fk else None
    referred_cols = grade_fk.get("referred_columns") if grade_fk else None
    grade_pk = referred_cols[0] if referred_cols else "id"

    if not grade_table:
        table_names = set(insp.get_table_names())
        for candidate in ("grades", "grade_levels", "curriculum_grades", "school_grades", "education_levels"):
            if candidate in table_names:
                grade_table = candidate
                break

    if not grade_table:
        raise RuntimeError(
            "curriculum_units.grade_id exists, but the audit could not resolve its referenced grade table."
        )

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="Did not recognize type \'vector\'.*",
            category=SAWarning,
        )
        grade_cols = {c["name"] for c in insp.get_columns(grade_table)}

    if grade_pk not in grade_cols:
        grade_pk = "id" if "id" in grade_cols else sorted(grade_cols)[0]

    grade_rows = db.execute(text(f"SELECT * FROM {grade_table}")).mappings().all()

    import re as _re

    def _derive_grade(row):
        preferred = ["level", "grade_level", "grade", "number", "code", "name", "name_vi", "name_en"]
        ordered = [c for c in preferred if c in row]
        ordered += [c for c in row.keys() if c not in ordered]

        for col in ordered:
            value = row.get(col)
            if value is None:
                continue
            s = str(value).strip()
            if s in {"10", "11", "12"}:
                return int(s)

        for col in ordered:
            value = row.get(col)
            if value is None:
                continue
            m = _re.search(r"(?<!\\d)(10|11|12)(?!\\d)", str(value))
            if m:
                return int(m.group(1))
        return None

    grade_by_id = {}
    for row in grade_rows:
        grade_num = _derive_grade(row)
        gid = row.get(grade_pk)
        if grade_num in (10, 11, 12) and gid is not None:
            grade_by_id[str(gid)] = grade_num

    unit_filter = ""
    unit_order = "ORDER BY code"
    if "lesson_number" in unit_cols:
        unit_filter = "WHERE lesson_number IS NOT NULL"
        unit_order = "ORDER BY lesson_number, code"

    raw_units = db.execute(
        text(
            f"""
            SELECT id, code, grade_id,
                   content_status, power_status,
                   is_power_ready, metadata_json
            FROM curriculum_units
            {unit_filter}
            {unit_order}
            """
        )
    ).mappings().all()

    result = []
    unresolved = []
    for row in raw_units:
        item = dict(row)
        grade_num = grade_by_id.get(str(item.get("grade_id")))
        if grade_num is None:
            unresolved.append(str(item.get("grade_id")))
            continue
        if grade is not None and grade_num != grade:
            continue
        item["grade_level"] = grade_num
        result.append(item)

    if unresolved:
        raise RuntimeError(
            "Could not resolve grade_id value(s) to grades 10/11/12: "
            + ", ".join(sorted(set(unresolved)))
            + f". Resolved grade table: {grade_table}"
        )

    result.sort(key=lambda r: (int(r["grade_level"]), r["code"]))
    return result


def db_count_for_unit(db, tables, columns, table: str, unit_id: str) -> int | None:
    if table not in tables:
        return None
    fk = first_existing(columns[table], ["curriculum_unit_id", "unit_id", "power_unit_id"])
    if not fk:
        return None
    for sql in (
        f"SELECT COUNT(*) FROM {table} WHERE {fk}=CAST(:uid AS uuid)",
        f"SELECT COUNT(*) FROM {table} WHERE CAST({fk} AS text)=:uid",
    ):
        try:
            return int(db.execute(text(sql), {"uid": unit_id}).scalar_one())
        except Exception:
            db.rollback()
    return None


def audit_unit(db, tables, columns, unit: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    code = unit["code"]
    grade = int(unit["grade_level"])
    uid = str(unit["id"])
    metadata = unit.get("metadata_json") or {}
    if not isinstance(metadata, dict):
        metadata = {}

    if unit.get("content_status") != "ingested":
        errors.append(f"content_status={unit.get('content_status')!r}, expected 'ingested'")
    if unit.get("power_status") != "ready":
        errors.append(f"power_status={unit.get('power_status')!r}, expected 'ready'")
    if unit.get("is_power_ready") is not True:
        errors.append("is_power_ready is not true")

    draft_version = metadata.get("power_draft_version")
    if draft_version is None:
        warnings.append("metadata_json.power_draft_version missing")

    primary_meta = metadata.get("primary_concept_code")
    if not primary_meta:
        errors.append("metadata_json.primary_concept_code missing")

    map_count = db_count_for_unit(db, tables, columns, "curriculum_unit_sources", uid)
    if map_count is not None and map_count < 1:
        errors.append("no curriculum_unit_sources mapping")

    blueprint_db_count = db_count_for_unit(db, tables, columns, "power_unit_blueprints", uid)
    if blueprint_db_count is not None and blueprint_db_count < 1:
        errors.append("no power_unit_blueprints row")

    question_db_count = db_count_for_unit(db, tables, columns, "questions", uid)
    if question_db_count is not None and not (8 <= question_db_count <= 10):
        errors.append(f"DB question count={question_db_count}, expected 8-10")

    curriculum_concept_count = db_count_for_unit(db, tables, columns, "curriculum_concepts", uid)
    if curriculum_concept_count is not None and curriculum_concept_count < 3:
        errors.append(f"DB curriculum concept count={curriculum_concept_count}, expected >=3")

    bp_path = BLUEPRINT_DIR / f"{code}.json"
    bp_errors, bp_warnings, metrics = audit_blueprint(bp_path, metadata)
    errors.extend(bp_errors)
    warnings.extend(bp_warnings)

    return {
        "grade": grade,
        "code": code,
        "unit_id": uid,
        "draft_version": draft_version,
        "db_question_count": question_db_count,
        "db_curriculum_concept_count": curriculum_concept_count,
        "blueprint_concepts": metrics.get("concepts"),
        "blueprint_core_concepts": metrics.get("core_concepts"),
        "blueprint_work_tasks": metrics.get("work_tasks"),
        "blueprint_questions": metrics.get("questions"),
        "primary_concept": metrics.get("primary") or norm_code(primary_meta),
        "primary_evaluate_hits": metrics.get("primary_evaluate_hits"),
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
        "metrics": metrics,
    }


def print_summary(results: list[dict[str, Any]]):
    print("\n=== POWER CURRICULUM FULL AUDIT ===")
    grouped = defaultdict(list)
    for r in results:
        grouped[r["grade"]].append(r)

    total_pass = 0
    total_fail = 0
    total_warn_units = 0

    for grade in sorted(grouped):
        rows = grouped[grade]
        p = sum(r["status"] == "PASS" for r in rows)
        f = len(rows) - p
        w = sum(bool(r["warnings"]) for r in rows)
        total_pass += p
        total_fail += f
        total_warn_units += w
        expected = EXPECTED_GRADE_TOTALS.get(grade)
        print(f"Grade {grade}: audited={len(rows)}/{expected} PASS={p} FAIL={f} warning-units={w}")

    print(f"TOTAL: audited={len(results)}/90 PASS={total_pass} FAIL={total_fail} warning-units={total_warn_units}")

    failed = [r for r in results if r["status"] == "FAIL"]
    if failed:
        print("\n=== FAILURES ===")
        for r in failed:
            print(f"[FAIL] {r['code']}")
            for err in r["errors"]:
                print(f"  [ERROR] {err}")
            for warn in r["warnings"]:
                print(f"  [WARN] {warn}")
    else:
        print("\n[PASS] No blocking curriculum audit errors.")


def write_reports(results: list[dict[str, Any]], grade_arg: str):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stem = f"power_curriculum_audit_grade_{grade_arg}"
    json_path = REPORT_DIR / f"{stem}.json"
    csv_path = REPORT_DIR / f"{stem}.csv"

    json_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    fields = [
        "grade", "code", "status", "draft_version",
        "db_question_count", "db_curriculum_concept_count",
        "blueprint_concepts", "blueprint_core_concepts",
        "blueprint_work_tasks", "blueprint_questions",
        "primary_concept", "primary_evaluate_hits",
        "errors", "warnings",
    ]

    with csv_path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for r in results:
            row = {k: r.get(k) for k in fields}
            row["errors"] = " | ".join(r["errors"])
            row["warnings"] = " | ".join(r["warnings"])
            writer.writerow(row)

    print(f"\nJSON report: {json_path}")
    print(f"CSV report : {csv_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Strict full audit of activated POWER curriculum packages.")
    parser.add_argument("--grade", default="all", choices=["all", "10", "11", "12"])
    parser.add_argument("--strict-warnings", action="store_true")
    args = parser.parse_args()

    grade = None if args.grade == "all" else int(args.grade)

    db = SessionLocal()
    try:
        tables, columns = get_tables_and_columns(db)
        units = load_units(db, grade)
        expected = 90 if grade is None else EXPECTED_GRADE_TOTALS[grade]
        if len(units) != expected:
            print(f"[ERROR] catalog count={len(units)}, expected={expected} for grade={args.grade}")
            return 2
        results = [audit_unit(db, tables, columns, u) for u in units]
    finally:
        db.close()

    print_summary(results)
    write_reports(results, args.grade)

    failures = sum(r["status"] == "FAIL" for r in results)
    warnings = sum(len(r["warnings"]) for r in results)

    if failures:
        return 10
    if args.strict_warnings and warnings:
        return 11
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
