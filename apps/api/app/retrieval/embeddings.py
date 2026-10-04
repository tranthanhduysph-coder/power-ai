from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Protocol

from app.core.config import get_settings

_TOKEN = re.compile(r"\w+", flags=re.UNICODE)


class EmbeddingProvider(Protocol):
    name: str
    model: str
    dimension: int

    def embed(self, text: str) -> list[float]: ...


@dataclass(slots=True)
class LocalHashEmbeddingProvider:
    """Zero-cost deterministic lexical embedding for local plumbing tests."""

    dimension: int = 1536
    name: str = "local_hash"
    model: str = "local-hash-v1"

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        normalized = unicodedata.normalize("NFKC", text).casefold()
        tokens = _TOKEN.findall(normalized)
        if not tokens:
            return vector

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


@dataclass(slots=True)
class OpenAIEmbeddingProvider:
    dimension: int = 1536
    name: str = "openai"
    model: str = "text-embedding-3-small"
    _client: Any = field(init=False, repr=False)

    def __post_init__(self) -> None:
        from openai import OpenAI

        settings = get_settings()
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai")
        self._client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.embedding_model

    def embed(self, text: str) -> list[float]:
        response = self._client.embeddings.create(
            model=self.model,
            input=text,
            dimensions=self.dimension,
        )
        return list(response.data[0].embedding)


def get_embedding_provider(provider: str = "local_hash", dimension: int = 1536) -> EmbeddingProvider:
    if provider == "local_hash":
        return LocalHashEmbeddingProvider(dimension=dimension)
    if provider == "openai":
        return OpenAIEmbeddingProvider(dimension=dimension)
    raise ValueError(f"Unsupported embedding provider '{provider}'")


def vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in values) + "]"
