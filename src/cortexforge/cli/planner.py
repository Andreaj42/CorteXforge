"""CLI argument parser for CorteXForge planner."""

from argparse import ArgumentParser, Namespace
from pathlib import Path


def build_parser() -> ArgumentParser:
    """
    Build and configure the cli argument parser for CorteXForge planner.

    Returns:
        ArgumentParser: Configured argument parser instance with
    """
    parser = ArgumentParser(
        prog="CorteXForge planner", description="Dataset Generator"
    )
    parser.add_argument("--username", type=str, help="username on CorteXlab")
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
        "--nodes-path",
        type=Path,
        default="configs/nodes.yaml",
        help="Path to nodes.yaml file",
    )
    return parser


def parse_args(argv: list[str] | None = None) -> Namespace:
    """Parse command line arguments."""
    parser = build_parser()
    return parser.parse_args(argv)
