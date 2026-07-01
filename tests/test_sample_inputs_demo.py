import json
import subprocess
import sys
from pathlib import Path


def _run_cli(repo_root: Path, output_path: Path, config_path: Path | None = None):
    command = [
        sys.executable,
        str(repo_root / "cli.py"),
        "--input",
        str(repo_root / "sample_inputs"),
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


def test_sample_inputs_default_run_handles_edge_cases(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]
    output_path = tmp_path / "default.json"

    result = _run_cli(repo_root, output_path, repo_root / "configs" / "default.json")

    assert result.returncode == 0, result.stderr or result.stdout

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert len(payload) >= 2

    by_name = {profile["full_name"]: profile for profile in payload if profile.get("full_name")}
    assert by_name["Alex Stone"]["emails"] == ["alex.stone@example.com"]
    assert by_name["Alex Stone"]["phones"] is None
    assert by_name["Jane Doe"]["emails"] == ["jane.doe@example.com"]
    assert by_name["Jane Doe"]["phones"] == ["+14155552671"]

    if "Abhinav Khot" in by_name:
        assert by_name["Abhinav Khot"]["emails"] == ["abhinav.khot@example.com"]


def test_sample_inputs_projection_config_reshapes_output(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]
    output_path = tmp_path / "projected.json"

    result = _run_cli(repo_root, output_path, repo_root / "configs" / "custom_projection.json")

    assert result.returncode == 0, result.stderr or result.stdout

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert len(payload) >= 2

    by_name = {profile["full_name"]: profile for profile in payload if profile.get("full_name")}
    alex = by_name["Alex Stone"]
    jane = by_name["Jane Doe"]

    assert {k: alex[k] for k in ("full_name", "primary_email", "phone", "skills")} == {
        "full_name": "Alex Stone",
        "primary_email": "alex.stone@example.com",
        "phone": None,
        "skills": ["JavaScript"],
    }
    assert {k: jane[k] for k in ("full_name", "primary_email", "phone", "skills")} == {
        "full_name": "Jane Doe",
        "primary_email": "jane.doe@example.com",
        "phone": "+14155552671",
        "skills": ["Go", "Python"],
    }
    assert isinstance(alex["overall_confidence"], (int, float))
    assert isinstance(jane["overall_confidence"], (int, float))
    assert isinstance(alex["provenance"], list) and alex["provenance"]
    assert isinstance(jane["provenance"], list) and jane["provenance"]

    if "Abhinav Khot" in by_name:
        abhinav = by_name["Abhinav Khot"]
        assert abhinav["primary_email"] == "abhinav.khot@example.com"
        assert isinstance(abhinav["skills"], list)
