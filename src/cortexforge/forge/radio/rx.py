from logging import getLogger
from time import time, sleep
from datetime import datetime, timezone

from cortexforge.forge.radio.rx_recorder import RxRecorder
from cortexforge.forge.utils.sigmf_writer import write_sigmf
from cortexforge.forge.utils.compute_baseline import compute_baseline
from cortexforge.forge.utils.load_timeline import load_timeline

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

    tb.start()
    t0 = time()
    while time() - t0 < args.duration:
        sleep(0.05)

    tb.stop()
    tb.wait()
    
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

