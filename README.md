# Multi-Source Candidate Data Transformer

This project builds a deterministic Python pipeline that ingests candidate data from:

- recruiter CSV files
- recruiter notes text files
- GitHub profile data via the public REST API

and emits one canonical, schema-valid JSON profile per candidate.

## Repo Structure

```
.
|-- cli.py
|-- configs/
|   |-- default.json
|   `-- custom_projection.json
|-- outputs/
|-- run_tests.py
|-- sample_inputs/
|   |-- bad.csv
|   |-- github.txt
|   |-- notes.txt
|   `-- recruiter_export.csv
|   `-- unknown.md
|-- src/
|   |-- confidence.py
|   |-- detect.py
|   |-- extract.py
|   |-- merge.py
|   |-- normalize.py
|   |-- pipeline.py
|   |-- project.py
|   |-- validate.py
|   `-- extractors/
|       |-- csv_extractor.py
|       |-- github_extractor.py
|       |-- notes_extractor.py
|       `-- __init__.py
`-- tests/
  |-- test_merge.py
  |-- test_normalize.py
  |-- test_pipeline_projection_config.py
  |-- test_pipeline_robustness.py
  `-- test_project.py
```

## Install

```bash
python -m pip install -r requirements.txt
```

## Run

Projected output mode:

```bash
python cli.py --input ./sample_inputs --config ./configs/custom_projection.json --out ./outputs/profiles.json
```

Default canonical output mode:

```bash
python cli.py --input ./sample_inputs --out ./outputs/profiles_full.json
```

If you omit `--config`, the pipeline uses the full canonical schema instead of reshaping the output.

## Tests

```bash
pytest -q
```

Simplest one-command runner:

```bash
python run_tests.py
```

Run only projection/determinism tests:

```bash
python run_tests.py tests/test_pipeline_projection_config.py -q
```

## Design Notes and Assumptions

- Pipeline stages are implemented in this order and as separate modules: detect -> extract -> normalize -> merge -> confidence -> project -> validate -> emit.
- Unknown files are skipped with warnings.
- Missing, empty, malformed, and partially unavailable sources never crash the run.
- GitHub 404 and rate-limit 403 responses are warned and skipped.
- Notes parsing uses regex/keyword heuristics only.
- Unknown/unparseable values are set to null or omitted per policy; no values are invented.
- Determinism: sorted keys, stable list ordering, and no wall-clock output fields.

## Deliberately Descoped

- fuzzy name matching
- ML-based skill matching
- LinkedIn as a live source
- general-purpose NLP for notes parsing
