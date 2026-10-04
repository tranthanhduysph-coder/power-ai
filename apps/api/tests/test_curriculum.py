from app.services.curriculum import build_catalog_tree


def test_catalog_tree_preserves_hierarchy_and_grade():
    rows = [
        {"grade": 12, "code": "PART", "parent_code": None, "sort_order": 1, "unit_type": "part"},
        {"grade": 12, "code": "CH1", "parent_code": "PART", "sort_order": 1, "unit_type": "chapter"},
        {"grade": 12, "code": "L1", "parent_code": "CH1", "sort_order": 1, "unit_type": "lesson", "is_power_ready": True},
        {"grade": 11, "code": "P11", "parent_code": None, "sort_order": 1, "unit_type": "part"},
    ]
    tree = build_catalog_tree(rows)
    assert [g["grade"] for g in tree] == [11, 12]
    grade12 = tree[1]
    assert grade12["items"][0]["code"] == "PART"
    assert grade12["items"][0]["children"][0]["code"] == "CH1"
    assert grade12["items"][0]["children"][0]["children"][0]["code"] == "L1"
