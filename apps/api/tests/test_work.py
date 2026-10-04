from app.services.work import get_work_blueprint, validate_work_payload


def _complete_responses():
    return {
        "W1_DIRECTION": "Hai mạch khuôn ngược chiều nhau và DNA polymerase chỉ kéo dài mạch mới theo chiều 5′→3′, nên tại cùng một chạc tái bản hai mạch mới không thể được tổng hợp theo cùng một kiểu liên tục.",
        "W2_COMPARE": "Mạch dẫn đầu được tổng hợp liên tục theo hướng chạc tái bản mở ra, còn mạch chậm được tổng hợp gián đoạn thành các đoạn Okazaki. Dù khác kiểu tổng hợp, cả hai mạch mới đều được kéo dài theo chiều 5′→3′.",
        "W3_CAUSAL": "Vì hai mạch DNA ngược chiều nhau nhưng DNA polymerase chỉ tổng hợp mạch mới theo chiều 5′→3′, một mạch có thể được kéo dài liên tục còn mạch kia phải tổng hợp từng đoạn ngắn. Các đoạn Okazaki sau đó được nối lại để tạo thành mạch DNA liên tục.",
    }


def test_work_blueprint_has_three_learner_tasks():
    blueprint = get_work_blueprint("B12_DNA_REPLICATION", "vi")
    assert len(blueprint["tasks"]) == 3
    assert all(task["minimum_chars"] >= 90 for task in blueprint["tasks"])


def test_work_complete_requires_evidence_for_each_task():
    result = validate_work_payload(
        unit_code="B12_DNA_REPLICATION",
        language="vi",
        responses=_complete_responses(),
        confidence_after=4,
        completed=True,
    )
    assert result.errors == []
    assert result.completion_ratio == 1.0
    assert len(result.completed_tasks) == 3
    assert result.evidence_chars > 300


def test_work_partial_save_is_allowed():
    result = validate_work_payload(
        unit_code="B12_DNA_REPLICATION",
        language="vi",
        responses={"W1_DIRECTION": "Tôi mới đang viết câu trả lời."},
        confidence_after=3,
        completed=False,
    )
    assert result.errors == []
    assert result.completion_ratio == 0.0
