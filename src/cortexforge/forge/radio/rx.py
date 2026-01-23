#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import signal
import time
from datetime import datetime, timezone

from cortexforge.forge.config import defaults
from cortexforge.forge.radio.rx_recorder import RxRecorder
from cortexforge.forge.utils.logger import setup_logger
from cortexforge.forge.utils.sigmf_writer import write_sigmf


def main(args):
    logger = setup_logger()
    logger.info(args)
    logger.info(
        f"[RX] freq={defaults.FREQUENCY} rate={defaults.SAMPLE_RATE} "
        f"gain={defaults.RX_GAIN} ant={defaults.RX_ANTENNA} "
        f"duration={defaults.DURATION} out={args.output_path}"
    )

    out_dir = args.output_path
    out_dir.mkdir(parents=True, exist_ok=True)

    # temp raw file (will be renamed to .sigmf-data)
    raw_path = out_dir / "temp.cf32"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    base_path = out_dir / f"{stamp}"

    tb = RxRecorder(
        usrp_args="",
        freq=defaults.FREQUENCY,
        rate=defaults.SAMPLE_RATE,
        gain=defaults.RX_GAIN,
        out_path=str(raw_path),
        antenna=defaults.RX_ANTENNA,
    )

    stop_flag = {"stop": False}

    def handler(sig, frame):
        stop_flag["stop"] = True

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

    tb.start()
    t0 = time.time()
    while not stop_flag["stop"] and (time.time() - t0) < defaults.DURATION:
        time.sleep(0.05)
    tb.stop()
    tb.wait()

    data_path, meta_path = write_sigmf(
        base_path=str(base_path),
        data_file=str(raw_path),
        sample_rate=defaults.SAMPLE_RATE,
        center_freq=defaults.FREQUENCY,
        datatype="cf32_le",
        author="Andrea Joly",
        description="CorteXForge RX recording",
        gain=defaults.RX_GAIN,
    )
    logger.info(f"SigMF written: {data_path} and {meta_path}")
