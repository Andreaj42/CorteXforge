from logging import getLogger
from time import sleep
from datetime import datetime, timezone

from cortexforge.forge.radio.rx_recorder import RxRecorder
from cortexforge.forge.utils.sigmf_writer import write_sigmf
from cortexforge.forge.utils.compute_baseline import compute_baseline
from cortexforge.forge.utils.load_timeline import load_timeline
from cortexforge.forge.utils.sync_barrier.rx_barrier_server import RxBarrierServer
from cortexforge.forge.utils.sync_barrier.sync_config import SyncConfig
from cortexforge.forge.utils.uhd_time import arm_time_reset_next_pps


logger = getLogger(__name__)

def timeline_to_sigmf_annotations(events, rx_sample_rate):
    ann = []
    for ev in events:
        start = int(round(ev["t_start_s"] * rx_sample_rate))
        count = int(round(ev["duration_s"] * rx_sample_rate))

        bw = (1.0 + ev["rolloff"]) * ev["symbol_rate"]
        f0 = ev["freq_hz"]
        f_low = f0 - bw / 2.0
        f_high = f0 + bw / 2.0

        ann.append({
            "core:sample_start": start,
            "core:sample_count": count,
            "core:freq_lower_edge": f_low,
            "core:freq_upper_edge": f_high,
            "core:label": str(ev["modulation"]),
            "cortexforge:radio": ev["radio"],
            "cortexforge:tx_gain_db": ev["tx_gain_db"],
            "cortexforge:amplitude": ev["amplitude"],
            "cortexforge:symbol_rate": ev["symbol_rate"],
            "cortexforge:rolloff": ev["rolloff"]
        })

    ann.sort(key=lambda a: a["core:sample_start"])
    return ann


def main(args):
    out_dir = args.output_path
    out_dir.mkdir(parents=True, exist_ok=True)

    # temp raw file (will be renamed to .sigmf-data)
    raw_path = out_dir / "temp.cf32"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    base_path = out_dir / f"{stamp}"

    tb = RxRecorder(
        usrp_args="",
        freq=args.frequency,
        rate=args.sample_rate,
        gain=args.gain,
        out_path=str(raw_path),
    )
    cfg = SyncConfig(
        server_host="mnode24",
        port_reg=5555,
        port_pub=5556,
        expected_tx=3,
    )
    barrier = RxBarrierServer(cfg)
    barrier.wait_for_all()

    barrier.broadcast({"type": "GO"})
    arm_time_reset_next_pps(tb.src)
    #logger.info("Current UHD time (before starting record): %f", tb.src.get_time_now().get_real_secs())

    tb.start()
    #logger.info("Current UHD time (starting record): %f", tb.src.get_time_now().get_real_secs())

    while tb.src.get_time_now().get_real_secs() < args.duration:
        sleep(0.001)

    tb.stop()
    tb.wait()
    #logger.info("Current UHD time (stop recording): %f", tb.src.get_time_now().get_real_secs())

    stats = compute_baseline(
        path=str(raw_path),
        sample_rate=args.sample_rate
    )

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
            events=load_timeline(args.timeline),
            rx_sample_rate=args.sample_rate,
        ),
    )
    logger.info(f"SigMF written: {data_path} and {meta_path}")

