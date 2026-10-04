from app.content.power_builder import UnitSourceContext, build_generation_prompt


def test_prompt_is_source_grounded_and_power_owned():
    context = UnitSourceContext(
        unit={"code":"B10_X","grade":10,"unit_type":"lesson","name_vi":"Bài X","name_en":"Lesson X","printed_page_start":1,"printed_page_end":2},
        source_code="BIO10_KNTT", source_title="Sinh học 10", pdf_page_start=2, pdf_page_end=3,
        text="NỘI DUNG SGK", fingerprint="abc",
    )
    prompt = build_generation_prompt(context)
    assert "Use ONLY the supplied Vietnamese textbook context" in prompt
    assert "Prepare → Organize → Work → Evaluate → Rethink" in prompt
    assert "learner, not the AI" in prompt
    assert "NỘI DUNG SGK" in prompt


def test_prompt_requires_real_json_booleans_for_true_false_diagnostics():
    context = UnitSourceContext(
        unit={"code":"B10_X","grade":10,"unit_type":"lesson","name_vi":"Bài X","name_en":"Lesson X","printed_page_start":1,"printed_page_end":2},
        source_code="BIO10_KNTT", source_title="Sinh học 10", pdf_page_start=2, pdf_page_end=3,
        text="NỘI DUNG SGK", fingerprint="abc",
    )
    prompt = build_generation_prompt(context)
    assert "MUST use JSON boolean expected: true or false" in prompt


def test_prompt_requires_canonical_dotted_concept_codes():
    context = UnitSourceContext(
        unit={"code":"B10_X","grade":10,"unit_type":"lesson","name_vi":"Bài X","name_en":"Lesson X","printed_page_start":1,"printed_page_end":2},
        source_code="BIO10_KNTT", source_title="Sinh học 10", pdf_page_start=2, pdf_page_end=3,
        text="NỘI DUNG SGK", fingerprint="abc",
    )
    prompt = build_generation_prompt(context)
    assert "canonical dotted identifiers" in prompt
    assert "Never use BIO_GENE" in prompt
