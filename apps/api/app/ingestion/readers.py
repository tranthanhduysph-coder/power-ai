from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import pymupdf

from app.core.config import get_settings
from app.ingestion.manifest import project_root
from app.ingestion.models import DocumentPage
from app.ingestion.vision import OpenAIVisionPageExtractor


def pdf_page_count(path: str | Path) -> int:
    file_path = Path(path)
    with pymupdf.open(file_path) as document:
        return len(document)


def _cache_path(cache_namespace: str, page_number: int) -> Path:
    settings = get_settings()
    root = project_root() / settings.vision_cache_dir
    return root / cache_namespace / f"page-{page_number:04d}.json"


def _load_cached_page(cache_namespace: str, page_number: int) -> DocumentPage | None:
    path = _cache_path(cache_namespace, page_number)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return DocumentPage(
        number=page_number,
        text=str(data.get("text") or ""),
        printed_page_label=data.get("printed_page_label"),
        extraction_method=str(data.get("extraction_method") or "vision"),
        extraction_provider=data.get("extraction_provider"),
        extraction_model=data.get("extraction_model"),
        visuals=list(data.get("visuals") or []),
        metadata=dict(data.get("metadata") or {}),
    )


def _save_cached_page(cache_namespace: str, page: DocumentPage) -> None:
    path = _cache_path(cache_namespace, page.number)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "page_number": page.number,
                "printed_page_label": page.printed_page_label,
                "text": page.text,
                "extraction_method": page.extraction_method,
                "extraction_provider": page.extraction_provider,
                "extraction_model": page.extraction_model,
                "visuals": page.visuals,
                "metadata": page.metadata,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _vision_extractor():
    settings = get_settings()
    if settings.vision_provider == "openai":
        return OpenAIVisionPageExtractor()
    if settings.vision_provider in {"disabled", "none", "off", ""}:
        return None
    raise ValueError(f"Unsupported VISION_PROVIDER: {settings.vision_provider}")


def read_document(
    path: str | Path,
    *,
    page_numbers: Iterable[int] | None = None,
    cache_namespace: str = "default",
    language: str = "vi",
) -> list[DocumentPage]:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Source document not found: {file_path}")

    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return _read_pdf(
            file_path,
            page_numbers=page_numbers,
            cache_namespace=cache_namespace,
            language=language,
        )
    if suffix in {".txt", ".md"}:
        return [DocumentPage(number=1, text=file_path.read_text(encoding="utf-8"))]

    raise ValueError(f"Unsupported source format: {suffix}. Use PDF, TXT, or MD.")


def _read_pdf(
    path: Path,
    *,
    page_numbers: Iterable[int] | None,
    cache_namespace: str,
    language: str,
) -> list[DocumentPage]:
    settings = get_settings()
    extractor = None

    with pymupdf.open(path) as document:
        total = len(document)
        selected = sorted(set(page_numbers or range(1, total + 1)))
        invalid = [number for number in selected if number < 1 or number > total]
        if invalid:
            raise ValueError(f"PDF page numbers out of range 1-{total}: {invalid[:10]}")

        pages: list[DocumentPage] = []
        for number in selected:
            pdf_page = document[number - 1]
            native_text = (pdf_page.get_text("text") or "").strip()

            if len(native_text) >= settings.vision_min_text_chars:
                pages.append(
                    DocumentPage(
                        number=number,
                        text=native_text,
                        extraction_method="native_text",
                        extraction_provider="pymupdf",
                        extraction_model=pymupdf.__version__,
                    )
                )
                continue

            cached = _load_cached_page(cache_namespace, number)
            if cached is not None:
                pages.append(cached)
                continue

            if extractor is None:
                extractor = _vision_extractor()
            if extractor is None:
                raise RuntimeError(
                    f"PDF page {number} has no usable text layer. "
                    "Set VISION_PROVIDER=openai and OPENAI_API_KEY in .env to read scanned pages directly."
                )

            matrix = pymupdf.Matrix(settings.vision_render_scale, settings.vision_render_scale)
            pixmap = pdf_page.get_pixmap(matrix=matrix, alpha=False)
            image_bytes = pixmap.tobytes("jpeg", jpg_quality=88)
            extracted = extractor.extract(
                image_bytes=image_bytes,
                page_number=number,
                language=language,
            )
            page = DocumentPage(
                number=number,
                text=extracted.text,
                printed_page_label=extracted.printed_page_label,
                extraction_method="vision",
                extraction_provider=extractor.provider_name,
                extraction_model=extractor.model,
                visuals=extracted.visuals,
            )
            _save_cached_page(cache_namespace, page)
            pages.append(page)

    return pages


def extract_page_range(
    pages: list[DocumentPage],
    page_start: int | None,
    page_end: int | None,
) -> str:
    if not pages:
        return ""

    start = page_start or pages[0].number
    end = page_end or pages[-1].number
    if start < 1 or end < start:
        raise ValueError(f"Invalid page range: {start}-{end}")

    selected = [p.text.strip() for p in pages if start <= p.number <= end and p.text.strip()]
    return "\n\n".join(selected)
