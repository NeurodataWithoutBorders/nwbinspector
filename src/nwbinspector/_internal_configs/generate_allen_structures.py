"""One-time script to fetch Allen Mouse Brain CCF structure names and generate a bundled JSON file."""

import json
from pathlib import Path
from urllib.request import urlopen


def flatten_structures(structure: dict, acronyms: list, names: list) -> None:
    """Recursively flatten the nested structure tree."""
    acronyms.append(structure["acronym"])
    names.append(structure["name"])
    for child in structure.get("children", []):
        flatten_structures(child, acronyms, names)


def main() -> None:
    url = "http://api.brain-map.org/api/v2/structure_graph_download/1.json"
    print(f"Fetching Allen CCF structure graph from {url}...")
    with urlopen(url) as response:
        data = json.loads(response.read().decode())

    acronyms: list[str] = []
    names: list[str] = []
    root = data["msg"][0]
    flatten_structures(root, acronyms, names)

    output_path = Path(__file__).parent / "allen_ccf_structure_names.json"
    with open(output_path, "w") as f:
        json.dump({"acronyms": acronyms, "names": names}, f)

    print(f"Wrote {len(acronyms)} structures to {output_path}")


if __name__ == "__main__":
    main()
