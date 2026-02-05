from datetime import datetime, timezone
from json import dumps
from pathlib import Path
import hashlib


def _sha512_hex(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Compute SHA-512 hash of a file and return it as a hex string."""
    h = hashlib.sha512()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()

def write_sigmf(
    base_path: str,
    data_file: str,
    sample_rate: float,
    center_freq: float,
    gain: float,
    stat,
    hardware: str,
    description: str = "CorteXForge capture",
    author: str = "CorteXForge",
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

    # Move the data to .sigmf-data if needed
    if data_src.resolve() != data_path.resolve():
        data_path.parent.mkdir(parents=True, exist_ok=True)
        data_src.replace(data_path)

    meta = {
        "global": {
            "core:author": author,
            "core:description": description,
            "core:recorder": "CorteXForge",
            "core:hw": hardware,
            "core:datatype": "cf32_le",
            "core:sample_rate": float(sample_rate),
            "core:data_file": data_path.name,
            "core:sha512": _sha512_hex(data_path),
        },
        "captures": [
            {
                "core:datetime": datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                "core:frequency": float(center_freq),
                "core:sample_start": 0,
                "cortexforge:gain": gain,
                "cortexforge:baseline": {
                    "sample_start": stat["skip_samples"],
                    "sample_count": stat["win_samples"],
                    "power_dbfs": stat["power_dbfs"]
                }
            }
        ],
        "annotations": [],
    }

    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(dumps(meta, indent=2))
    return str(data_path), str(meta_path)
