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
            f'--output-path /cortexlab/homes/{args.username}/out/"'
        ),
        tx_command=(
            f'bash -lc "cortexforge-forge tx '
            f'--timeline /cortexlab/homes/{args.username}/timeline.csv"'
        ),
        description="Dataset Generator",
        output_path="configs/scenario.yaml",
    )

    experiment = ExperimentScenario(
        nodes=nodes,
        duration=args.duration,
        rx_frequency=args.rx_frequency,
        rx_sample_rate=args.rx_sample_rate,
    )
    experiment.to_csv("configs/timeline.csv")

    logger.info("Scenario generation completed.")


if __name__ == "__main__":
    main()
