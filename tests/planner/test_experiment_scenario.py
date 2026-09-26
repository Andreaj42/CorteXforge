import pandas as pd
import pytest

from cortexforge.planner.generators.experiment_scenario import ExperimentScenario


def make_scenario(duration=30):
    return ExperimentScenario(
        tx_nodes=["mnode1", "mnode2"],
        duration=duration,
        rx_sample_rate=5_000_000,
        modulations=["BPSK", "QPSK", "16QAM"],
        amplitudes=[0.3, 0.6, 0.9],
        symbol_rates=[500_000, 1_000_000],
        roll_offs=[0.1, 0.35],
    )


def test_arbitrary_number_of_signals():
    scenario = make_scenario()

    df = scenario.generate_table(
        n_signals=137,
        seed=42,
    )

    assert len(df) == 137


def test_only_requested_parameter_values_are_used():
    scenario = make_scenario()

    df = scenario.generate_table(
        n_signals=200,
        seed=42,
    )

    assert set(df["radio"]) <= {"mnode1", "mnode2"}
    assert set(df["modulation"]) <= {"BPSK", "QPSK", "16QAM"}
    assert set(df["amplitude"]) <= {0.3, 0.6, 0.9}
    assert set(df["symbol_rate"]) <= {500_000, 1_000_000}
    assert set(df["roll_off"]) <= {0.1, 0.35}


def test_same_seed_is_reproducible():
    a = make_scenario().generate_table(
        n_signals=100,
        seed=42,
    )

    b = make_scenario().generate_table(
        n_signals=100,
        seed=42,
    )

    pd.testing.assert_frame_equal(a, b)


def test_rf_sampling_is_independent_from_timeline_placement():
    short = make_scenario(duration=20)
    long = make_scenario(duration=40)

    a = short.generate_table(
        n_signals=100,
        seed=42,
    )

    b = long.generate_table(
        n_signals=100,
        seed=42,
    )

    parameter_columns = [
        "radio",
        "duration_s",
        "modulation",
        "amplitude",
        "roll_off",
        "symbol_rate",
    ]

    a_params = (
        a[parameter_columns].sort_values(parameter_columns).reset_index(drop=True)
    )

    b_params = (
        b[parameter_columns].sort_values(parameter_columns).reset_index(drop=True)
    )

    pd.testing.assert_frame_equal(
        a_params,
        b_params,
    )


@pytest.mark.parametrize(
    "amplitude",
    [-1.0, 0.0, 1.01, 2.0],
)
def test_invalid_amplitudes_are_rejected(amplitude):
    with pytest.raises(ValueError):
        ExperimentScenario(
            tx_nodes=["mnode1"],
            duration=30,
            rx_sample_rate=5_000_000,
            modulations=["BPSK"],
            amplitudes=[amplitude],
            symbol_rates=[1_000_000],
            roll_offs=[0.35],
        )
