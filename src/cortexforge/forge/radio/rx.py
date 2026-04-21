from logging import getLogger
from time import sleep
from datetime import datetime, timezone
from gnuradio import uhd

from cortexforge.forge.radio.rx_recorder import RxRecorder
from cortexforge.forge.utils.sigmf_writer import write_sigmf
from cortexforge.forge.utils.compute_baseline import compute_baseline
from cortexforge.forge.utils.load_timeline import load_timeline
from cortexforge.forge.utils.sync_barrier.rx_barrier_server import RxBarrierServer
from cortexforge.forge.utils.sync_barrier.sync_config import SyncConfig
from cortexforge.forge.utils.uhd_time import arm_time_reset_next_pps
from cortexforge.forge.utils.sigmf.sigmf_annotations import timeline_to_sigmf_annotations
from cortexforge.forge.utils.node_identity import get_node_name


logger = getLogger(__name__)


def main(args):
    out_dir = args.output_path
    out_dir.mkdir(parents=True, exist_ok=True)

    timeline = load_timeline(args.timeline)

    radios = {str(ev["radio"]) for ev in timeline if ev.get("radio")}

    logger.debug(f"Radios in timeline: {radios}, expecting {len(radios)} to synchronize")

    raw_path = out_dir / "temp.cf32"

    tb = RxRecorder(
        usrp_args="",
        freq=args.frequency,
        rate=args.sample_rate,
        gain=args.gain,
        out_path=str(raw_path),
    )
    cfg = SyncConfig(
        server_host=get_node_name(),
        port_reg=5555,
        port_pub=5556,
        expected_tx=len(radios),
    )
    barrier = RxBarrierServer(cfg)
    barrier.wait_for_all()

    barrier.broadcast({"type": "GO"})
    arm_time_reset_next_pps(tb.src)

    capture_start_uhd = 1.0
    if hasattr(tb.src, "set_start_time"):
        tb.src.set_start_time(uhd.time_spec(capture_start_uhd))
        logger.info("RX stream scheduled at UHD t=%.3f s", capture_start_uhd)
        rx_uhd_t0 = capture_start_uhd
    else:
        rx_uhd_t0 = None
        logger.warning("RX source has no set_start_time(); using runtime t0 estimate")

    tb.start()
    if rx_uhd_t0 is None:
        rx_uhd_t0 = tb.src.get_time_now().get_real_secs()

    while tb.src.get_time_now().get_real_secs() < rx_uhd_t0 + args.duration:
        sleep(0.001)

    tb.stop()
    tb.wait()

    stats = compute_baseline(
        path=str(raw_path),
        sample_rate=args.sample_rate
    )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    base_path = out_dir / f"{stamp}"


    logger.info(f"Recording stats: {stats}")
    data_path, meta_path = write_sigmf(
        base_path=str(base_path),
        data_file=str(raw_path),
        stat=stats,
        sample_rate=args.sample_rate,
        center_freq=args.frequency,
        hardware=tb.src.get_usrp_info().get('mboard_id'),
        author="Andrea Joly",
        description="CorteXForge recording",
        gain=args.gain,
        annotations = timeline_to_sigmf_annotations(
            events=timeline,
            rx_sample_rate=args.sample_rate,
            rx_uhd_t0=rx_uhd_t0,
            tx_center_freq=args.frequency,
            tx_gain=args.gain,
            rx_data_path=str(raw_path),
            baseline_stat=stats,
        ),
    )
    logger.info(f"SigMF written: {data_path} and {meta_path}")
