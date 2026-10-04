from app.services.rethink import (
    aggregate_evidence_confidence,
    build_candidate_misconceptions,
    recommend_next_action,
    validate_rethink_payload,
)


def test_aggregate_evidence_confidence_combines_multiple_signals():
    assert aggregate_evidence_confidence([0.55, 0.55]) == 0.7975


def test_build_candidate_misconceptions_groups_question_evidence():
    rows = [
        {
            "misconception_code": "MIS_DNA_DIRECTION",
            "concept_code": "BIO.DNA.REPLICATION.POLYMERASE",
            "concept_name_vi": "DNA polymerase",
            "concept_name_en": "DNA polymerase",
            "statement_vi": "Sai chiều",
            "statement_en": "Wrong direction",
            "correction_vi": "Đúng là 5′→3′",
            "correction_en": "Correct is 5′→3′",
            "evidence_weight": 0.55,
            "question_code": "Q1",
        },
        {
            "misconception_code": "MIS_DNA_DIRECTION",
            "concept_code": "BIO.DNA.REPLICATION.POLYMERASE",
            "concept_name_vi": "DNA polymerase",
            "concept_name_en": "DNA polymerase",
            "statement_vi": "Sai chiều",
            "statement_en": "Wrong direction",
            "correction_vi": "Đúng là 5′→3′",
            "correction_en": "Correct is 5′→3′",
            "evidence_weight": 0.55,
            "question_code": "Q5",
        },
    ]
    result = build_candidate_misconceptions(rows)
    assert len(result) == 1
    assert result[0]["code"] == "MIS_DNA_DIRECTION"
    assert result[0]["confidence"] == 0.7975
    assert result[0]["evidence_count"] == 2


def test_validate_rethink_requires_real_reflection_when_completing():
    result = validate_rethink_payload(
        understanding_gain="ngắn",
        error_cause="",
        corrected_explanation="quá ngắn",
        action_plan="ngắn",
        confidence_after_rethink=3,
        confirmed_misconceptions=[],
        allowed_misconceptions={"MIS_DNA_DIRECTION"},
        completed=True,
    )
    assert len(result.errors) >= 4


def test_recommend_next_action_prioritizes_confirmed_misconception():
    result = recommend_next_action(
        accuracy=0.9,
        weak_concepts=[],
        confirmed_misconceptions=["MIS_DNA_DIRECTION"],
        confidence_after_rethink=4,
        language="vi",
    )
    assert result["type"] == "review_and_retry"
    assert result["priority"] == 1
