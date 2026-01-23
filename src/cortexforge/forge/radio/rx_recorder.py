from gnuradio import blocks, gr, uhd


class RxRecorder(gr.top_block):
    """
    GNU Radio top block for recording from a USRP device.
    """
    def __init__(self, usrp_args: str, freq: float, rate: float, gain: float, out_path: str, antenna: str) -> None:
        super().__init__("Rx recorder")

        self.src = uhd.usrp_source(
            usrp_args,
            uhd.stream_args(cpu_format="fc32", channels=[0]),
        )
        self.src.set_clock_source("internal", 0)
        self.src.set_samp_rate(rate)
        self.src.set_center_freq(freq, 0)
        self.src.set_gain(gain, 0)
        self.src.set_antenna(antenna, 0)

        self.sink = blocks.file_sink(gr.sizeof_gr_complex, out_path, False)
        self.sink.set_unbuffered(False)

        self.connect(self.src, self.sink)
