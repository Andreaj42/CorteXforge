import random
from typing import List

import pandas as pd


class ExperimentScenario:
    """
    Generate a pseudo-random experiment schedule as a CSV.

    Constraints:
    - Signals start no earlier than warmup_time.
    - Signals must end before or at the total experiment duration.
    - The receiver node and its params are fixed for the whole experiment.
    """

    def __init__(
        self,
        nodes: List[str],
        duration: float,
        rx_sample_rate: int,
        warmup_time: float = 2.0,
        amplitude_range: tuple[float, float] = (0.01, 1.0),
    ):
        if len(nodes) < 2:
            raise ValueError("You must provide at least one RX node and one TX node.")

        if warmup_time >= duration:
            raise ValueError("warmup_time must be strictly less than total duration.")

        min_amplitude, max_amplitude = amplitude_range
        if not (0.01 <= min_amplitude <= max_amplitude <= 1.0):
            raise ValueError("amplitude_range must stay within [0.01, 1.0].")

        self.nodes = nodes
        self.duration = duration
        self.rx_sample_rate = rx_sample_rate
        self.warmup_time = warmup_time
        self.amplitude_range = amplitude_range
        self.rx_node = nodes[0]
        self.tx_nodes = nodes[1:]

        self.modulations = [
            "AM-DSB",
            "AM-SSB",
            "FM",
            "OOK",
            "PAM4",
            "4ASK",
            "8ASK",
            "BPSK",
            "QPSK",
            "8PSK",
            "16PSK",
            "32PSK",
            "CPFSK",
            "GFSK",
            "16QAM",
            "32QAM_RECT",
            "32QAM_CROSS",
            "64QAM",
            "128QAM_RECT",
            "128QAM_CROSS",
            "256QAM",
        ]

        self.duration_range_s = (0.002, 0.020)

    @staticmethod
    def _intervals_overlap(
        start_a: float,
        duration_a: float,
        start_b: float,
        duration_b: float,
    ) -> bool:
        end_a = start_a + duration_a
        end_b = start_b + duration_b
        return start_a < end_b and start_b < end_a

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
                )
                for existing_start, existing_duration in scheduled_intervals
            )

            if not has_overlap:
                return candidate_start

        raise RuntimeError(
            "Unable to place a non-overlapping signal. "
            "Try reducing n_signals, reducing signal durations, "
            "or increasing the experiment duration."
        )

    def generate_table(
        self,
        n_signals: int = 100,
        allow_overlap: bool = True,
        seed: int | None = None,
    ) -> pd.DataFrame:
        """
        Generate a pandas DataFrame with the experiment timeline.

        Args:
            n_signals: Number of signals to generate.
            allow_overlap: If False, generated signals will not overlap in time.
            seed: Optional seed for reproducibility.
        """
        rng = random.Random(seed)

        rows = []
        scheduled_intervals = []

        for _ in range(n_signals):
            signal_node = rng.choice(self.tx_nodes)
            signal_duration = round(rng.uniform(*self.duration_range_s), 6)
            signal_modulation = rng.choice(self.modulations)
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
                    "symbol_rate": 3_125_000,
                    "sample_rate_sps": 25_000_000,
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
        n_signals: int = 100,
        allow_overlap: bool = True,
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
