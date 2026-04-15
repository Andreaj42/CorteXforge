from cortexforge.forge.radio.waveforms_analog import make_analog_burst
from cortexforge.forge.radio.waveforms_numerique import make_digital_burst

MODULATION_ALIASES = {
    "32QAM": "32QAM_RECT",
    "128QAM": "128QAM_RECT",
    "4PAM": "PAM4",
}

ANALOG_MODULATIONS = {"AM-DSB", "AM-SSB", "FM"}


def make_burst(
    modulation: str,
    sample_rate: float,
    symbol_rate: float,
    duration_s: float,
    rolloff: float,
    amplitude: float,
    span_symbols: int = 11,
):
    modulation = MODULATION_ALIASES.get(modulation.upper(), modulation.upper())
    if modulation in ANALOG_MODULATIONS:
        return make_analog_burst(
            modulation=modulation,
            sample_rate=sample_rate,
            symbol_rate=symbol_rate,
            duration_s=duration_s,
            rolloff=rolloff,
            amplitude=amplitude,
            span_symbols=span_symbols,
        )

    return make_digital_burst(
        modulation=modulation,
        sample_rate=sample_rate,
        symbol_rate=symbol_rate,
        duration_s=duration_s,
        rolloff=rolloff,
        amplitude=amplitude,
        span_symbols=span_symbols,
    )
