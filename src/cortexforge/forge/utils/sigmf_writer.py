import json
from datetime import datetime, timezone
from pathlib import Path


def write_sigmf(
    base_path: str,
    data_file: str,
    sample_rate: float,
    center_freq: float,
    datatype: str = "cf32_le",
    description: str = "CorteXForge capture",
    author: str = "CorteXForge",
    gain: float | None = None,
):
    """
    base_path: path without extension, e.g. /.../out/noise_node6
    data_file: existing IQ file path (fc32 raw)
    Creates:
      - base_path.sigmf-data
      - base_path.sigmf-meta
    """
    base = Path(base_path)
    data_src = Path(data_file)

    meta_path = base.with_suffix(".sigmf-meta")
    data_path = base.with_suffix(".sigmf-data")

    # Move (rename) the data to .sigmf-data if needed
    if data_src.resolve() != data_path.resolve():
        data_path.parent.mkdir(parents=True, exist_ok=True)
        data_src.replace(data_path)

    meta = {
        "global": {
            "core:author": author,
            "core:description": description,
            "core:recorder": "CorteXForge",
            "core:datatype": datatype,
            "core:sample_rate": float(sample_rate),
            "core:version": "1.0.0",
        },
        "captures": [
            {
                "core:frequency": float(center_freq),
                "core:sample_start": 0,
                "core:datetime": datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                "cortexforge:rx_gain": float(gain),
            }
        ],
        "annotations": [],
    }

    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True))
    return str(data_path), str(meta_path)
