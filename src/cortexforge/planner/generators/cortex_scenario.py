import logging
from pathlib import Path
from typing import List

from yaml import safe_dump

logger = logging.getLogger(__name__)


def generate_cortex_scenario(
    nodes: List[str],
    duration: int,
    image: str,
    command: str,
    description: str = "Dataset Generator",
    output_path: str = "scenario.yaml",
):
    data = {"description": description, "duration": duration, "nodes": {}}

    for node in nodes:
        data["nodes"][node.replace("mnode", "node")] = {
            "container": [
                {
                    "image": image,
                    "command": command,
                }
            ]
        }

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        safe_dump(data, f, sort_keys=False)

    logger.info(f"Cortexlab scenario written to {out_path}")
