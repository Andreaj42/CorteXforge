import csv
from typing import Any


def load_timeline(path: str) -> list[dict[str, Any]]:
    """
    Load a TX timeline CSV file.

    Returns
    -------
    events : list of dict
        Each dict contains the parsed parameters for one TX event.
    """
    events = []

    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            event = {
                "radio": row["radio"],
                "start_time_s": float(row["start_time"]),
                "duration_s": float(row["duration_s"]),
                "sample_rate_sps": int(row["sample_rate_sps"]),
                "tx_frequency": int(row["tx_frequency"]),
                "tx_gain": float(row["tx_gain"]),
                "amplitude": float(row["amplitude"]),
                "modulation": row["modulation"],
                "symbol_rate": float(row["symbol_rate"]),
                "roll_off": float(row["roll_off"]),
                "waveform_seed": int(row["waveform_seed"]),
            }
            events.append(event)

    events.sort(key=lambda e: e["start_time_s"])
    return events
