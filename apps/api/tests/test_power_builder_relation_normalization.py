from app.content.power_builder import normalize_power_draft_payload


def test_relation_normalization_drops_self_unknown_and_duplicate_links():
    payload = {
        "concepts": [
            {"code": "BIO_A"},
            {"code": "BIO_B"},
            {"code": "BIO_C"},
        ],
        "relations": [
            {"source_code": "BIO_A", "target_code": "BIO_B", "relation_type": "related"},
            {"source_code": "BIO_A", "target_code": "BIO_A", "relation_type": "related"},
            {"source_code": "BIO_A", "target_code": "BIO_UNKNOWN", "relation_type": "related"},
            {"source_code": "BIO_A", "target_code": "BIO_B", "relation_type": "related"},
            {"source_code": "BIO_B", "target_code": "BIO_C", "relation_type": "part_of"},
        ],
    }

    normalized = normalize_power_draft_payload(payload)

    assert [c["code"] for c in normalized["concepts"]] == ["BIO.A", "BIO.B", "BIO.C"]
    assert normalized["relations"] == [
        {"source_code": "BIO.A", "target_code": "BIO.B", "relation_type": "related"},
        {"source_code": "BIO.B", "target_code": "BIO.C", "relation_type": "part_of"},
    ]


def test_relation_normalization_keeps_unsupported_type_for_strict_validator():
    payload = {
        "concepts": [{"code": "BIO_A"}, {"code": "BIO_B"}],
        "relations": [
            {"source_code": "BIO_A", "target_code": "BIO_B", "relation_type": "invented"}
        ],
    }

    normalized = normalize_power_draft_payload(payload)
    assert normalized["relations"][0]["relation_type"] == "invented"
