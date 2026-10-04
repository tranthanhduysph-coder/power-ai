from __future__ import annotations

import re

from app.ingestion.models import TextChunk

_WHITESPACE = re.compile(r"[ \t]+")
_TOKENISH = re.compile(r"\w+|[^\w\s]", flags=re.UNICODE)


def normalize_text(text: str) -> str:
    lines = [_WHITESPACE.sub(" ", line).strip() for line in text.replace("\r\n", "\n").split("\n")]
    out: list[str] = []
    blank = False
    for line in lines:
        if not line:
            if out and not blank:
                out.append("")
            blank = True
        else:
            out.append(line)
            blank = False
    return "\n".join(out).strip()


def estimate_token_count(text: str) -> int:
    # Provider-agnostic estimate; sufficient for chunk accounting. Exact token
    # counts can be added later for the selected production model.
    count = len(_TOKENISH.findall(text))
    return max(1, int(round(count * 1.10))) if text.strip() else 0


def _split_long_block(block: str, max_chars: int) -> list[str]:
    if len(block) <= max_chars:
        return [block]

    # Prefer sentence-ish boundaries before falling back to hard character cuts.
    sentences = re.split(r"(?<=[.!?。！？])\s+", block)
    if len(sentences) == 1:
        return [block[i : i + max_chars] for i in range(0, len(block), max_chars)]

    pieces: list[str] = []
    current = ""
    for sentence in sentences:
        candidate = sentence if not current else f"{current} {sentence}"
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            pieces.append(current)
        if len(sentence) <= max_chars:
            current = sentence
        else:
            pieces.extend(sentence[i : i + max_chars] for i in range(0, len(sentence), max_chars))
            current = ""
    if current:
        pieces.append(current)
    return pieces


def chunk_text(text: str, max_chars: int = 2400, overlap_chars: int = 250) -> list[TextChunk]:
    if max_chars < 400:
        raise ValueError("max_chars must be >= 400")
    if overlap_chars < 0 or overlap_chars >= max_chars:
        raise ValueError("overlap_chars must be >= 0 and < max_chars")

    cleaned = normalize_text(text)
    if not cleaned:
        return []

    raw_blocks = [b.strip() for b in re.split(r"\n\s*\n", cleaned) if b.strip()]
    blocks: list[str] = []
    for block in raw_blocks:
        blocks.extend(_split_long_block(block, max_chars))

    chunks: list[str] = []
    current = ""
    for block in blocks:
        candidate = block if not current else f"{current}\n\n{block}"
        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            chunks.append(current.strip())
        overlap = current[-overlap_chars:].strip() if current and overlap_chars else ""
        current = f"{overlap}\n\n{block}".strip() if overlap else block
        if len(current) > max_chars:
            # This can happen when overlap + an already max-sized block exceed the limit.
            chunks.append(current[:max_chars].strip())
            current = current[max_chars - overlap_chars :].strip() if overlap_chars else ""

    if current:
        chunks.append(current.strip())

    # Avoid duplicate chunks caused by very short trailing overlap.
    deduped: list[str] = []
    for chunk in chunks:
        if chunk and (not deduped or chunk != deduped[-1]):
            deduped.append(chunk)

    return [
        TextChunk(index=i, text=chunk, token_count=estimate_token_count(chunk))
        for i, chunk in enumerate(deduped)
    ]
