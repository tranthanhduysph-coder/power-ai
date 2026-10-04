from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from pathlib import Path


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"\s+", " ", value).strip()


class ConceptAliasMapper:
    def __init__(self, aliases: dict[str, list[str]]):
        self.aliases = {
            code: [_normalize(alias) for alias in values if alias.strip()]
            for code, values in aliases.items()
        }

    @classmethod
    def from_json(cls, path: str | Path) -> "ConceptAliasMapper":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(data)

    def rank(self, text: str, explicit_codes: list[str] | None = None) -> list[tuple[str, float, str]]:
        normalized = _normalize(text)
        scores: Counter[str] = Counter()
        methods: dict[str, str] = {}

        for code in explicit_codes or []:
            scores[code] += 100.0
            methods[code] = "explicit"

        for code, aliases in self.aliases.items():
            for alias in aliases:
                if not alias:
                    continue
                occurrences = normalized.count(alias)
                if occurrences:
                    # Longer aliases are more specific; repeated mentions add evidence.
                    scores[code] += occurrences * (1.0 + min(len(alias), 40) / 40.0)
                    methods.setdefault(code, "alias")

        if not scores:
            return []

        top = max(scores.values())
        return [
            (code, min(1.0, score / top), methods.get(code, "alias"))
            for code, score in scores.most_common()
        ]
