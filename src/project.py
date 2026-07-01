from typing import Any, Dict, List, Optional

from src.normalize import canonicalize_skill, normalize_phone_e164


class ProjectionError(Exception):
    pass


MISSING = object()


def _tokenize(path: str) -> List[str]:
    tokens: List[str] = []
    i = 0
    while i < len(path):
        if path[i] == ".":
            i += 1
            continue
        if path[i] == "[":
            j = path.find("]", i)
            if j < 0:
                raise ProjectionError(f"Invalid path token: {path}")
            tokens.append(path[i : j + 1])
            i = j + 1
            continue
        j = i
        while j < len(path) and path[j] not in ".[":
            j += 1
        tokens.append(path[i:j])
        i = j
    return tokens


def _resolve_path(data: Any, path: str) -> Any:
    tokens = _tokenize(path)
    current = [data]
    list_mode = False
    for token in tokens:
        next_items: List[Any] = []
        if token == "[]":
            list_mode = True
            for item in current:
                if isinstance(item, list):
                    next_items.extend(item)
            current = next_items
            continue

        if token.startswith("[") and token.endswith("]"):
            raw = token[1:-1]
            if raw == "":
                for item in current:
                    if isinstance(item, list):
                        next_items.extend(item)
                current = next_items
                continue
            try:
                idx = int(raw)
            except ValueError as exc:
                raise ProjectionError(f"Invalid list index token: {token}") from exc
            for item in current:
                if isinstance(item, list) and 0 <= idx < len(item):
                    next_items.append(item[idx])
            current = next_items
            continue

        for item in current:
            if isinstance(item, dict) and token in item:
                next_items.append(item[token])
        current = next_items

    if not current:
        return MISSING
    if list_mode:
        return current
    if len(current) == 1:
        return current[0]
    return current


def _set_output_path(out: Dict[str, Any], path: str, value: Any) -> None:
    tokens = [token for token in _tokenize(path) if not token.startswith("[")]
    if not tokens:
        raise ProjectionError(f"Invalid output path: {path}")
    node = out
    for token in tokens[:-1]:
        node = node.setdefault(token, {})
    node[tokens[-1]] = value


def _apply_normalize_override(value: Any, name: Optional[str]) -> Any:
    if name is None:
        return value

    lowered = name.lower()
    if lowered == "e164":
        if isinstance(value, list):
            return [normalize_phone_e164(v) for v in value]
        return normalize_phone_e164(value)

    if lowered == "canonical":
        if isinstance(value, list):
            out = []
            for token in value:
                canonical, _ = canonicalize_skill(str(token))
                out.append(canonical)
            return out
        canonical, _ = canonicalize_skill(str(value))
        return canonical

    raise ProjectionError(f"Unsupported normalize override: {name}")


def _is_missing_or_empty(value: Any) -> bool:
    if value is MISSING:
        return True
    if value is None:
        return True
    if value == "":
        return True
    if isinstance(value, list) and not value:
        return True
    return False


def project(canonical: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    fields = config.get("fields", [])
    on_missing = config.get("on_missing", "null")
    include_confidence = bool(config.get("include_confidence", False))
    include_provenance = bool(config.get("include_provenance", True))

    out: Dict[str, Any] = {}
    for field in fields:
        path = field["path"]
        from_path = field.get("from", path)
        value = _resolve_path(canonical, from_path)

        if _is_missing_or_empty(value):
            if on_missing == "null":
                _set_output_path(out, path, None)
                continue
            if on_missing == "omit":
                continue
            if on_missing == "error":
                raise ProjectionError(f"Missing projected field: {path}")
            raise ProjectionError(f"Unsupported on_missing policy: {on_missing}")

        value = _apply_normalize_override(value, field.get("normalize"))

        _set_output_path(out, path, value)

    if include_confidence:
        out["overall_confidence"] = canonical.get("overall_confidence")
    if include_provenance:
        out["provenance"] = canonical.get("provenance", [])

    return out
