from app.services.work import build_work_blueprint, validate_work_against_blueprint


WORK = {
    "vi": {
        "title": "Làm việc sâu với cơ chế tái bản DNA",
        "intro": "Tự xử lý kiến thức.",
        "tasks": [
            {"code": "W1", "title": "Nhiệm vụ 1", "prompt": "Giải thích", "concept_codes": ["BIO.DNA.REPLICATION"], "minimum_chars": 10, "scaffold": []},
            {"code": "W2", "title": "Nhiệm vụ 2", "prompt": "So sánh", "concept_codes": ["BIO.DNA.REPLICATION"], "minimum_chars": 10, "scaffold": []},
            {"code": "W3", "title": "Nhiệm vụ 3", "prompt": "Kết nối", "concept_codes": ["BIO.DNA.REPLICATION"], "minimum_chars": 10, "scaffold": []},
        ],
        "self_check_prompt": "Bạn tự tin đến mức nào?",
    },
    "en": {
        "title": "Work deeply",
        "intro": "Process the knowledge yourself.",
        "tasks": [],
        "self_check_prompt": "How confident are you?",
    },
}


def _responses():
    return {"W1": "01234567890", "W2": "abcdefghijk", "W3": "ABCDEFGHIJK"}


def test_work_blueprint_has_three_learner_tasks():
    blueprint = build_work_blueprint("B12_DNA_REPLICATION", WORK, "vi")
    assert len(blueprint["tasks"]) == 3


def test_work_complete_requires_evidence_for_each_task():
    blueprint = build_work_blueprint("B12_DNA_REPLICATION", WORK, "vi")
    result = validate_work_against_blueprint(
        blueprint=blueprint,
        responses=_responses(),
        confidence_after=4,
        completed=True,
    )
    assert result.errors == []
    assert result.completion_ratio == 1.0
    assert len(result.completed_tasks) == 3


def test_work_partial_save_is_allowed():
    blueprint = build_work_blueprint("B12_DNA_REPLICATION", WORK, "vi")
    result = validate_work_against_blueprint(
        blueprint=blueprint,
        responses={"W1": "short"},
        confidence_after=3,
        completed=False,
    )
    assert result.errors == []
    assert result.completion_ratio == 0.0
