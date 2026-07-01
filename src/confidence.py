from typing import Any, Dict, List

BASE_CONFIDENCE = {
    ("csv", "direct"): 0.95,
    ("github", "api"): 0.90,
    ("notes", "email_regex"): 0.75,
    ("notes", "phone_regex"): 0.75,
    ("notes", "years_regex"): 0.70,
    ("notes", "skills_keyword"): 0.65,
    ("notes", "name_cue"): 0.60,
    ("notes", "company_title_inferred"): 0.55,
}

FIELD_WEIGHTS = {
    "full_name": 3,
    "emails": 3,
    "phones": 2,
    "years_experience": 2,
    "experience": 2,
    "skills": 1,
    "headline": 1,
    "education": 1,
}


def _base_for(source: str, method: str) -> float:
    if (source, method) in BASE_CONFIDENCE:
        return BASE_CONFIDENCE[(source, method)]
    if source == "notes":
        return 0.55
    if source == "github":
        return 0.90
    if source == "csv":
        return 0.95
    return 0.50


def apply_confidence(canonical_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for record in canonical_records:
        grouped: Dict[str, set] = {}
        for prov in record.get("provenance", []):
            key = f"{prov.get('field')}::{prov.get('value_repr')}"
            grouped.setdefault(key, set()).add(prov.get("source"))

        for prov in record.get("provenance", []):
            key = f"{prov.get('field')}::{prov.get('value_repr')}"
            corroborators = max(len(grouped.get(key, set())) - 1, 0)
            base = _base_for(prov.get("source", ""), prov.get("method", ""))
            prov["confidence"] = min(0.98, base + 0.10 * corroborators)

        field_scores: Dict[str, List[float]] = {}
        for prov in record.get("provenance", []):
            if not prov.get("accepted"):
                continue
            field = prov.get("field")
            if field not in FIELD_WEIGHTS:
                continue
            field_scores.setdefault(field, []).append(float(prov.get("confidence", 0.0)))

        total = 0.0
        weight_total = 0.0
        for field, scores in field_scores.items():
            if not scores:
                continue
            field_score = sum(scores) / len(scores)
            weight = FIELD_WEIGHTS.get(field, 1)
            total += field_score * weight
            weight_total += weight

        record["overall_confidence"] = round(total / weight_total, 4) if weight_total else 0.0

        # Skill-level confidence is projected from accepted provenance for each skill name.
        skill_conf_by_name: Dict[str, float] = {}
        for prov in record.get("provenance", []):
            if prov.get("field") != "skills" or not prov.get("accepted"):
                continue
            value_repr = prov.get("value_repr", "")
            name = value_repr
            if value_repr.startswith("{") and "name:" in value_repr:
                name = value_repr.split("name:", 1)[1].split(",", 1)[0].strip("} ")
            skill_conf_by_name[name] = max(skill_conf_by_name.get(name, 0.0), prov.get("confidence", 0.0))

        for skill in record.get("skills", []):
            name = skill.get("name")
            conf = skill_conf_by_name.get(name, 0.55 if skill.get("mapped") is False else 0.75)
            skill["confidence"] = round(conf, 4)
            existing_sources = skill.get("sources") or []
            skill["sources"] = sorted(set(existing_sources))

    return canonical_records
