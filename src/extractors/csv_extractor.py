import csv
import logging
from pathlib import Path
from typing import Dict, List

EXPECTED_COLUMNS = ["name", "email", "phone", "current_company", "title"]


def extract_csv(path: Path) -> List[Dict]:
    records: List[Dict] = []
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                logging.warning("Skipping empty CSV file: %s", path)
                return records

            missing = [col for col in EXPECTED_COLUMNS if col not in reader.fieldnames]
            if missing:
                logging.warning("CSV missing expected columns %s in %s", missing, path)

            for row in reader:
                if not any((row.get(k) or "").strip() for k in reader.fieldnames):
                    continue

                records.append(
                    {
                        "source": "csv",
                        "source_file": str(path),
                        "name": (row.get("name") or "").strip(),
                        "email": (row.get("email") or "").strip(),
                        "phone": (row.get("phone") or "").strip(),
                        "current_company": (row.get("current_company") or "").strip(),
                        "title": (row.get("title") or "").strip(),
                        "_methods": {
                            "name": "direct",
                            "email": "direct",
                            "phone": "direct",
                            "current_company": "direct",
                            "title": "direct",
                        },
                    }
                )
    except Exception as exc:  # pragma: no cover - defensive branch
        logging.warning("Failed to parse CSV %s: %s", path, exc)

    return records
