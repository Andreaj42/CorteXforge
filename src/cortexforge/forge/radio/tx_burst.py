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

        self.src = blocks.vector_source_c(iq_list, repeat=False)
        self.sink = uhd.usrp_sink(
            usrp_args,
            uhd.stream_args(cpu_format="fc32", channels=[0]),
        )
        self.sink.set_clock_source("internal", 0)
        self.sink.set_samp_rate(rate)
        self.sink.set_center_freq(freq, 0)
        self.sink.set_gain(gain, 0)
        self.sink.set_antenna("TX/RX", 0)

        self.connect(self.src, self.sink)
