import numpy as np

MODULATION_ALIASES = {
    "32QAM": "32QAM_RECT",
    "128QAM": "128QAM_RECT",
}


def rrc_taps(beta: float, sps: int, span: int) -> np.ndarray:
    """
    Root Raised Cosine taps.
    span: in symbols (total taps = span*sps + 1)
    """
    N = span * sps
    t = np.arange(-N / 2, N / 2 + 1) / sps
    taps = np.zeros_like(t, dtype=np.float64)

    for i, ti in enumerate(t):
        if abs(ti) < 1e-12:
            taps[i] = 1.0 - beta + (4 * beta / np.pi)
        elif beta > 0 and abs(abs(4 * beta * ti) - 1.0) < 1e-12:
            # t = +- 1/(4beta)
            taps[i] = (beta / np.sqrt(2)) * (
                (1 + 2 / np.pi) * np.sin(np.pi / (4 * beta))
                + (1 - 2 / np.pi) * np.cos(np.pi / (4 * beta))
            )
        else:
            num = np.sin(np.pi * ti * (1 - beta)) + 4 * beta * ti * np.cos(
                np.pi * ti * (1 + beta)
            )
            den = np.pi * ti * (1 - (4 * beta * ti) ** 2)
            taps[i] = num / den

    taps /= np.sqrt(np.sum(taps**2) + 1e-12)  # normalize energy
    return taps.astype(np.float32)


def bits(rng, nbits: int) -> np.ndarray:
    return rng.integers(0, 2, size=nbits, dtype=np.int8)


def _pam_gray_levels(nbits: int) -> np.ndarray:
    levels = np.arange(-(2**nbits - 1), 2**nbits, 2, dtype=np.float32)
    gray = np.arange(2**nbits, dtype=np.int32) ^ (np.arange(2**nbits, dtype=np.int32) >> 1)
    return levels[gray]


def _bits_to_int(bb: np.ndarray) -> np.ndarray:
    weights = (1 << np.arange(bb.shape[1] - 1, -1, -1)).astype(np.int32)
    return (bb.astype(np.int32) * weights).sum(axis=1)


def _psk_symbols(b: np.ndarray, bits_per_symbol: int) -> np.ndarray:
    idx = _bits_to_int(b.reshape(-1, bits_per_symbol))
    phase = 2 * np.pi * idx / (2**bits_per_symbol)
    return np.exp(1j * phase).astype(np.complex64)


def _qam_symbols(b: np.ndarray, i_bits: int, q_bits: int) -> np.ndarray:
    b = b.reshape(-1, i_bits + q_bits)
    i_levels = _pam_gray_levels(i_bits)
    q_levels = _pam_gray_levels(q_bits)
    i = i_levels[_bits_to_int(b[:, :i_bits])]
    q = q_levels[_bits_to_int(b[:, i_bits:])]
    x = i + 1j * q
    x /= np.sqrt(np.mean(np.abs(x) ** 2))
    return x.astype(np.complex64)


def _cross_qam_constellation(grid_size: int, corner_levels_to_remove: int) -> np.ndarray:
    # Cross-QAM: odd grid of size grid_size x grid_size with square corner blocks removed.
    levels = np.arange(-(grid_size - 1), grid_size, 2, dtype=np.float32)
    corner_threshold = grid_size - 2 * corner_levels_to_remove
    constellation = np.array(
        [
            i + 1j * q
            for q in levels
            for i in levels
            if not (abs(i) >= corner_threshold and abs(q) >= corner_threshold)
        ],
        dtype=np.complex64,
    )
    return constellation


def _cross_qam_symbols(
    b: np.ndarray,
    bits_per_symbol: int,
    grid_size: int,
    corner_levels_to_remove: int,
) -> np.ndarray:
    b = b.reshape(-1, bits_per_symbol)
    constellation = _cross_qam_constellation(grid_size, corner_levels_to_remove)

    idx = _bits_to_int(b)
    x = constellation[idx].astype(np.complex64)
    x /= np.sqrt(np.mean(np.abs(x) ** 2))
    return x.astype(np.complex64)


def _cross_32qam_symbols(b: np.ndarray) -> np.ndarray:
    return _cross_qam_symbols(b, bits_per_symbol=5, grid_size=6, corner_levels_to_remove=1)


def _cross_128qam_symbols(b: np.ndarray) -> np.ndarray:
    return _cross_qam_symbols(b, bits_per_symbol=7, grid_size=12, corner_levels_to_remove=2)


def _ask_symbols(b: np.ndarray, bits_per_symbol: int) -> np.ndarray:
    if bits_per_symbol == 1:
        return b.astype(np.complex64)

    levels = _pam_gray_levels(bits_per_symbol)
    x = levels[_bits_to_int(b.reshape(-1, bits_per_symbol))].astype(np.float32)
    x /= np.sqrt(np.mean(np.abs(x) ** 2))
    return x.astype(np.complex64)


def map_symbols(mod: str, b: np.ndarray) -> np.ndarray:
    mod = MODULATION_ALIASES.get(mod.upper(), mod.upper())

    if mod == "OOK":
        return _ask_symbols(b, 1)
    if mod == "4ASK":
        return _ask_symbols(b, 2)
    if mod == "8ASK":
        return _ask_symbols(b, 3)
    if mod == "BPSK":
        return _psk_symbols(b, 1)
    if mod == "QPSK":
        return _psk_symbols(b, 2)
    if mod == "8PSK":
        return _psk_symbols(b, 3)
    if mod == "16PSK":
        return _psk_symbols(b, 4)
    if mod == "32PSK":
        return _psk_symbols(b, 5)
    if mod == "16QAM":
        return _qam_symbols(b, 2, 2)
    if mod == "32QAM_RECT":
        return _qam_symbols(b, 3, 2)
    if mod == "32QAM_CROSS":
        return _cross_32qam_symbols(b)
    if mod == "64QAM":
        return _qam_symbols(b, 3, 3)
    if mod == "128QAM_RECT":
        return _qam_symbols(b, 4, 3)
    if mod == "128QAM_CROSS":
        return _cross_128qam_symbols(b)
    if mod == "256QAM":
        return _qam_symbols(b, 4, 4)
    raise ValueError(f"Unsupported modulation: {mod}")


def make_burst(
    modulation: str,
    sample_rate: float,
    symbol_rate: float,
    duration_s: float,
    rolloff: float,
    amplitude: float,
    span_symbols: int = 11,
) -> np.ndarray:
    modulation = MODULATION_ALIASES.get(modulation.upper(), modulation.upper())
    sps = int(round(sample_rate / symbol_rate))
    if sps < 2:
        raise ValueError(
            f"sps too small (sample_rate/symbol_rate={sample_rate / symbol_rate:.2f}). Increase sample_rate or decrease symbol_rate."
        )

    nsamp = int(round(duration_s * sample_rate))
    nsyms = int(np.ceil(nsamp / sps))

    rng = np.random.default_rng()
    bps = {
        "OOK": 1,
        "4ASK": 2,
        "8ASK": 3,
        "BPSK": 1,
        "QPSK": 2,
        "8PSK": 3,
        "16PSK": 4,
        "32PSK": 5,
        "16QAM": 4,
        "32QAM_RECT": 5,
        "32QAM_CROSS": 5,
        "64QAM": 6,
        "128QAM_RECT": 7,
        "128QAM_CROSS": 7,
        "256QAM": 8,
    }[modulation]
    b = bits(rng, nsyms * bps)
    syms = map_symbols(modulation, b)

    # upsample + RRC
    up = np.zeros(nsyms * sps, dtype=np.complex64)
    up[::sps] = syms
    taps = rrc_taps(rolloff, sps, span_symbols)
    shaped = np.convolve(up, taps.astype(np.complex64), mode="same")

    burst = shaped[:nsamp]
    burst *= float(amplitude)
    return burst.astype(np.complex64)
