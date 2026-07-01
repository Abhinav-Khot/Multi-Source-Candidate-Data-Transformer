import json
from pathlib import Path

from src.pipeline import run_pipeline


def _write_minimal_inputs(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "recruiter_export.csv").write_text(
        "name,email,phone,current_company,title\n"
        "Jane Doe,jane@example.com,+14155552671,Acme Corp,Senior Engineer\n",
        encoding="utf-8",
    )
    (root / "notes.txt").write_text(
        "Spoke with Jane Doe, jane@example.com, +1 (415) 555-2671. "
        "5 years experience in backend, knows js and Python, currently at Acme Corp as a senior engineer.",
        encoding="utf-8",
    )


def test_pipeline_uses_custom_projection_config_shape(tmp_path: Path):
    input_dir = tmp_path / "inputs"
    _write_minimal_inputs(input_dir)

    config = json.loads(Path("configs/custom_projection.json").read_text(encoding="utf-8"))
    out = run_pipeline(str(input_dir), config=config)

    assert len(out) == 1
    profile = out[0]

    assert "full_name" in profile
    assert "primary_email" in profile
    assert "phone" in profile
    assert "skills" in profile
    assert "overall_confidence" in profile
    assert "provenance" in profile
    assert profile["primary_email"] == "jane@example.com"
    assert profile["phone"] == "+14155552671"
    assert "JavaScript" in profile["skills"]


def test_pipeline_is_deterministic_for_same_input_and_config(tmp_path: Path):
    input_dir = tmp_path / "inputs"
    _write_minimal_inputs(input_dir)
    config = json.loads(Path("configs/custom_projection.json").read_text(encoding="utf-8"))

    first = run_pipeline(str(input_dir), config=config)
    second = run_pipeline(str(input_dir), config=config)

    first_json = json.dumps(first, sort_keys=True, separators=(",", ":"))
    second_json = json.dumps(second, sort_keys=True, separators=(",", ":"))
    assert first_json == second_json
