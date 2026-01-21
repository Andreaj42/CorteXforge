import yaml
from pathlib import Path


def load_yaml(path: str | Path) -> dict:
    """Load a YAML file and return its contents as a dictionary."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    with path.open("r") as f:
        return yaml.safe_load(f)


def load_nodes(path: str | Path = "configs/nodes.yaml") -> list[str]:
    """Return a list of node IDs from a YAML file."""
    data = load_yaml(path)
    if "nodes" not in data:
        raise ValueError(f"The file {path} does not contain a 'nodes' key.")
    nodes = [n["id"] for n in data["nodes"] if "id" in n]
    if not nodes:
        raise ValueError(f"No nodes found in {path}.")
    return nodes
