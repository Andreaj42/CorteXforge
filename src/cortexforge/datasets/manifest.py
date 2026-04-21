import json
from pathlib import Path

from .types import DatasetManifest, GeneratorManifest, SplitManifest

REQUIRED_TOP_LEVEL_FIELDS = {"name", "version", "format", "generator", "splits"}
REQUIRED_GENERATOR_FIELDS = {"name", "version"}


def validate_manifest(path: str | Path) -> None:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Manifest not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    missing = REQUIRED_TOP_LEVEL_FIELDS - raw.keys()
    if missing:
        raise ValueError(f"Missing required manifest fields: {sorted(missing)}")

    generator = raw["generator"]
    if not isinstance(generator, dict):
        raise ValueError("'generator' must be a dictionary")

    missing_generator = REQUIRED_GENERATOR_FIELDS - generator.keys()
    if missing_generator:
        raise ValueError(
            f"Missing required generator fields: {sorted(missing_generator)}"
        )

    splits = raw["splits"]
    if not isinstance(splits, dict) or not splits:
        raise ValueError("'splits' must be a non-empty dictionary")

    for split_name, split_data in splits.items():
        if not isinstance(split_data, dict):
            raise ValueError(f"Split '{split_name}' must be a dictionary")

        if "recordings" not in split_data:
            raise ValueError(f"Split '{split_name}' is missing 'recordings'")

        if not isinstance(split_data["recordings"], list):
            raise ValueError(f"Split '{split_name}' field 'recordings' must be a list")


def load_manifest(path: str | Path) -> DatasetManifest:
    path = Path(path)
    validate_manifest(path)
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    splits = {
        split_name: SplitManifest(recordings=split_data["recordings"])
        for split_name, split_data in raw["splits"].items()
    }

    generator = GeneratorManifest(**raw["generator"])

    return DatasetManifest(
        name=raw["name"],
        version=raw["version"],
        description=raw.get("description", ""),
        format=raw["format"],
        generator=generator,
        splits=splits,
    )
