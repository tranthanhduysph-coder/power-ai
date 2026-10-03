from typing import Any


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
        {
            "type": "diagram",
            "title": "DNA replication fork",
            "nodes": [
                {"id": "fork", "label": "Replication fork" if lang == "en" else "Chạc tái bản"},
                {"id": "leading", "label": "Leading strand" if lang == "en" else "Mạch dẫn đầu"},
                {"id": "lagging", "label": "Lagging strand" if lang == "en" else "Mạch chậm"},
                {"id": "okazaki", "label": "Okazaki fragments" if lang == "en" else "Các đoạn Okazaki"},
            ],
            "edges": [
                {"from": "fork", "to": "leading"},
                {"from": "fork", "to": "lagging"},
                {"from": "lagging", "to": "okazaki"},
            ],
        },
        {"type": "table", **table},
        {"type": "checkpoint", "prompt": prompt},
    ]
