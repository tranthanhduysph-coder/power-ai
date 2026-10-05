from app.content.power_builder import validate_power_draft


def _valid_payload():
    concepts = [
        {"code": f"BIO.TEST.C{i}", "name_vi": f"C{i}", "name_en": f"C{i}", "description_vi": "Mô tả", "description_en": "Description", "is_core": i <= 4}
        for i in range(1, 6)
    ]
    diagnostics = [
        {"code": "P1", "concept_code": "BIO.TEST.C1", "question_type": "true_false", "prompt_vi": "A", "prompt_en": "A", "options": [], "expected": True},
        {"code": "P2", "concept_code": "BIO.TEST.C2", "question_type": "mcq", "prompt_vi": "B", "prompt_en": "B", "options": [{"key": k, "text_vi": k, "text_en": k} for k in "ABCD"], "expected": "A"},
        {"code": "P3", "concept_code": "BIO.TEST.C3", "question_type": "true_false", "prompt_vi": "C", "prompt_en": "C", "options": [], "expected": False},
    ]
    tasks = [
        {"code": f"W{i}", "title": "Task", "prompt": "Prompt", "concept_codes": [f"BIO.TEST.C{i}"], "minimum_chars": 80, "scaffold": ["a", "b"]}
        for i in range(1, 4)
    ]
    questions = []
    for i in range(1, 5):
        questions.append({"question_type":"mcq","difficulty":"medium","cognitive_level":"understand","stem_vi":"S","stem_en":"S","answer_json":{"option":"A"},"explanation_vi":"E","explanation_en":"E","concept_code":"BIO.TEST.C1","options":[{"key":k,"text_vi":k,"text_en":k,"is_correct":k=="A"} for k in "ABCD"]})
    for i in range(4):
        questions.append({"question_type":"true_false","difficulty":"easy","cognitive_level":"understand","stem_vi":"S","stem_en":"S","answer_json":{"value": i % 2 == 0},"explanation_vi":"E","explanation_en":"E","concept_code":"BIO.TEST.C2","options":[]})
    return {
        "schema_version":"1.2",
        "concepts":concepts,
        "relations":[{"source_code":"BIO.TEST.C1","target_code":"BIO.TEST.C2","relation_type":"related"}],
        "prepare":{"title_vi":"T","title_en":"T","outcomes_vi":["A","B"],"outcomes_en":["A","B"],"keywords":["x"],"diagnostic_items":diagnostics},
        "work":{"vi":{"title":"T","intro":"I","tasks":tasks,"self_check_prompt":"S"},"en":{"title":"T","intro":"I","tasks":[dict(x) for x in tasks],"self_check_prompt":"S"}},
        "policy":{"primary_concept_code":"BIO.TEST.C1","minimum_anchor_concepts":3,"minimum_links":3},
        "questions":questions,
    }


def test_valid_power_draft_contract():
    result = validate_power_draft(_valid_payload())
    assert result["valid"] is True
    assert result["errors"] == []


def test_unknown_concept_reference_is_rejected():
    payload = _valid_payload()
    payload["questions"][0]["concept_code"] = "BIO.UNKNOWN"
    result = validate_power_draft(payload)
    assert result["valid"] is False
    assert any("unknown concept" in error for error in result["errors"])


def test_requires_enough_evaluate_questions():
    payload = _valid_payload()
    payload["questions"] = payload["questions"][:4]
    result = validate_power_draft(payload)
    assert result["valid"] is False
    assert any("8–10" in error for error in result["errors"])


def test_boolean_like_model_values_are_normalized_before_validation():
    from app.content.power_builder import normalize_power_draft_payload

    payload = _valid_payload()
    payload["prepare"]["diagnostic_items"][0]["expected"] = "true"
    payload["prepare"]["diagnostic_items"][2]["expected"] = "Sai"
    payload["questions"][4]["answer_json"]["value"] = "Đúng"
    payload["questions"][0]["options"][0]["is_correct"] = "true"
    payload["questions"][0]["options"][1]["is_correct"] = "false"

    normalized = normalize_power_draft_payload(payload)
    assert normalized["prepare"]["diagnostic_items"][0]["expected"] is True
    assert normalized["prepare"]["diagnostic_items"][2]["expected"] is False
    assert normalized["questions"][4]["answer_json"]["value"] is True
    assert normalized["questions"][0]["options"][0]["is_correct"] is True
    assert normalized["questions"][0]["options"][1]["is_correct"] is False
    assert validate_power_draft(normalized)["valid"] is True


def test_underscore_concept_codes_and_references_are_canonicalized():
    from app.content.power_builder import normalize_power_draft_payload

    payload = _valid_payload()
    mapping = {}
    for concept in payload["concepts"]:
        old = concept["code"]
        new = old.replace(".", "_")
        mapping[old] = new
        concept["code"] = new

    for relation in payload["relations"]:
        relation["source_code"] = mapping[relation["source_code"]]
        relation["target_code"] = mapping[relation["target_code"]]
    for item in payload["prepare"]["diagnostic_items"]:
        item["concept_code"] = mapping[item["concept_code"]]
    for lang in ("vi", "en"):
        for task in payload["work"][lang]["tasks"]:
            task["concept_codes"] = [mapping[c] for c in task["concept_codes"]]
    payload["policy"]["primary_concept_code"] = mapping[payload["policy"]["primary_concept_code"]]
    for q in payload["questions"]:
        q["concept_code"] = mapping[q["concept_code"]]

    normalized = normalize_power_draft_payload(payload)
    assert normalized["concepts"][0]["code"] == "BIO.TEST.C1"
    assert normalized["policy"]["primary_concept_code"] == "BIO.TEST.C1"
    assert validate_power_draft(normalized)["valid"] is True
