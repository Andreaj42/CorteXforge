"""CLI argument parser for CorteXForge planner."""

from argparse import ArgumentParser, Namespace
from pathlib import Path


def configure_parser(parser: ArgumentParser) -> ArgumentParser:
    """Attach planner-specific arguments to an existing parser."""
    parser.add_argument(
        "--username", required=True, type=str, help="username on CorteXlab"
    )
    parser.add_argument(
        "--duration", type=int, default=60, help="Experiment duration in seconds"
    )
    parser.add_argument(
        "--rx-frequency", type=int, default=2450000000, help="Receiver frequency"
    )
    parser.add_argument("--rx-gain", type=int, default=10, help="Receiver gain")
    parser.add_argument(
        "--rx-sample-rate", type=int, default=250000, help="Receiver sample-rate"
    )
    parser.add_argument(
        "--overlapping",
        action="store_true",
        help="Allow overlapping signals in timeline",
    )
    parser.add_argument(
        "--nodes-path",
        type=Path,
        default="configs/nodes.yaml",
        help="Path to nodes.yaml file",
    )
    return parser


def build_parser() -> ArgumentParser:
    """Build and configure the standalone planner parser."""
    parser = ArgumentParser(prog="cortexforge planner", description="Dataset Generator")
    return configure_parser(parser)


def parse_args(argv: list[str] | None = None) -> Namespace:
    """Parse command line arguments."""
    parser = build_parser()
    return parser.parse_args(argv)
