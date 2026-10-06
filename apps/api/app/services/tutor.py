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

    if lang == "vi":
        rich_text = (
            "#### Ý chính\n\n"
            f"{text}\n\n"
            "**Điểm cần nhớ:** cả hai mạch mới đều được kéo dài theo chiều **5′→3′**; sự khác nhau là ở cách tổng hợp liên tục hay gián đoạn."
        )
    else:
        rich_text = (
            "#### Key idea\n\n"
            f"{text}\n\n"
            "**Remember:** both new strands are extended **5′→3′**; the difference is continuous versus discontinuous synthesis."
        )
    return [
        {"type": "text", "content": rich_text},
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
    image_data_url: str | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    settings = get_settings()
    if settings.ai_provider != "openai":
        return "mock", mock_tutor_blocks(language, message)
    if image_data_url and not settings.tutor_vision_enabled:
        raise RuntimeError("Tutor image analysis is disabled")
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
            "Answer the learner in English using the supplied textbook context"
            + (" and the learner-provided image" if image_data_url else "")
            + ". If the context is insufficient for a biological claim, say so. "
            + ("You may describe visible image features, but do not invent biological details that are not supported by the image or source context. " if image_data_url else "")
            + "Do not invent citations. "
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
            "Trả lời người học bằng tiếng Việt dựa trên ngữ cảnh SGK/tài liệu được cung cấp"
            + (" và hình ảnh do người học gửi" if image_data_url else "")
            + ". Nếu ngữ cảnh chưa đủ cho một kết luận Sinh học, hãy nói rõ. "
            + ("Có thể mô tả những gì nhìn thấy trong hình nhưng không suy diễn chi tiết Sinh học ngoài bằng chứng từ hình hoặc nguồn. " if image_data_url else "")
            + "Không tự tạo trích dẫn. "
        )
        phase_rule = {
            "PREPARE": "Người học đang ở PREPARE. Hãy làm rõ kiến thức nền và mục tiêu; không giảng thay toàn bộ bài. Chỉ giải thích rất ngắn khi cần rồi đặt một câu hỏi kiểm tra sẵn sàng học tập.",
            "ORGANIZE": "Người học đang ở ORGANIZE. Nếu learner_context có organize_map, hãy bám vào bản đồ do chính người học đang xây. Yêu cầu họ giải thích hoặc tinh chỉnh từng quan hệ; ưu tiên quan hệ khái niệm, phân loại, trình tự và so sánh. Không thay người học bằng một sơ đồ hoàn chỉnh có sẵn trừ khi họ đã thử xây và chủ động yêu cầu xem mẫu tham khảo.",
            "WORK": "Người học đang ở WORK. Giải thích và scaffold kiến thức Sinh học rõ ràng, có thể dùng ví dụ và một câu kiểm tra hiểu biết ngắn.",
            "EVALUATE": "Người học đang ở EVALUATE. Không đưa thẳng đáp án cho một bài đánh giá đang làm; hãy gợi ý, nêu tiêu chí hoặc phản hồi vào lập luận.",
            "RETHINK": "Người học đang ở RETHINK. Giúp xác định vì sao sai, phát biểu lại ý đúng và nêu một điều chỉnh cụ thể cho lần học tiếp theo.",
        }.get(phase, "Giải thích kiến thức Sinh học ngắn gọn, rõ ràng.")
    if language == "en":
        format_rule = (
            " Format the answer as clean Markdown that will be rendered as semantic HTML. "
            "Use short paragraphs, optional level-4 headings (####), **bold** only for key terms, *italics* sparingly, "
            "and bullet or numbered lists only when they genuinely improve readability. "
            "Do not output raw HTML, fenced code blocks, decorative symbols, repeated hashes, emoji, or markdown tables. "
            "Keep the response visually calm and usually under 350 words unless the learner explicitly asks for detail."
        )
    else:
        format_rule = (
            " Trình bày bằng Markdown sạch để giao diện chuyển thành HTML có ngữ nghĩa. "
            "Dùng đoạn văn ngắn; có thể dùng tiêu đề cấp 4 (####); chỉ **in đậm** thuật ngữ hoặc ý then chốt; *in nghiêng* rất hạn chế; "
            "chỉ dùng danh sách khi thật sự giúp dễ đọc. Không xuất HTML thô, code block, ký hiệu trang trí, chuỗi dấu # dư thừa, emoji hoặc bảng Markdown. "
            "Xuống dòng hợp lý, văn phong tự nhiên và thường không quá 350 từ trừ khi người học chủ động yêu cầu giải thích chi tiết."
        )
    instruction = base + phase_rule + format_rule

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    prompt_text = (
        f"{instruction}\n\nPOWER PHASE: {phase}\nLEARNER CONTEXT: {learner_context}"
        f"\n\nLEARNER QUESTION:\n{message}\n\nSOURCE CONTEXT:\n{context}"
    )
    content: list[dict[str, Any]] = [{"type": "input_text", "text": prompt_text}]
    if image_data_url:
        content.append({"type": "input_image", "image_url": image_data_url, "detail": "auto"})

    response = client.responses.create(
        model=settings.tutor_model,
        input=[{"role": "user", "content": content}],
    )
    return "openai", [{"type": "text", "content": response.output_text.strip()}]


def generate_grounded_image(
    *,
    language: str,
    prompt: str,
    retrieved: list[Any],
) -> tuple[str, str]:
    settings = get_settings()
    if settings.ai_provider != "openai":
        raise RuntimeError("Image generation requires AI_PROVIDER=openai")
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required for image generation")

    context_parts: list[str] = []
    total_chars = 0
    for item in retrieved:
        if total_chars >= 7000:
            break
        page = (
            f"{item.page_start}"
            if item.page_start == item.page_end or item.page_end is None
            else f"{item.page_start}-{item.page_end}"
        )
        excerpt = (item.text or "")[: max(0, 7000 - total_chars)]
        context_parts.append(
            f"SOURCE={item.source_code}; PDF_PAGE={page}; SECTION={item.section_title or ''}\n{excerpt}"
        )
        total_chars += len(excerpt)
    context = "\n\n---\n\n".join(context_parts)
    if not context:
        raise ValueError("No grounded source context is available for image generation")

    if language == "en":
        full_prompt = (
            "Create a scientifically accurate educational Biology illustration for a secondary-school learner. "
            "Use the source context below as the factual basis. Prefer a clean textbook-style diagram or explanatory illustration, "
            "with minimal labels, no decorative text, no watermark, and no unsupported details. "
            f"Learner request: {prompt}\n\nSOURCE CONTEXT:\n{context}"
        )
    else:
        full_prompt = (
            "Tạo một hình minh họa Sinh học chính xác về mặt khoa học cho học sinh trung học. "
            "Dùng ngữ cảnh nguồn dưới đây làm cơ sở nội dung. Ưu tiên sơ đồ hoặc hình giải thích sạch, kiểu sách giáo khoa, "
            "ít nhãn, không thêm chữ trang trí, không watermark và không thêm chi tiết không được nguồn hỗ trợ. "
            f"Yêu cầu của người học: {prompt}\n\nNGỮ CẢNH NGUỒN:\n{context}"
        )

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    result = client.images.generate(
        model=settings.image_model,
        prompt=full_prompt,
        size="1024x1024",
        quality="medium",
    )
    image_base64 = result.data[0].b64_json if result.data else None
    if not image_base64:
        raise RuntimeError("OpenAI returned no image data")
    return settings.image_model, f"data:image/png;base64,{image_base64}"
