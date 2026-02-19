"""CLI argument parser for CorteXForge forge."""

from argparse import ArgumentParser, Namespace
from pathlib import Path


def build_parser() -> ArgumentParser:
    """
    Build and configure the cli argument parser for CorteXForge forge.

    Returns:
        ArgumentParser: Configured argument parser instance with
    """
    parser = ArgumentParser(
        prog="CorteXForge forge", description="Dataset Generator"
    )
    sub = parser.add_subparsers(
        dest="role",
        required=True,
        help="Radio role for this node (rx=receiver, tx=transmitter)",
    )

    rx = sub.add_parser("rx", help="Receiver mode")
    rx.add_argument(
        "--frequency", type=int, required=True, help="Receiver center frequency (Hz)")
    rx.add_argument(
        "--sample-rate", type=int, required=True, help="Receiver sample rate (Sps)")
    rx.add_argument(
        "--gain", type=int, required=True, help="Receiver gain (dB)")
    rx.add_argument(
        "--duration", type=int, required=True, help="Capture duration (seconds)")
    rx.add_argument(
        "--timeline", type=Path, required=True, help="Path to timeline CSV")
    rx.add_argument(
        "--output-path",
        type=Path,
        required=True,
        help=(
            "Path to output directory for results "
            "(e.g. /cortexlab/homes/<username>/out)"
        ),
    )

    tx = sub.add_parser("tx", help="Transmitter")
    tx.add_argument(
        "--timeline", type=Path, required=True, help="Path to timeline CSV")
    return parser


def parse_args(argv: list[str] | None = None) -> Namespace:
    """Parse command line arguments."""
    parser = build_parser()
    return parser.parse_args(argv)
