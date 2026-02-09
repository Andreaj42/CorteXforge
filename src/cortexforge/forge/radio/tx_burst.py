import numpy as np
from gnuradio import blocks, gr, uhd


class TxBurst(gr.top_block):
    """
    GNU Radio top block for transmitting a burst from a USRP device.
    """

    def __init__(
        self, usrp_args: str, freq: float, rate: float, gain: float, iq
    ) -> None:
        super().__init__("Tx Burst")

        iq_np = np.asarray(iq, dtype=np.complex64)
        iq_list = iq_np.tolist()

        self.tx_channel = 0

        self.src = blocks.vector_source_c(iq_list, repeat=False)
        self.sink = uhd.usrp_sink(
            usrp_args,
            uhd.stream_args(cpu_format="fc32", channels=[self.tx_channel]),
        )
        self.sink.set_clock_source("internal", self.tx_channel)
        self.sink.set_samp_rate(rate)
        self.sink.set_center_freq(freq, self.tx_channel)
        self.sink.set_gain(gain, self.tx_channel)
        self.sink.set_antenna("TX/RX", self.tx_channel)

        self.connect(self.src, self.sink)
