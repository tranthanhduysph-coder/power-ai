from pathlib import Path


def test_v111_reconciliation_migration_requires_section_and_chunk_evidence():
    root = Path(__file__).resolve().parents[3]
    sql = (root / "database" / "migrations" / "009_content_status_reconciliation.sql").read_text(encoding="utf-8")
    assert "source_sections" in sql
    assert "content_chunks" in sql
    assert "ss.code = cu.code" in sql
    assert "s.ingest_status = 'ready'" in sql
