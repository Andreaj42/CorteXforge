import numpy as np
import math


MIN_LINEAR_POWER = np.finfo(np.float32).tiny


def _dbfs_from_mean_power(mean_power):
    return 10.0 * math.log10(max(float(mean_power), MIN_LINEAR_POWER) / 2.0)


def measure_window_power(path, sample_start, sample_count):
    """
    Measure the average power of a complex float32 IQ window.

    Returns a dictionary describing the effective measured window.
    """
    if sample_count <= 0:
        raise ValueError("sample_count must be strictly positive")

    offset_bytes = int(sample_start) * 2 * np.dtype(np.float32).itemsize
    count_iq = int(sample_count) * 2

    x = np.fromfile(path, dtype=np.float32, count=count_iq, offset=offset_bytes)
    if x.size < 2:
        raise ValueError("window contains no IQ samples")

    i = x[0::2]
    q = x[1::2]
    effective_samples = min(i.size, q.size)
    if effective_samples == 0:
        raise ValueError("window contains incomplete IQ samples")

    mean_power = float(
        np.mean(
            i[:effective_samples] * i[:effective_samples]
            + q[:effective_samples] * q[:effective_samples]
        )
    )

    return {
        "sample_start": int(sample_start),
        "sample_count": int(effective_samples),
        "mean_power": mean_power,
        "power_dbfs": _dbfs_from_mean_power(mean_power),
    }


def compute_baseline(path, sample_rate, skip=0.5, win_size=1.0):
    """
    Compute the baseline (noise mean) of the given data between skip and skip + win_size in seconds.

    Parameters:
    path: The input data for which to compute the baseline.
    sample_rate: The sample rate of the data in samples per second.

    Returns:
    float: The computed baseline value.
    """
    skip_samples = int(skip * sample_rate)
    win_samples = int(win_size * sample_rate)
    stats = measure_window_power(
        path, sample_start=skip_samples, sample_count=win_samples
    )

    return {
        "skip_samples": skip_samples,
        "win_samples": stats["sample_count"],
        "mean_power": stats["mean_power"],
        "power_dbfs": stats["power_dbfs"],
    }
