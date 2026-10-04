from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.ingestion.chunker import chunk_text
from app.ingestion.concept_mapper import ConceptAliasMapper
from app.ingestion.manifest import load_manifest, project_root
from app.ingestion.models import DocumentPage, SectionSpec
from app.ingestion.readers import pdf_page_count, read_document
from app.retrieval.embeddings import get_embedding_provider, vector_literal


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _aliases_path() -> Path:
    return project_root() / "content" / "ontology" / "concept_aliases.json"


def _upsert_source(db: Session, manifest, checksum: str) -> str:
    row = db.execute(
        text(
            """
            INSERT INTO sources(
                code, title, language, grade_level, edition, publisher,
                source_role, license_status, storage_key, content_sha256,
                ingest_status, metadata_json, updated_at
            ) VALUES (
                :code, :title, :language, :grade_level, :edition, :publisher,
                :source_role, :license_status, :storage_key, :content_sha256,
                'ingesting', CAST(:metadata_json AS jsonb), now()
            )
            ON CONFLICT (code) DO UPDATE SET
                title = EXCLUDED.title,
                language = EXCLUDED.language,
                grade_level = EXCLUDED.grade_level,
                edition = EXCLUDED.edition,
                publisher = EXCLUDED.publisher,
                source_role = EXCLUDED.source_role,
                license_status = EXCLUDED.license_status,
                storage_key = EXCLUDED.storage_key,
                content_sha256 = EXCLUDED.content_sha256,
                ingest_status = 'ingesting',
                metadata_json = EXCLUDED.metadata_json,
                updated_at = now()
            RETURNING id::text
            """
        ),
        {
            "code": manifest.source.code,
            "title": manifest.source.title,
            "language": manifest.source.language,
            "grade_level": manifest.source.grade_level,
            "edition": manifest.source.edition,
            "publisher": manifest.source.publisher,
            "source_role": manifest.source.source_role,
            "license_status": manifest.source.license_status,
            "storage_key": manifest.source.storage_key or str(manifest.document_path),
            "content_sha256": checksum,
            "metadata_json": _json(manifest.source.metadata),
        },
    ).mappings().one()
    return row["id"]


def _create_job(db: Session, source_id: str, manifest, provider) -> str:
    return db.execute(
        text(
            """
            INSERT INTO ingestion_jobs(
                source_id, source_code, manifest_path, document_path, status,
                embedding_provider, embedding_model
            ) VALUES (
                CAST(:source_id AS uuid), :source_code, :manifest_path, :document_path,
                'running', :embedding_provider, :embedding_model
            )
            RETURNING id::text
            """
        ),
        {
            "source_id": source_id,
            "source_code": manifest.source.code,
            "manifest_path": str(manifest.path),
            "document_path": str(manifest.document_path),
            "embedding_provider": provider.name,
            "embedding_model": provider.model,
        },
    ).scalar_one()


def _sections_or_fallback(manifest, total_pages: int) -> list[SectionSpec]:
    if manifest.sections:
        return manifest.sections
    return [
        SectionSpec(
            code=f"{manifest.source.code}_FULL",
            title=manifest.source.title,
            page_start=1,
            page_end=max(1, total_pages),
            concept_codes=[],
            level=1,
        )
    ]


def _required_page_numbers(sections: list[SectionSpec], total_pages: int) -> list[int]:
    page_numbers: set[int] = set()
    for section in sections:
        start = section.page_start or 1
        end = section.page_end or total_pages
        if start < 1 or end < start or end > total_pages:
            raise ValueError(
                f"Invalid page range for {section.code}: {start}-{end}; PDF has {total_pages} pages"
            )
        page_numbers.update(range(start, end + 1))
    return sorted(page_numbers)


def _upsert_source_page(db: Session, source_id: str, page: DocumentPage) -> None:
    db.execute(
        text(
            """
            INSERT INTO source_pages(
                source_id, page_number, printed_page_label, text_content,
                visuals_json, extraction_method, extraction_provider,
                extraction_model, metadata_json, updated_at
            ) VALUES (
                CAST(:source_id AS uuid), :page_number, :printed_page_label,
                :text_content, CAST(:visuals_json AS jsonb), :extraction_method,
                :extraction_provider, :extraction_model,
                CAST(:metadata_json AS jsonb), now()
            )
            ON CONFLICT (source_id, page_number) DO UPDATE SET
                printed_page_label = EXCLUDED.printed_page_label,
                text_content = EXCLUDED.text_content,
                visuals_json = EXCLUDED.visuals_json,
                extraction_method = EXCLUDED.extraction_method,
                extraction_provider = EXCLUDED.extraction_provider,
                extraction_model = EXCLUDED.extraction_model,
                metadata_json = EXCLUDED.metadata_json,
                updated_at = now()
            """
        ),
        {
            "source_id": source_id,
            "page_number": page.number,
            "printed_page_label": page.printed_page_label,
            "text_content": page.text,
            "visuals_json": _json(page.visuals),
            "extraction_method": page.extraction_method,
            "extraction_provider": page.extraction_provider,
            "extraction_model": page.extraction_model,
            "metadata_json": _json(page.metadata),
        },
    )


def ingest_manifest(db: Session, manifest_path: str | Path) -> dict[str, Any]:
    settings = get_settings()
    manifest = load_manifest(manifest_path)
    if not manifest.document_path.exists():
        raise FileNotFoundError(
            f"Document declared in manifest does not exist: {manifest.document_path}"
        )

    provider = get_embedding_provider(settings.embedding_provider, settings.embedding_dimension)
    mapper = ConceptAliasMapper.from_json(_aliases_path())
    checksum = _sha256(manifest.document_path)

    source_id = _upsert_source(db, manifest, checksum)
    job_id = _create_job(db, source_id, manifest, provider)
    db.commit()

    try:
        if manifest.document_path.suffix.lower() == ".pdf":
            total_pages = pdf_page_count(manifest.document_path)
        else:
            total_pages = 1

        sections = _sections_or_fallback(manifest, total_pages)
        required_pages = _required_page_numbers(sections, total_pages)
        pages = read_document(
            manifest.document_path,
            page_numbers=required_pages,
            cache_namespace=checksum,
            language=manifest.source.language,
        )
        page_by_number = {page.number: page for page in pages}

        if manifest.replace_existing:
            db.execute(
                text("DELETE FROM content_chunks WHERE source_id = CAST(:id AS uuid)"),
                {"id": source_id},
            )
            db.execute(
                text("DELETE FROM source_sections WHERE source_id = CAST(:id AS uuid)"),
                {"id": source_id},
            )
            db.execute(
                text("DELETE FROM source_pages WHERE source_id = CAST(:id AS uuid)"),
                {"id": source_id},
            )
            db.flush()

        for page in pages:
            _upsert_source_page(db, source_id, page)

        known_concepts = {
            row["code"]: row["id"]
            for row in db.execute(text("SELECT id::text AS id, code FROM concepts")).mappings().all()
        }

        section_ids: dict[str, str] = {}
        chunks_created = 0

        for order, spec in enumerate(sections):
            parent_id = section_ids.get(spec.parent_code) if spec.parent_code else None
            section_id = db.execute(
                text(
                    """
                    INSERT INTO source_sections(
                        source_id, parent_id, code, title, page_start, page_end,
                        sort_order, section_level, metadata_json
                    ) VALUES (
                        CAST(:source_id AS uuid), CAST(:parent_id AS uuid), :code, :title,
                        :page_start, :page_end, :sort_order, :section_level,
                        CAST(:metadata_json AS jsonb)
                    ) RETURNING id::text
                    """
                ),
                {
                    "source_id": source_id,
                    "parent_id": parent_id,
                    "code": spec.code,
                    "title": spec.title,
                    "page_start": spec.page_start,
                    "page_end": spec.page_end,
                    "sort_order": order,
                    "section_level": spec.level,
                    "metadata_json": _json(spec.metadata),
                },
            ).scalar_one()
            section_ids[spec.code] = section_id

            start = spec.page_start or 1
            end = spec.page_end or total_pages
            section_pages = [page_by_number[n] for n in range(start, end + 1) if n in page_by_number]
            section_chunk_index = 0

            # Chunk page-by-page so retrieval keeps exact PDF page provenance.
            for page in section_pages:
                chunks = chunk_text(
                    page.text,
                    max_chars=settings.ingest_chunk_max_chars,
                    overlap_chars=settings.ingest_chunk_overlap_chars,
                )
                for chunk in chunks:
                    ranked = mapper.rank(chunk.text, explicit_codes=spec.concept_codes)
                    mapped = [item for item in ranked if item[0] in known_concepts]
                    primary_concept_id = known_concepts[mapped[0][0]] if mapped else None
                    content_hash = hashlib.sha256(chunk.text.encode("utf-8")).hexdigest()
                    embedding = vector_literal(provider.embed(chunk.text))
                    chunk_metadata = {
                        "printed_page_label": page.printed_page_label,
                        "extraction_method": page.extraction_method,
                        "extraction_provider": page.extraction_provider,
                        "extraction_model": page.extraction_model,
                        "visuals": page.visuals,
                    }

                    chunk_id = db.execute(
                        text(
                            """
                            INSERT INTO content_chunks(
                                source_id, section_id, concept_id, language,
                                page_start, page_end, text_content, token_count,
                                embedding, chunk_index, content_hash, metadata_json,
                                embedding_provider, embedding_model, updated_at
                            ) VALUES (
                                CAST(:source_id AS uuid), CAST(:section_id AS uuid),
                                CAST(:concept_id AS uuid), :language,
                                :page_start, :page_end, :text_content, :token_count,
                                CAST(:embedding AS vector), :chunk_index, :content_hash,
                                CAST(:metadata_json AS jsonb), :embedding_provider,
                                :embedding_model, now()
                            ) RETURNING id::text
                            """
                        ),
                        {
                            "source_id": source_id,
                            "section_id": section_id,
                            "concept_id": primary_concept_id,
                            "language": manifest.source.language,
                            "page_start": page.number,
                            "page_end": page.number,
                            "text_content": chunk.text,
                            "token_count": chunk.token_count,
                            "embedding": embedding,
                            "chunk_index": section_chunk_index,
                            "content_hash": content_hash,
                            "metadata_json": _json(chunk_metadata),
                            "embedding_provider": provider.name,
                            "embedding_model": provider.model,
                        },
                    ).scalar_one()

                    for code, relevance, method in mapped:
                        db.execute(
                            text(
                                """
                                INSERT INTO content_chunk_concepts(chunk_id, concept_id, relevance, mapping_method)
                                VALUES (CAST(:chunk_id AS uuid), CAST(:concept_id AS uuid), :relevance, :method)
                                ON CONFLICT (chunk_id, concept_id) DO UPDATE SET
                                    relevance = EXCLUDED.relevance,
                                    mapping_method = EXCLUDED.mapping_method
                                """
                            ),
                            {
                                "chunk_id": chunk_id,
                                "concept_id": known_concepts[code],
                                "relevance": relevance,
                                "method": method,
                            },
                        )
                    section_chunk_index += 1
                    chunks_created += 1

        db.execute(
            text("UPDATE sources SET ingest_status = 'ready', updated_at = now() WHERE id = CAST(:source_id AS uuid)"),
            {"source_id": source_id},
        )
        db.execute(
            text(
                """
                UPDATE ingestion_jobs
                SET status = 'completed', sections_created = :sections_created,
                    chunks_created = :chunks_created, completed_at = now(),
                    metadata_json = CAST(:metadata_json AS jsonb)
                WHERE id = CAST(:job_id AS uuid)
                """
            ),
            {
                "job_id": job_id,
                "sections_created": len(sections),
                "chunks_created": chunks_created,
                "metadata_json": _json(
                    {
                        "pages_processed": len(pages),
                        "page_numbers": required_pages,
                        "vision_pages": sum(1 for page in pages if page.extraction_method == "vision"),
                    }
                ),
            },
        )
        db.commit()
        return {
            "job_id": job_id,
            "source_code": manifest.source.code,
            "document": str(manifest.document_path),
            "pages_processed": len(pages),
            "vision_pages": sum(1 for page in pages if page.extraction_method == "vision"),
            "sections_created": len(sections),
            "chunks_created": chunks_created,
            "embedding_provider": provider.name,
            "embedding_model": provider.model,
        }
    except Exception as exc:
        db.rollback()
        try:
            db.execute(
                text("UPDATE sources SET ingest_status = 'failed', updated_at = now() WHERE id = CAST(:id AS uuid)"),
                {"id": source_id},
            )
            db.execute(
                text(
                    """
                    UPDATE ingestion_jobs
                    SET status = 'failed', error_message = :message, completed_at = now()
                    WHERE id = CAST(:id AS uuid)
                    """
                ),
                {"id": job_id, "message": str(exc)[:4000]},
            )
            db.commit()
        except Exception:
            db.rollback()
        raise
