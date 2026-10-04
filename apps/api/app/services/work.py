from __future__ import annotations

from dataclasses import dataclass
from typing import Any


_WORK_BLUEPRINTS: dict[str, dict[str, Any]] = {
    "B12_DNA_REPLICATION": {
        "vi": {
            "title": "Làm việc sâu với cơ chế tái bản DNA",
            "intro": (
                "Work là pha bạn tự xử lý kiến thức. Hãy dùng sơ đồ ở Organize, SGK và POWER Tutor để "
                "giải thích bằng lời của chính bạn; Tutor chỉ gợi ý và phản hồi, không làm thay nhiệm vụ."
            ),
            "tasks": [
                {
                    "code": "W1_DIRECTION",
                    "title": "Nhiệm vụ 1 · Chiều tổng hợp DNA",
                    "prompt": (
                        "Giải thích vì sao việc DNA polymerase chỉ tổng hợp mạch mới theo chiều 5′→3′ lại dẫn đến hai kiểu tổng hợp khác nhau tại chạc tái bản."
                    ),
                    "concept_codes": ["BIO.DNA.REPLICATION"],
                    "minimum_chars": 90,
                    "scaffold": [
                        "Hai mạch khuôn DNA có chiều tương đối như thế nào?",
                        "DNA polymerase chỉ kéo dài đầu nào của mạch mới?",
                        "Điều đó ảnh hưởng ra sao đến hai mạch mới tại chạc tái bản?",
                    ],
                },
                {
                    "code": "W2_COMPARE",
                    "title": "Nhiệm vụ 2 · So sánh hai mạch mới",
                    "prompt": (
                        "So sánh mạch dẫn đầu và mạch chậm theo ít nhất ba tiêu chí: tính liên tục, hướng di chuyển tương đối của chạc tái bản và sự xuất hiện của đoạn Okazaki."
                    ),
                    "concept_codes": ["BIO.DNA.REPLICATION"],
                    "minimum_chars": 100,
                    "scaffold": [
                        "Không chỉ liệt kê; hãy nêu nguyên nhân của điểm khác nhau.",
                        "Cả hai mạch mới vẫn được tổng hợp theo cùng chiều hóa học 5′→3′.",
                    ],
                },
                {
                    "code": "W3_CAUSAL",
                    "title": "Nhiệm vụ 3 · Chuỗi nguyên nhân – kết quả",
                    "prompt": (
                        "Tạo một lời giải thích ngắn theo chuỗi nguyên nhân – kết quả từ cấu trúc hai mạch DNA đến việc hình thành và nối các đoạn Okazaki."
                    ),
                    "concept_codes": ["BIO.DNA.REPLICATION"],
                    "minimum_chars": 120,
                    "scaffold": [
                        "Bắt đầu từ hai mạch DNA ngược chiều.",
                        "Nối tiếp bằng giới hạn chiều tổng hợp của DNA polymerase.",
                        "Kết thúc bằng tổng hợp gián đoạn và vai trò nối các đoạn mới tạo thành.",
                    ],
                },
            ],
            "self_check_prompt": "Sau khi hoàn thành, bạn tự tin đến mức nào rằng mình có thể tự giải thích cơ chế này mà không nhìn đáp án?",
        },
        "en": {
            "title": "Work deeply with DNA replication",
            "intro": (
                "Work is where you process the biology yourself. Use your Organize map, the textbook, and POWER Tutor to explain in your own words; the Tutor should scaffold and give feedback, not complete the task for you."
            ),
            "tasks": [
                {
                    "code": "W1_DIRECTION",
                    "title": "Task 1 · Direction of DNA synthesis",
                    "prompt": (
                        "Explain why DNA polymerase synthesizing new DNA only 5′→3′ produces two different synthesis patterns at a replication fork."
                    ),
                    "concept_codes": ["BIO.DNA.REPLICATION"],
                    "minimum_chars": 90,
                    "scaffold": [
                        "How are the two DNA templates oriented relative to each other?",
                        "Which end of the new strand can DNA polymerase extend?",
                        "How does that constraint affect the two new strands at the fork?",
                    ],
                },
                {
                    "code": "W2_COMPARE",
                    "title": "Task 2 · Compare the two new strands",
                    "prompt": (
                        "Compare the leading and lagging strands using at least three criteria: continuity, movement relative to the replication fork, and the presence of Okazaki fragments."
                    ),
                    "concept_codes": ["BIO.DNA.REPLICATION"],
                    "minimum_chars": 100,
                    "scaffold": [
                        "Do not only list differences; explain what causes them.",
                        "Both new strands are still synthesized chemically in the 5′→3′ direction.",
                    ],
                },
                {
                    "code": "W3_CAUSAL",
                    "title": "Task 3 · Cause-and-effect chain",
                    "prompt": (
                        "Write a short cause-and-effect explanation from the antiparallel DNA structure to the formation and joining of Okazaki fragments."
                    ),
                    "concept_codes": ["BIO.DNA.REPLICATION"],
                    "minimum_chars": 120,
                    "scaffold": [
                        "Start with the antiparallel DNA strands.",
                        "Then use the directional constraint of DNA polymerase.",
                        "End with discontinuous synthesis and joining the newly formed fragments.",
                    ],
                },
            ],
            "self_check_prompt": "After completing the tasks, how confident are you that you could explain the mechanism without looking at an answer?",
        },
    }
}


@dataclass(frozen=True)
class WorkValidation:
    responses: dict[str, str]
    completed_tasks: list[str]
    confidence_after: int
    evidence_chars: int
    completion_ratio: float
    errors: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "responses": self.responses,
            "completed_tasks": self.completed_tasks,
            "confidence_after": self.confidence_after,
            "evidence_chars": self.evidence_chars,
            "completion_ratio": self.completion_ratio,
            "errors": self.errors,
        }


def get_work_blueprint(unit_code: str, language: str = "vi") -> dict[str, Any]:
    try:
        raw = _WORK_BLUEPRINTS[unit_code]["en" if language == "en" else "vi"]
    except KeyError as exc:
        raise KeyError(unit_code) from exc
    return {
        "unit_code": unit_code,
        "title": raw["title"],
        "intro": raw["intro"],
        "tasks": raw["tasks"],
        "self_check_prompt": raw["self_check_prompt"],
    }


def validate_work_payload(
    *,
    unit_code: str,
    language: str,
    responses: dict[str, str],
    confidence_after: int,
    completed: bool,
) -> WorkValidation:
    blueprint = get_work_blueprint(unit_code, language)
    clean_responses = {str(k): str(v).strip() for k, v in responses.items() if str(v).strip()}
    allowed_codes = {task["code"] for task in blueprint["tasks"]}
    clean_responses = {k: v for k, v in clean_responses.items() if k in allowed_codes}

    errors: list[str] = []
    completed_tasks: list[str] = []
    for task in blueprint["tasks"]:
        value = clean_responses.get(task["code"], "")
        if len(value) >= int(task["minimum_chars"]):
            completed_tasks.append(task["code"])
        elif completed:
            errors.append(
                f"{task['code']} requires at least {task['minimum_chars']} characters of learner evidence"
            )

    if not 1 <= confidence_after <= 5:
        errors.append("confidence_after must be between 1 and 5")

    evidence_chars = sum(len(value) for value in clean_responses.values())
    completion_ratio = round(len(completed_tasks) / max(len(blueprint["tasks"]), 1), 3)

    return WorkValidation(
        responses=clean_responses,
        completed_tasks=completed_tasks,
        confidence_after=confidence_after,
        evidence_chars=evidence_chars,
        completion_ratio=completion_ratio,
        errors=errors,
    )
