import random
from typing import List

import pandas as pd


class ExperimentScenario:
    """
    Generate a pseudo-random experiment schedule as a CSV.

    The CSV has the following columns:
    id, start_time, duration, modulation, tx_SNR, Frequency, bandwidth, Rx_node

    Constraints:
    - Signals start no earlier than warmup_time (default: 20 seconds).
    - Signals must end before or at the total experiment duration.
    - The receiver node is fixed for the whole experiment.
    """

    def __init__(
        self,
        nodes: List[str],
        duration: int,
        warmup_time: float = 20.0,
    ):
        if warmup_time >= duration:
            raise ValueError("warmup_time must be strictly less than total duration.")

        self.nodes = nodes
        self.duration = duration
        self.warmup_time = warmup_time

        self.rx_node = nodes[0]
        self.tx_nodes = nodes[1:]
        self.modulations = ["BPSK", "QPSK", "QAM16"]
        self.snr_range = (0.0, 30.0)
        self.freq_range = (160, 6.6e6)
        self.bandwidth_choices = (1e6, 2e6, 5e6)

    def generate_table(self) -> pd.DataFrame:
        """
        Generate a pandas DataFrame with the required columns.

        Parameters
        ----------

        Returns
        -------
        pd.DataFrame
            DataFrame with columns:
            id, start_time, duration, modulation, tx_SNR, Frequency, bandwidth, Rx_node
        """
        rng = random.Random()
        max_signal_duration = self.duration - self.warmup_time

        rows = []
        for i in range(0, 10):
            signal_node = rng.choice(self.tx_nodes)
            signal_duration = rng.uniform(1, max_signal_duration / 4)
            signal_start_time = rng.uniform(
                self.warmup_time, self.duration - signal_duration
            )
            signal_modulation = rng.choice(self.modulations)
            signal_snr = rng.uniform(*self.snr_range)
            signal_frequency = int(rng.uniform(*self.freq_range))
            signal_bandwidth = rng.choice(self.bandwidth_choices)
            rows.append(
                {
                    "id": i,
                    "tx_node": signal_node,
                    "start_time": signal_start_time,
                    "duration": signal_duration,
                    "modulation": signal_modulation,
                    "tx_snr": signal_snr,
                    "frequency": signal_frequency,
                    "bandwidth": signal_bandwidth,
                    "rx_node": self.rx_node,
                }
            )
        df = pd.DataFrame(
            rows,
            columns=[
                "id",
                "tx_node",
                "start_time",
                "duration",
                "modulation",
                "tx_snr",
                "frequency",
                "bandwidth",
                "rx_node",
            ],
        )
        return df

    def to_csv(self, output_path: str):
        """
        Generate the table and write it directly to a CSV file.
        """
        df = self.generate_table()
        df.to_csv(output_path, index=False)
