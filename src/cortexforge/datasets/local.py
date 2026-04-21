import json
from pathlib import Path

from .hash import _sha512_hex
from .manifest import load_manifest
from .types import LocalDataset


def validate_sigmf_recording(meta_path: Path) -> None:
    if not meta_path.exists():
        raise FileNotFoundError(f"Missing SigMF metadata: {meta_path}")

    # Load JSON
    with meta_path.open("r", encoding="utf-8") as f:
        meta = json.load(f)

    if "global" not in meta:
        raise ValueError(f"Invalid SigMF meta (missing 'global'): {meta_path}")

    global_meta = meta["global"]

    # ---- core:data_file ----
    data_file = global_meta.get("core:data_file")
    if not data_file:
        raise ValueError(f"Missing 'core:data_file' in {meta_path}")

    data_path = meta_path.parent / data_file

    if not data_path.exists():
        raise FileNotFoundError(
            f"SigMF data file not found: {data_path} (referenced in {meta_path})"
        )

    # ---- SHA512 ----
    expected_hash = global_meta.get("core:sha512")

    if expected_hash:
        actual_hash = _sha512_hex(data_path)

        if actual_hash != expected_hash:
            raise ValueError(
                f"SHA512 mismatch for {data_path}\n"
                f"Expected: {expected_hash}\n"
                f"Got:      {actual_hash}"
            )


def _associated_data_path(meta_path: Path) -> Path:
    if meta_path.name.endswith(".sigmf-meta"):
        return meta_path.with_name(meta_path.name.replace(".sigmf-meta", ".sigmf-data"))
    raise ValueError(f"Expected a .sigmf-meta file, got: {meta_path}")


def load_local_dataset(
    dataset_dir: str | Path,
    split: str,
    verify: bool = True,
) -> LocalDataset:
    dataset_dir = Path(dataset_dir)
    manifest = load_manifest(dataset_dir / "manifest.json")

    if split not in manifest.splits:
        raise ValueError(f"Unknown split: {split!r}")

    recordings = []
    for rel_path in manifest.splits[split].recordings:
        meta_path = dataset_dir / rel_path

        if verify:
            validate_sigmf_recording(meta_path)

        if not meta_path.exists():
            raise FileNotFoundError(f"Missing SigMF metadata file: {meta_path}")

        data_path = _associated_data_path(meta_path)
        if not data_path.exists():
            raise FileNotFoundError(f"Missing SigMF data file: {data_path}")

        recordings.append(meta_path)

    return LocalDataset(
        name=manifest.name,
        version=manifest.version,
        split=split,
        root=dataset_dir,
        recordings=recordings,
    )
