import argparse


def build_parser() -> argparse.ArgumentParser:
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


def parse_args(argv=None):
    parser = build_parser()
    return parser.parse_args(argv)
