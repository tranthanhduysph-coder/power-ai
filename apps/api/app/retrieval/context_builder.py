from __future__ import annotations

from app.retrieval.search import RetrievalResult


def build_context(results: list[RetrievalResult], max_chars: int = 7000) -> str:
    blocks: list[str] = []
    used = 0
    for index, item in enumerate(results, start=1):
        page = ""
        if item.page_start is not None:
            page = f" p.{item.page_start}"
            if item.page_end and item.page_end != item.page_start:
                page = f" pp.{item.page_start}-{item.page_end}"
        header = f"[{index}] {item.source_code} | {item.section_title or 'Untitled'}{page}"
        block = f"{header}\n{item.text.strip()}"
        if blocks and used + len(block) > max_chars:
            break
        blocks.append(block)
        used += len(block)
    return "\n\n".join(blocks)
