from datetime import datetime, timezone
from logging import getLogger
from time import sleep

from gnuradio import uhd

from cortexforge.forge.radio.rx_recorder import RxRecorder
from cortexforge.forge.utils.compute_baseline import check_parseval, compute_baseline
from cortexforge.forge.utils.load_timeline import load_timeline
from cortexforge.forge.utils.node_identity import get_node_name
from cortexforge.forge.utils.sigmf.sigmf_annotations import (
    timeline_to_sigmf_annotations,
)
from cortexforge.forge.utils.sigmf_writer import write_sigmf
from cortexforge.forge.utils.sync_barrier.sync_barrier_client import SyncBarrierClient
from cortexforge.forge.utils.sync_barrier.sync_config import SyncConfig
from cortexforge.forge.utils.uhd_time import arm_time_reset_next_pps

logger = getLogger(__name__)


def main(args) -> None:
    node_name = get_node_name()

    out_dir = args.output_path / node_name
    out_dir.mkdir(parents=True, exist_ok=True)

    raw_path = out_dir / "temp.cf32"

    logger.info("Starting receiver on node %s", node_name)
    logger.info("Output directory: %s", out_dir)

    timeline = load_timeline(args.timeline)

    tb = RxRecorder(
        usrp_args="",
        freq=args.frequency,
        rate=args.sample_rate,
        gain=args.gain,
        out_path=str(raw_path),
    )

    cfg = SyncConfig(
        server_host=args.sync_node,
        port_reg=5555,
        port_pub=5556,
    )

    client = SyncBarrierClient(
        cfg,
        node_name=node_name,
        role="rx",
    )

    logger.info(
        "Receiver initialized. Registering to synchronization node %s",
        args.sync_node,
    )

    client.register()

    logger.info("Waiting for synchronization GO...")
    client.wait_go()

    logger.info("GO received. Arming UHD time synchronization.")

    # Reset UHD time to zero on the next PPS edge.
    arm_time_reset_next_pps(tb.src)

    capture_start_uhd = 1.0

    if hasattr(tb.src, "set_start_time"):
        tb.src.set_start_time(uhd.time_spec(capture_start_uhd))

        logger.info(
            "RX stream scheduled at UHD t=%.3f s",
            capture_start_uhd,
        )

        rx_uhd_t0 = capture_start_uhd

    else:
        rx_uhd_t0 = None
        logger.warning("RX source has no set_start_time(); using runtime t0 estimate")

    tb.start()

    if rx_uhd_t0 is None:
        rx_uhd_t0 = tb.src.get_time_now().get_real_secs()

    capture_end_uhd = rx_uhd_t0 + args.duration

    logger.info(
        "Recording from UHD t=%.6f to t=%.6f",
        rx_uhd_t0,
        capture_end_uhd,
    )

    while tb.src.get_time_now().get_real_secs() < capture_end_uhd:
        sleep(0.001)

    tb.stop()
    tb.wait()

    logger.info("Recording completed.")

    expected_size = int(args.duration * args.sample_rate) * 8
    actual_size = raw_path.stat().st_size

    logger.info("Expected size: %d bytes", expected_size)
    logger.info("Actual size: %d bytes", actual_size)

    check_parseval(
        path=str(raw_path),
        sample_start=int(0.5 * args.sample_rate),
        sample_count=100 * 16384,
        sample_rate=args.sample_rate,
        center_frequency=args.frequency,
    )

    stats = compute_baseline(
        path=str(raw_path),
        sample_rate=args.sample_rate,
    )

    logger.info("Recording stats: %s", stats)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    base_path = out_dir / stamp

    annotations = timeline_to_sigmf_annotations(
        events=timeline,
        rx_sample_rate=args.sample_rate,
        rx_center_frequency=args.frequency,
        rx_uhd_t0=rx_uhd_t0,
        rx_data_path=str(raw_path),
        baseline_stat=stats,
    )

    data_path, meta_path = write_sigmf(
        base_path=str(base_path),
        data_file=str(raw_path),
        stat=stats,
        sample_rate=args.sample_rate,
        center_freq=args.frequency,
        hardware=tb.src.get_usrp_info().get("mboard_id"),
        author="Andrea Joly",
        description=f"CorteXforge recording from {node_name}",
        gain=args.gain,
        annotations=annotations,
    )

    logger.info(
        "SigMF written: %s and %s",
        data_path,
        meta_path,
    )
