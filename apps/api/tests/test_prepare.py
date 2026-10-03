from app.services.prepare import analyze_goal, get_prepare_blueprint, score_diagnostic


def test_prepare_blueprint_hides_answers():
    blueprint = get_prepare_blueprint("B12_DNA_REPLICATION", "vi")
    assert len(blueprint["diagnostic_items"]) == 3
    assert all("expected" not in item for item in blueprint["diagnostic_items"])


def test_goal_feedback_rewards_smart_goal():
    result = analyze_goal(
        "Tôi có thể giải thích vì sao tái bản DNA có mạch chậm và đoạn Okazaki và trả lời đúng 4/5 câu hỏi.",
        30,
        "B12_DNA_REPLICATION",
        "vi",
    )
    assert result["score"] == 5
    assert all(result["checks"].values())


def test_prepare_diagnostic_scoring():
    result = score_diagnostic(
        "B12_DNA_REPLICATION",
        {
            "PREP_DNA_01": True,
            "PREP_DNA_02": "A",
            "PREP_DNA_03": "B",
        },
    )
    assert result["correct"] == 3
    assert result["answered"] == 3
    assert result["readiness"] == 1.0
    assert result["missing"] == []
