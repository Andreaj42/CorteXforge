from __future__ import annotations

import math
import re

GRID_SPACING_M = 1.8

_NODE_GRID = {
    1: (0, 0), 3: (1, 0), 5: (2, 0), 7: (3, 0), 9: (4, 0),
    11: (5, 0), 13: (6, 0), 15: (7, 0), 17: (8, 0), 19: (9, 0),

    2: (0, 1), 4: (1, 1), 6: (2, 1), 8: (3, 1), 10: (4, 1),
    12: (5, 1), 14: (6, 1), 16: (7, 1), 18: (8, 1), 20: (9, 1),

    21: (0, 2), 23: (1, 2), 25: (2, 2), 27: (3, 2), 29: (4, 2),
    31: (5, 2), 33: (6, 2), 35: (7, 2), 37: (8, 2), 39: (9, 2),

    22: (0, 3), 24: (1, 3), 26: (2, 3), 28: (3, 3), 30: (4, 3),
    32: (5, 3), 34: (6, 3), 36: (7, 3), 38: (8, 3), 40: (9, 3),
}

NODE_COORDS_M = {
    node_id: (col * GRID_SPACING_M, row * GRID_SPACING_M)
    for node_id, (col, row) in _NODE_GRID.items()
}


def parse_node_id(node_name: str) -> int:
    match = re.search(r"(\d+)$", node_name)
    if not match:
        raise ValueError(f"Cannot extract node id from '{node_name}'")
    return int(match.group(1))


def get_node_coords_m(node_name: str) -> tuple[float, float]:
    node_id = parse_node_id(node_name)
    if node_id not in NODE_COORDS_M:
        raise KeyError(f"Unknown node id: {node_id}")
    return NODE_COORDS_M[node_id]


def distance(tx_node: str, rx_node: str) -> float:
    tx_x, tx_y = get_node_coords_m(tx_node)
    rx_x, rx_y = get_node_coords_m(rx_node)
    return round(math.hypot(tx_x - rx_x, tx_y - rx_y), 3)