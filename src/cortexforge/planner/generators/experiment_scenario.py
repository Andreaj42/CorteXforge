import random
from typing import List

import pandas as pd


class ExperimentScenario:
    """
    Generate a pseudo-random experiment schedule as a CSV.

    The CSV has the following columns:
    id, start_time, duration, modulation, tx_SNR, frequency, bandwidth

    Constraints:
    - Signals start no earlier than warmup_time (default: 2 seconds).
    - Signals must end before or at the total experiment duration.
    - The receiver node and their params are fixed for the whole experiment.
    """

    def __init__(
        self,
        nodes: List[str],
        duration: int,
        rx_frequency: int,
        rx_sample_rate: int,
        warmup_time: float = 2.0,
    ):
        if warmup_time >= duration:
            raise ValueError("warmup_time must be strictly less than total duration.")

        self.nodes = nodes
        self.duration = duration
        self.rx_frequency = rx_frequency
        self.rx_sample_rate = rx_sample_rate

        self.warmup_time = warmup_time
        self.rx_node = nodes[0]
        self.tx_nodes = nodes[1:]
        self.modulations = ["OOK", "BPSK", "QPSK", "8PSK", "16PSK", "32PSK", "16QAM", "32QAM", "64QAM", "128QAM", "256QAM"]
        self.snr_range = (0.0, 30.0)
        self.freq_range = (160, 6.6e6)
        self.tx_frequency = rx_frequency

    def generate_table(self) -> pd.DataFrame:
        """
        Generate a pandas DataFrame with the timeline columns.
        """
        rng = random.Random()

        rows = []
        for _ in range(0, 30):
            signal_node = rng.choice(self.tx_nodes)
            signal_duration = round(rng.uniform(0, 0.050), 6)
            signal_start_time = round(
                rng.uniform(self.warmup_time, self.duration - signal_duration), 6
            )
            signal_modulation = rng.choice(self.modulations)
            signal_snr = int(rng.uniform(*self.snr_range))
            signal_frequency = int(
                rng.uniform(
                    self.rx_frequency - self.rx_sample_rate / 2,
                    self.rx_frequency + self.rx_sample_rate / 2,
                )
            )
            rows.append(
                {
                    "tx_node": signal_node,
                    "start_time": signal_start_time,
                    "duration": signal_duration,
                    "modulation": signal_modulation,
                    "snr": signal_snr,
                    "frequency": signal_frequency,
                }
            )
        df = pd.DataFrame(
            rows,
            columns=[
                "tx_node",
                "start_time",
                "duration",
                "modulation",
                "snr",
                "frequency",
            ],
        )
        return df

    def to_csv(self, output_path: str):
        """
        Generate the table and write it directly to a CSV file.
        """
        df = self.generate_table()
        df.index.name = "id"
        df.to_csv(output_path)
