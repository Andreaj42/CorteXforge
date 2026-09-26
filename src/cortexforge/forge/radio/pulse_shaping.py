import numpy as np


def rrc_taps(beta: float, sps: int, span: int) -> np.ndarray:
    """
    Generate Root Raised Cosine filter taps.

    Args:
        beta: Roll-off factor.
        sps: Samples per symbol.
        span: Filter span in symbols.

    Returns:
        Unit-energy RRC filter taps.
    """
    n = span * sps
    t = np.arange(-n / 2, n / 2 + 1) / sps
    taps = np.zeros_like(t, dtype=np.float64)

    for i, ti in enumerate(t):
        if abs(ti) < 1e-12:
            taps[i] = 1.0 - beta + (4 * beta / np.pi)

        elif beta > 0 and abs(abs(4 * beta * ti) - 1.0) < 1e-12:
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

    taps /= np.sqrt(np.sum(taps**2) + 1e-12)

    return taps.astype(np.float32)
