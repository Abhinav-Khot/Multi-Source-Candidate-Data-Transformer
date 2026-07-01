import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass(frozen=True)
class SourceDescriptor:
    source_type: str
    path: Path
    meta: Dict[str, str]


def detect_sources(input_dir: str) -> List[SourceDescriptor]:
    descriptors: List[SourceDescriptor] = []
    root = Path(input_dir)
    if not root.exists() or not root.is_dir():
        logging.warning("Input path is missing or not a directory: %s", input_dir)
        return descriptors

    for path in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        if not path.is_file():
            continue

        name = path.name.lower()
        suffix = path.suffix.lower()

        if suffix == ".csv":
            descriptors.append(SourceDescriptor("recruiter_csv", path, {}))
            continue

        if suffix == ".txt" and name == "github.txt":
            descriptors.append(SourceDescriptor("github_manifest", path, {}))
            continue

        if suffix == ".txt":
            descriptors.append(SourceDescriptor("recruiter_notes", path, {}))
            continue

        logging.warning("Skipping unknown file type: %s", path)

    return descriptors
