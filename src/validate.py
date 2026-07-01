from typing import Any, Dict, List


class ValidationError(Exception):
    pass


TYPE_CHECKS = {
    "string": lambda v: isinstance(v, str),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "string[]": lambda v: isinstance(v, list) and all(isinstance(i, str) for i in v),
    "array": lambda v: isinstance(v, list),
    "object": lambda v: isinstance(v, dict),
}


def _resolve(projected: Dict[str, Any], path: str) -> Any:
    node: Any = projected
    for token in path.split("."):
        if not isinstance(node, dict) or token not in node:
            return None
        node = node[token]
    return node


def _validate_type(path: str, value: Any, type_name: str) -> None:
    check = TYPE_CHECKS.get(type_name)
    if check is None:
        raise ValidationError(f"Unsupported type in schema: {type_name} for {path}")
    if value is None:
        return
    if not check(value):
        raise ValidationError(f"Type mismatch for {path}: expected {type_name}")


def _default_schema() -> List[Dict[str, Any]]:
    return [
        {"path": "candidate_id", "type": "string", "required": True},
        {"path": "full_name", "type": "string", "required": True},
        {"path": "emails", "type": "string[]", "required": True},
        {"path": "phones", "type": "string[]", "required": True},
        {"path": "location", "type": "object", "required": True},
        {"path": "links", "type": "object", "required": True},
        {"path": "headline", "type": "string", "required": False},
        {"path": "years_experience", "type": "number", "required": False},
        {"path": "skills", "type": "array", "required": True},
        {"path": "experience", "type": "array", "required": True},
        {"path": "education", "type": "array", "required": True},
        {"path": "provenance", "type": "array", "required": True},
        {"path": "overall_confidence", "type": "number", "required": True},
    ]


def validate_projected(projected: Dict[str, Any], config: Dict[str, Any] = None) -> None:
    schema = config.get("fields") if config else None
    if not schema:
        schema = _default_schema()

    for field in schema:
        path = field["path"]
        required = bool(field.get("required", False))
        type_name = field.get("type", "string")
        value = _resolve(projected, path)

        if required and value is None:
            raise ValidationError(f"Missing required field: {path}")

        _validate_type(path, value, type_name)
