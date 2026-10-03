from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.retrieval.embeddings import get_embedding_provider, vector_literal


@dataclass(slots=True)
class RetrievalResult:
    chunk_id: str
    source_code: str
    source_title: str
    section_title: str | None
    page_start: int | None
    page_end: int | None
    printed_page_label: str | None
    language: str
    text: str
    score: float
    concept_codes: list[str]
    visuals: list[dict[str, Any]]

    def as_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "source_code": self.source_code,
            "source_title": self.source_title,
            "section_title": self.section_title,
            "page_start": self.page_start,
            "page_end": self.page_end,
            "printed_page_label": self.printed_page_label,
            "language": self.language,
            "text": self.text,
            "score": round(self.score, 5),
            "concept_codes": self.concept_codes,
            "visuals": self.visuals,
        }


def search_chunks(
    db: Session,
    query: str,
    *,
    concept_code: str | None = None,
    source_codes: list[str] | None = None,
    language: str | None = None,
    top_k: int = 5,
) -> list[RetrievalResult]:
    settings = get_settings()
    provider = get_embedding_provider(settings.embedding_provider, settings.embedding_dimension)
    query_embedding = vector_literal(provider.embed(query))

    filters = ["cc.embedding IS NOT NULL"]
    params: dict[str, Any] = {"embedding": query_embedding, "top_k": max(1, min(top_k, 20))}

    if language:
        filters.append("cc.language = :language")
        params["language"] = language

    if concept_code:
        filters.append(
            """(
                primary_concept.code = :concept_code
                OR EXISTS (
                    SELECT 1
                    FROM content_chunk_concepts ccc_filter
                    JOIN concepts c_filter ON c_filter.id = ccc_filter.concept_id
                    WHERE ccc_filter.chunk_id = cc.id AND c_filter.code = :concept_code
                )
            )"""
        )
        params["concept_code"] = concept_code

    sql = text(
        f"""
        SELECT
            cc.id::text AS chunk_id,
            s.code AS source_code,
            s.title AS source_title,
            ss.title AS section_title,
            cc.page_start,
            cc.page_end,
            cc.language,
            cc.text_content,
            cc.metadata_json,
            1 - (cc.embedding <=> CAST(:embedding AS vector)) AS score,
            COALESCE(
                array_agg(DISTINCT mapped_concept.code)
                    FILTER (WHERE mapped_concept.code IS NOT NULL),
                ARRAY[]::text[]
            ) AS concept_codes
        FROM content_chunks cc
        JOIN sources s ON s.id = cc.source_id
        LEFT JOIN source_sections ss ON ss.id = cc.section_id
        LEFT JOIN concepts primary_concept ON primary_concept.id = cc.concept_id
        LEFT JOIN content_chunk_concepts ccc ON ccc.chunk_id = cc.id
        LEFT JOIN concepts mapped_concept ON mapped_concept.id = ccc.concept_id
        WHERE {' AND '.join(filters)}
        {{source_filter}}
        GROUP BY cc.id, s.code, s.title, ss.title
        ORDER BY cc.embedding <=> CAST(:embedding AS vector)
        LIMIT :top_k
        """.replace(
            "{source_filter}", "AND s.code IN :source_codes" if source_codes else ""
        )
    )

    if source_codes:
        sql = sql.bindparams(bindparam("source_codes", expanding=True))
        params["source_codes"] = source_codes

    rows = db.execute(sql, params).mappings().all()
    results: list[RetrievalResult] = []
    for row in rows:
        metadata = row["metadata_json"] or {}
        if isinstance(metadata, str):
            import json

            metadata = json.loads(metadata)
        results.append(
            RetrievalResult(
                chunk_id=row["chunk_id"],
                source_code=row["source_code"],
                source_title=row["source_title"],
                section_title=row["section_title"],
                page_start=row["page_start"],
                page_end=row["page_end"],
                printed_page_label=metadata.get("printed_page_label"),
                language=row["language"],
                text=row["text_content"],
                score=float(row["score"] or 0.0),
                concept_codes=list(row["concept_codes"] or []),
                visuals=list(metadata.get("visuals") or []),
            )
        )
    return results
