from app.ingestion.vision import _extract_json_object


def test_extract_json_object_accepts_fenced_json():
    raw = '''```json
{"printed_page_label":"36","text":"DNA","visuals":[]}
```'''
    data = _extract_json_object(raw)
    assert data["printed_page_label"] == "36"
    assert data["text"] == "DNA"
