from pathlib import Path

from src.pipeline import run_pipeline


def test_malformed_source_file_does_not_crash(tmp_path: Path):
    input_dir = tmp_path / "inputs"
    input_dir.mkdir()

    bad_csv = input_dir / "bad.csv"
    bad_csv.write_bytes(b"\x00\x01\x02")

    good_notes = input_dir / "notes.txt"
    good_notes.write_text(
        "Spoke with Jane Doe, jane@example.com, +1 415 555 2671. 5 years experience in backend.",
        encoding="utf-8",
    )

    out = run_pipeline(str(input_dir), config=None)
    assert isinstance(out, list)
    assert len(out) >= 1
