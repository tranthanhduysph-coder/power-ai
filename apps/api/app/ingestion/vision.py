from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass
from typing import Any

from app.core.config import get_settings


_JSON_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", flags=re.IGNORECASE | re.DOTALL)


@dataclass(slots=True)
class VisionPageResult:
    text: str
    printed_page_label: str | None
    visuals: list[dict[str, Any]]


def _extract_json_object(raw: str) -> dict[str, Any]:
    cleaned = _JSON_FENCE.sub("", raw.strip()).strip()
    try:
        value = json.loads(cleaned)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end > start:
        value = json.loads(cleaned[start : end + 1])
        if isinstance(value, dict):
            return value
    raise ValueError("Vision model did not return a valid JSON object")


class OpenAIVisionPageExtractor:
    provider_name = "openai"

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.openai_api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is missing. Set it in the repository .env before ingesting image-only PDFs."
            )
        from openai import OpenAI

        self.model = settings.vision_model
        self.client = OpenAI(api_key=settings.openai_api_key)

    def extract(self, *, image_bytes: bytes, page_number: int, language: str) -> VisionPageResult:
        encoded = base64.b64encode(image_bytes).decode("ascii")
        prompt = f"""
You are extracting ONE scanned textbook page for a private learning system.
Language of the source is primarily: {language}.

Return VALID JSON ONLY with this exact top-level shape:
{{
  "printed_page_label": "string or null",
  "text": "full readable page text in logical reading order",
  "visuals": [
    {{
      "type": "figure|table|diagram|chart|photo|other",
      "label": "visible figure/table label or null",
      "caption": "visible caption or null",
      "description": "brief factual description of what the visual shows"
    }}
  ]
}}

Rules:
- Preserve the textbook wording. Do NOT summarize ordinary paragraphs.
- Include headings, bullets, questions, callout boxes, equations and table contents.
- For tables, transcribe the table into readable Markdown inside the text field when feasible.
- Keep Vietnamese diacritics exactly when readable.
- If a small fragment is genuinely unreadable, write [không đọc rõ] instead of guessing.
- The printed_page_label is the page number printed on the textbook page, not PDF index {page_number}.
- Do not add facts not visible on the page.
""".strip()

        response = self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {
                            "type": "input_image",
                            "image_url": f"data:image/jpeg;base64,{encoded}",
                            "detail": "high",
                        },
                    ],
                }
            ],
        )
        data = _extract_json_object(response.output_text)
        text_value = str(data.get("text") or "").strip()
        label = data.get("printed_page_label")
        label = str(label).strip() if label not in (None, "") else None
        visuals_raw = data.get("visuals") or []
        visuals = [item for item in visuals_raw if isinstance(item, dict)]
        return VisionPageResult(text=text_value, printed_page_label=label, visuals=visuals)
