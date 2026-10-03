from __future__ import annotations

from pathlib import Path

from app.ingestion.models import DocumentPage


def read_document(path: str | Path) -> list[DocumentPage]:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Source document not found: {file_path}")

    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return _read_pdf(file_path)
    if suffix in {".txt", ".md"}:
        return [DocumentPage(number=1, text=file_path.read_text(encoding="utf-8"))]

    raise ValueError(f"Unsupported source format: {suffix}. Use PDF, TXT, or MD.")


def _read_pdf(path: Path) -> list[DocumentPage]:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages: list[DocumentPage] = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append(DocumentPage(number=index, text=text))
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
