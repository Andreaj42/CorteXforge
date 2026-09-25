import math

import numpy as np

MIN_LINEAR_POWER = np.finfo(np.float32).tiny
SC16_DTYPE = np.dtype("<i2")
SC16_SCALE = 32768.0
SC16_BYTES_PER_SAMPLE = 4


def _sc16_to_complex64(raw):
    """
    Convert interleaved sc16 IQ samples to normalized complex64.
    """
    if raw.size % 2 != 0:
        raw = raw[:-1]

    i = raw[0::2].astype(np.float32)
    q = raw[1::2].astype(np.float32)

    return (i / SC16_SCALE + 1j * (q / SC16_SCALE)).astype(np.complex64)


def _dbfs_from_mean_power(mean_power):
    return 10.0 * math.log10(max(float(mean_power), MIN_LINEAR_POWER) / 2.0)


def scale_noise_power_to_band(
    full_band_noise_power,
    sample_rate,
    target_bandwidth_hz,
):
    """
    Scale a full-band noise power to a target bandwidth.
    For white noise:
        P_noise(B) = N0 * B
    """
    return full_band_noise_power * target_bandwidth_hz / sample_rate


def measure_window_power(path, sample_start, sample_count):
    """
    Measure the average power of an interleaved complex int16 IQ window.

    Returns a dictionary describing the effective measured window.
    """
    offset_bytes = int(sample_start) * SC16_BYTES_PER_SAMPLE
    count_iq = int(sample_count) * 2

    x = np.fromfile(path, dtype=SC16_DTYPE, count=count_iq, offset=offset_bytes)
    z = _sc16_to_complex64(x)

    effective_samples = z.size

    mean_power = float(np.mean(z.real * z.real + z.imag * z.imag))

    return {
        "sample_start": int(sample_start),
        "sample_count": int(effective_samples),
        "mean_power": mean_power,
        "power_dbfs": _dbfs_from_mean_power(mean_power),
    }


def measure_band_power(
    path,
    sample_start,
    sample_count,
    sample_rate,
    center_frequency,
    freq_low,
    freq_high,
    fft_size=16384,
):
    """
    Measure average IQ power contained between freq_low and freq_high.

    center_frequency:
        RX tuning frequency in Hz.

    freq_low / freq_high:
        Absolute RF frequencies in Hz.
    """

    # Convert absolute RF frequencies to complex-baseband frequencies.
    low_bb = float(freq_low) - float(center_frequency)
    high_bb = float(freq_high) - float(center_frequency)

    nyquist = float(sample_rate) / 2.0

    if low_bb < -nyquist or high_bb > nyquist:
        raise ValueError("requested frequency band lies outside RX bandwidth")

    if high_bb <= low_bb:
        raise ValueError("invalid frequency band")

    # Frequencies represented by the complex FFT.
    frequencies = np.fft.fftfreq(
        fft_size,
        d=1.0 / float(sample_rate),
    )

    band_mask = (frequencies >= low_bb) & (frequencies < high_bb)

    if not np.any(band_mask):
        raise ValueError("requested band contains no FFT bins")

    n_blocks = int(sample_count) // fft_size

    if n_blocks == 0:
        raise ValueError("window is shorter than fft_size")

    offset_bytes = int(sample_start) * SC16_BYTES_PER_SAMPLE

    band_powers = []

    with open(path, "rb") as f:
        f.seek(offset_bytes)

        for _ in range(n_blocks):
            raw = np.fromfile(
                f,
                dtype=SC16_DTYPE,
                count=2 * fft_size,
            )

            if raw.size < 2 * fft_size:
                break

            z = _sc16_to_complex64(raw)

            spectrum = np.fft.fft(z)

            # Parseval:
            #
            # mean(|x|²)
            #     = sum(|FFT(x)|²) / N²
            #
            # Keeping only selected bins gives the power
            # contained in that frequency interval.
            band_power = float(np.sum(np.abs(spectrum[band_mask]) ** 2) / (fft_size**2))

            band_powers.append(band_power)

    if not band_powers:
        raise ValueError("unable to read complete FFT blocks")

    mean_power = float(np.mean(band_powers))

    return {
        "sample_start": int(sample_start),
        "sample_count": len(band_powers) * fft_size,
        "freq_low": float(freq_low),
        "freq_high": float(freq_high),
        "bandwidth_hz": float(freq_high - freq_low),
        "mean_power": mean_power,
        "power_dbfs": _dbfs_from_mean_power(mean_power),
    }


def check_parseval(
    path,
    sample_start,
    sample_count,
    sample_rate,
    center_frequency,
):
    """
    Check that full-band power measured in time domain and
    frequency domain are equivalent.
    """

    time_stats = measure_window_power(
        path=path,
        sample_start=sample_start,
        sample_count=sample_count,
    )

    fft_stats = measure_band_power(
        path=path,
        sample_start=sample_start,
        sample_count=sample_count,
        sample_rate=sample_rate,
        center_frequency=center_frequency,
        freq_low=center_frequency - sample_rate / 2,
        freq_high=center_frequency + sample_rate / 2,
    )

    difference_db = fft_stats["power_dbfs"] - time_stats["power_dbfs"]

    print("=" * 60)
    print("PARSEVAL SANITY CHECK")
    print("=" * 60)
    print(f"Time-domain power : {time_stats['power_dbfs']:.6f} dBFS")
    print(f"FFT full-band     : {fft_stats['power_dbfs']:.6f} dBFS")
    print(f"Difference        : {difference_db:+.6f} dB")
    print("=" * 60)

    return difference_db


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
    noise_psd = stats["mean_power"] / float(sample_rate)

    return {
        "skip_samples": skip_samples,
        "win_samples": stats["sample_count"],
        "mean_power": stats["mean_power"],
        "power_dbfs": stats["power_dbfs"],
        "bandwidth_hz": float(sample_rate),
        "noise_psd": noise_psd,
    }
