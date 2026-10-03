from app.services.organize import validate_organize_payload


CONCEPTS = {"A", "B", "C", "D", "E"}


def test_organize_complete_requires_learner_owned_structure():
    result = validate_organize_payload(
        allowed_concepts=CONCEPTS,
        anchors=["A", "B", "C"],
        links=[
            {"source": "A", "relation": "prerequisite", "target": "B"},
            {"source": "B", "relation": "causes", "target": "C"},
            {"source": "C", "relation": "related", "target": "D"},
        ],
        synthesis="A connects to B, which helps explain why C and D are related.",
        completed=True,
    )
    assert result.errors == []
    assert result.coverage == 0.8
    assert len(result.links) == 3


def test_organize_rejects_invalid_relations_and_self_links():
    result = validate_organize_payload(
        allowed_concepts=CONCEPTS,
        anchors=["A"],
        links=[
            {"source": "A", "relation": "magic", "target": "B"},
            {"source": "A", "relation": "related", "target": "A"},
        ],
        synthesis="short",
        completed=True,
    )
    assert any("Unsupported relation" in error for error in result.errors)
    assert any("cannot be linked to itself" in error for error in result.errors)
    assert any("at least 3 anchor" in error for error in result.errors)
    assert any("at least 3 concept relationships" in error for error in result.errors)


def test_organize_can_save_partial_state():
    result = validate_organize_payload(
        allowed_concepts=CONCEPTS,
        anchors=["A"],
        links=[],
        synthesis="",
        completed=False,
    )
    assert result.errors == []
    assert result.anchors == ["A"]
