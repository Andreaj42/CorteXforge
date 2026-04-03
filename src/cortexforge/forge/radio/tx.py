import time
from logging import getLogger

from cortexforge.forge.radio.tx_burst import TxTimeline
from cortexforge.forge.radio.waveforms import make_burst
from cortexforge.forge.utils.load_timeline import load_timeline
from cortexforge.forge.utils.node_identity import get_node_name
from cortexforge.forge.utils.sync_barrier.sync_config import SyncConfig
from cortexforge.forge.utils.sync_barrier.tx_barrier_client import TxBarrierClient
from cortexforge.forge.utils.uhd_time import arm_time_reset_next_pps

logger = getLogger(__name__)


def main(args):
    node_name = get_node_name()
    timeline_all = load_timeline(args.timeline)
    timeline = [ev for ev in timeline_all if ev.get("radio") == node_name]

    if not timeline:
        logger.warning("No TX events found for node %s.", node_name)
        return

    # Prepare I/Q burst
    events_with_iq = []
    for ev in timeline:
        iq = make_burst(
            modulation=ev["modulation"],
            sample_rate=ev["sample_rate_sps"],
            symbol_rate=ev["symbol_rate"],
            duration_s=ev["duration_s"],
            rolloff=ev["rolloff"],
            amplitude=ev["amplitude"],
        ).astype("complex64")

        ev2 = dict(ev)
        ev2["iq"] = iq
        events_with_iq.append(ev2)

        logger.info(
            f"event start={ev['t_start_s']} dur={ev['duration_s']} "
            f"modulation={ev['modulation']}"
        )

    tb = TxTimeline(
        usrp_args="",
        rate=events_with_iq[0]["sample_rate_sps"],
        center_freq=args.frequency,
        gain=args.gain,
        events_with_iq=events_with_iq,
    )

    cfg = SyncConfig(server_host=args.record_node, port_reg=5555, port_pub=5556)
    client = TxBarrierClient(cfg, node_name=node_name)
    client.register()

    msg = client.wait_broadcast()
    assert msg["type"] == "GO"

    # logger.info(f"UHD before reset: {tb.sink.get_time_now().get_real_secs():.6f} s")

    arm_time_reset_next_pps(tb.sink)
    # logger.info(f"UHD after reset: {tb.sink.get_time_now().get_real_secs():.6f} s")

    tb.start()
    # logger.info(f"UHD time at start: {tb.sink.get_time_now().get_real_secs():.6f} s")

    # 5) Attendre jusqu’à la fin du dernier burst
    last_ev = max(events_with_iq, key=lambda e: e["t_start_s"] + e["duration_s"])
    t_end = float(last_ev["t_start_s"] + last_ev["duration_s"]) + 1.0

    while tb.sink.get_time_now().get_real_secs() < t_end:
        time.sleep(0.001)

    tb.stop()
    tb.wait()
    logger.info("Timeline complete.")
