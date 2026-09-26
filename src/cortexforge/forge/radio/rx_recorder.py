from logging import getLogger

import pmt
from gnuradio import blocks, gr, uhd

logger = getLogger(__name__)


class RxRecorder(gr.top_block):
    """
    GNU Radio top block for recording from a USRP device.
    """

    def __init__(
        self, usrp_args: str, freq: float, rate: float, gain: float, out_path: str
    ) -> None:
        super().__init__("Rx Recorder")

        self.rx_channel = 0

        self.src = uhd.usrp_source(
            usrp_args,
            uhd.stream_args(
                cpu_format="sc16", otw_format="sc16", channels=[self.rx_channel]
            ),
        )
        self.src.set_clock_source("external", self.rx_channel)
        self.src.set_time_source("external", self.rx_channel)
        self.src.set_samp_rate(rate)
        self.src.set_center_freq(freq, self.rx_channel)
        self._try_set_rx_agc(False)
        self.src.set_gain(gain, self.rx_channel)
        self.src.set_antenna("TX/RX", self.rx_channel)
        self.sink = blocks.file_sink(gr.sizeof_short * 2, out_path, False)
        self.sink.set_unbuffered(False)
        self.rx_time_tags = blocks.tag_debug(
            gr.sizeof_short * 2,
            "rx_time",
            "rx_time",
        )
        self.rx_time_tags.set_display(False)
        self.rx_time_tags.set_save_all(True)
        self.connect(self.src, self.sink)
        self.connect(self.src, self.rx_time_tags)

    def _try_set_rx_agc(self, enable: bool = False) -> None:
        try:
            self.src.set_rx_agc(enable)
        except RuntimeError as e:
            logger.warning("RX AGC not supported by this radio; msg: %s", str(e))

    def log_diagnostics(self, enabled: bool = False) -> None:
        if not enabled:
            return

        logger.info(
            "RX sample rate: requested=%.0f Sps, actual=%.0f Sps",
            self.requested_sample_rate,
            self.src.get_samp_rate(),
        )

        logger.info(
            "USRP timing sources: clock=%s, time=%s",
            self.src.get_clock_source(self.rx_channel),
            self.src.get_time_source(self.rx_channel),
        )

        tags = list(self.rx_time_tags.current_tags())

        logger.info(
            "RX time tags: count=%d",
            len(tags),
        )

        for tag in tags:
            seconds = pmt.to_uint64(pmt.tuple_ref(tag.value, 0))
            fraction = pmt.to_double(pmt.tuple_ref(tag.value, 1))

            logger.info(
                "RX time: sample=%d, UHD t=%.9f s",
                tag.offset,
                seconds + fraction,
            )
