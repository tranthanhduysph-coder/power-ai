from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from app.ingestion.manifest import project_root


@dataclass(frozen=True, slots=True)
class KNTTBookSpec:
    grade: int
    source_code: str
    title: str
    language: str
    source_role: str
    publisher: str
    edition: str
    license_status: str
    document_path: str
    pdf_page_offset: int
    expected_pdf_pages: int

    @property
    def absolute_document_path(self) -> Path:
        return project_root() / self.document_path


def registry_path() -> Path:
    return project_root() / "content" / "sources" / "kntt_books.json"


def load_registry(path: str | Path | None = None) -> dict[int, KNTTBookSpec]:
    source = Path(path) if path is not None else registry_path()
    data = json.loads(source.read_text(encoding="utf-8"))
    books: dict[int, KNTTBookSpec] = {}
    for raw in data.get("books", []):
        spec = KNTTBookSpec(
            grade=int(raw["grade"]),
            source_code=str(raw["source_code"]),
            title=str(raw["title"]),
            language=str(raw.get("language", "vi")),
            source_role=str(raw.get("source_role", "curriculum")),
            publisher=str(raw.get("publisher", "NXB Giáo dục Việt Nam")),
            edition=str(raw.get("edition", "Kết nối tri thức với cuộc sống")),
            license_status=str(raw.get("license_status", "review_required")),
            document_path=str(raw["document_path"]),
            pdf_page_offset=int(raw["pdf_page_offset"]),
            expected_pdf_pages=int(raw["expected_pdf_pages"]),
        )
        if spec.grade in books:
            raise ValueError(f"Duplicate KNTT book registry entry for grade {spec.grade}")
        books[spec.grade] = spec
    return books


def printed_to_pdf_page(printed_page: int, offset: int) -> int:
    if printed_page < 1:
        raise ValueError("Printed page must be >= 1")
    return printed_page + offset


def pdf_range(printed_start: int, printed_end: int, offset: int) -> tuple[int, int]:
    if printed_end < printed_start:
        raise ValueError(f"Invalid printed page range {printed_start}-{printed_end}")
    return printed_to_pdf_page(printed_start, offset), printed_to_pdf_page(printed_end, offset)


def validate_unit_rows(units: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [dict(row) for row in units]
    if not rows:
        raise ValueError("No curriculum units found for this book")

    numbers: list[int] = []
    for row in rows:
        if row.get("lesson_number") is None:
            raise ValueError(f"Unit {row.get('code')} has no lesson_number")
        if row.get("printed_page_start") is None or row.get("printed_page_end") is None:
            raise ValueError(f"Unit {row.get('code')} has no printed page range")
        numbers.append(int(row["lesson_number"]))

    expected = list(range(1, max(numbers) + 1))
    if sorted(numbers) != expected:
        raise ValueError(f"Curriculum numbering is not contiguous: got {sorted(numbers)}")
    return sorted(rows, key=lambda row: int(row["lesson_number"]))


def build_manifest_data(spec: KNTTBookSpec, units: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = validate_unit_rows(units)
    sections: list[dict[str, Any]] = []
    for row in rows:
        printed_start = int(row["printed_page_start"])
        printed_end = int(row["printed_page_end"])
        page_start, page_end = pdf_range(printed_start, printed_end, spec.pdf_page_offset)
        sections.append(
            {
                "code": row["code"],
                "title": row["name_vi"],
                "page_start": page_start,
                "page_end": page_end,
                "concept_codes": list(row.get("concept_codes") or []),
                "level": 1,
                "metadata": {
                    "curriculum_unit_code": row["code"],
                    "unit_type": row["unit_type"],
                    "lesson_number": int(row["lesson_number"]),
                    "printed_page_start": printed_start,
                    "printed_page_end": printed_end,
                    "pdf_page_offset": spec.pdf_page_offset,
                },
            }
        )

    return {
        "source": {
            "code": spec.source_code,
            "title": spec.title,
            "language": spec.language,
            "grade_level": spec.grade,
            "edition": spec.edition,
            "publisher": spec.publisher,
            "source_role": spec.source_role,
            "license_status": spec.license_status,
            "storage_key": spec.document_path,
            "metadata": {
                "curriculum": "KNTT",
                "pdf_page_offset": spec.pdf_page_offset,
                "expected_pdf_pages": spec.expected_pdf_pages,
                "content_build": "v1.1",
            },
        },
        "document": {"path": spec.document_path},
        "replace_existing": True,
        "sections": sections,
    }


def expected_pdf_pages_for_units(spec: KNTTBookSpec, units: Iterable[dict[str, Any]]) -> set[int]:
    pages: set[int] = set()
    for row in validate_unit_rows(units):
        start, end = pdf_range(
            int(row["printed_page_start"]),
            int(row["printed_page_end"]),
            spec.pdf_page_offset,
        )
        pages.update(range(start, end + 1))
    return pages
