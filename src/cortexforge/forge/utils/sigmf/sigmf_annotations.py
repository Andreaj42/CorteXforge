from cortexforge.forge.utils.node_layout import distance
from cortexforge.forge.utils.node_identity import get_node_name


def make_sigmf_annotations(annotations):
    return sorted(annotations, key=lambda a: a["core:sample_start"])


def timeline_to_sigmf_annotations(
    events, rx_sample_rate, rx_uhd_t0, tx_center_freq, tx_gain
):
    ann = []
    for ev in events:
        start = int((ev["t_start_s"] - rx_uhd_t0) * rx_sample_rate)
        count = int(ev["duration_s"] * rx_sample_rate)

        bw = (1.0 + ev["rolloff"]) * ev["symbol_rate"]
        f0 = tx_center_freq
        f_low = f0 - bw / 2.0
        f_high = f0 + bw / 2.0

        ann.append({
            "core:sample_start": start,
            "core:sample_count": count,
            "core:freq_lower_edge": f_low,
            "core:freq_upper_edge": f_high,
            "core:label": ev["modulation"],
            "cortexforge:transmitter": ev["radio"],
            "cortexforge:distance_m": distance(ev["radio"], get_node_name()),
            "cortexforge:tx_gain_db": tx_gain,
            "cortexforge:amplitude": ev["amplitude"],
            "cortexforge:symbol_rate": ev["symbol_rate"],
            "cortexforge:rolloff": ev["rolloff"]
        })

    return make_sigmf_annotations(ann)
