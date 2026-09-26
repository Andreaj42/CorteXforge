from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

SignalType = Literal["analog", "digital"]
ConstellationShape = Literal["square", "rect", "cross"]


@dataclass(frozen=True, slots=True)
class ModulationSpec:
    signal_type: SignalType
    bits_per_symbol: int | None = None
    constellation_shape: ConstellationShape | None = None


MODULATION_SPECS: dict[str, ModulationSpec] = {
    "OOK": ModulationSpec(signal_type="digital", bits_per_symbol=1),
    "4ASK": ModulationSpec(signal_type="digital", bits_per_symbol=2),
    "8ASK": ModulationSpec(signal_type="digital", bits_per_symbol=3),
    "BPSK": ModulationSpec(signal_type="digital", bits_per_symbol=1),
    "QPSK": ModulationSpec(signal_type="digital", bits_per_symbol=2),
    "8PSK": ModulationSpec(signal_type="digital", bits_per_symbol=3),
    "16PSK": ModulationSpec(signal_type="digital", bits_per_symbol=4),
    "32PSK": ModulationSpec(signal_type="digital", bits_per_symbol=5),
    "OQPSK": ModulationSpec(signal_type="digital", bits_per_symbol=2),
    "16APSK": ModulationSpec(signal_type="digital", bits_per_symbol=4),
    "32APSK": ModulationSpec(signal_type="digital", bits_per_symbol=5),
    "64APSK": ModulationSpec(signal_type="digital", bits_per_symbol=6),
    "128APSK": ModulationSpec(signal_type="digital", bits_per_symbol=7),
    "256APSK": ModulationSpec(signal_type="digital", bits_per_symbol=8),
    "512APSK": ModulationSpec(signal_type="digital", bits_per_symbol=9),
    "1024APSK": ModulationSpec(signal_type="digital", bits_per_symbol=10),
    "16QAM": ModulationSpec(
        signal_type="digital", constellation_shape="square", bits_per_symbol=4
    ),
    "32QAM_RECT": ModulationSpec(
        signal_type="digital", constellation_shape="rect", bits_per_symbol=5
    ),
    "32QAM_CROSS": ModulationSpec(
        signal_type="digital", constellation_shape="cross", bits_per_symbol=5
    ),
    "64QAM": ModulationSpec(
        signal_type="digital", constellation_shape="square", bits_per_symbol=6
    ),
    "128QAM_RECT": ModulationSpec(
        signal_type="digital", constellation_shape="rect", bits_per_symbol=7
    ),
    "128QAM_CROSS": ModulationSpec(
        signal_type="digital", constellation_shape="cross", bits_per_symbol=7
    ),
    "256QAM": ModulationSpec(
        signal_type="digital", constellation_shape="square", bits_per_symbol=8
    ),
    "512QAM_RECT": ModulationSpec(
        signal_type="digital", constellation_shape="rect", bits_per_symbol=9
    ),
    "512QAM_CROSS": ModulationSpec(
        signal_type="digital", constellation_shape="cross", bits_per_symbol=9
    ),
    "1024QAM": ModulationSpec(
        signal_type="digital", constellation_shape="square", bits_per_symbol=10
    ),
    "GMSK": ModulationSpec(signal_type="digital", bits_per_symbol=1),
    "CPFSK": ModulationSpec(signal_type="digital", bits_per_symbol=1),
    "GFSK": ModulationSpec(signal_type="digital", bits_per_symbol=1),
    "AM-SSB-WC": ModulationSpec(signal_type="analog"),
    "AM-SSB-SC": ModulationSpec(signal_type="analog"),
    "AM-DSB-WC": ModulationSpec(signal_type="analog"),
    "AM-DSB-SC": ModulationSpec(signal_type="analog"),
    "FM": ModulationSpec(signal_type="analog"),
}


SUPPORTED_MODULATIONS = tuple(MODULATION_SPECS)
AMBIGUOUS_MODULATIONS: dict[str, tuple[str, ...]] = {
    "32QAM": ("32QAM_RECT", "32QAM_CROSS"),
    "128QAM": ("128QAM_RECT", "128QAM_CROSS"),
    "512QAM": ("512QAM_RECT", "512QAM_CROSS"),
}


def normalize_modulation(modulation: str) -> str:
    normalized = modulation.strip().upper()
    if normalized in AMBIGUOUS_MODULATIONS:
        choices = ", ".join(AMBIGUOUS_MODULATIONS[normalized])

        raise ValueError(
            f"Ambiguous modulation '{normalized}'. Choose explicitly between: {choices}"
        )

    if normalized not in MODULATION_SPECS:
        supported = ", ".join(SUPPORTED_MODULATIONS)

        raise ValueError(
            f"Unsupported modulation '{modulation}'. "
            f"Supported modulations are: {supported}"
        )

    return normalized


def normalize_modulations(modulations: Iterable[str]) -> list[str]:
    return list(
        dict.fromkeys(normalize_modulation(modulation) for modulation in modulations)
    )


def get_modulation_spec(modulation: str) -> ModulationSpec:
    canonical_name = normalize_modulation(modulation)
    return MODULATION_SPECS[canonical_name]
