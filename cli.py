import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from src.pipeline import emit_json, run_pipeline


def _load_config(config_path: Optional[str]) -> Optional[Dict[str, Any]]:
    if not config_path:
        return None

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-source candidate data transformer")
    parser.add_argument("--input", required=True, help="Input folder containing source files")
    parser.add_argument("--config", required=False, help="Optional runtime projection config")
    parser.add_argument("--out", required=True, help="Output JSON path")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    config = _load_config(args.config)
    profiles = run_pipeline(args.input, config)
    emit_json(profiles, args.out)


if __name__ == "__main__":
    main()
