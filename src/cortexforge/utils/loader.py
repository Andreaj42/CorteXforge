import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


def load_yaml(path: Path) -> dict:
    """Load a YAML file and return its contents as a dictionary."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    with path.open("r") as f:
        return yaml.safe_load(f)


def load_nodes(path: Path = "configs/nodes.yaml") -> list[str]:
    """
    Load node IDs from a YAML configuration configs/nodes.yaml file.

    Expected YAML format:
    nodes:
      - id: mnode1
      - id: mnode2
      ...
    """
    data = load_yaml(path)

    nodes = [node["id"] for node in data["nodes"]]

    if len(nodes) < 2:
        raise ValueError("At least two nodes are required")

    logger.info("Loaded %d nodes: %s", len(nodes), nodes)
    return nodes
