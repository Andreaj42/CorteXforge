from cortexforge.cli.planner import build_parser
from cortexforge.planner.defaults import (
    DEFAULT_TX_AMPLITUDES,
    DEFAULT_TX_ROLL_OFFS,
    DEFAULT_TX_SYMBOL_RATES,
)


def test_default_tx_parameters():
    parser = build_parser()

    args = parser.parse_args(
        [
            "--username",
            "test_user",
            "--rx-nodes",
            "mnode1",
            "--tx-nodes",
            "mnode2",
            "--sync-node",
            "mnode3",
        ]
    )

    assert args.tx_amplitudes == list(DEFAULT_TX_AMPLITUDES)
    assert args.tx_symbol_rates == list(DEFAULT_TX_SYMBOL_RATES)
    assert args.tx_roll_offs == list(DEFAULT_TX_ROLL_OFFS)


def test_discrete_parameters_from_spaces():
    parser = build_parser()

    args = parser.parse_args(
        [
            "--username",
            "test_user",
            "--rx-nodes",
            "mnode1",
            "--tx-nodes",
            "mnode2",
            "--sync-node",
            "mnode3",
            "--tx-amplitudes",
            "0.3",
            "0.6",
            "0.9",
            "--tx-symbol-rates",
            "500000",
            "1000000",
            "--tx-roll-offs",
            "0.1",
            "0.35",
        ]
    )

    assert args.tx_amplitudes == [0.3, 0.6, 0.9]
    assert args.tx_symbol_rates == [500_000.0, 1_000_000.0]
    assert args.tx_roll_offs == [0.1, 0.35]


def test_discrete_parameters_from_commas():
    parser = build_parser()

    args = parser.parse_args(
        [
            "--username",
            "test_user",
            "--rx-nodes",
            "mnode1",
            "--tx-nodes",
            "mnode2",
            "--sync-node",
            "mnode3",
            "--tx-amplitudes",
            "0.3,0.6,0.9",
            "--tx-symbol-rates",
            "500000,1000000",
            "--tx-roll-offs",
            "0.1,0.35",
        ]
    )

    assert args.tx_amplitudes == [0.3, 0.6, 0.9]
    assert args.tx_symbol_rates == [500_000.0, 1_000_000.0]
    assert args.tx_roll_offs == [0.1, 0.35]
