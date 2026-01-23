"""CLI argument parser for CorteXForge forge."""

import argparse


def build_parser() -> argparse.ArgumentParser:
    """
    Build and configure the cli argument parser for CorteXForge forge.

    Returns:
        argparse.ArgumentParser: Configured argument parser instance with
    """
    parser = argparse.ArgumentParser(
        prog="CorteXForge forge", description="Dataset Generator"
    )
    sub = parser.add_subparsers(
        dest="role",
        required=True,
        help="Radio role for this node (rx=receiver, tx=transmitter)",
    )

    # RX
    # rx_p = sub.add_parser("rx", help="Receiver mode")
    sub.add_parser("rx", help="Receiver mode")

    # TX
    tx_p = sub.add_parser("tx", help="Transmitter")
    tx_p.add_argument(
        "--timeline", type=str, required=True, help="Path to timeline CSV"
    )
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = build_parser()
    return parser.parse_args(argv)
