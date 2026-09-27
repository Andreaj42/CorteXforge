from datetime import datetime, timezone
from pathlib import Path

from cortexforge.cli.planner import parse_args
from cortexforge.planner.generators.cortexlab_scenario import (
    generate_cortexlab_scenario,
)
from cortexforge.planner.generators.experiment_scenario import ExperimentScenario
from cortexforge.utils.logger import setup_logger

logger = setup_logger()


def print_distribution(df, column: str) -> None:
    counts = df[column].value_counts().sort_index()
    ratios = counts / len(df)

    print(f"\n{column}:")
    for value in counts.index:
        print(f"  {value!s:20} {counts[value]:5d} ({100 * ratios[value]:6.2f}%)")


def validate_nodes(
    rx_nodes: list[str],
    tx_nodes: list[str],
    sync_node: str,
) -> None:
    rx_set = set(rx_nodes)
    tx_set = set(tx_nodes)

    if len(rx_set) != len(rx_nodes):
        raise ValueError("Receiver nodes must be unique.")

    if len(tx_set) != len(tx_nodes):
        raise ValueError("Transmitter nodes must be unique.")

    overlap = rx_set & tx_set
    if overlap:
        raise ValueError(f"Nodes cannot be both RX and TX: {sorted(overlap)}")

    if sync_node in rx_set:
        raise ValueError(f"Synchronization node {sync_node} cannot also be a receiver.")

    if sync_node in tx_set:
        raise ValueError(
            f"Synchronization node {sync_node} cannot also be a transmitter."
        )


def run(args) -> None:
    logger.info("Starting scenario generation...")
    experiment_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    logger.info("Experiment ID: %s", experiment_id)

    output_dir = Path(f"cxf/{experiment_id}/")
    output_dir.mkdir(parents=True, exist_ok=True)

    validate_nodes(
        rx_nodes=args.rx_nodes,
        tx_nodes=args.tx_nodes,
        sync_node=args.sync_node,
    )

    scenario = ExperimentScenario(
        tx_nodes=args.tx_nodes,
        duration=args.duration,
        rx_sample_rate=args.rx_sample_rate,
        modulations=args.tx_modulations,
        symbol_rates=args.tx_symbol_rates,
        roll_offs=args.tx_roll_offs,
        amplitudes=args.tx_amplitudes,
    )
    df = scenario.generate_table(
        n_signals=args.n_signals,
        tx_gain=args.tx_gain,
        tx_frequency=args.tx_frequency,
        allow_overlap=args.overlapping,
        seed=args.seed,
    )
    print(df.head())
    timeline_path = output_dir / "timeline.csv"
    df.index.name = "id"
    df.to_csv(timeline_path)
    for column in [
        "modulation",
        "radio",
        "amplitude",
        "symbol_rate",
        "roll_off",
    ]:
        print_distribution(df, column)

    n_participants = len(args.rx_nodes) + len(args.tx_nodes)
    rx_sample_count = args.duration * args.rx_sample_rate
    generate_cortexlab_scenario(
        rx_nodes=args.rx_nodes,
        tx_nodes=args.tx_nodes,
        sync_node=args.sync_node,
        duration=len(args.rx_nodes) * args.duration,
        image="ghcr.io/andreaj42/cortexforge:latest",
        rx_command=(
            f'bash -lc "cortexforge forge rx '
            f"--sample-count {rx_sample_count} "
            f"--frequency {args.rx_frequency} "
            f"--gain {args.rx_gain} "
            f"--sample-rate {args.rx_sample_rate} "
            f"--output-path /cortexlab/homes/{args.username}/out/{experiment_id}/ "
            f"--timeline /cortexlab/homes/{args.username}/cxf/{experiment_id}/timeline.csv "
            f'--sync-node {args.sync_node}"'
        ),
        tx_command=(
            f'bash -lc "cortexforge forge tx '
            f"--timeline /cortexlab/homes/{args.username}/cxf/{experiment_id}/timeline.csv "
            f"--sync-node {args.sync_node} "
            f"--gain {args.tx_gain} "
            f'--frequency {args.tx_frequency}"'
        ),
        sync_command=(
            'bash -lc "cortexforge forge sync '
            f'--expected-participants {n_participants}"'
        ),
        output_path=f"cxf/{experiment_id}/scenario.yaml",
    )

    logger.info("Scenario generation completed.")


def main(argv: list[str] | None = None) -> None:
    run(parse_args(argv))


if __name__ == "__main__":
    main()
