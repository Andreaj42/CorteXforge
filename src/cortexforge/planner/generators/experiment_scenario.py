import random
from collections.abc import Sequence

import pandas as pd

from cortexforge.modulations import SUPPORTED_MODULATIONS, normalize_modulations
from cortexforge.planner.defaults import (
    DEFAULT_BURST_DURATION_RANGE_S,
    DEFAULT_MIN_BURST_GAP_S,
    DEFAULT_TX_SAMPLE_RATE,
    DEFAULT_WARMUP_TIME_S,
)


class ExperimentScenario:
    """
    Generate a pseudo-random experiment schedule.

    Constraints:
    - Signals start no earlier than warmup_time.
    - Signals must end before or at the total experiment duration.
    - Non-overlapping signals are separated by min_burst_gap_s.
    - Signal parameters are independently sampled from discrete candidate sets.
    - The receiver configuration is fixed for the whole experiment.
    """

    def __init__(
        self,
        tx_nodes: list[str],
        duration: float,
        rx_sample_rate: int,
        amplitudes: Sequence[float],
        symbol_rates: Sequence[float],
        roll_offs: Sequence[float],
        modulations: list[str] | None = None,
        warmup_time: float = DEFAULT_WARMUP_TIME_S,
        tx_sample_rate: int = DEFAULT_TX_SAMPLE_RATE,
        min_burst_gap_s: float = DEFAULT_MIN_BURST_GAP_S,
    ):
        if not tx_nodes:
            raise ValueError("At least one transmitter node must be provided.")

        if len(set(tx_nodes)) != len(tx_nodes):
            raise ValueError("Transmitter nodes must be unique.")

        self.tx_nodes = list(tx_nodes)

        if warmup_time >= duration:
            raise ValueError("warmup_time must be strictly less than total duration.")

        if min_burst_gap_s < 0:
            raise ValueError("min_burst_gap_s must be greater than or equal to 0.")

        self.duration = duration
        self.rx_sample_rate = rx_sample_rate
        self.warmup_time = warmup_time
        self.min_burst_gap_s = min_burst_gap_s

        selected_modulations = (
            SUPPORTED_MODULATIONS if modulations is None else modulations
        )
        self.modulations = self._validate_modulations(selected_modulations)
        self.amplitudes = list(amplitudes)
        self.symbol_rates = list(symbol_rates)
        self.roll_offs = list(roll_offs)

        self.tx_sample_rate = tx_sample_rate

        self.burst_duration_range_s = DEFAULT_BURST_DURATION_RANGE_S

        self._validate_signal_parameters()

    def _validate_signal_parameters(self) -> None:
        if not self.amplitudes:
            raise ValueError("At least one amplitude must be provided.")

        if len(set(self.amplitudes)) != len(self.amplitudes):
            raise ValueError("Amplitude values must be unique.")

        if len(set(self.symbol_rates)) != len(self.symbol_rates):
            raise ValueError("Symbol-rate values must be unique.")

        if len(set(self.roll_offs)) != len(self.roll_offs):
            raise ValueError("Roll-off values must be unique.")

        for amplitude in self.amplitudes:
            if not 0.0 < amplitude <= 1.0:
                raise ValueError(
                    f"Invalid amplitude {amplitude}: values must belong to (0, 1]."
                )

        if not self.symbol_rates:
            raise ValueError("At least one symbol rate must be provided.")

        if not self.roll_offs:
            raise ValueError("At least one roll-off must be provided.")

        for symbol_rate in self.symbol_rates:
            if symbol_rate <= 0:
                raise ValueError("Symbol rates must be strictly positive.")

            sps = self.tx_sample_rate / symbol_rate

            if not sps.is_integer():
                raise ValueError(
                    f"Invalid symbol rate {symbol_rate}: "
                    f"tx_sample_rate / symbol_rate = {sps:.6f}. "
                    "The waveform generator requires an integer SPS."
                )

            if sps < 2:
                raise ValueError(
                    f"Symbol rate {symbol_rate} gives SPS={sps:.0f}, which is too small."
                )

            if "OQPSK" in self.modulations and int(sps) % 2 != 0:
                raise ValueError(
                    f"OQPSK requires an even SPS, but Rs={symbol_rate} gives SPS={sps}."
                )

        for roll_off in self.roll_offs:
            if not 0.0 <= roll_off <= 1.0:
                raise ValueError("Roll-off values must belong to [0, 1].")

        for symbol_rate in self.symbol_rates:
            for roll_off in self.roll_offs:
                nominal_bandwidth = (1.0 + roll_off) * symbol_rate

                if nominal_bandwidth >= self.rx_sample_rate:
                    raise ValueError(
                        f"Rs={symbol_rate} and alpha={roll_off} "
                        f"give B={nominal_bandwidth:.0f} Hz, "
                        f"which does not fit inside "
                        f"RX Fs={self.rx_sample_rate} Hz."
                    )

    def _sample_parameter_sequence(
        self,
        n_signals: int,
        rng: random.Random,
    ) -> list[tuple[str, str, float, float, float, float]]:
        """
        Sample signal configurations independently from discrete parameter sets.

        Returns tuples:
            (
                modulation,
                tx_node,
                amplitude,
                symbol_rate,
                roll_off,
                duration_s,
            )
        """
        if n_signals <= 0:
            raise ValueError("n_signals must be strictly positive.")

        sequence = []

        for _ in range(n_signals):
            sequence.append(
                (
                    rng.choice(self.modulations),
                    rng.choice(self.tx_nodes),
                    rng.choice(self.amplitudes),
                    rng.choice(self.symbol_rates),
                    rng.choice(self.roll_offs),
                    round(rng.uniform(*self.burst_duration_range_s), 6),
                )
            )
        return sequence

    @staticmethod
    def _validate_modulations(modulations: list[str]) -> list[str]:
        if not modulations:
            raise ValueError("At least one modulation must be provided.")

        return normalize_modulations(modulations)

    @staticmethod
    def _intervals_overlap(
        start_a: float,
        duration_a: float,
        start_b: float,
        duration_b: float,
        min_gap_s: float = 0.0,
    ) -> bool:
        end_a = start_a + duration_a
        end_b = start_b + duration_b
        return start_a < end_b + min_gap_s and start_b < end_a + min_gap_s

    def _find_non_overlapping_start(
        self,
        signal_duration: float,
        scheduled_intervals: list[tuple],
        rng: random.Random,
        max_attempts: int = 1000,
    ) -> float:
        latest_start = self.duration - signal_duration
        if latest_start < self.warmup_time:
            raise ValueError(
                "Signal duration is too large for the available experiment window."
            )

        for _ in range(max_attempts):
            candidate_start = round(rng.uniform(self.warmup_time, latest_start), 6)

            has_overlap = any(
                self._intervals_overlap(
                    candidate_start,
                    signal_duration,
                    existing_start,
                    existing_duration,
                    self.min_burst_gap_s,
                )
                for existing_start, existing_duration in scheduled_intervals
            )

            if not has_overlap:
                return candidate_start

        raise RuntimeError(
            "Unable to place a non-overlapping signal. "
            "Try reducing n_signals, reducing signal durations, "
            "reducing min_burst_gap_s, or increasing the experiment duration."
        )

    def generate_table(
        self,
        n_signals: int,
        tx_gain: int = 30,
        tx_frequency: int = 2450000000,
        allow_overlap: bool = False,
        seed: int | None = None,
    ) -> pd.DataFrame:
        """
        Generate a pandas DataFrame with the experiment timeline.

        Args:
            n_signals: Number of signals to generate.
            allow_overlap: If False, generated signals will not overlap and will
                keep at least min_burst_gap_s between bursts.
            seed: Optional seed for reproducibility.
        """
        parameter_rng = random.Random(seed)
        timing_rng = random.Random(None if seed is None else seed + 1)
        waveform_rng = random.Random(None if seed is None else seed + 2)

        signal_parameters = self._sample_parameter_sequence(n_signals, parameter_rng)

        rows = []
        scheduled_intervals = []

        for (
            signal_modulation,
            signal_node,
            signal_amplitude,
            signal_symbol_rate,
            signal_roll_off,
            signal_duration,
        ) in signal_parameters:
            if allow_overlap:
                signal_start_time = round(
                    timing_rng.uniform(
                        self.warmup_time,
                        self.duration - signal_duration,
                    ),
                    6,
                )
            else:
                signal_start_time = self._find_non_overlapping_start(
                    signal_duration=signal_duration,
                    scheduled_intervals=scheduled_intervals,
                    rng=timing_rng,
                )

                scheduled_intervals.append((signal_start_time, signal_duration))

            rows.append(
                {
                    "radio": signal_node,
                    "start_time": signal_start_time,
                    "duration_s": signal_duration,
                    "modulation": signal_modulation,
                    "amplitude": signal_amplitude,
                    "tx_gain": tx_gain,
                    "tx_frequency": tx_frequency,
                    "roll_off": signal_roll_off,
                    "symbol_rate": signal_symbol_rate,
                    "sample_rate_sps": self.tx_sample_rate,
                    "waveform_seed": waveform_rng.getrandbits(32),
                }
            )

        df = pd.DataFrame(
            rows,
            columns=[
                "radio",
                "start_time",
                "duration_s",
                "modulation",
                "amplitude",
                "tx_gain",
                "tx_frequency",
                "roll_off",
                "symbol_rate",
                "sample_rate_sps",
                "waveform_seed",
            ],
        )

        df = df.sort_values("start_time").reset_index(drop=True)
        return df
