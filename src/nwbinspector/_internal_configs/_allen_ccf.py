"""Loader for Allen Mouse Brain CCF ontology terms."""

import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def get_allen_ccf_location_terms() -> frozenset:
    """Return a frozenset of all valid Allen CCF location strings (acronyms + names combined)."""
    data_path = Path(__file__).parent / "allen_ccf_structure_names.json"
    with open(data_path) as f:
        data = json.load(f)
    return frozenset(data["acronyms"] + data["names"])
