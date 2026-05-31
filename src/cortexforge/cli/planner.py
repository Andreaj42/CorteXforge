"""CLI argument parser for CorteXForge planner."""

from argparse import Action, ArgumentParser, Namespace
from pathlib import Path

from cortexforge.planner.modulations import DEFAULT_MODULATIONS


def _split_modulations(value: str) -> list[str]:
    return [item.strip().upper() for item in value.split(",") if item.strip()]


class _ModulationAction(Action):
    """Parse comma-separated and repeated modulation values into a flat list."""

    def __call__(self, parser, namespace, values, option_string=None):
        modulations = list(getattr(namespace, self.dest, None) or [])
        for value in values:
            modulations.extend(_split_modulations(value))
        unknown = sorted(set(modulations) - set(DEFAULT_MODULATIONS))
        if unknown:
            parser.error(
                f"unsupported modulation(s): {', '.join(unknown)}. "
                f"Supported values are: {', '.join(DEFAULT_MODULATIONS)}"
            )
        setattr(namespace, self.dest, modulations)


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
        "--n-signals",
        type=int,
        default=288,
        help=(
            "Number of signals to generate. Must be a multiple of the selected "
            "modulation count."
        ),
    )
    parser.add_argument(
        "--nodes-path",
        type=Path,
        default="configs/nodes.yaml",
        help="Path to nodes.yaml file",
    )
    parser.add_argument(
        "--modulations",
        action=_ModulationAction,
        nargs="+",
        metavar="MOD",
        default=None,
        help=(
            "Modulations to include in the generated dataset. "
            "Use a space-separated list or comma-separated values. "
            "Defaults to all planner modulations."
        ),
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
