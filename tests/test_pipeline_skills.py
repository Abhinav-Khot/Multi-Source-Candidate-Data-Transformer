from src.pipeline import _canonicalize_skills


def test_canonicalize_skills_merges_duplicates_and_sources():
    candidates = [
        {
            "skills": [
                {"name": "Python", "confidence": 0.65, "sources": ["notes"]},
                {"name": "Python", "confidence": 0.95, "sources": ["csv"]},
                {"name": "Go", "confidence": 0.7, "sources": ["github"]},
            ]
        }
    ]

    _canonicalize_skills(candidates)

    assert candidates[0]["skills"] == [
        {"name": "Go", "confidence": 0.7, "sources": ["github"]},
        {"name": "Python", "confidence": 0.95, "sources": ["csv", "notes"]},
    ]
