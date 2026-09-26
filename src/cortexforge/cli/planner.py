"""CLI argument parser for CorteXforge planner."""

from argparse import Action, ArgumentDefaultsHelpFormatter, ArgumentParser, Namespace

from cortexforge.modulations import normalize_modulation
from cortexforge.planner.defaults import (
    DEFAULT_TX_AMPLITUDES,
    DEFAULT_TX_ROLL_OFFS,
    DEFAULT_TX_SYMBOL_RATES,
)


def _split_modulations(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


class _NumericListAction(Action):
    """Parse comma-separated and/or space-separated numeric values."""

    def __init__(self, option_strings, dest, numeric_type=float, **kwargs):
        self.numeric_type = numeric_type
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        parsed = []

        try:
            for value in values:
                for item in value.split(","):
                    item = item.strip()
                    if item:
                        parsed.append(self.numeric_type(item))
        except ValueError:
            parser.error(f"invalid value for {option_string}")

        setattr(namespace, self.dest, parsed)


class _ModulationAction(Action):
    """Parse and validate modulation values."""

    def __call__(self, parser, namespace, values, option_string=None):
        modulations = list(getattr(namespace, self.dest, None) or [])

        try:
            for value in values:
                for modulation in _split_modulations(value):
                    modulations.append(normalize_modulation(modulation))

        except ValueError as exc:
            parser.error(str(exc))

        modulations = list(dict.fromkeys(modulations))
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
        "--rx-nodes",
        nargs="+",
        type=str,
        required=True,
        help="Receiver nodes",
    )

    parser.add_argument(
        "--tx-nodes",
        nargs="+",
        type=str,
        required=True,
        help="Transmitter nodes",
    )

    parser.add_argument(
        "--sync-node",
        type=str,
        required=True,
        help="Dedicated node coordinating experiment synchronization",
    )

    parser.add_argument(
        "--rx-frequency", type=int, default=2450000000, help="Receiver frequency"
    )
    parser.add_argument("--rx-gain", type=int, default=1, help="Receiver gain")
    parser.add_argument(
        "--rx-sample-rate", type=int, default=16666667, help="Receiver sample-rate"
    )
    parser.add_argument("--tx-gain", type=int, default=30, help="Transmitter gain")
    parser.add_argument(
        "--tx-frequency", type=int, default=2450000000, help="Transmitter frequency"
    )
    parser.add_argument(
        "--overlapping",
        action="store_true",
        help="Allow overlapping signals in timeline",
    )
    parser.add_argument(
        "--n-signals", type=int, default=288, help="Number of signals to generate."
    )
    parser.add_argument(
        "--tx-modulations",
        action=_ModulationAction,
        nargs="+",
        default=None,
        help=(
            "Modulations to include in the generated dataset. "
            "Use a space-separated list or comma-separated values. "
            "Defaults to all planner modulations."
        ),
    )
    parser.add_argument(
        "--tx-amplitudes",
        action=_NumericListAction,
        numeric_type=float,
        nargs="+",
        default=list(DEFAULT_TX_AMPLITUDES),
        help=(
            "Discrete signal amplitudes. Example: --tx-amplitudes 0.3 0.45 0.6 0.75 0.9"
        ),
    )
    parser.add_argument(
        "--tx-symbol-rates",
        action=_NumericListAction,
        numeric_type=float,
        nargs="+",
        default=list(DEFAULT_TX_SYMBOL_RATES),
        help=(
            "Discrete symbol rates in symbols/s. "
            "Example: --tx-symbol-rates 250000 500000 1000000 1250000"
        ),
    )
    parser.add_argument(
        "--tx-roll-offs",
        action=_NumericListAction,
        numeric_type=float,
        nargs="+",
        default=list(DEFAULT_TX_ROLL_OFFS),
        help=("Discrete RRC roll-off factors. Example: --tx-roll-offs 0.1 0.35 0.5"),
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility",
    )
    return parser


def build_parser() -> ArgumentParser:
    """Build and configure the standalone planner parser."""
    parser = ArgumentParser(
        prog="cortexforge planner",
        description="Dataset Generator",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    return configure_parser(parser)


def parse_args(argv: list[str] | None = None) -> Namespace:
    """Parse command line arguments."""
    parser = build_parser()
    return parser.parse_args(argv)
