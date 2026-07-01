import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.confidence import apply_confidence
from src.detect import detect_sources
from src.extract import extract_sources
from src.merge import merge_records
from src.project import project
from src.validate import validate_projected


def _canonicalize_skills(candidates: List[Dict[str, Any]]) -> None:
    for candidate in candidates:
        merged_by_name: Dict[str, Dict[str, Any]] = {}
        for skill in candidate.get("skills", []):
            name = skill.get("name") if isinstance(skill, dict) else str(skill)
            if not name:
                continue
            if name not in merged_by_name:
                merged_by_name[name] = {
                    "name": name,
                    "confidence": skill.get("confidence", 0.0) if isinstance(skill, dict) else 0.0,
                    "sources": set(skill.get("sources", [])) if isinstance(skill, dict) else set(),
                }
                continue

            merged_by_name[name]["confidence"] = max(
                merged_by_name[name]["confidence"],
                skill.get("confidence", 0.0) if isinstance(skill, dict) else 0.0,
            )
            if isinstance(skill, dict):
                merged_by_name[name]["sources"].update(skill.get("sources", []))

        candidate["skills"] = [
            {"name": item["name"], "confidence": item["confidence"], "sources": sorted(item["sources"])}
            for item in sorted(merged_by_name.values(), key=lambda s: s["name"].lower())
        ]


def _sort_deterministic(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _sort_deterministic(value[k]) for k in sorted(value.keys())}
    if isinstance(value, list):
        normalized = [_sort_deterministic(v) for v in value]
        try:
            return sorted(normalized, key=lambda item: json.dumps(item, sort_keys=True, separators=(",", ":")))
        except TypeError:
            return normalized
    return value


def run_pipeline(input_dir: str, config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    descriptors = detect_sources(input_dir)
    raw_records = extract_sources(descriptors)
    merged = merge_records(raw_records)
    merged = apply_confidence(merged)
    _canonicalize_skills(merged)

    outputs: List[Dict[str, Any]] = []
    if config and config.get("fields"):
        for candidate in merged:
            projected = project(candidate, config)
            validate_projected(projected, config)
            outputs.append(_sort_deterministic(projected))
    else:
        for candidate in merged:
            validate_projected(candidate, None)
            outputs.append(_sort_deterministic(candidate))

    outputs = sorted(outputs, key=lambda item: json.dumps(item, sort_keys=True, separators=(",", ":")))
    return outputs


def emit_json(profiles: List[Dict[str, Any]], out_path: str) -> None:
    target = Path(out_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(profiles, handle, indent=2, sort_keys=True)
        handle.write("\n")

    logging.info("Wrote %d profiles to %s", len(profiles), out_path)
