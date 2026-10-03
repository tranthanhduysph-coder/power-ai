from __future__ import annotations

from typing import Any


_UNIT_BLUEPRINTS: dict[str, dict[str, Any]] = {
    "B12_DNA_REPLICATION": {
        "title_vi": "DNA và cơ chế tái bản DNA",
        "title_en": "DNA and DNA replication",
        "outcomes_vi": [
            "Nêu được nguyên tắc và ý nghĩa của quá trình tái bản DNA.",
            "Giải thích được vì sao xuất hiện mạch dẫn đầu, mạch chậm và các đoạn Okazaki.",
            "Phân biệt được vai trò cơ bản của DNA polymerase và DNA ligase trong tái bản DNA.",
        ],
        "outcomes_en": [
            "State the principles and significance of DNA replication.",
            "Explain why leading and lagging strands, including Okazaki fragments, arise.",
            "Distinguish the basic roles of DNA polymerase and DNA ligase in DNA replication.",
        ],
        "keywords": [
            "dna",
            "tái bản",
            "replication",
            "polymerase",
            "mạch",
            "strand",
            "okazaki",
            "ligase",
        ],
        "diagnostic_items": [
            {
                "code": "PREP_DNA_01",
                "concept_code": "BIO.DNA.STRUCTURE",
                "question_type": "true_false",
                "prompt_vi": "Hai mạch polynucleotide của DNA chạy ngược chiều nhau.",
                "prompt_en": "The two polynucleotide strands of DNA run antiparallel to each other.",
                "options": [],
                "expected": True,
            },
            {
                "code": "PREP_DNA_02",
                "concept_code": "BIO.DNA.STRUCTURE",
                "question_type": "mcq",
                "prompt_vi": "Trong DNA, adenine (A) bắt cặp bổ sung với base nào?",
                "prompt_en": "In DNA, which base pairs complementarily with adenine (A)?",
                "options": [
                    {"key": "A", "text_vi": "Thymine (T)", "text_en": "Thymine (T)"},
                    {"key": "B", "text_vi": "Guanine (G)", "text_en": "Guanine (G)"},
                    {"key": "C", "text_vi": "Cytosine (C)", "text_en": "Cytosine (C)"},
                    {"key": "D", "text_vi": "Uracil (U)", "text_en": "Uracil (U)"},
                ],
                "expected": "A",
            },
            {
                "code": "PREP_DNA_03",
                "concept_code": "BIO.DNA.STRUCTURE",
                "question_type": "mcq",
                "prompt_vi": "Một nucleotide DNA gồm ba thành phần nào?",
                "prompt_en": "Which three components make up a DNA nucleotide?",
                "options": [
                    {"key": "A", "text_vi": "Đường ribose, phosphate và base nitrogen", "text_en": "Ribose, phosphate and a nitrogenous base"},
                    {"key": "B", "text_vi": "Đường deoxyribose, phosphate và base nitrogen", "text_en": "Deoxyribose, phosphate and a nitrogenous base"},
                    {"key": "C", "text_vi": "Glucose, phosphate và amino acid", "text_en": "Glucose, phosphate and an amino acid"},
                    {"key": "D", "text_vi": "Deoxyribose, lipid và base nitrogen", "text_en": "Deoxyribose, lipid and a nitrogenous base"},
                ],
                "expected": "B",
            },
        ],
    }
}


_ACTION_VERBS_VI = (
    "mô tả",
    "giải thích",
    "phân biệt",
    "so sánh",
    "trình bày",
    "xác định",
    "vận dụng",
    "trả lời",
    "nêu",
)
_ACTION_VERBS_EN = (
    "describe",
    "explain",
    "distinguish",
    "compare",
    "identify",
    "apply",
    "answer",
    "state",
)


def get_prepare_blueprint(unit_code: str, language: str = "vi") -> dict[str, Any]:
    blueprint = _UNIT_BLUEPRINTS.get(unit_code)
    if not blueprint:
        raise KeyError(unit_code)
    lang = "en" if language == "en" else "vi"
    return {
        "unit_code": unit_code,
        "title": blueprint[f"title_{lang}"],
        "outcomes": blueprint[f"outcomes_{lang}"],
        "diagnostic_items": [
            {
                "code": item["code"],
                "concept_code": item["concept_code"],
                "question_type": item["question_type"],
                "prompt": item[f"prompt_{lang}"],
                "options": [
                    {
                        "key": option["key"],
                        "text": option[f"text_{lang}"],
                    }
                    for option in item["options"]
                ],
            }
            for item in blueprint["diagnostic_items"]
        ],
    }


def analyze_goal(goal: str, target_minutes: int, unit_code: str, language: str = "vi") -> dict[str, Any]:
    blueprint = _UNIT_BLUEPRINTS.get(unit_code)
    if not blueprint:
        raise KeyError(unit_code)

    lang = "en" if language == "en" else "vi"
    normalized = " ".join(goal.strip().lower().split())
    verbs = _ACTION_VERBS_EN if lang == "en" else _ACTION_VERBS_VI

    relevant = any(keyword in normalized for keyword in blueprint["keywords"])
    specific = relevant and len(normalized) >= 20
    measurable = any(verb in normalized for verb in verbs) or any(ch.isdigit() for ch in normalized)
    achievable = 10 <= target_minutes <= 90 and len(normalized) >= 10
    time_bound = target_minutes > 0

    checks = {
        "specific": specific,
        "measurable": measurable,
        "achievable": achievable,
        "relevant": relevant,
        "time_bound": time_bound,
    }
    score = sum(1 for value in checks.values() if value)

    if lang == "en":
        suggestions = []
        if not specific:
            suggestions.append("Name the exact DNA-replication idea you want to understand.")
        if not measurable:
            suggestions.append("Use an observable verb such as explain, compare, identify or answer.")
        if not achievable:
            suggestions.append("Keep this session focused and use a realistic duration between 10 and 90 minutes.")
        if not relevant:
            suggestions.append("Link the goal directly to DNA replication or one of its core concepts.")
        if not time_bound:
            suggestions.append("Set a target duration for this learning session.")
        example = (
            f"Within {target_minutes} minutes, I can explain why DNA replication has leading and lagging strands "
            "and answer at least 4 out of 5 related questions correctly."
        )
    else:
        suggestions = []
        if not specific:
            suggestions.append("Nêu rõ nội dung cụ thể của tái bản DNA mà bạn muốn hiểu.")
        if not measurable:
            suggestions.append("Dùng động từ có thể quan sát được như giải thích, so sánh, xác định hoặc trả lời.")
        if not achievable:
            suggestions.append("Giữ mục tiêu đủ tập trung và chọn thời lượng thực tế từ 10 đến 90 phút.")
        if not relevant:
            suggestions.append("Gắn mục tiêu trực tiếp với tái bản DNA hoặc một khái niệm cốt lõi của bài.")
        if not time_bound:
            suggestions.append("Đặt thời lượng mục tiêu cho phiên học.")
        example = (
            f"Trong {target_minutes} phút, tôi có thể giải thích vì sao tái bản DNA có mạch dẫn đầu và mạch chậm, "
            "đồng thời trả lời đúng ít nhất 4/5 câu hỏi liên quan."
        )

    return {
        "score": score,
        "max_score": 5,
        "checks": checks,
        "suggestions": suggestions,
        "example": example,
    }


def score_diagnostic(unit_code: str, answers: dict[str, Any]) -> dict[str, Any]:
    blueprint = _UNIT_BLUEPRINTS.get(unit_code)
    if not blueprint:
        raise KeyError(unit_code)

    results = []
    correct = 0
    missing = []
    weak_concepts: set[str] = set()

    for item in blueprint["diagnostic_items"]:
        code = item["code"]
        if code not in answers:
            missing.append(code)
            continue

        received = answers[code]
        expected = item["expected"]
        if item["question_type"] == "mcq":
            received = str(received).strip().upper()
        elif item["question_type"] == "true_false":
            if isinstance(received, str):
                received = received.strip().lower() in {"true", "1", "yes", "đúng", "dung"}
            else:
                received = bool(received)

        is_correct = received == expected
        correct += int(is_correct)
        if not is_correct:
            weak_concepts.add(item["concept_code"])
        results.append(
            {
                "code": code,
                "concept_code": item["concept_code"],
                "is_correct": is_correct,
            }
        )

    total = len(blueprint["diagnostic_items"])
    answered = total - len(missing)
    readiness = (correct / total) if total else 0.0
    return {
        "correct": correct,
        "total": total,
        "answered": answered,
        "readiness": round(readiness, 4),
        "missing": missing,
        "weak_concepts": sorted(weak_concepts),
        "results": results,
    }
