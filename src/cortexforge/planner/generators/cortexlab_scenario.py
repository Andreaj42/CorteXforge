import logging
from pathlib import Path

from yaml import safe_dump

logger = logging.getLogger(__name__)


def generate_cortexlab_scenario(
    rx_nodes: list[str],
    tx_nodes: list[str],
    sync_node: str,
    duration: int,
    image: str,
    rx_command: str,
    tx_command: str,
    sync_command: str,
    output_path: str = "scenario.yaml",
):
    data = {
        "description": "CorteXforge",
        "duration": duration,
        "nodes": {},
    }

    # Receiver nodes
    for node in rx_nodes:
        data["nodes"][node.replace("mnode", "node")] = {
            "container": [
                {
                    "image": image,
                    "command": rx_command,
                }
            ]
        }

    # Transmitter nodes
    for node in tx_nodes:
        data["nodes"][node.replace("mnode", "node")] = {
            "container": [
                {
                    "image": image,
                    "command": tx_command,
                }
            ]
        }

    # Synchronization node
    data["nodes"][sync_node.replace("mnode", "node")] = {
        "container": [
            {
                "image": image,
                "command": sync_command,
            }
        ]
    }

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w") as f:
        safe_dump(data, f, sort_keys=False)

    logger.info(f"Cortexlab scenario written to {out_path}")
