from gnuradio import blocks, gr, uhd


class RxRecorder(gr.top_block):
    """
    GNU Radio top block for recording from a USRP device.
    """

    def __init__(
        self, usrp_args: str, freq: float, rate: float, gain: float, out_path: str
    ) -> None:
        super().__init__("Rx Recorder")

        self.src = uhd.usrp_source(
            usrp_args,
            uhd.stream_args(cpu_format="sc16", channels=[0]),
        )
        self.src.set_clock_source("internal", 0)
        self.src.set_samp_rate(rate)
        self.src.set_center_freq(freq, 0)
        self.src.set_rx_agc(False)
        self.src.set_gain(gain, 0)
        self.src.set_antenna("TX/RX", 0)
        self.sink = blocks.file_sink(gr.sizeof_short * 2, out_path, False)
        self.sink.set_unbuffered(False)
        self.connect(self.src, self.sink)
