from logging import getLogger
from time import time, sleep
from datetime import datetime, timezone

from cortexforge.forge.utils.node_identity import get_node_name
from cortexforge.forge.radio.rx_recorder import RxRecorder
from cortexforge.forge.utils.sigmf_writer import write_sigmf

logger = getLogger(__name__)

def main(args):
    out_dir = args.output_path
    out_dir.mkdir(parents=True, exist_ok=True)

    # temp raw file (will be renamed to .sigmf-data)
    raw_path = out_dir / "temp.sc16"
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

    data_path, meta_path = write_sigmf(
        base_path=str(base_path),
        data_file=str(raw_path),
        sample_rate=args.sample_rate,
        center_freq=args.frequency,
        hardware=f"{get_node_name()}, {tb.src.get_usrp_info().get('mboard_id')}",
        author="Andrea Joly",
        description="CorteXForge recording",
        gain=args.gain,
    )
    logger.info(f"SigMF written: {data_path} and {meta_path}")
