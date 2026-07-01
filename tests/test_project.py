from src.project import project


def test_project_example_config_and_on_missing_null():
    canonical = {
        "full_name": "Jane Doe",
        "emails": ["jane@example.com"],
        "phones": ["+14155552671"],
        "skills": [{"name": "js"}, {"name": "Python"}],
        "overall_confidence": 0.92,
        "provenance": [{"field": "emails", "source": "csv", "method": "direct", "value_repr": "jane@example.com", "confidence": 0.95, "accepted": True}],
    }
    config = {
        "fields": [
            {"path": "full_name", "type": "string", "required": True},
            {"path": "primary_email", "from": "emails[0]", "type": "string", "required": True},
            {"path": "phone", "from": "phones[0]", "type": "string", "normalize": "E164"},
            {"path": "skills", "from": "skills[].name", "type": "string[]", "normalize": "canonical"},
            {"path": "missing_field", "from": "not.here", "type": "string"},
        ],
        "include_confidence": True,
        "on_missing": "null",
    }

    projected = project(canonical, config)

    assert projected["full_name"] == "Jane Doe"
    assert projected["primary_email"] == "jane@example.com"
    assert projected["phone"] == "+14155552671"
    assert projected["skills"] == ["JavaScript", "Python"]
    assert projected["missing_field"] is None
    assert "overall_confidence" in projected
    assert "provenance" in projected
