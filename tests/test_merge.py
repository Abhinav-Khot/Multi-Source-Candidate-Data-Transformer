from src.merge import merge_records


def test_merge_fallback_chain_email_phone_name_soft_match():
    email_pair = [
        {"source": "csv", "name": "Jane Doe", "email": "jane@example.com", "phone": "", "_methods": {"name": "direct", "email": "direct"}},
        {"source": "notes", "name": "Jane Doe", "email": "jane@example.com", "phone": "", "_methods": {"name": "name_cue", "email": "email_regex"}},
    ]
    phone_pair = [
        {"source": "csv", "name": "John Roe", "email": "", "phone": "+14155550000", "_methods": {"name": "direct", "phone": "direct"}},
        {"source": "notes", "name": "John Roe", "email": "", "phone": "+1 (415) 555-0000", "_methods": {"name": "name_cue", "phone": "phone_regex"}},
    ]
    name_pair = [
        {"source": "csv", "name": "Alex Smith", "email": "", "phone": "", "_methods": {"name": "direct"}},
        {"source": "notes", "name": "Alex Smith", "email": "", "phone": "", "_methods": {"name": "name_cue"}},
    ]

    merged = merge_records(email_pair + phone_pair + name_pair)

    by_name = {item["full_name"]: item for item in merged}
    assert len(by_name["Jane Doe"]["emails"]) == 1
    assert by_name["John Roe"]["phones"] == ["+14155550000"]
    assert any(
        p["field"] == "full_name" and p["source"] == "merge" and p["method"] == "name_soft"
        for p in by_name["Alex Smith"]["provenance"]
    )


def test_merge_conflict_trust_order_and_provenance_acceptance():
    records = [
        {
            "source": "csv",
            "name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "",
            "title": "Engineer",
            "_methods": {"name": "direct", "email": "direct", "title": "direct"},
        },
        {
            "source": "github",
            "name": "Jane D.",
            "email": "jane@example.com",
            "phone": "",
            "bio": "Principal Engineer",
            "_methods": {"name": "api", "bio": "api"},
        },
    ]

    merged = merge_records(records)
    assert len(merged) == 1
    candidate = merged[0]

    assert candidate["full_name"] == "Jane Doe"
    assert candidate["headline"] == "Principal Engineer"

    full_name_entries = [
        p for p in candidate["provenance"] if p["field"] == "full_name" and p["value_repr"] in {"Jane Doe", "Jane D."}
    ]
    assert any(p["accepted"] and p["value_repr"] == "Jane Doe" for p in full_name_entries)
    assert any((not p["accepted"]) and p["value_repr"] == "Jane D." for p in full_name_entries)
