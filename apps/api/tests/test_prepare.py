from app.services.prepare import (
    analyze_goal_against_blueprint,
    build_prepare_blueprint,
    score_diagnostic_against_blueprint,
)


PREPARE = {
    "title_vi": "DNA và cơ chế tái bản DNA",
    "title_en": "DNA and DNA replication",
    "outcomes_vi": ["Giải thích được cơ chế tái bản DNA."],
    "outcomes_en": ["Explain the mechanism of DNA replication."],
    "keywords": ["dna", "tái bản", "replication", "okazaki"],
    "diagnostic_items": [
        {
            "code": "PREP_DNA_01",
            "concept_code": "BIO.DNA.STRUCTURE",
            "question_type": "true_false",
            "prompt_vi": "Hai mạch DNA ngược chiều.",
            "prompt_en": "DNA strands are antiparallel.",
            "options": [],
            "expected": True,
        },
        {
            "code": "PREP_DNA_02",
            "concept_code": "BIO.DNA.STRUCTURE",
            "question_type": "mcq",
            "prompt_vi": "A bắt cặp với base nào?",
            "prompt_en": "Which base pairs with A?",
            "options": [{"key": "A", "text_vi": "T", "text_en": "T"}],
            "expected": "A",
        },
    ],
}


def test_prepare_blueprint_hides_answers():
    blueprint = build_prepare_blueprint("B12_DNA_REPLICATION", PREPARE, "vi")
    assert len(blueprint["diagnostic_items"]) == 2
    assert all("expected" not in item for item in blueprint["diagnostic_items"])


def test_goal_feedback_rewards_smart_goal():
    result = analyze_goal_against_blueprint(
        "Tôi có thể giải thích tái bản DNA và đoạn Okazaki và trả lời đúng 4/5 câu hỏi.",
        30,
        "B12_DNA_REPLICATION",
        "vi",
        PREPARE,
    )
    assert result["score"] == 5
    assert all(result["checks"].values())


def test_prepare_diagnostic_scoring():
    result = score_diagnostic_against_blueprint(
        PREPARE,
        {"PREP_DNA_01": True, "PREP_DNA_02": "A"},
    )
    assert result["correct"] == 2
    assert result["answered"] == 2
    assert result["readiness"] == 1.0
    assert result["missing"] == []
