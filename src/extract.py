from typing import Dict, List

from src.detect import SourceDescriptor
from src.extractors.csv_extractor import extract_csv
from src.extractors.github_extractor import extract_github_manifest
from src.extractors.notes_extractor import extract_notes


def extract_sources(descriptors: List[SourceDescriptor]) -> List[Dict]:
    records: List[Dict] = []
    for descriptor in descriptors:
        if descriptor.source_type == "recruiter_csv":
            records.extend(extract_csv(descriptor.path))
        elif descriptor.source_type == "recruiter_notes":
            records.extend(extract_notes(descriptor.path))
        elif descriptor.source_type == "github_manifest":
            records.extend(extract_github_manifest(descriptor.path))
    return records
