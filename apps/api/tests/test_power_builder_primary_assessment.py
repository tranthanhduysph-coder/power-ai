from app.content.power_builder import normalize_power_draft_payload, build_generation_prompt, UnitSourceContext


def _base_payload():
    return {
        "concepts": [
            {
                "code": "BIO_GENE_EXPRESSION",
                "name_vi": "Biểu hiện gene",
                "name_en": "Gene expression",
                "is_core": True,
            },
            {
                "code": "BIO_TRANSCRIPTION",
                "name_vi": "Phiên mã",
                "name_en": "Transcription",
                "is_core": True,
            },
            {
                "code": "BIO_TRANSLATION",
                "name_vi": "Dịch mã",
                "name_en": "Translation",
                "is_core": True,
            },
        ],
        "policy": {"primary_concept_code": "BIO_GENE_EXPRESSION"},
        "questions": [],
    }


def test_primary_question_mapping_repairs_clear_metadata_mistag():
    payload = _base_payload()
    payload["questions"] = [
        {
            "question_type": "mcq",
            "concept_code": "BIO_TRANSCRIPTION",
            "stem_vi": "Biểu hiện gene bao gồm những quá trình nào?",
            "stem_en": "Which processes are involved in gene expression?",
        }
    ]
    normalized = normalize_power_draft_payload(payload)
    assert normalized["questions"][0]["concept_code"] == "BIO.GENE.EXPRESSION"


def test_primary_question_mapping_does_not_relabel_unrelated_question():
    payload = _base_payload()
    payload["questions"] = [
        {
            "question_type": "mcq",
            "concept_code": "BIO_TRANSCRIPTION",
            "stem_vi": "Phiên mã tạo ra sản phẩm nào?",
            "stem_en": "What product is formed by transcription?",
        }
    ]
    normalized = normalize_power_draft_payload(payload)
    assert normalized["questions"][0]["concept_code"] == "BIO.TRANSCRIPTION"


def test_generation_prompt_requires_primary_evaluate_coverage():
    context = UnitSourceContext(
        unit={
            "code": "B12_TEST",
            "grade": 12,
            "unit_type": "lesson",
            "name_vi": "Bài thử",
            "name_en": "Test unit",
            "printed_page_start": 1,
            "printed_page_end": 2,
        },
        source_code="BIO12_KNTT",
        source_title="Sinh học 12",
        pdf_page_start=3,
        pdf_page_end=4,
        text="Nội dung nguồn",
        fingerprint="abc",
    )
    prompt = build_generation_prompt(context)
    assert "Evaluate MUST directly assess policy.primary_concept_code" in prompt
