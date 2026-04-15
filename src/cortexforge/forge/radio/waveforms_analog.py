import numpy as np

from cortexforge.forge.radio.waveform_numerique import rrc_taps


def _analytic_signal(x: np.ndarray) -> np.ndarray:
    n = len(x)
    X = np.fft.fft(x.astype(np.float32))
    h = np.zeros(n, dtype=np.float32)

    if n % 2 == 0:
        h[0] = 1.0
        h[n // 2] = 1.0
        h[1 : n // 2] = 2.0
    else:
        h[0] = 1.0
        h[1 : (n + 1) // 2] = 2.0

    return np.fft.ifft(X * h).astype(np.complex64)


def _make_message(
    sample_rate: float,
    symbol_rate: float,
    duration_s: float,
    rolloff: float,
    span_symbols: int,
) -> np.ndarray:
    sps = int(round(sample_rate / symbol_rate))
    if sps < 2:
        raise ValueError(
            f"sps too small (sample_rate/symbol_rate={sample_rate / symbol_rate:.2f}). Increase sample_rate or decrease symbol_rate."
        )

    nsamp = int(round(duration_s * sample_rate))
    nsyms = int(np.ceil(nsamp / sps))

    rng = np.random.default_rng()
    msg_syms = rng.uniform(-1.0, 1.0, size=nsyms).astype(np.float32)

    up = np.zeros(nsyms * sps, dtype=np.float32)
    up[::sps] = msg_syms
    taps = rrc_taps(rolloff, sps, span_symbols)
    shaped = np.convolve(up, taps, mode="same")[:nsamp]

    peak = np.max(np.abs(shaped))
    if peak > 0:
        shaped /= peak
    return shaped.astype(np.float32)


def make_analog_burst(
    modulation: str,
    sample_rate: float,
    symbol_rate: float,
    duration_s: float,
    rolloff: float,
    amplitude: float,
    span_symbols: int,
) -> np.ndarray:
    msg = _make_message(
        sample_rate=sample_rate,
        symbol_rate=symbol_rate,
        duration_s=duration_s,
        rolloff=rolloff,
        span_symbols=span_symbols,
    )

    if modulation == "AM-DSB":
        carrier_leak = 0.5
        burst = (carrier_leak + 0.5 * msg).astype(np.complex64)
    elif modulation == "AM-SSB":
        burst = _analytic_signal(msg)
        peak = np.max(np.abs(burst))
        if peak > 0:
            burst /= peak
    elif modulation == "FM":
        freq_dev_hz = min(symbol_rate * 0.25, sample_rate * 0.20)
        phase = 2 * np.pi * freq_dev_hz * np.cumsum(msg, dtype=np.float64) / sample_rate
        burst = np.exp(1j * phase).astype(np.complex64)
    else:
        raise ValueError(f"Unsupported analog modulation: {modulation}")

    burst *= float(amplitude)
    return burst.astype(np.complex64)
