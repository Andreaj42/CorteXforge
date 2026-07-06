from datetime import datetime, timezone

from cortexforge.forge.utils.node_identity import get_node_name


def make_sigmf_captures(center_freq: float, gain: float, hardware: str, stat):
    return [
        {
            "core:datetime": datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            "core:frequency": float(center_freq),
            "core:sample_start": 0,
            "core:hw": hardware,
            "cortexforge:node": get_node_name(),
            "cortexforge:gain": gain,
            "cortexforge:baseline": {
                "sample_start": stat["skip_samples"],
                "sample_count": stat["win_samples"],
                "power_dbfs": stat["power_dbfs"],
            },
        }
    ]
