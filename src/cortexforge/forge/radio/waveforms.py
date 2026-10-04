from cortexforge.forge.radio.waveforms_analog import make_analog_burst
from cortexforge.forge.radio.waveforms_digital import make_digital_burst
from cortexforge.modulations import get_modulation_spec, normalize_modulation


def make_burst(
    modulation: str,
    sample_rate: float,
    symbol_rate: float,
    duration_s: float,
    rolloff: float,
    amplitude: float,
    span_symbols: int = 11,
    seed: int | None = None,
):
    modulation = normalize_modulation(modulation)
    spec = get_modulation_spec(modulation)
    if spec.signal_type == "analog":
        return make_analog_burst(
            modulation=modulation,
            sample_rate=sample_rate,
            symbol_rate=symbol_rate,
            duration_s=duration_s,
            rolloff=rolloff,
            amplitude=amplitude,
            span_symbols=span_symbols,
            seed=seed,
        )

    return make_digital_burst(
        modulation=modulation,
        sample_rate=sample_rate,
        symbol_rate=symbol_rate,
        duration_s=duration_s,
        rolloff=rolloff,
        amplitude=amplitude,
        span_symbols=span_symbols,
        seed=seed,
    )
