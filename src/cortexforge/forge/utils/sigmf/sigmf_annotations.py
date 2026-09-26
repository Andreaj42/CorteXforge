import math

from cortexforge.forge.utils.compute_baseline import (
    MIN_LINEAR_POWER,
    measure_band_power,
)
from cortexforge.forge.utils.node_identity import get_node_name
from cortexforge.forge.utils.node_layout import distance


def make_sigmf_annotations(annotations):
    return sorted(annotations, key=lambda a: a["core:sample_start"])


def theoretical_bandwidth_hz(ev):
    modulation = ev["modulation"].upper()
    symbol_rate = float(ev["symbol_rate"])
    rolloff = float(ev["roll_off"])

    # Default occupied RF bandwidth.
    bw = (1.0 + rolloff) * symbol_rate

    if modulation in {"AM-SSB", "AM-SSB-WC", "AM-SSB-SC"}:
        return 0.5 * bw
    # Règle de Carson
    if modulation == "FM":
        sample_rate = float(ev["sample_rate_sps"])
        freq_dev_hz = min(symbol_rate * 0.25, sample_rate * 0.20)
        message_bw = 0.5 * bw
        return 2.0 * (freq_dev_hz + message_bw)

    return bw


def timeline_to_sigmf_annotations(
    events,
    rx_sample_rate,
    rx_center_frequency,
    rx_data_path=None,
    baseline_stat=None,
):
    ann = []

    baseline_start = baseline_stat["skip_samples"]
    baseline_count = baseline_stat["win_samples"]

    # Avoid recomputing the same 1-second baseline FFT
    # for every annotation having the same frequency band.
    baseline_cache = {}

    for ev in events:
        start = round(ev["start_time_s"] * rx_sample_rate)

        count = round(ev["duration_s"] * rx_sample_rate)

        modulation = ev["modulation"].upper()

        signal_bandwidth_hz = theoretical_bandwidth_hz(ev)

        f0 = ev["tx_frequency"]

        if modulation in {
            "AM-SSB",
            "AM-SSB-WC",
            "AM-SSB-SC",
        }:
            f_low = f0
            f_high = f0 + signal_bandwidth_hz
        else:
            f_low = f0 - signal_bandwidth_hz / 2.0
            f_high = f0 + signal_bandwidth_hz / 2.0

        annotation = {
            "core:sample_start": start,
            "core:sample_count": count,
            "core:freq_lower_edge": f_low,
            "core:freq_upper_edge": f_high,
            "core:label": ev["modulation"],
            "cortexforge:transmitter": ev["radio"],
            "cortexforge:distance_m": distance(
                ev["radio"],
                get_node_name(),
            ),
            "cortexforge:tx_gain_db": ev["tx_gain"],
            "cortexforge:amplitude": ev["amplitude"],
            "cortexforge:symbol_rate": ev["symbol_rate"],
            "cortexforge:roll_off": ev["roll_off"],
        }

        if rx_data_path is not None and start >= 0 and count > 0:
            try:
                # ---------------------------------
                # Noise in the SAME frequency band
                # ---------------------------------

                band_key = (
                    float(f_low),
                    float(f_high),
                )

                if band_key not in baseline_cache:
                    baseline_cache[band_key] = measure_band_power(
                        rx_data_path,
                        sample_start=baseline_start,
                        sample_count=baseline_count,
                        sample_rate=rx_sample_rate,
                        center_frequency=rx_center_frequency,
                        freq_low=f_low,
                        freq_high=f_high,
                    )

                noise_stats = baseline_cache[band_key]

                # ---------------------------------
                # Signal + noise in SAME band
                # ---------------------------------

                burst_stats = measure_band_power(
                    rx_data_path,
                    sample_start=start,
                    sample_count=count,
                    sample_rate=rx_sample_rate,
                    center_frequency=rx_center_frequency,
                    freq_low=f_low,
                    freq_high=f_high,
                )

                noise_mean_power = noise_stats["mean_power"]

                total_mean_power = burst_stats["mean_power"]

                # ---------------------------------
                # Signal estimate
                # ---------------------------------

                signal_mean_power = total_mean_power - noise_mean_power

                annotation["cortexforge:rx_total_power_dbfs"] = burst_stats[
                    "power_dbfs"
                ]

                annotation["cortexforge:rx_noise_power_dbfs"] = noise_stats[
                    "power_dbfs"
                ]

                annotation["cortexforge:measurement_bandwidth_hz"] = signal_bandwidth_hz

                if signal_mean_power > 0:
                    annotation["cortexforge:rx_signal_power_dbfs"] = 10.0 * math.log10(
                        signal_mean_power / 2.0
                    )

                    annotation["cortexforge:snr_db"] = 10.0 * math.log10(
                        signal_mean_power
                        / max(
                            noise_mean_power,
                            MIN_LINEAR_POWER,
                        )
                    )

                else:
                    annotation["cortexforge:rx_signal_power_dbfs"] = "Non estimable"

                    annotation["cortexforge:snr_db"] = "Non estimable"

            except ValueError:
                pass

        ann.append(annotation)

    return make_sigmf_annotations(ann)
