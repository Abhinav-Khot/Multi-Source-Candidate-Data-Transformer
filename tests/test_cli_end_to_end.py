import json
import subprocess
import sys
from pathlib import Path


def _run_cli(repo_root: Path, input_dir: Path, output_path: Path, config_path: Path | None = None):
    command = [
        sys.executable,
        str(repo_root / "cli.py"),
        "--input",
        str(input_dir),
        "--out",
        str(output_path),
    ]
    if config_path is not None:
        command.extend(["--config", str(config_path)])

    return subprocess.run(
        command,
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )


def _read_output(output_path: Path):
    return json.loads(output_path.read_text(encoding="utf-8"))


def _expected_mixed_profile():
    return {
        "candidate_id": "email:jane@example.com",
        "education": None,
        "emails": ["jane@example.com"],
        "experience": [
            {
                "company": "Acme Corp",
                "end": None,
                "start": None,
                "summary": None,
                "title": "Senior Engineer",
            }
        ],
        "full_name": "Jane Doe",
        "headline": "Senior Engineer",
        "links": {"github": None, "linkedin": None, "portfolio": None, "other": []},
        "location": {"city": None, "country": None, "region": None},
        "overall_confidence": 0.8618,
        "phones": ["+14155552671"],
        "provenance": [
            {
                "accepted": False,
                "confidence": 0.7,
                "field": "full_name",
                "method": "name_cue",
                "source": "notes",
                "value_repr": "Jane Doe",
            },
            {
                "accepted": True,
                "confidence": 0.65,
                "field": "skills",
                "method": "skills_keyword",
                "source": "notes",
                "value_repr": "{mapped:None,name:js,sources:[notes]}",
            },
            {
                "accepted": True,
                "confidence": 0.65,
                "field": "skills",
                "method": "skills_keyword",
                "source": "notes",
                "value_repr": "{mapped:None,name:python,sources:[notes]}",
            },
            {
                "accepted": True,
                "confidence": 0.7,
                "field": "full_name",
                "method": "name_cue",
                "source": "notes",
                "value_repr": "Jane Doe",
            },
            {
                "accepted": True,
                "confidence": 0.7,
                "field": "years_experience",
                "method": "years_regex",
                "source": "notes",
                "value_repr": "5",
            },
            {
                "accepted": True,
                "confidence": 0.85,
                "field": "emails",
                "method": "email_regex",
                "source": "notes",
                "value_repr": "jane@example.com",
            },
            {
                "accepted": True,
                "confidence": 0.95,
                "field": "experience",
                "method": "direct",
                "source": "csv",
                "value_repr": "{company:Acme Corp,end:None,start:None,summary:None,title:Senior Engineer}",
            },
            {
                "accepted": True,
                "confidence": 0.95,
                "field": "headline",
                "method": "direct",
                "source": "csv",
                "value_repr": "Senior Engineer",
            },
            {
                "accepted": True,
                "confidence": 0.95,
                "field": "phones",
                "method": "direct",
                "source": "csv",
                "value_repr": "+14155552671",
            },
            {
                "accepted": True,
                "confidence": 0.98,
                "field": "emails",
                "method": "direct",
                "source": "csv",
                "value_repr": "jane@example.com",
            },
            {
                "accepted": True,
                "confidence": 0.98,
                "field": "full_name",
                "method": "direct",
                "source": "csv",
                "value_repr": "Jane Doe",
            },
        ],
        "skills": [
            {"name": "js", "confidence": 0.65, "sources": ["notes"]},
            {"name": "python", "confidence": 0.65, "sources": ["notes"]},
        ],
        "years_experience": 5,
    }


def _expected_notes_profile():
    return {
        "candidate_id": "email:jane@example.com",
        "education": None,
        "emails": ["jane@example.com"],
        "experience": None,
        "full_name": "Jane Doe",
        "headline": None,
        "links": {"github": None, "linkedin": None, "portfolio": None, "other": []},
        "location": {"city": None, "country": None, "region": None},
        "overall_confidence": 0.6812,
        "phones": None,
        "provenance": [
            {
                "accepted": True,
                "confidence": 0.6,
                "field": "full_name",
                "method": "name_cue",
                "source": "notes",
                "value_repr": "Jane Doe",
            },
            {
                "accepted": True,
                "confidence": 0.7,
                "field": "years_experience",
                "method": "years_regex",
                "source": "notes",
                "value_repr": "5",
            },
            {
                "accepted": True,
                "confidence": 0.75,
                "field": "emails",
                "method": "email_regex",
                "source": "notes",
                "value_repr": "jane@example.com",
            },
        ],
        "skills": None,
        "years_experience": 5,
    }


def _expected_canonical_profile():
    return {
        "candidate_id": "email:alice@example.com",
        "education": [],
        "emails": ["alice@example.com"],
        "experience": [
            {
                "company": "Initech",
                "end": None,
                "start": None,
                "summary": None,
                "title": "Engineer",
            }
        ],
        "full_name": "Alice Chen",
        "headline": "Engineer",
        "links": {"github": None, "linkedin": None, "portfolio": None, "other": []},
        "location": {"city": None, "country": None, "region": None},
        "overall_confidence": 0.95,
        "phones": ["+14155551234"],
        "provenance": [
            {
                "accepted": True,
                "confidence": 0.95,
                "field": "emails",
                "method": "direct",
                "source": "csv",
                "value_repr": "alice@example.com",
            },
            {
                "accepted": True,
                "confidence": 0.95,
                "field": "experience",
                "method": "direct",
                "source": "csv",
                "value_repr": "{company:Initech,end:None,start:None,summary:None,title:Engineer}",
            },
            {
                "accepted": True,
                "confidence": 0.95,
                "field": "full_name",
                "method": "direct",
                "source": "csv",
                "value_repr": "Alice Chen",
            },
            {
                "accepted": True,
                "confidence": 0.95,
                "field": "headline",
                "method": "direct",
                "source": "csv",
                "value_repr": "Engineer",
            },
            {
                "accepted": True,
                "confidence": 0.95,
                "field": "phones",
                "method": "direct",
                "source": "csv",
                "value_repr": "+14155551234",
            },
        ],
        "skills": [],
        "years_experience": None,
    }


def test_cli_happy_path_writes_projected_output(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]
    input_dir = tmp_path / "happy_inputs"
    output_path = tmp_path / "happy.json"
    input_dir.mkdir(parents=True, exist_ok=True)

    (input_dir / "recruiter_export.csv").write_text(
        "name,email,phone,current_company,title\n"
        "Jane Doe,jane@example.com,+14155552671,Acme Corp,Senior Engineer\n",
        encoding="utf-8",
    )
    (input_dir / "notes.txt").write_text(
        "Spoke with Jane Doe, jane@example.com, +1 415 555 2671. 5 years experience in backend, knows js and Python.",
        encoding="utf-8",
    )

    result = _run_cli(repo_root, input_dir, output_path, repo_root / "configs" / "default.json")

    assert result.returncode == 0, result.stderr or result.stdout
    assert _read_output(output_path) == [_expected_mixed_profile()]


def test_cli_skips_unknown_and_keeps_valid_sources(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]
    input_dir = tmp_path / "mixed_inputs"
    output_path = tmp_path / "mixed.json"
    input_dir.mkdir(parents=True, exist_ok=True)

    (input_dir / "readme.md").write_text("this should be skipped", encoding="utf-8")
    (input_dir / "recruiter_export.csv").write_text(
        "name,email,phone,current_company,title\n"
        "Jane Doe,jane@example.com,+14155552671,Acme Corp,Senior Engineer\n",
        encoding="utf-8",
    )
    (input_dir / "notes.txt").write_text(
        "Spoke with Jane Doe, jane@example.com, +1 415 555 2671. 5 years experience in backend, knows js and Python.",
        encoding="utf-8",
    )

    result = _run_cli(repo_root, input_dir, output_path, repo_root / "configs" / "default.json")

    assert result.returncode == 0, result.stderr or result.stdout
    assert _read_output(output_path) == [_expected_mixed_profile()]


def test_cli_handles_malformed_csv_and_still_emits_from_notes(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]
    input_dir = tmp_path / "bad_csv_inputs"
    output_path = tmp_path / "bad_csv.json"
    input_dir.mkdir(parents=True, exist_ok=True)

    (input_dir / "bad.csv").write_bytes(b"\x00\x01\x02")
    (input_dir / "notes.txt").write_text(
        "Spoke with Jane Doe, jane@example.com, +1 415 555 2671. 5 years experience in backend.",
        encoding="utf-8",
    )

    result = _run_cli(repo_root, input_dir, output_path, repo_root / "configs" / "default.json")

    assert result.returncode == 0, result.stderr or result.stdout
    assert _read_output(output_path) == [_expected_notes_profile()]


def test_cli_without_config_uses_full_canonical_schema(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]
    input_dir = tmp_path / "canonical_inputs"
    output_path = tmp_path / "canonical.json"
    input_dir.mkdir(parents=True, exist_ok=True)

    (input_dir / "recruiter_export.csv").write_text(
        "name,email,phone,current_company,title\n"
        "Alice Chen,alice@example.com,+14155551234,Initech,Engineer\n",
        encoding="utf-8",
    )

    result = _run_cli(repo_root, input_dir, output_path, None)

    assert result.returncode == 0, result.stderr or result.stdout
    assert _read_output(output_path) == [_expected_canonical_profile()]


def test_cli_empty_input_directory_emits_empty_list(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]
    input_dir = tmp_path / "empty_inputs"
    output_path = tmp_path / "empty.json"
    input_dir.mkdir(parents=True, exist_ok=True)

    result = _run_cli(repo_root, input_dir, output_path, repo_root / "configs" / "default.json")

    assert result.returncode == 0, result.stderr or result.stdout
    assert _read_output(output_path) == []
