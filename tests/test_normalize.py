from src.normalize import canonicalize_skill, normalize_date_yyyy_mm, normalize_phone_e164


def test_normalize_date_yyyy_mm_valid_and_unknown_month():
    assert normalize_date_yyyy_mm("2024-05") == "2024-05"
    assert normalize_date_yyyy_mm("May 2024") == "2024-05"
    assert normalize_date_yyyy_mm("2024") is None


def test_normalize_phone_e164_and_ungeocodable_null():
    assert normalize_phone_e164("+1 415-555-2671") == "+14155552671"
    assert normalize_phone_e164("415-555-2671") is None


def test_skill_canonicalization_alias_and_passthrough():
    assert canonicalize_skill("js") == ("JavaScript", True)
    assert canonicalize_skill("Kotlin") == ("Kotlin", False)
