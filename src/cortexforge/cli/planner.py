import argparse


def build_parser() -> argparse.ArgumentParser:
    """
    Build and configure the cli argument parser for CorteXForge planner.

    Returns:
        argparse.ArgumentParser: Configured argument parser instance with
    """
    parser = argparse.ArgumentParser(
        prog="CorteXForge planner", description="Dataset Generator"
    )
    parser.add_argument(
        "--duration", type=int, default=600, help="Experiment duration in seconds"
    )
    parser.add_argument(
        "--nodes-path",
        type=str,
        default="configs/nodes.yaml",
        help="Path to nodes.yaml file",
    )
    return parser


def parse_args(argv=None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = build_parser()
    return parser.parse_args(argv)
