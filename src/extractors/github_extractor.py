import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests


def _extract_username(raw: str) -> Optional[str]:
    candidate = raw.strip()
    if not candidate:
        return None

    url_match = re.search(r"github\.com/([A-Za-z0-9-]+)", candidate)
    if url_match:
        return url_match.group(1)

    if re.match(r"^[A-Za-z0-9-]+$", candidate):
        return candidate
    return None


def _parse_manifest_line(line: str) -> Tuple[Optional[str], Optional[str]]:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None, None

    if "," in stripped:
        left, right = [piece.strip() for piece in stripped.split(",", 1)]
        if "@" in left:
            return left.lower(), _extract_username(right)
        if "@" in right:
            return right.lower(), _extract_username(left)
        return None, _extract_username(right or left)

    parts = stripped.split()
    if len(parts) == 1:
        return None, _extract_username(parts[0])

    for piece in parts:
        if "@" in piece:
            other = next((p for p in parts if p != piece), "")
            return piece.lower(), _extract_username(other)

    return None, _extract_username(parts[0])


def _safe_get(url: str) -> Optional[requests.Response]:
    try:
        return requests.get(url, timeout=10)
    except Exception as exc:  # pragma: no cover - network defensive branch
        logging.warning("GitHub request failed for %s: %s", url, exc)
        return None


def extract_github_manifest(path: Path) -> List[Dict]:
    records: List[Dict] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception as exc:  # pragma: no cover - defensive branch
        logging.warning("Failed to read GitHub manifest %s: %s", path, exc)
        return records

    for line in lines:
        candidate_email, username = _parse_manifest_line(line)
        if not username:
            continue

        user_resp = _safe_get(f"https://api.github.com/users/{username}")
        if user_resp is None:
            continue

        if user_resp.status_code == 404:
            logging.warning("GitHub user not found: %s", username)
            continue
        if user_resp.status_code == 403:
            logging.warning("GitHub API rate-limited for user: %s", username)
            continue
        if user_resp.status_code != 200:
            logging.warning("GitHub API error for %s: %s", username, user_resp.status_code)
            continue

        repos_resp = _safe_get(f"https://api.github.com/users/{username}/repos")
        if repos_resp is None:
            continue
        if repos_resp.status_code == 403:
            logging.warning("GitHub API rate-limited for repos: %s", username)
            continue
        if repos_resp.status_code != 200:
            logging.warning("GitHub repos fetch failed for %s: %s", username, repos_resp.status_code)
            continue

        try:
            user_data = user_resp.json() if user_resp.text else {}
        except ValueError as exc:
            logging.warning("GitHub user payload was not valid JSON for %s: %s", username, exc)
            continue

        try:
            repos_data = repos_resp.json() if repos_resp.text else []
        except ValueError as exc:
            logging.warning("GitHub repos payload was not valid JSON for %s: %s", username, exc)
            continue

        if not isinstance(repos_data, list):
            logging.warning("GitHub repos payload was not a list for %s", username)
            continue
        languages = sorted(
            {
                repo.get("language")
                for repo in repos_data
                if isinstance(repo, dict) and repo.get("language")
            }
        )

        records.append(
            {
                "source": "github",
                "source_file": str(path),
                "candidate_email": candidate_email or "",
                "github_username": username,
                "name": (user_data.get("name") or "").strip(),
                "bio": (user_data.get("bio") or "").strip(),
                "profile_url": (user_data.get("html_url") or "").strip(),
                "languages": languages,
                "_methods": {
                    "name": "api",
                    "bio": "api",
                    "languages": "api",
                    "profile_url": "api",
                },
            }
        )

    return records
