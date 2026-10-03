from app.ingestion.chunker import chunk_text, normalize_text


def test_chunker_preserves_content_and_limits_size():
    text = ("DNA polymerase tổng hợp mạch mới theo chiều 5′→3′. " * 120).strip()
    chunks = chunk_text(text, max_chars=600, overlap_chars=80)
    assert len(chunks) > 1
    assert all(chunk.text for chunk in chunks)
    assert all(chunk.token_count > 0 for chunk in chunks)
    assert all(len(chunk.text) <= 600 for chunk in chunks)


def test_normalize_text_collapses_spaces():
    assert normalize_text("DNA   replication\n\n\nOkazaki") == "DNA replication\n\nOkazaki"
