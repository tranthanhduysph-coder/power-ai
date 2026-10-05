from app.content.power_builder import normalize_power_draft_payload, validate_power_draft


def _concepts(n=7):
    return [
        {
            "code": f"BIO_TEST_C{i}",
            "name_vi": f"Khái niệm {i}",
            "name_en": f"Concept {i}",
            "description_vi": "Mô tả",
            "description_en": "Description",
            "is_core": False,
        }
        for i in range(1, n + 1)
    ]


def test_core_normalization_promotes_to_minimum_three_and_primary():
    payload = {
        "concepts": _concepts(5),
        "policy": {"primary_concept_code": "BIO_TEST_C5"},
    }
    normalized = normalize_power_draft_payload(payload)
    core = [c["code"] for c in normalized["concepts"] if c.get("is_core") is True]
    assert len(core) == 3
    assert "BIO.TEST.C5" in core


def test_core_normalization_trims_to_six_and_keeps_primary():
    concepts = _concepts(8)
    for concept in concepts:
        concept["is_core"] = True
    payload = {
        "concepts": concepts,
        "policy": {"primary_concept_code": "BIO_TEST_C8"},
    }
    normalized = normalize_power_draft_payload(payload)
    core = [c["code"] for c in normalized["concepts"] if c.get("is_core") is True]
    assert len(core) == 6
    assert "BIO.TEST.C8" in core


def test_core_normalization_keeps_valid_count_stable():
    concepts = _concepts(5)
    for i in range(4):
        concepts[i]["is_core"] = True
    payload = {
        "concepts": concepts,
        "policy": {"primary_concept_code": "BIO_TEST_C1"},
    }
    normalized = normalize_power_draft_payload(payload)
    core = [c["code"] for c in normalized["concepts"] if c.get("is_core") is True]
    assert core == ["BIO.TEST.C1", "BIO.TEST.C2", "BIO.TEST.C3", "BIO.TEST.C4"]
