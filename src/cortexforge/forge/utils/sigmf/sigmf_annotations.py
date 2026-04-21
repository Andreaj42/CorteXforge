import math

from cortexforge.forge.utils.node_layout import distance
from cortexforge.forge.utils.node_identity import get_node_name
from cortexforge.forge.utils.compute_baseline import MIN_LINEAR_POWER, measure_window_power


def make_sigmf_annotations(annotations):
    return sorted(annotations, key=lambda a: a["core:sample_start"])


def theoretical_bandwidth_hz(ev):
    modulation = ev["modulation"].upper()
    symbol_rate = float(ev["symbol_rate"])
    rolloff = float(ev["rolloff"])

    # Default occupied RF bandwidth.
    bw = (1.0 + rolloff) * symbol_rate

    if modulation == "AM-SSB":
        return 0.5 * bw
    # Règle de Carson
    if modulation == "FM":
        sample_rate = float(ev["sample_rate_sps"])
        freq_dev_hz = min(symbol_rate * 0.25, sample_rate * 0.20)
        message_bw = 0.5 * bw
        return 2.0 * (freq_dev_hz + message_bw)

    return bw


def timeline_to_sigmf_annotations(
    events, rx_sample_rate, rx_uhd_t0, tx_center_freq, tx_gain, rx_data_path=None, baseline_stat=None
):
    ann = []
    baseline_mean_power = None
    if baseline_stat is not None:
        baseline_mean_power = float(baseline_stat.get("mean_power", 0.0))

    for ev in events:
        start = int((ev["t_start_s"] - rx_uhd_t0) * rx_sample_rate)
        count = int(ev["duration_s"] * rx_sample_rate)

        modulation = ev["modulation"].upper()
        bw = theoretical_bandwidth_hz(ev)
        f0 = tx_center_freq

        if modulation == "AM-SSB":
            f_low = f0
            f_high = f0 + bw
        else:
            f_low = f0 - bw / 2.0
            f_high = f0 + bw / 2.0

        annotation = {
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
            "cortexforge:rolloff": ev["rolloff"],
        }

        if rx_data_path is not None and baseline_mean_power is not None and start >= 0 and count > 0:
            try:
                burst_stats = measure_window_power(
                    rx_data_path,
                    sample_start=start,
                    sample_count=count,
                )
                total_mean_power = burst_stats["mean_power"]
                signal_mean_power = max(total_mean_power - baseline_mean_power, MIN_LINEAR_POWER)
                annotation["cortexforge:rx_total_power_dbfs"] = burst_stats["power_dbfs"]
                annotation["cortexforge:rx_signal_power_dbfs"] = (
                    10.0 * math.log10(signal_mean_power / 2.0)
                )
                annotation["cortexforge:snr_db"] = 10.0 * math.log10(
                    signal_mean_power / max(baseline_mean_power, MIN_LINEAR_POWER)
                )
            except ValueError:
                pass

        ann.append(annotation)

    return make_sigmf_annotations(ann)
