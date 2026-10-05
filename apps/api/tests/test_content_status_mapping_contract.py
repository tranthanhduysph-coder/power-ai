from pathlib import Path


def test_reconcile_uses_unit_source_page_mapping():
    root = Path(__file__).resolve().parents[3]
    script = (root / "scripts" / "content" / "build_kntt.py").read_text(encoding="utf-8")
    assert "FROM curriculum_unit_sources cus" in script
    assert "JOIN content_chunks cc ON cc.source_id = s.id" in script
    assert "cc.page_end >= cus.pdf_page_start" in script
    assert "cc.page_start <= cus.pdf_page_end" in script
    assert "ss.code = cu.code" not in script
