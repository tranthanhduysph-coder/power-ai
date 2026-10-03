from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class DocumentPage:
    number: int
    text: str
    printed_page_label: str | None = None
    extraction_method: str = "native_text"
    extraction_provider: str | None = None
    extraction_model: str | None = None
    visuals: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SectionSpec:
    code: str
    title: str
    page_start: int | None = None
    page_end: int | None = None
    parent_code: str | None = None
    concept_codes: list[str] = field(default_factory=list)
    level: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SourceSpec:
    code: str
    title: str
    language: str
    source_role: str
    grade_level: int | None = None
    edition: str | None = None
    publisher: str | None = None
    license_status: str = "review_required"
    storage_key: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class IngestionManifest:
    path: Path
    source: SourceSpec
    document_path: Path
    sections: list[SectionSpec]
    replace_existing: bool = True


@dataclass(slots=True)
class TextChunk:
    index: int
    text: str
    token_count: int
