import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="CorteXForge planner", description="Dataset Generator"
    )
    parser.add_argument("--file", type=int, default=600, help="Timelive file path")
    return parser


def parse_args(argv=None):
    parser = build_parser()
    return parser.parse_args(argv)
