import numpy as np

def rrc_taps(beta: float, sps: int, span: int) -> np.ndarray:
    """
    Root Raised Cosine taps.
    span: in symbols (total taps = span*sps + 1)
    """
    N = span * sps
    t = np.arange(-N/2, N/2 + 1) / sps
    taps = np.zeros_like(t, dtype=np.float64)

    for i, ti in enumerate(t):
        if abs(ti) < 1e-12:
            taps[i] = 1.0 - beta + (4*beta/np.pi)
        elif beta > 0 and abs(abs(4*beta*ti) - 1.0) < 1e-12:
            # t = +- 1/(4beta)
            taps[i] = (beta/np.sqrt(2)) * (
                (1 + 2/np.pi) * np.sin(np.pi/(4*beta)) +
                (1 - 2/np.pi) * np.cos(np.pi/(4*beta))
            )
        else:
            num = np.sin(np.pi*ti*(1-beta)) + 4*beta*ti*np.cos(np.pi*ti*(1+beta))
            den = np.pi*ti*(1-(4*beta*ti)**2)
            taps[i] = num / den

    taps /= np.sqrt(np.sum(taps**2) + 1e-12)  # normalize energy
    return taps.astype(np.float32)

def bits(rng, nbits: int) -> np.ndarray:
    return rng.integers(0, 2, size=nbits, dtype=np.int8)

def map_symbols(mod: str, b: np.ndarray) -> np.ndarray:
    if mod == "BPSK":
        x = 2*b.astype(np.float32) - 1.0
        return x.astype(np.complex64)
    if mod == "QPSK":
        b = b.reshape(-1, 2)
        i = 2*b[:,0].astype(np.float32) - 1.0
        q = 2*b[:,1].astype(np.float32) - 1.0
        return ((i + 1j*q) / np.sqrt(2)).astype(np.complex64)
    if mod == "8PSK":
        b = b.reshape(-1, 3)
        idx = (b[:,0]<<2) | (b[:,1]<<1) | b[:,2]
        phase = 2*np.pi*idx/8.0
        return np.exp(1j*phase).astype(np.complex64)
    if mod == "16QAM":
        b = b.reshape(-1, 4)
        def lvl(bb0, bb1):
            v = (bb0<<1) | bb1
            return np.array([-3,-1,3,1], dtype=np.float32)[v]
        i = lvl(b[:,0], b[:,1])
        q = lvl(b[:,2], b[:,3])
        x = (i + 1j*q) / np.sqrt(10)  # normalize average power
        return x.astype(np.complex64)
    raise ValueError(f"Unsupported modulation: {mod}")

def make_burst(modulation: str, sample_rate: float, symbol_rate: float,
               duration_s: float, rolloff: float,
               amplitude: float, span_symbols: int = 11) -> np.ndarray:
    sps = int(round(sample_rate / symbol_rate))
    if sps < 2:
        raise ValueError(f"sps too small (sample_rate/symbol_rate={sample_rate/symbol_rate:.2f}). Increase sample_rate or decrease symbol_rate.")

    nsamp = int(round(duration_s * sample_rate))
    nsyms = int(np.ceil(nsamp / sps))

    rng = np.random.default_rng()
    bps = {"BPSK":1, "QPSK":2, "8PSK":3, "16QAM":4}[modulation.upper()]
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
