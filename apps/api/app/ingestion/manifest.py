from __future__ import annotations

import json
from pathlib import Path

from app.ingestion.models import IngestionManifest, SectionSpec, SourceSpec


def project_root() -> Path:
    # Host development layout: <repo>/apps/api/app/ingestion/manifest.py
    # API container layout: /app/app/ingestion/manifest.py
    if Path("/app/database").exists() and Path("/app/app").exists():
        return Path("/app")
    return Path(__file__).resolve().parents[4]


def _resolve_document_path(manifest_path: Path, raw_path: str) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate

    root_candidate = project_root() / candidate
    if root_candidate.exists():
        return root_candidate
    return manifest_path.parent / candidate


def load_manifest(path: str | Path) -> IngestionManifest:
    manifest_path = Path(path).resolve()
    data = json.loads(manifest_path.read_text(encoding="utf-8"))

    source_data = data["source"]
    source = SourceSpec(
        code=source_data["code"],
        title=source_data["title"],
        language=source_data["language"],
        source_role=source_data["source_role"],
        grade_level=source_data.get("grade_level"),
        edition=source_data.get("edition"),
        publisher=source_data.get("publisher"),
        license_status=source_data.get("license_status", "review_required"),
        storage_key=source_data.get("storage_key"),
        metadata=source_data.get("metadata", {}),
    )

    document_data = data["document"]
    document_path = _resolve_document_path(manifest_path, document_data["path"])

    sections = [
        SectionSpec(
            code=item["code"],
            title=item["title"],
            page_start=item.get("page_start"),
            page_end=item.get("page_end"),
            parent_code=item.get("parent_code"),
            concept_codes=item.get("concept_codes", []),
            level=item.get("level", 1),
            metadata=item.get("metadata", {}),
        )
        for item in data.get("sections", [])
    ]

    return IngestionManifest(
        path=manifest_path,
        source=source,
        document_path=document_path,
        sections=sections,
        replace_existing=bool(data.get("replace_existing", True)),
    )
