"""Unified CLI entrypoint for CorteXForge."""

from argparse import ArgumentParser, Namespace

from cortexforge.cli.datasets import configure_parser as configure_datasets_parser
from cortexforge.cli.forge import configure_parser as configure_forge_parser
from cortexforge.cli.planner import configure_parser as configure_planner_parser


def build_parser() -> ArgumentParser:
    """Build the root CLI parser."""
    parser = ArgumentParser(prog="cortexforge", description="CorteXForge command line")
    sub = parser.add_subparsers(
        dest="command",
        required=True,
        help="CorteXForge subcommand",
    )

    configure_planner_parser(
        sub.add_parser("planner", help="Generate scenarios and experiment files")
    )
    configure_forge_parser(
        sub.add_parser("forge", help="Run transmitter or receiver commands")
    )
    configure_datasets_parser(
        sub.add_parser("datasets", help="Inspect locally available datasets")
    )
    return parser


def parse_args(argv: list[str] | None = None) -> Namespace:
    """Parse root CLI arguments."""
    return build_parser().parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Dispatch to the selected CorteXForge subcommand."""
    args = parse_args(argv)

    if args.command == "planner":
        from cortexforge.planner.main import run as planner_run

        planner_run(args)
        return

    if args.command == "forge":
        from cortexforge.forge.main import run as forge_run

        forge_run(args)
        return

    if args.command == "datasets":
        from cortexforge.datasets.main import run as datasets_run

        datasets_run(args)
        return

    raise ValueError(f"Unknown command: {args.command}")
