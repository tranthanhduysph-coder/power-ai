from app.content.kntt import (
    KNTTBookSpec,
    build_manifest_data,
    expected_pdf_pages_for_units,
    pdf_range,
    printed_to_pdf_page,
)


def spec() -> KNTTBookSpec:
    return KNTTBookSpec(
        grade=12,
        source_code="BIO12_KNTT",
        title="Biology 12",
        language="vi",
        source_role="curriculum",
        publisher="NXB",
        edition="KNTT",
        license_status="review_required",
        document_path="private_sources/biology12_kntt.pdf",
        pdf_page_offset=2,
        expected_pdf_pages=199,
    )


def units():
    return [
        {
            "id": "u1",
            "code": "B12_L01",
            "name_vi": "DNA",
            "name_en": "DNA",
            "unit_type": "lesson",
            "lesson_number": 1,
            "printed_page_start": 5,
            "printed_page_end": 8,
            "concept_codes": ["BIO.DNA.REPLICATION"],
        },
        {
            "id": "u2",
            "code": "B12_L02",
            "name_vi": "Gene",
            "name_en": "Gene",
            "unit_type": "lesson",
            "lesson_number": 2,
            "printed_page_start": 9,
            "printed_page_end": 12,
            "concept_codes": [],
        },
    ]


def test_printed_to_pdf_page_uses_verified_offset():
    assert printed_to_pdf_page(5, 2) == 7
    assert pdf_range(5, 8, 2) == (7, 10)


def test_manifest_sections_keep_curriculum_and_pdf_provenance():
    payload = build_manifest_data(spec(), units())
    first = payload["sections"][0]
    assert payload["source"]["code"] == "BIO12_KNTT"
    assert first["page_start"] == 7
    assert first["page_end"] == 10
    assert first["metadata"]["printed_page_start"] == 5
    assert first["concept_codes"] == ["BIO.DNA.REPLICATION"]


def test_expected_pages_deduplicates_adjacent_units():
    pages = expected_pdf_pages_for_units(spec(), units())
    assert min(pages) == 7
    assert max(pages) == 14
    assert len(pages) == 8


def test_manifest_rejects_noncontiguous_lesson_numbers():
    broken = units()
    broken[1] = {**broken[1], "lesson_number": 3}
    try:
        build_manifest_data(spec(), broken)
    except ValueError as exc:
        assert "not contiguous" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
