import numpy as np
import pmt
import math
from gnuradio import gr, uhd

class BurstScheduler(gr.sync_block):
    """
    Sort un flux complexe et place des tags UHD:
    - tx_time (PMT tuple (int_secs, frac_secs)) au 1er sample du burst
    - tx_sob au 1er sample
    - tx_eob au dernier sample
    """

    def __init__(self, events, sample_rate, amplitude_scale=1.0):
        gr.sync_block.__init__(
            self,
            name="BurstScheduler",
            in_sig=None,
            out_sig=[np.complex64],
        )
        self.events = list(events)
        self.fs = float(sample_rate)
        self.amp_scale = float(amplitude_scale)

        # Pré-génère tous les bursts
        self.bursts = []
        for ev in self.events:
            iq = ev["iq"].astype(np.complex64) * self.amp_scale
            t0 = float(ev["t_start_s"])
            self.bursts.append((t0, iq))

        self.cur_idx = 0
        self.cur_pos = 0
        self.finished = False

    def _tag_tx_time(self, abs_offset, t0_s):
        # UHD attend tx_time = (int_secs, frac_secs)
        int_s = int(math.floor(t0_s))
        frac_s = float(t0_s - int_s)
        key = pmt.intern("tx_time")
        val = pmt.make_tuple(pmt.from_long(int_s), pmt.from_double(frac_s))
        self.add_item_tag(0, abs_offset, key, val)

    def _tag_flag(self, abs_offset, key_str):
        self.add_item_tag(0, abs_offset, pmt.intern(key_str), pmt.PMT_T)

    def work(self, input_items, output_items):
        out = output_items[0]
        n = len(out)
        out[:] = 0

        if self.finished:
            return -1  # Fin de flux

        produced = 0
        while produced < n and not self.finished:
            if self.cur_idx >= len(self.bursts):
                self.finished = True
                break

            t0_s, iq = self.bursts[self.cur_idx]

            # Premier sample du burst -> tags SOB + tx_time
            if self.cur_pos == 0:
                abs_off = self.nitems_written(0) + produced
                self._tag_tx_time(abs_off, t0_s)
                self._tag_flag(abs_off, "tx_sob")

            remaining = len(iq) - self.cur_pos
            space = n - produced
            k = min(remaining, space)

            out[produced:produced+k] = iq[self.cur_pos:self.cur_pos+k]
            self.cur_pos += k
            produced += k

            # Dernier sample du burst -> tag EOB sur CE sample
            if self.cur_pos >= len(iq):
                abs_off_last = self.nitems_written(0) + produced - 1
                self._tag_flag(abs_off_last, "tx_eob")
                self.cur_idx += 1
                self.cur_pos = 0

        return produced




class TxTimeline(gr.top_block):
    def __init__(self, usrp_args, rate, center_freq, gain, events_with_iq):
        super().__init__("TxTimeline")

        self.sink = uhd.usrp_sink(
            usrp_args,
            uhd.stream_args(cpu_format="fc32", channels=[0]),
        )

        self.sink.set_clock_source("external", 0)
        self.sink.set_time_source("external", 0)

        self.sink.set_samp_rate(rate)
        self.sink.set_center_freq(center_freq, 0)
        self.sink.set_gain(gain, 0)
        self.sink.set_antenna("TX/RX", 0)

        self.src = BurstScheduler(events_with_iq, sample_rate=rate)

        self.connect(self.src, self.sink)
