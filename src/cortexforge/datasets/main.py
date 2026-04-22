from pathlib import Path

from cortexforge.cli.datasets import parse_args
from cortexforge.datasets import (
    describe_dataset,
    download_dataset,
    list_registry_datasets,
    list_versions,
)
from cortexforge.utils.logger import setup_logger

logger = setup_logger()


def _format_size(size_bytes: int | None) -> str:
    if size_bytes is None:
        return "unknown size"

    value = float(size_bytes)
    units = ["B", "KB", "MB", "GB", "TB"]

    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024

    return f"{size_bytes} B"


def _render_catalog(root: Path) -> str:
    datasets = list_registry_datasets(root)

    if not datasets:
        return "No datasets available in registry."

    lines = [f"Datasets available in registry ({len(datasets)}):"]

    for dataset in datasets:
        versions = ", ".join(dataset["versions"]) or "-"
        description = dataset["description"] or "No description provided."
        lines.append(
            "\n".join(
                [
                    f"- {dataset['name']}",
                    f"  Description : {description}",
                    f"  Latest      : {dataset['latest']}",
                    f"  Versions    : {versions}",
                    f"  Size        : {_format_size(dataset['size_bytes'])}",
                    f"  Install dir : {(root / dataset['root_dir']).resolve()}",
                ]
            )
        )

    return "\n\n".join(lines)


def run(args) -> None:
    if args.datasets_command == "list":
        logger.info(_render_catalog(Path(args.root)))
        return

    if args.datasets_command == "versions":
        versions = list_versions(args.name, args.root)
        datasets = list_registry_datasets(args.root)
        description = next(
            (dataset["description"] for dataset in datasets if dataset["name"] == args.name),
            "",
        )
        lines = [
            f"Dataset: {args.name}",
            f"Description: {description or 'No description provided.'}",
            f"Versions: {', '.join(versions) if versions else '-'}",
        ]
        logger.info("\n".join(lines))
        return

    if args.datasets_command == "describe":
        manifest = describe_dataset(args.name, args.version, args.root)
        from dataclasses import asdict
        import json

        logger.info(json.dumps(asdict(manifest), indent=2, sort_keys=True))
        return

    if args.datasets_command == "download":
        manifest = download_dataset(
            args.name,
            args.root,
            version=args.version,
            force=args.force,
        )
        install_dir = (Path(args.root) / manifest.name / manifest.version).resolve()
        logger.info("Installed in: %s", install_dir)
        return

    raise ValueError(f"Unknown datasets command: {args.datasets_command}")


def main(argv: list[str] | None = None) -> None:
    run(parse_args(argv))
