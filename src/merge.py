from copy import deepcopy
from typing import Any, Dict, List, Optional

from src.normalize import normalize_email, normalize_full_name, normalize_name_key, normalize_phone_e164

SOURCE_RANK = {"csv": 3, "notes": 2, "github": 1}
HEADLINE_RANK = {"github": 3, "notes": 2, "csv": 1}
EXPERIENCE_RANK = {"notes": 3, "csv": 2, "github": 1}


def _empty_candidate() -> Dict[str, Any]:
    return {
        "candidate_id": "",
        "full_name": "",
        "emails": [],
        "phones": [],
        "location": {"city": None, "region": None, "country": None},
        "links": {"linkedin": None, "github": None, "portfolio": None, "other": []},
        "headline": None,
        "years_experience": None,
        "skills": [],
        "experience": [],
        "education": [],
        "provenance": [],
        "overall_confidence": 0.0,
        "_field_values": {},
        "_soft_match": False,
    }


def _value_repr(value: Any) -> str:
    if isinstance(value, dict):
        items = sorted((str(k), _value_repr(v)) for k, v in value.items())
        return "{" + ",".join(f"{k}:{v}" for k, v in items) + "}"
    if isinstance(value, list):
        return "[" + ",".join(_value_repr(v) for v in value) + "]"
    return str(value)


def _append_provenance(
    candidate: Dict[str, Any],
    field: str,
    source: str,
    method: str,
    value: Any,
    accepted: bool,
) -> None:
    candidate["provenance"].append(
        {
            "field": field,
            "source": source,
            "method": method,
            "value_repr": _value_repr(value),
            "confidence": 0.0,
            "accepted": accepted,
        }
    )


def _register_scalar(
    candidate: Dict[str, Any],
    field: str,
    value: Any,
    source: str,
    method: str,
    rank_map: Dict[str, int],
) -> None:
    if value in (None, ""):
        return

    contenders = candidate["_field_values"].setdefault(field, [])
    contenders.append({"value": value, "source": source, "method": method})

    ranked = sorted(
        contenders,
        key=lambda item: (-rank_map.get(item["source"], 0), item["source"], _value_repr(item["value"])),
    )
    winner = ranked[0]
    candidate[field] = winner["value"]

    for contender in contenders:
        accepted = contender is winner
        _append_provenance(candidate, field, contender["source"], contender["method"], contender["value"], accepted)


def _register_list_values(
    candidate: Dict[str, Any],
    field: str,
    values: List[Any],
    source: str,
    method: str,
) -> None:
    if not values:
        return

    existing = candidate[field]
    seen = {_value_repr(v): v for v in existing}
    for value in values:
        value_key = _value_repr(value)
        if value_key not in seen:
            existing.append(value)
            seen[value_key] = value
        _append_provenance(candidate, field, source, method, value, True)


def _dedupe_by_repr(items: List[Any]) -> List[Any]:
    by_key: Dict[str, Any] = {}
    for item in items:
        by_key[_value_repr(item)] = deepcopy(item)
    return [by_key[key] for key in sorted(by_key.keys())]


def _normalize_fragment(raw: Dict[str, Any]) -> Dict[str, Any]:
    source = raw.get("source", "")
    methods = raw.get("_methods", {})
    full_name = normalize_full_name(raw.get("name"))

    emails = []
    direct_email = normalize_email(raw.get("email"))
    if direct_email:
        emails.append(direct_email)

    candidate_email = normalize_email(raw.get("candidate_email"))
    if candidate_email and candidate_email not in emails:
        emails.append(candidate_email)

    phones = []
    direct_phone = normalize_phone_e164(raw.get("phone"))
    if direct_phone:
        phones.append(direct_phone)

    skills = []
    if source == "notes":
        skills = [{"name": token, "mapped": None, "sources": ["notes"]} for token in raw.get("skills", [])]
    elif source == "github":
        skills = [{"name": token, "mapped": None, "sources": ["github"]} for token in raw.get("languages", [])]

    experience = []
    if raw.get("current_company") or raw.get("title"):
        experience.append(
            {
                "company": raw.get("current_company") or None,
                "title": raw.get("title") or None,
                "start": None,
                "end": None,
                "summary": None,
            }
        )

    links = {"linkedin": None, "github": None, "portfolio": None, "other": []}
    if source == "github" and raw.get("profile_url"):
        links["github"] = raw.get("profile_url")

    return {
        "source": source,
        "methods": methods,
        "full_name": full_name,
        "emails": emails,
        "phones": phones,
        "headline": (raw.get("bio") or raw.get("title") or "").strip() or None,
        "years_experience": raw.get("years_experience"),
        "skills": skills,
        "experience": experience,
        "education": [],
        "location": {"city": None, "region": None, "country": None},
        "links": links,
        "name_key": normalize_name_key(full_name),
    }


def _candidate_match_key(candidate: Dict[str, Any]) -> Dict[str, Optional[str]]:
    email = candidate["emails"][0] if candidate["emails"] else None
    phone = candidate["phones"][0] if candidate["phones"] else None
    name = normalize_name_key(candidate.get("full_name")) if candidate.get("full_name") else None
    return {"email": email, "phone": phone, "name": name}


def _find_match(candidates: List[Dict[str, Any]], fragment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if fragment["emails"]:
        target = fragment["emails"][0]
        for candidate in candidates:
            if target in candidate["emails"]:
                return candidate
        return None

    if fragment["phones"]:
        target = fragment["phones"][0]
        for candidate in candidates:
            if target in candidate["phones"]:
                return candidate
        return None

    if fragment["name_key"]:
        target = fragment["name_key"]
        for candidate in candidates:
            keys = _candidate_match_key(candidate)
            if keys["name"] == target:
                return candidate
    return None


def _merge_fragment(candidate: Dict[str, Any], fragment: Dict[str, Any]) -> None:
    source = fragment["source"]
    methods = fragment["methods"]

    _register_scalar(
        candidate,
        "full_name",
        fragment["full_name"],
        source,
        methods.get("name", "direct"),
        SOURCE_RANK,
    )
    _register_scalar(
        candidate,
        "headline",
        fragment["headline"],
        source,
        methods.get("bio", methods.get("title", "direct")),
        HEADLINE_RANK,
    )
    _register_scalar(
        candidate,
        "years_experience",
        fragment["years_experience"],
        source,
        methods.get("years_experience", "direct"),
        EXPERIENCE_RANK,
    )

    _register_list_values(candidate, "emails", fragment["emails"], source, methods.get("email", "direct"))
    _register_list_values(candidate, "phones", fragment["phones"], source, methods.get("phone", "direct"))
    _register_list_values(candidate, "skills", fragment["skills"], source, methods.get("skills", "direct"))
    _register_list_values(candidate, "experience", fragment["experience"], source, methods.get("title", "direct"))
    _register_list_values(candidate, "education", fragment["education"], source, methods.get("education", "direct"))

    if fragment["links"].get("github"):
        _register_scalar(
            candidate,
            "links",
            {
                "linkedin": candidate["links"]["linkedin"],
                "github": fragment["links"]["github"],
                "portfolio": candidate["links"]["portfolio"],
                "other": candidate["links"]["other"],
            },
            source,
            methods.get("profile_url", "api"),
            SOURCE_RANK,
        )
        if isinstance(candidate["links"], dict):
            candidate["links"]["github"] = fragment["links"]["github"]


def _finalize_candidate_ids(candidates: List[Dict[str, Any]]) -> None:
    for index, candidate in enumerate(candidates, start=1):
        if candidate["emails"]:
            candidate_id = f"email:{candidate['emails'][0]}"
        elif candidate["phones"]:
            candidate_id = f"phone:{candidate['phones'][0]}"
        elif candidate["full_name"]:
            candidate_id = f"name:{normalize_name_key(candidate['full_name'])}"
        else:
            candidate_id = f"candidate:{index:04d}"
        candidate["candidate_id"] = candidate_id


def merge_records(raw_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    fragments = [_normalize_fragment(record) for record in raw_records]

    # Stable order ensures deterministic matching.
    fragments = sorted(
        fragments,
        key=lambda item: (
            0 if item["emails"] else 1 if item["phones"] else 2 if item["name_key"] else 3,
            item["emails"][0] if item["emails"] else "",
            item["phones"][0] if item["phones"] else "",
            item["name_key"] or "",
            item["source"],
        ),
    )

    candidates: List[Dict[str, Any]] = []
    for fragment in fragments:
        candidate = _find_match(candidates, fragment)
        if candidate is None:
            candidate = _empty_candidate()
            candidates.append(candidate)

        before_emails = bool(candidate["emails"])
        before_phones = bool(candidate["phones"])
        _merge_fragment(candidate, fragment)

        if not before_emails and not before_phones and not fragment["emails"] and not fragment["phones"] and fragment["name_key"]:
            candidate["_soft_match"] = True
            _append_provenance(candidate, "full_name", "merge", "name_soft", fragment["name_key"], True)

    _finalize_candidate_ids(candidates)

    for candidate in candidates:
        candidate["emails"] = sorted(set(candidate["emails"]))
        candidate["phones"] = sorted(set(candidate["phones"]))
        candidate["skills"] = _dedupe_by_repr(candidate["skills"])
        candidate["experience"] = _dedupe_by_repr(candidate["experience"])
        candidate["education"] = _dedupe_by_repr(candidate["education"])
        candidate["provenance"] = sorted(
            candidate["provenance"],
            key=lambda p: (p["field"], p["source"], p["method"], p["value_repr"], not p["accepted"]),
        )
        candidate.pop("_field_values", None)
        candidate.pop("_soft_match", None)

    return sorted(candidates, key=lambda c: c["candidate_id"])
