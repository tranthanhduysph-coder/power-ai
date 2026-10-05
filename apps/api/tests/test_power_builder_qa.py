from app.content.power_builder import assess_power_draft


def _payload():
    concepts = [
        {
            "code": f"BIO.TEST.C{i}",
            "name_vi": f"Khái niệm {i}",
            "name_en": f"Concept {i}",
            "description_vi": "Mô tả khái niệm",
            "description_en": "Concept description",
            "is_core": i <= 4,
        }
        for i in range(1, 6)
    ]
    diagnostics = [
        {"code":"P1","concept_code":"BIO.TEST.C1","question_type":"true_false","prompt_vi":"P1","prompt_en":"P1","options":[],"expected":True},
        {"code":"P2","concept_code":"BIO.TEST.C2","question_type":"mcq","prompt_vi":"P2","prompt_en":"P2","options":[{"key":k,"text_vi":k,"text_en":k} for k in "ABCD"],"expected":"A"},
        {"code":"P3","concept_code":"BIO.TEST.C3","question_type":"true_false","prompt_vi":"P3","prompt_en":"P3","options":[],"expected":False},
    ]
    tasks = [
        {"code":f"W{i}","title":"Task","prompt":f"Explain relationship {i}","concept_codes":[f"BIO.TEST.C{i}"],"minimum_chars":80,"scaffold":["a","b"]}
        for i in range(1,4)
    ]
    questions = []
    for i in range(4):
        questions.append({
            "question_type":"mcq","difficulty":"medium" if i % 2 else "easy","cognitive_level":"understand" if i % 2 else "remember",
            "stem_vi":f"Câu MCQ {i}","stem_en":f"MCQ {i}","answer_json":{"option":"A"},"explanation_vi":"Giải thích","explanation_en":"Explanation",
            "concept_code":f"BIO.TEST.C{(i % 3)+1}","options":[{"key":k,"text_vi":k,"text_en":k,"is_correct":k=="A"} for k in "ABCD"]
        })
    for i in range(4):
        questions.append({
            "question_type":"true_false","difficulty":"hard" if i % 2 else "medium","cognitive_level":"apply" if i % 2 else "understand",
            "stem_vi":f"Câu Đ/S {i}","stem_en":f"TF {i}","answer_json":{"value":i % 2 == 0},"explanation_vi":"Giải thích","explanation_en":"Explanation",
            "concept_code":f"BIO.TEST.C{(i % 3)+1}","options":[]
        })
    return {
        "schema_version":"1.2",
        "concepts":concepts,
        "relations":[{"source_code":"BIO.TEST.C1","target_code":"BIO.TEST.C2","relation_type":"related"}],
        "prepare":{"title_vi":"Chuẩn bị","title_en":"Prepare","outcomes_vi":["A","B"],"outcomes_en":["A","B"],"keywords":["x"],"diagnostic_items":diagnostics},
        "work":{"vi":{"title":"Work","intro":"I","tasks":tasks,"self_check_prompt":"S"},"en":{"title":"Work","intro":"I","tasks":[dict(x) for x in tasks],"self_check_prompt":"S"}},
        "policy":{"primary_concept_code":"BIO.TEST.C1","minimum_anchor_concepts":3,"minimum_links":3},
        "questions":questions,
    }


def test_qa_passes_valid_current_package():
    result = assess_power_draft(_payload(), stored_fingerprint="same", current_fingerprint="same", source_chars=5000)
    assert result["passed"] is True
    assert result["errors"] == []
    assert result["metrics"]["question_count"] == 8


def test_qa_rejects_stale_source_fingerprint():
    result = assess_power_draft(_payload(), stored_fingerprint="old", current_fingerprint="new", source_chars=5000)
    assert result["passed"] is False
    assert any("fingerprint" in error for error in result["errors"])


def test_qa_rejects_duplicate_question_stems():
    payload = _payload()
    payload["questions"][1]["stem_vi"] = payload["questions"][0]["stem_vi"]
    result = assess_power_draft(payload, stored_fingerprint="same", current_fingerprint="same", source_chars=5000)
    assert result["passed"] is False
    assert any("duplicate Vietnamese question stems" in error for error in result["errors"])
