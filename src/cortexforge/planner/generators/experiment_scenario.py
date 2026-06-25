import random
from typing import List

import pandas as pd

from cortexforge.planner.modulations import DEFAULT_MODULATIONS


class ExperimentScenario:
    """
    Generate a pseudo-random experiment schedule as a CSV.

    Constraints:
    - Signals start no earlier than warmup_time.
    - Signals must end before or at the total experiment duration.
    - Non-overlapping signals are separated by min_burst_gap_s.
    - Modulations are evenly distributed across generated signals.
    - The receiver node and its params are fixed for the whole experiment.
    """

    def __init__(
        self,
        nodes: List[str],
        duration: float,
        rx_sample_rate: int,
        warmup_time: float = 2.0,
        amplitude_range: tuple[float, float] = (0.05, 0.2),
        modulations: List[str] | None = None,
        min_burst_gap_s: float = 0.010,
    ):
        if len(nodes) < 2:
            raise ValueError("You must provide at least one RX node and one TX node.")

        if warmup_time >= duration:
            raise ValueError("warmup_time must be strictly less than total duration.")

        min_amplitude, max_amplitude = amplitude_range
        if not (0.01 <= min_amplitude <= max_amplitude <= 1.0):
            raise ValueError("amplitude_range must stay within [0.01, 1.0].")

        if min_burst_gap_s < 0:
            raise ValueError("min_burst_gap_s must be greater than or equal to 0.")

        self.nodes = nodes
        self.duration = duration
        self.rx_sample_rate = rx_sample_rate
        self.warmup_time = warmup_time
        self.amplitude_range = amplitude_range
        self.min_burst_gap_s = min_burst_gap_s
        self.rx_node = nodes[0]
        self.tx_nodes = nodes[1:]

        selected_modulations = (
            DEFAULT_MODULATIONS if modulations is None else modulations
        )
        self.modulations = self._validate_modulations(selected_modulations)

        self.duration_range_s = (0.02, 0.10)

    @staticmethod
    def _validate_modulations(modulations: List[str]) -> List[str]:
        if not modulations:
            raise ValueError("At least one modulation must be provided.")

        normalized = list(
            dict.fromkeys(modulation.upper() for modulation in modulations)
        )
        unknown = sorted(set(normalized) - set(DEFAULT_MODULATIONS))
        if unknown:
            supported = ", ".join(DEFAULT_MODULATIONS)
            raise ValueError(
                f"Unsupported planner modulation(s): {', '.join(unknown)}. "
                f"Supported modulations are: {supported}"
            )

        return normalized

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
        scheduled_intervals: List[tuple],
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

    def _balanced_modulation_sequence(
        self,
        n_signals: int,
        rng: random.Random,
    ) -> list[str]:
        if n_signals <= 0:
            raise ValueError("n_signals must be strictly positive.")

        n_modulations = len(self.modulations)
        if n_signals % n_modulations != 0:
            raise ValueError(
                "n_signals must be a multiple of the number of selected "
                f"modulations ({n_modulations}) to keep a balanced distribution."
            )

        repetitions = n_signals // n_modulations
        signal_modulations = self.modulations * repetitions
        rng.shuffle(signal_modulations)
        return signal_modulations

    def generate_table(
        self,
        n_signals: int = 288,
        allow_overlap: bool = False,
        seed: int | None = None,
    ) -> pd.DataFrame:
        """
        Generate a pandas DataFrame with the experiment timeline.

        Args:
            n_signals: Number of signals to generate. Must be a multiple of the
                selected modulation count.
            allow_overlap: If False, generated signals will not overlap and will
                keep at least min_burst_gap_s between bursts.
            seed: Optional seed for reproducibility.
        """
        rng = random.Random(seed)

        signal_modulations = self._balanced_modulation_sequence(n_signals, rng)

        rows = []
        scheduled_intervals = []

        for signal_modulation in signal_modulations:
            signal_node = rng.choice(self.tx_nodes)
            signal_duration = round(rng.uniform(*self.duration_range_s), 6)
            signal_amplitude = round(rng.uniform(*self.amplitude_range), 2)

            if allow_overlap:
                signal_start_time = round(
                    rng.uniform(self.warmup_time, self.duration - signal_duration), 6
                )
            else:
                signal_start_time = self._find_non_overlapping_start(
                    signal_duration=signal_duration,
                    scheduled_intervals=scheduled_intervals,
                    rng=rng,
                )
                scheduled_intervals.append((signal_start_time, signal_duration))

            rows.append(
                {
                    "radio": signal_node,
                    "start_time": signal_start_time,
                    "duration_s": signal_duration,
                    "modulation": signal_modulation,
                    "amplitude": signal_amplitude,
                    "roll_off": 0.35,
                    "symbol_rate": 2_500_000,
                    "sample_rate_sps": 10_000_000,
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
                "roll_off",
                "symbol_rate",
                "sample_rate_sps",
            ],
        )

        df = df.sort_values("start_time").reset_index(drop=True)
        return df

    def to_csv(
        self,
        output_path: str,
        n_signals: int = 288,
        allow_overlap: bool = False,
        seed: int | None = None,
    ):
        """
        Generate the table and write it directly to a CSV file.
        """
        df = self.generate_table(
            n_signals=n_signals,
            allow_overlap=allow_overlap,
            seed=seed,
        )
        df.index.name = "id"
        df.to_csv(output_path)
