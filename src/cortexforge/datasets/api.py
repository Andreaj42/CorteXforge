from pathlib import Path

from .local import load_local_dataset
from .manifest import load_manifest


def load_dataset(
    name: str,
    version: str,
    split: str,
    root: str | Path,
    verify: bool = True,
):
    dataset_dir = Path(root) / name / version
    return load_local_dataset(dataset_dir=dataset_dir, split=split, verify=verify)


def describe_dataset(
    name: str,
    version: str,
    root: str | Path,
):
    dataset_dir = Path(root) / name / version
    return load_manifest(dataset_dir / "manifest.json")


def list_datasets(root: str | Path) -> list[str]:
    root = Path(root)

    if not root.exists():
        return []

    datasets = []

    for dataset_dir in root.iterdir():
        if not dataset_dir.is_dir():
            continue

        has_valid_version = any(
            (version_dir / "manifest.json").exists()
            for version_dir in dataset_dir.iterdir()
            if version_dir.is_dir()
        )

        if has_valid_version:
            datasets.append(dataset_dir.name)

    return sorted(datasets)


def list_versions(name: str, root: str | Path) -> list[str]:
    root = Path(root)
    dataset_dir = root / name

    if not dataset_dir.exists() or not dataset_dir.is_dir():
        return []

    versions = [
        version_dir.name
        for version_dir in dataset_dir.iterdir()
        if version_dir.is_dir() and (version_dir / "manifest.json").exists()
    ]

    return sorted(versions)


def list_datasets_with_versions(root: str | Path) -> dict[str, list[str]]:
    root = Path(root)

    if not root.exists():
        return {}

    result = {}

    for dataset_dir in root.iterdir():
        if not dataset_dir.is_dir():
            continue

        versions = [
            version_dir.name
            for version_dir in dataset_dir.iterdir()
            if (version_dir / "manifest.json").exists()
        ]

        if versions:
            result[dataset_dir.name] = sorted(versions)

    return result
