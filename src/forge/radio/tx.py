import time
from dataclasses import dataclass
from config import defaults
from utils.logger import setup_logger
from radio.tx_burst import tx_burst
from radio.waveforms import make_burst
from utils.load_timeline import load_timeline
from utils.node_identity import get_node_name


def main(args):
    logger = setup_logger()
    node_name = get_node_name(logger)
    timeline_all = load_timeline(args.timeline)

    timeline = [ev for ev in timeline_all if ev.get("radio") == node_name]

    logger.info(f"[TX] Loaded {len(timeline_all)} events total, selected {len(timeline)} for node={node_name}")

    logger.info(f"[TX] Loaded {len(timeline)} events from {args.timeline}")
    logger.info(f"[TX] default antenna={defaults.DEFAULT_TX_ANT}")

    t0 = time.time()

    for ev in timeline:
        now = time.time()
        dt = (t0 + ev["t_start_s"]) - now
        if dt > 0:
            time.sleep(dt)

        logger.info(
            f"[TX] event start={ev['t_start_s']}s dur={ev['duration_s']}s "
            f"f={ev['freq_hz']} rate={ev['sample_rate_sps']} gain={ev['tx_gain_db']} "
            f"amp={ev['amplitude']} mod={ev['modulation']} symrate={ev['symbol_rate']} "
            f"rolloff={ev['rolloff']}"
        )

        iq = make_burst(
            modulation=ev["modulation"],
            sample_rate=ev["sample_rate_sps"],
            symbol_rate=ev["symbol_rate"],
            duration_s=ev["duration_s"],
            rolloff=ev["rolloff"],
            amplitude=ev["amplitude"],
        )

        tb = tx_burst(
            usrp_args="",
            freq=ev["freq_hz"],
            rate=ev["sample_rate_sps"],
            gain=ev["tx_gain_db"],
            antenna=defaults.DEFAULT_TX_ANT,
            iq=iq,
        )
        tb.run()
        tb.stop()

    logger.info("[TX] Timeline complete.")
