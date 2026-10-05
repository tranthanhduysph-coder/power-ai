from pathlib import Path


def test_reconcile_requires_explicit_unit_page_range_and_overlap():
    root = Path(__file__).resolve().parents[3]
    script = (root / "scripts" / "content" / "build_kntt.py").read_text(encoding="utf-8")
    assert "FROM curriculum_unit_sources cus" in script
    assert "JOIN content_chunks cc ON cc.source_id = s.id" in script
    assert "cus.pdf_page_start IS NOT NULL" in script
    assert "cus.pdf_page_end IS NOT NULL" in script
    assert "cc.page_end >= cus.pdf_page_start" in script
    assert "cc.page_start <= cus.pdf_page_end" in script
    assert "cus.pdf_page_start IS NULL OR" not in script
    assert "cus.pdf_page_end IS NULL OR" not in script
    assert "s.ingest_status = 'ready'" not in script
