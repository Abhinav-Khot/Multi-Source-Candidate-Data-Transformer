import logging
import re
from pathlib import Path
from typing import Dict, List

KNOWN_SKILL_TOKENS = {
    "python",
    "go",
    "golang",
    "java",
    "javascript",
    "js",
    "typescript",
    "c++",
    "c#",
    "ruby",
    "rust",
    "sql",
}


def _split_candidate_blocks(text: str) -> List[str]:
    blocks = [chunk.strip() for chunk in re.split(r"\n\s*\n", text) if chunk.strip()]
    if not blocks:
        return []
    return blocks


def _extract_note_block(block: str, source_file: str) -> Dict:
    email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", block)
    phone_match = re.search(r"(?:\+?\d[\d\-\s().]{7,}\d)", block)
    years_match = re.search(r"\b(\d{1,2})\s*(?:yrs?|years?)\b", block, flags=re.IGNORECASE)
    company_title_match = re.search(
        r"currently\s+at\s+(.+?)\s+as\s+(?:a\s+|an\s+)?([^.,\n]+)",
        block,
        flags=re.IGNORECASE,
    )
    spoke_with_match = re.search(
        r"spoke\s+with\s+([A-Z][a-z]+\s+[A-Z][a-z]+)",
        block,
        flags=re.IGNORECASE,
    )

    token_matches = set(
        token.lower()
        for token in re.findall(r"[A-Za-z+#]+", block)
        if token.lower() in KNOWN_SKILL_TOKENS
    )

    has_any = bool(
        email_match
        or phone_match
        or years_match
        or company_title_match
        or spoke_with_match
        or token_matches
    )
    if not has_any:
        return {}

    current_company = ""
    title = ""
    if company_title_match:
        current_company = company_title_match.group(1).strip()
        title = company_title_match.group(2).strip()

    methods = {}
    if email_match:
        methods["email"] = "email_regex"
    if phone_match:
        methods["phone"] = "phone_regex"
    if years_match:
        methods["years_experience"] = "years_regex"
    if current_company:
        methods["current_company"] = "company_title_inferred"
    if title:
        methods["title"] = "company_title_inferred"
    if spoke_with_match:
        methods["name"] = "name_cue"
    if token_matches:
        methods["skills"] = "skills_keyword"

    return {
        "source": "notes",
        "source_file": source_file,
        "name": spoke_with_match.group(1).strip() if spoke_with_match else "",
        "email": email_match.group(0).strip() if email_match else "",
        "phone": phone_match.group(0).strip() if phone_match else "",
        "years_experience": int(years_match.group(1)) if years_match else None,
        "current_company": current_company,
        "title": title,
        "skills": sorted(token_matches),
        "raw_text": block,
        "_methods": methods,
    }


def extract_notes(path: Path) -> List[Dict]:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:  # pragma: no cover - defensive branch
        logging.warning("Failed to read notes file %s: %s", path, exc)
        return []

    if not text.strip():
        logging.warning("Skipping empty notes file: %s", path)
        return []

    records: List[Dict] = []
    for block in _split_candidate_blocks(text):
        parsed = _extract_note_block(block, str(path))
        if parsed:
            records.append(parsed)

    return records
