from cortexforge.cli.planner import parse_args
from cortexforge.planner.generators.cortex_scenario import generate_cortex_scenario
from cortexforge.planner.generators.experiment_scenario import ExperimentScenario
from cortexforge.utils.loader import load_nodes
from cortexforge.utils.logger import setup_logger

logger = setup_logger()


def main():
    logger.info("Starting scenario generation...")
    args = parse_args()
    nodes = load_nodes(args.nodes_path)

    generate_cortex_scenario(
        nodes=nodes,
        duration=args.duration,
        image="ghcr.io/andreaj42/cortexforge:latest",
        command='bash -lc "python3 /cortexlab/homes/andrea_joly/CorteXForge/src/cortexforge/forge/main.py"',
        description="Dataset Generator",
        output_path="configs/scenario.yaml",
    )

    experiment = ExperimentScenario(nodes=nodes, duration=args.duration)
    experiment.to_csv("configs/timeline.csv")

    logger.info("Scenario generation completed.")


if __name__ == "__main__":
    main()
