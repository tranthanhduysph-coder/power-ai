from __future__ import annotations

from typing import Any

from app.core.config import get_settings


DNA_OVERVIEW = {
    "vi": (
        "DNA polymerase chỉ kéo dài mạch mới theo chiều 5′→3′. Vì hai mạch khuôn DNA ngược chiều nhau, "
        "một mạch mới được tổng hợp liên tục (mạch dẫn đầu), còn mạch kia phải tổng hợp gián đoạn thành các đoạn Okazaki (mạch chậm)."
    ),
    "en": (
        "DNA polymerase extends a new strand only in the 5′→3′ direction. Because the two DNA templates are antiparallel, "
        "one new strand is synthesized continuously (leading strand), whereas the other is synthesized discontinuously as Okazaki fragments (lagging strand)."
    ),
}


def mock_tutor_blocks(language: str, message: str) -> list[dict[str, Any]]:
    lang = "en" if language == "en" else "vi"
    text = DNA_OVERVIEW[lang]
    if lang == "vi":
        table = {
            "headers": ["Đặc điểm", "Mạch dẫn đầu", "Mạch chậm"],
            "rows": [
                ["Kiểu tổng hợp", "Liên tục", "Gián đoạn"],
                ["Đoạn Okazaki", "Không", "Có"],
                ["Chiều tổng hợp mạch mới", "5′→3′", "5′→3′"],
            ],
        }
        prompt = "Vì sao mạch chậm cần các đoạn Okazaki?"
    else:
        table = {
            "headers": ["Feature", "Leading strand", "Lagging strand"],
            "rows": [
                ["Synthesis", "Continuous", "Discontinuous"],
                ["Okazaki fragments", "No", "Yes"],
                ["New-strand direction", "5′→3′", "5′→3′"],
            ],
        }
        prompt = "Why does the lagging strand require Okazaki fragments?"

    return [
        {"type": "text", "content": text},
        {"type": "table", **table},
        {"type": "checkpoint", "prompt": prompt},
    ]


def grounded_tutor_blocks(
    *,
    language: str,
    message: str,
    retrieved: list[Any],
) -> tuple[str, list[dict[str, Any]]]:
    settings = get_settings()
    if settings.ai_provider != "openai":
        return "mock", mock_tutor_blocks(language, message)
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required when AI_PROVIDER=openai")

    context_parts: list[str] = []
    for item in retrieved:
        page = (
            f"{item.page_start}"
            if item.page_start == item.page_end or item.page_end is None
            else f"{item.page_start}-{item.page_end}"
        )
        printed = item.printed_page_label or ""
        context_parts.append(
            f"SOURCE={item.source_code}; TITLE={item.source_title}; PDF_PAGE={page}; PRINTED_PAGE={printed}; SECTION={item.section_title or ''}\n{item.text}"
        )
    context = "\n\n---\n\n".join(context_parts)

    if language == "en":
        instruction = (
            "Answer the learner in English using only the supplied textbook context. "
            "If the context is insufficient, say that the source currently available is insufficient. "
            "Be concise, pedagogically clear, and do not invent citations."
        )
    else:
        instruction = (
            "Trả lời người học bằng tiếng Việt, chỉ dựa trên ngữ cảnh SGK/tài liệu được cung cấp. "
            "Nếu ngữ cảnh chưa đủ, nói rõ nguồn hiện có chưa đủ. "
            "Giải thích ngắn gọn, dễ học và không tự tạo trích dẫn."
        )

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.responses.create(
        model=settings.tutor_model,
        input=[
            {
                "role": "user",
                "content": (
                    f"{instruction}\n\nLEARNER QUESTION:\n{message}\n\nSOURCE CONTEXT:\n{context}"
                ),
            }
        ],
    )
    return "openai", [{"type": "text", "content": response.output_text.strip()}]
