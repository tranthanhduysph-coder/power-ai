from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
API_DIR = ROOT / "apps" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from sqlalchemy import text  # noqa: E402

from app.content.kntt import (  # noqa: E402
    KNTTBookSpec,
    build_manifest_data,
    expected_pdf_pages_for_units,
    load_registry,
    pdf_range,
)
from app.db.session import SessionLocal  # noqa: E402
from app.ingestion.readers import pdf_page_count  # noqa: E402
from app.ingestion.service import ingest_manifest  # noqa: E402


def _unit_rows(db, grade: int) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            SELECT cu.id::text AS id, cu.code, cu.name_vi, cu.name_en, cu.unit_type,
                   cu.lesson_number, cu.printed_page_start, cu.printed_page_end,
                   COALESCE(array_agg(c.code ORDER BY cc.is_core DESC, c.code)
                            FILTER (WHERE c.code IS NOT NULL), ARRAY[]::text[]) AS concept_codes
            FROM curriculum_units cu
            JOIN grades g ON g.id = cu.grade_id
            LEFT JOIN curriculum_concepts cc ON cc.curriculum_unit_id = cu.id
            LEFT JOIN concepts c ON c.id = cc.concept_id
            WHERE g.level = :grade
              AND cu.catalog_visible = true
              AND cu.lesson_number IS NOT NULL
              AND cu.unit_type IN ('lesson','practice','project')
            GROUP BY cu.id, cu.code, cu.name_vi, cu.name_en, cu.unit_type,
                     cu.lesson_number, cu.printed_page_start, cu.printed_page_end
            ORDER BY cu.lesson_number
            """
        ),
        {"grade": grade},
    ).mappings().all()
    return [dict(row) for row in rows]


def _generated_manifest_path(spec: KNTTBookSpec) -> Path:
    path = ROOT / "storage" / "generated-manifests" / f"{spec.source_code}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _write_manifest(spec: KNTTBookSpec, units: list[dict[str, Any]]) -> Path:
    path = _generated_manifest_path(spec)
    payload = build_manifest_data(spec, units)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _validate_pdf(spec: KNTTBookSpec, units: list[dict[str, Any]]) -> tuple[int, set[int]]:
    document = spec.absolute_document_path
    if not document.exists():
        raise FileNotFoundError(f"Missing source PDF: {document}")
    actual_pages = pdf_page_count(document)
    if actual_pages != spec.expected_pdf_pages:
        raise RuntimeError(
            f"Unexpected PDF page count for {spec.source_code}: {actual_pages}; "
            f"expected {spec.expected_pdf_pages}. Do not ingest until page mapping is verified."
        )
    expected_pages = expected_pdf_pages_for_units(spec, units)
    if not expected_pages:
        raise RuntimeError("No textbook pages planned")
    if max(expected_pages) > actual_pages:
        raise RuntimeError(
            f"Mapped page {max(expected_pages)} exceeds PDF page count {actual_pages}"
        )
    return actual_pages, expected_pages


def _set_unit_status(db, grade: int, status: str) -> None:
    db.execute(
        text(
            """
            UPDATE curriculum_units cu
            SET content_status = :status,
                content_updated_at = CASE WHEN :status IN ('ingested','failed') THEN now() ELSE content_updated_at END
            FROM grades g
            WHERE g.id = cu.grade_id
              AND g.level = :grade
              AND cu.catalog_visible = true
              AND cu.lesson_number IS NOT NULL
              AND cu.unit_type IN ('lesson','practice','project')
            """
        ),
        {"grade": grade, "status": status},
    )



def _reconcile_unit_status(db, grade: int) -> tuple[int, int]:
    """Derive curriculum-unit content status from actual ingested section/chunk evidence."""
    db.execute(
        text(
            """
            UPDATE curriculum_units cu
            SET content_status = 'not_ingested', content_updated_at = NULL
            FROM grades g
            WHERE g.id = cu.grade_id
              AND g.level = :grade
              AND cu.catalog_visible = true
              AND cu.lesson_number IS NOT NULL
              AND cu.unit_type IN ('lesson','practice','project')
            """
        ),
        {"grade": grade},
    )
    db.execute(
        text(
            """
            UPDATE curriculum_units cu
            SET content_status = 'ingested', content_updated_at = now()
            FROM grades g
            WHERE g.id = cu.grade_id
              AND g.level = :grade
              AND cu.catalog_visible = true
              AND cu.lesson_number IS NOT NULL
              AND cu.unit_type IN ('lesson','practice','project')
              AND EXISTS (
                  SELECT 1
                  FROM curriculum_unit_sources cus
                  JOIN sources s ON s.id = cus.source_id
                  JOIN content_chunks cc ON cc.source_id = s.id
                  WHERE cus.curriculum_unit_id = cu.id
                    AND cus.pdf_page_start IS NOT NULL
                    AND cus.pdf_page_end IS NOT NULL
                    AND cc.page_start IS NOT NULL
                    AND cc.page_end IS NOT NULL
                    AND cc.page_end >= cus.pdf_page_start
                    AND cc.page_start <= cus.pdf_page_end
              )
            """
        ),
        {"grade": grade},
    )
    total = int(db.execute(text("""
        SELECT count(*) FROM curriculum_units cu
        JOIN grades g ON g.id=cu.grade_id
        WHERE g.level=:grade AND cu.catalog_visible=true
          AND cu.lesson_number IS NOT NULL
          AND cu.unit_type IN ('lesson','practice','project')
    """), {"grade": grade}).scalar_one())
    ingested = int(db.execute(text("""
        SELECT count(*) FROM curriculum_units cu
        JOIN grades g ON g.id=cu.grade_id
        WHERE g.level=:grade AND cu.catalog_visible=true
          AND cu.lesson_number IS NOT NULL
          AND cu.unit_type IN ('lesson','practice','project')
          AND cu.content_status='ingested'
    """), {"grade": grade}).scalar_one())
    return ingested, total

def _sync_unit_sources(db, spec: KNTTBookSpec, units: list[dict[str, Any]]) -> None:
    source = db.execute(
        text("SELECT id::text AS id FROM sources WHERE code=:code"),
        {"code": spec.source_code},
    ).mappings().one_or_none()
    if not source:
        raise RuntimeError(f"Source {spec.source_code} was not created by ingestion")

    for unit in units:
        pdf_start, pdf_end = pdf_range(
            int(unit["printed_page_start"]),
            int(unit["printed_page_end"]),
            spec.pdf_page_offset,
        )
        metadata = json.dumps(
            {
                "mapping_method": "verified_printed_page_offset",
                "pdf_page_offset": spec.pdf_page_offset,
                "content_build": "v1.1",
            },
            ensure_ascii=False,
        )
        db.execute(
            text(
                """
                INSERT INTO curriculum_unit_sources(
                    curriculum_unit_id, source_id, source_role,
                    printed_page_start, printed_page_end,
                    pdf_page_start, pdf_page_end, metadata_json
                ) VALUES (
                    CAST(:unit_id AS uuid), CAST(:source_id AS uuid), 'primary',
                    :printed_start, :printed_end, :pdf_start, :pdf_end,
                    CAST(:metadata AS jsonb)
                )
                ON CONFLICT (curriculum_unit_id, source_id, source_role) DO UPDATE SET
                    printed_page_start = EXCLUDED.printed_page_start,
                    printed_page_end = EXCLUDED.printed_page_end,
                    pdf_page_start = EXCLUDED.pdf_page_start,
                    pdf_page_end = EXCLUDED.pdf_page_end,
                    metadata_json = EXCLUDED.metadata_json
                """
            ),
            {
                "unit_id": unit["id"],
                "source_id": source["id"],
                "printed_start": unit["printed_page_start"],
                "printed_end": unit["printed_page_end"],
                "pdf_start": pdf_start,
                "pdf_end": pdf_end,
                "metadata": metadata,
            },
        )


def _plan(spec: KNTTBookSpec, units: list[dict[str, Any]]) -> None:
    actual_pages, expected_pages = _validate_pdf(spec, units)
    manifest_path = _write_manifest(spec, units)
    first = units[0]
    last = units[-1]
    first_pdf = pdf_range(int(first["printed_page_start"]), int(first["printed_page_end"]), spec.pdf_page_offset)
    last_pdf = pdf_range(int(last["printed_page_start"]), int(last["printed_page_end"]), spec.pdf_page_offset)
    print(f"{spec.source_code} | Biology {spec.grade}")
    print(f"PDF: {spec.absolute_document_path}")
    print(f"PDF pages: {actual_pages} | verified offset: +{spec.pdf_page_offset}")
    print(f"Curriculum units: {len(units)}")
    print(f"Pages to ingest: {len(expected_pages)} unique PDF pages")
    print(f"First: {first['code']} | printed {first['printed_page_start']}-{first['printed_page_end']} | PDF {first_pdf[0]}-{first_pdf[1]}")
    print(f"Last:  {last['code']} | printed {last['printed_page_start']}-{last['printed_page_end']} | PDF {last_pdf[0]}-{last_pdf[1]}")
    print(f"Generated manifest: {manifest_path}")


def _ingest(spec: KNTTBookSpec, units: list[dict[str, Any]]) -> None:
    _validate_pdf(spec, units)
    manifest_path = _write_manifest(spec, units)
    db = SessionLocal()
    try:
        _set_unit_status(db, spec.grade, "planned")
        db.commit()
        print(f"Starting {spec.source_code} ingestion from {manifest_path}")
        result = ingest_manifest(db, manifest_path)
        _sync_unit_sources(db, spec, units)
        _set_unit_status(db, spec.grade, "ingested")
        _reconcile_unit_status(db, spec.grade)
        db.commit()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print(f"Mapped {len(units)} curriculum units to {spec.source_code}")
    except Exception:
        db.rollback()
        try:
            _set_unit_status(db, spec.grade, "failed")
            db.commit()
        except Exception:
            db.rollback()
        raise
    finally:
        db.close()


def _verify(spec: KNTTBookSpec, units: list[dict[str, Any]]) -> bool:
    _, expected_pages = _validate_pdf(spec, units)
    db = SessionLocal()
    try:
        source = db.execute(
            text(
                """
                SELECT id::text AS id, ingest_status
                FROM sources WHERE code=:code
                """
            ),
            {"code": spec.source_code},
        ).mappings().one_or_none()
        if not source:
            print(f"[FAIL] {spec.source_code}: source row missing")
            return False

        counts = db.execute(
            text(
                """
                SELECT
                  (SELECT count(*) FROM source_pages WHERE source_id=CAST(:source_id AS uuid)) AS pages,
                  (SELECT count(*) FROM source_sections WHERE source_id=CAST(:source_id AS uuid)) AS sections,
                  (SELECT count(*) FROM content_chunks WHERE source_id=CAST(:source_id AS uuid)) AS chunks,
                  (SELECT count(*) FROM curriculum_unit_sources WHERE source_id=CAST(:source_id AS uuid) AND source_role='primary') AS mappings
                """
            ),
            {"source_id": source["id"]},
        ).mappings().one()
        ingested_units = int(
            db.execute(
                text(
                    """
                    SELECT count(*) FROM curriculum_units cu
                    JOIN grades g ON g.id=cu.grade_id
                    WHERE g.level=:grade AND cu.lesson_number IS NOT NULL
                      AND cu.unit_type IN ('lesson','practice','project')
                      AND cu.catalog_visible=true AND cu.content_status='ingested'
                    """
                ),
                {"grade": spec.grade},
            ).scalar_one()
        )
        checks = [
            ("source ready", source["ingest_status"] == "ready", str(source["ingest_status"])),
            ("source pages", int(counts["pages"]) == len(expected_pages), f"{counts['pages']}/{len(expected_pages)}"),
            ("sections", int(counts["sections"]) == len(units), f"{counts['sections']}/{len(units)}"),
            ("chunks", int(counts["chunks"]) > 0, str(counts["chunks"])),
            ("unit mappings", int(counts["mappings"]) == len(units), f"{counts['mappings']}/{len(units)}"),
            ("unit status", ingested_units == len(units), f"{ingested_units}/{len(units)}"),
        ]
        ok = True
        for label, passed, detail in checks:
            print(f"[{'PASS' if passed else 'FAIL'}] {label}: {detail}")
            ok &= passed
        return ok
    finally:
        db.close()


def _selected_grades(args, registry: dict[int, KNTTBookSpec]) -> list[int]:
    if args.all:
        return sorted(registry)
    if args.grade is None:
        raise SystemExit("Use --grade 10|11|12 or --all")
    if args.grade not in registry:
        raise SystemExit(f"No book registry entry for grade {args.grade}")
    return [args.grade]


def main() -> int:
    parser = argparse.ArgumentParser(description="POWER AI KNTT textbook content build")
    parser.add_argument("command", choices=("plan", "ingest", "verify", "reconcile"))
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--grade", type=int, choices=(10, 11, 12))
    selection.add_argument("--all", action="store_true")
    args = parser.parse_args()

    registry = load_registry()
    grades = _selected_grades(args, registry)
    all_ok = True
    for index, grade in enumerate(grades):
        if index:
            print("\n" + "=" * 72 + "\n")
        spec = registry[grade]
        db = SessionLocal()
        try:
            units = _unit_rows(db, grade)
        finally:
            db.close()

        if args.command == "plan":
            _plan(spec, units)
        elif args.command == "ingest":
            _ingest(spec, units)
        elif args.command == "reconcile":
            db = SessionLocal()
            try:
                ingested, total = _reconcile_unit_status(db, grade)
                db.commit()
                print(f"Reconciled Biology {grade}: {ingested}/{total} units have ingested content evidence")
            finally:
                db.close()
        else:
            all_ok &= _verify(spec, units)
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
