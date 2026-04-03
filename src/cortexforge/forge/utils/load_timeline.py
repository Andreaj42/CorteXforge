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
                "radio": row["radio"],
                "t_start_s": float(row["start_time"]),
                "duration_s": float(row["duration_s"]),
                "sample_rate_sps": int(row["sample_rate_sps"]),
                "amplitude": float(row["amplitude"]),
                "modulation": row["modulation"],
                "symbol_rate": float(row["symbol_rate"]),
                "rolloff": float(row["roll_off"]),
            }
            if row.get("freq_hz") not in (None, ""):
                event["freq_hz"] = int(row["freq_hz"])
            if row.get("tx_gain_db") not in (None, ""):
                event["tx_gain_db"] = float(row["tx_gain_db"])
            events.append(event)

    events.sort(key=lambda e: e["t_start_s"])
    return events
