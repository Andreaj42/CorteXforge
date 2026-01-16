import os
import argparse
from generators.cortex_scenario import generate_cortex_scenario
from generators.experiment_scenario import ExperimentScenario
from utils.loader import load_nodes
from utils.logger import setup_logger


def main():
    logger = setup_logger()
    logger.info("Starting scenario generation...")
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--duration", type=int, default=6000, help="Scenario duration in seconds"
    )
    args = parser.parse_args()

    os.makedirs("scenarios", exist_ok=True)

    try:
        nodes = load_nodes("configs/nodes.yaml")
        if len(nodes) <= 1:
            raise ValueError("At least two nodes is required.")
        logger.info(f"Loaded {len(nodes)} nodes: {nodes}")
    except Exception as e:
        logger.error(f"Failed to load nodes: {e}")
        raise

    generate_cortex_scenario(
        nodes=nodes,
        duration=args.duration,
        image="ghcr.io/andreaj42/cortexforge:latest",
        command="bash -lc \"python3 /cortexlab/homes/andrea_joly/CorteXForge/forge/main.py\"",
        description="Dataset Generator",
        output_path="scenarios/scenario.yaml",
    )

    experiment = ExperimentScenario(nodes=nodes, duration=args.duration)
    experiment.to_csv("scenarios/timeline.csv")

    logger.info("Scenario generation completed.")


if __name__ == "__main__":
    main()
