from pathlib import Path

from src.extractors.github_extractor import extract_github_manifest


class _FakeResponse:
    def __init__(self, status_code, text, payload=None, json_error=None):
        self.status_code = status_code
        self.text = text
        self._payload = payload
        self._json_error = json_error

    def json(self):
        if self._json_error is not None:
            raise self._json_error
        return self._payload


def test_extract_github_manifest_skips_malformed_repos_json(monkeypatch, tmp_path: Path):
    manifest = tmp_path / "github.txt"
    manifest.write_text("octocat\n", encoding="utf-8")

    def fake_get(url, timeout=10):
        if url.endswith("/users/octocat"):
            return _FakeResponse(200, "{\"name\": \"The Octocat\", \"bio\": null, \"html_url\": \"https://github.com/octocat\"}", payload={"name": "The Octocat", "bio": None, "html_url": "https://github.com/octocat"})
        if url.endswith("/users/octocat/repos"):
            return _FakeResponse(200, "not json", json_error=ValueError("No JSON object could be decoded"))
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr("src.extractors.github_extractor.requests.get", fake_get)

    assert extract_github_manifest(manifest) == []


def test_extract_github_manifest_skips_malformed_user_json(monkeypatch, tmp_path: Path):
    manifest = tmp_path / "github.txt"
    manifest.write_text("octocat\n", encoding="utf-8")

    def fake_get(url, timeout=10):
        if url.endswith("/users/octocat"):
            return _FakeResponse(200, "not json", json_error=ValueError("No JSON object could be decoded"))
        if url.endswith("/users/octocat/repos"):
            raise AssertionError("repos endpoint should not be called when user JSON is malformed")
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr("src.extractors.github_extractor.requests.get", fake_get)

    assert extract_github_manifest(manifest) == []
