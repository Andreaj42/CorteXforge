import argparse

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="CorteXForge", description="Dataset Generator")
    sub = parser.add_subparsers(dest="role", required=True,
        help="Radio role for this node (rx=receiver, tx=transmitter)"
    )

    # RX
    rx_p = sub.add_parser("rx", help="Receiver mode")

    # TX
    tx_p = sub.add_parser("tx", help="Transmitter")
    tx_p.add_argument(
        "--timeline",
        type=str,
        required=True,
        help="Absolute path to timeline CSV"
    )
    return parser

def parse_args(argv=None):
    parser = build_parser()
    return parser.parse_args(argv)
