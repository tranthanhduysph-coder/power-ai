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
    phase: str = "WORK",
    learner_context: dict[str, Any] | None = None,
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

    phase = (phase or "WORK").upper()
    learner_context = learner_context or {}
    if language == "en":
        base = (
            "Answer the learner in English using only the supplied textbook context. "
            "If the context is insufficient, say that the source currently available is insufficient. "
            "Do not invent citations. "
        )
        phase_rule = {
            "PREPARE": "The learner is in PREPARE. Clarify prior knowledge and goals; avoid doing the whole lesson for them. Give at most one short explanation, then ask one focused readiness question.",
            "ORGANIZE": "The learner is in ORGANIZE. Use the learner's current organize_map when available. Ask them to justify or refine one relationship at a time; emphasize relationships, categories, sequences, and comparisons. Do not replace their map with a complete ready-made map unless explicitly requested after they have attempted one.",
            "WORK": "The learner is in WORK. Explain and scaffold the biology clearly, using examples and a brief check-for-understanding when useful.",
            "EVALUATE": "The learner is in EVALUATE. Do not simply reveal answers to an active assessment. Give hints, criteria, or feedback on reasoning instead.",
            "RETHINK": "The learner is in RETHINK. Help the learner identify why an error happened, articulate the corrected idea, and state one concrete adjustment for next time.",
        }.get(phase, "Explain the biology clearly and concisely.")
    else:
        base = (
            "Trả lời người học bằng tiếng Việt, chỉ dựa trên ngữ cảnh SGK/tài liệu được cung cấp. "
            "Nếu ngữ cảnh chưa đủ, nói rõ nguồn hiện có chưa đủ. Không tự tạo trích dẫn. "
        )
        phase_rule = {
            "PREPARE": "Người học đang ở PREPARE. Hãy làm rõ kiến thức nền và mục tiêu; không giảng thay toàn bộ bài. Chỉ giải thích rất ngắn khi cần rồi đặt một câu hỏi kiểm tra sẵn sàng học tập.",
            "ORGANIZE": "Người học đang ở ORGANIZE. Nếu learner_context có organize_map, hãy bám vào bản đồ do chính người học đang xây. Yêu cầu họ giải thích hoặc tinh chỉnh từng quan hệ; ưu tiên quan hệ khái niệm, phân loại, trình tự và so sánh. Không thay người học bằng một sơ đồ hoàn chỉnh có sẵn trừ khi họ đã thử xây và chủ động yêu cầu xem mẫu tham khảo.",
            "WORK": "Người học đang ở WORK. Giải thích và scaffold kiến thức Sinh học rõ ràng, có thể dùng ví dụ và một câu kiểm tra hiểu biết ngắn.",
            "EVALUATE": "Người học đang ở EVALUATE. Không đưa thẳng đáp án cho một bài đánh giá đang làm; hãy gợi ý, nêu tiêu chí hoặc phản hồi vào lập luận.",
            "RETHINK": "Người học đang ở RETHINK. Giúp xác định vì sao sai, phát biểu lại ý đúng và nêu một điều chỉnh cụ thể cho lần học tiếp theo.",
        }.get(phase, "Giải thích kiến thức Sinh học ngắn gọn, rõ ràng.")
    instruction = base + phase_rule

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.responses.create(
        model=settings.tutor_model,
        input=[
            {
                "role": "user",
                "content": (
                    f"{instruction}\n\nPOWER PHASE: {phase}\nLEARNER CONTEXT: {learner_context}\n\nLEARNER QUESTION:\n{message}\n\nSOURCE CONTEXT:\n{context}"
                ),
            }
        ],
    )
    return "openai", [{"type": "text", "content": response.output_text.strip()}]
