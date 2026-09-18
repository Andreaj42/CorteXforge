from cortexforge.cli.planner import parse_args
from cortexforge.planner.generators.cortexlab_scenario import (
    generate_cortexlab_scenario,
)
from cortexforge.planner.generators.experiment_scenario import ExperimentScenario
from cortexforge.utils.logger import setup_logger

logger = setup_logger()


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

    validate_nodes(
        rx_nodes=args.rx_nodes,
        tx_nodes=args.tx_nodes,
        sync_node=args.sync_node,
    )

    scenario = ExperimentScenario(
        tx_nodes=args.tx_nodes,
        duration=args.duration,
        rx_sample_rate=args.rx_sample_rate,
        modulations=args.modulations,
        warmup_time=4.0,
    )
    df = scenario.generate_table(
        n_signals=args.n_signals,
        tx_gain=args.tx_gain,
        tx_frequency=args.tx_frequency,
        allow_overlap=args.overlapping,
        seed=args.seed,
    )
    print(df.head())

    scenario.to_csv(
        "configs/timeline.csv",
        n_signals=args.n_signals,
        allow_overlap=args.overlapping,
        seed=args.seed,
    )
    n_participants = len(args.rx_nodes) + len(args.tx_nodes)

    generate_cortexlab_scenario(
        rx_nodes=args.rx_nodes,
        tx_nodes=args.tx_nodes,
        sync_node=args.sync_node,
        duration=2 * args.duration,
        image="ghcr.io/andreaj42/cortexforge:latest",
        rx_command=(
            f'bash -lc "cortexforge forge rx '
            f"--duration {args.duration} "
            f"--frequency {args.rx_frequency} "
            f"--gain {args.rx_gain} "
            f"--sample-rate {args.rx_sample_rate} "
            f"--output-path /cortexlab/homes/{args.username}/out/ "
            f"--timeline /cortexlab/homes/{args.username}/cxf/timeline.csv "
            f'--sync-node {args.sync_node}"'
        ),
        tx_command=(
            f'bash -lc "cortexforge forge tx '
            f"--timeline /cortexlab/homes/{args.username}/cxf/timeline.csv "
            f"--sync-node {args.sync_node} "
            f"--gain {args.tx_gain} "
            f'--frequency {args.tx_frequency}"'
        ),
        sync_command=(
            'bash -lc "cortexforge forge sync '
            f'--expected-participants {n_participants}"'
        ),
        output_path="configs/scenario.yaml",
    )

    logger.info("Scenario generation completed.")


def main(argv: list[str] | None = None) -> None:
    run(parse_args(argv))


if __name__ == "__main__":
    main()
