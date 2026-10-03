from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from dataclasses import dataclass
from typing import Protocol

_TOKEN = re.compile(r"\w+", flags=re.UNICODE)


class EmbeddingProvider(Protocol):
    name: str
    model: str
    dimension: int

    def embed(self, text: str) -> list[float]: ...


@dataclass(slots=True)
class LocalHashEmbeddingProvider:
    """Zero-cost deterministic lexical embedding for local development.

    It is intentionally not a production semantic model. It proves the full
    pgvector ingestion/retrieval path without API keys or model downloads.
    Replacing it later does not change the database or retrieval contracts.
    """

    dimension: int = 1536
    name: str = "local_hash"
    model: str = "local-hash-v1"

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        normalized = unicodedata.normalize("NFKC", text).casefold()
        tokens = _TOKEN.findall(normalized)
        if not tokens:
            return vector

        # Include unigrams and adjacent bigrams to preserve some phrase signal.
        features = tokens + [f"{a}::{b}" for a, b in zip(tokens, tokens[1:])]
        for feature in features:
            digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=16).digest()
            index = int.from_bytes(digest[:8], "big") % self.dimension
            sign = -1.0 if digest[8] & 1 else 1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm:
            vector = [value / norm for value in vector]
        return vector


def get_embedding_provider(provider: str = "local_hash", dimension: int = 1536) -> EmbeddingProvider:
    if provider == "local_hash":
        return LocalHashEmbeddingProvider(dimension=dimension)
    raise ValueError(
        f"Unsupported embedding provider '{provider}'. "
        "v0.2 ships with local_hash; add a production provider behind this interface later."
    )


def vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in values) + "]"
