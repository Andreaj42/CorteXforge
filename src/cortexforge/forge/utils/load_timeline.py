import csv
from typing import Any, Dict, List


def load_timeline(path: str) -> List[Dict[str, Any]]:
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
                "radio": row.get("radio"),
                "t_start_s": float(row["t_start_s"]),
                "duration_s": float(row["duration_s"]),
                "freq_hz": int(row["freq_hz"]),
                "sample_rate_sps": int(row["sample_rate_sps"]),
                "tx_gain_db": float(row["tx_gain_db"]),
                "amplitude": float(row["amplitude"]),
                "modulation": row["modulation"],
                "symbol_rate": float(row["symbol_rate"]),
                "rolloff": float(row["rolloff"])
            }
            events.append(event)

    events.sort(key=lambda e: e["t_start_s"])
    return events
