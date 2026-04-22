"""CLI argument parser for CorteXForge datasets."""

from argparse import ArgumentParser, Namespace
from pathlib import Path


def configure_parser(parser: ArgumentParser) -> ArgumentParser:
    """Attach datasets-specific arguments to an existing parser."""
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("datasets"),
        help="Path to the datasets root directory",
    )

    sub = parser.add_subparsers(
        dest="datasets_command",
        required=True,
        help="Dataset operation to execute",
    )

    sub.add_parser("list", help="List available datasets and their versions")

    versions = sub.add_parser("versions", help="List available versions for a dataset")
    versions.add_argument("name", type=str, help="Dataset name")

    describe = sub.add_parser("describe", help="Show a dataset manifest")
    describe.add_argument("name", type=str, help="Dataset name")
    describe.add_argument("version", type=str, help="Dataset version")

    download = sub.add_parser(
        "download",
        help="Download and extract a dataset version from the embedded registry",
    )
    download.add_argument("name", type=str, help="Dataset name")
    download.add_argument(
        "--version",
        type=str,
        default=None,
        help="Dataset version to download (defaults to latest)",
    )
    download.add_argument(
        "--force",
        action="store_true",
        help="Re-download and overwrite an existing local dataset version",
    )

    return parser


def build_parser() -> ArgumentParser:
    """Build and configure the standalone datasets parser."""
    parser = ArgumentParser(
        prog="cortexforge datasets",
        description="Inspect locally available datasets",
    )
    return configure_parser(parser)


def parse_args(argv: list[str] | None = None) -> Namespace:
    """Parse command line arguments."""
    parser = build_parser()
    return parser.parse_args(argv)
