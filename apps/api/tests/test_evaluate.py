from app.services.evaluate import summarize_evaluation


def test_evaluate_summary_groups_concepts_and_finds_weaknesses():
    rows = [
        {
            "is_correct": True,
            "concept_code": "BIO.DNA.REPLICATION",
            "concept_name_vi": "Tái bản DNA",
            "concept_name_en": "DNA replication",
            "mastery": {"mastery_score": 0.72},
        },
        {
            "is_correct": False,
            "concept_code": "BIO.DNA.REPLICATION",
            "concept_name_vi": "Tái bản DNA",
            "concept_name_en": "DNA replication",
            "mastery": {"mastery_score": 0.64},
        },
        {
            "is_correct": False,
            "concept_code": "BIO.DNA.OKAZAKI",
            "concept_name_vi": "Đoạn Okazaki",
            "concept_name_en": "Okazaki fragments",
            "mastery": {"mastery_score": 0.45},
        },
    ]

    result = summarize_evaluation(rows, practice_set_id="set-1", practice_attempt_id="attempt-1")

    assert result["total"] == 3
    assert result["correct"] == 1
    assert result["accuracy"] == 0.33333
    assert result["evidence_ready"] is True
    assert "BIO.DNA.OKAZAKI" in result["weak_concepts"]
    replication = next(x for x in result["concepts"] if x["concept_code"] == "BIO.DNA.REPLICATION")
    assert replication["total"] == 2
    assert replication["correct"] == 1
    assert replication["accuracy"] == 0.5
