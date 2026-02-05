import numpy as np
import math

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

    # 2 float32 per complex sample (I,Q)
    offset_bytes = skip_samples * 2 * np.dtype(np.float32).itemsize
    count_iq = win_samples * 2

    x = np.fromfile(path, dtype=np.float32, count=count_iq, offset=offset_bytes)
    i = x[0::2]
    q = x[1::2]
    mean_power = float(np.mean(i*i + q*q))
    power_dbfs = 10.0 * math.log10(mean_power / 2.0)

    return {
        "skip_samples": float(skip_samples),
        "win_samples": float(win_samples),
        "power_dbfs": float(power_dbfs)
    }
