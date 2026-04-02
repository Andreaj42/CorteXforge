from cortexforge.cli.planner import parse_args
from cortexforge.planner.generators.cortexlab_scenario import (
    generate_cortexlab_scenario,
)
from cortexforge.planner.generators.experiment_scenario import ExperimentScenario
from cortexforge.utils.loader import load_nodes
from cortexforge.utils.logger import setup_logger

logger = setup_logger()


def main() -> None:
    logger.info("Starting scenario generation...")
    args = parse_args()
    nodes = load_nodes(args.nodes_path)

    scenario = ExperimentScenario(
        nodes=nodes,
        duration=args.duration,
        rx_sample_rate=args.rx_sample_rate,
    )

    df = scenario.generate_table(n_signals=100, allow_overlap=args.overlapping, seed=42)
    print(df.head())

    scenario.to_csv(
        "configs/timeline.csv", n_signals=100, allow_overlap=args.overlapping, seed=42
    )

    generate_cortexlab_scenario(
        nodes=nodes,
        duration=args.duration + 30,
        image="ghcr.io/andreaj42/cortexforge:latest",
        rx_command=(
            f'bash -lc "cortexforge-forge rx '
            f"--duration {args.duration} "
            f"--frequency {args.rx_frequency} "
            f"--gain {args.rx_gain} "
            f"--sample-rate {args.rx_sample_rate} "
            f"--output-path /cortexlab/homes/{args.username}/out/ "
            f'--timeline /cortexlab/homes/{args.username}/timeline.csv"'
        ),
        tx_command=(
            f'bash -lc "cortexforge-forge tx '
            f"--timeline /cortexlab/homes/{args.username}/timeline.csv "
            f"--record-node {nodes[0]} "
            f"--frequency {args.rx_frequency} "
            f'--gain {args.rx_gain}"'
        ),
        description="Dataset Generator",
        output_path="configs/scenario.yaml",
    )
    logger.info("Scenario generation completed.")


if __name__ == "__main__":
    main()
