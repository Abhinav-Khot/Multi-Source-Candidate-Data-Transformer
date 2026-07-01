import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import phonenumbers

SKILL_ALIASES = {
    "js": "JavaScript",
    "javascript": "JavaScript",
    "java script": "JavaScript",
    "py": "Python",
    "python": "Python",
    "golang": "Go",
    "go": "Go",
    "ts": "TypeScript",
    "typescript": "TypeScript",
}

COUNTRY_ALIASES = {
    "united states": "US",
    "usa": "US",
    "us": "US",
    "india": "IN",
    "united kingdom": "GB",
    "uk": "GB",
    "canada": "CA",
}


def normalize_email(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    cleaned = value.strip().lower()
    return cleaned or None


def normalize_full_name(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    cleaned = re.sub(r"\s+", " ", value.strip())
    return cleaned or None


def normalize_name_key(value: Optional[str]) -> Optional[str]:
    normalized = normalize_full_name(value)
    if not normalized:
        return None
    return normalized.casefold()


def normalize_date_yyyy_mm(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None

    if re.match(r"^\d{4}-\d{2}$", cleaned):
        year, month = cleaned.split("-")
        month_num = int(month)
        if 1 <= month_num <= 12:
            return f"{int(year):04d}-{month_num:02d}"
        return None

    candidates = ["%Y/%m", "%Y-%m-%d", "%m/%Y", "%b %Y", "%B %Y"]
    for fmt in candidates:
        try:
            parsed = datetime.strptime(cleaned, fmt)
            return f"{parsed.year:04d}-{parsed.month:02d}"
        except ValueError:
            continue

    return None


def normalize_phone_e164(value: Optional[str], region: Optional[str] = None) -> Optional[str]:
    if not value:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None

    parse_region = region
    if cleaned.startswith("+"):
        parse_region = None
    if parse_region is None and not cleaned.startswith("+"):
        return None

    try:
        parsed = phonenumbers.parse(cleaned, parse_region)
    except phonenumbers.NumberParseException:
        return None

    if not phonenumbers.is_valid_number(parsed):
        return None

    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)


def normalize_country_iso2(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    cleaned = value.strip().lower()
    if not cleaned:
        return None
    if len(cleaned) == 2 and cleaned.isalpha():
        return cleaned.upper()
    return COUNTRY_ALIASES.get(cleaned)


def canonicalize_skill(token: Optional[str]) -> Tuple[Optional[str], bool]:
    if not token:
        return None, False
    cleaned = re.sub(r"\s+", " ", token.strip())
    if not cleaned:
        return None, False
    key = cleaned.lower()
    if key in SKILL_ALIASES:
        return SKILL_ALIASES[key], True
    return cleaned, False


def canonicalize_skills(tokens: List[str]) -> List[Dict[str, Any]]:
    out = []
    for token in tokens:
        name, mapped = canonicalize_skill(token)
        if not name:
            continue
        out.append({"name": name, "mapped": mapped})
    return out
