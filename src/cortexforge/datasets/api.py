import hashlib
import json
import logging
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

from .local import load_local_dataset
from .manifest import load_manifest

REGISTRY_PATH = Path(__file__).with_name("registry.json")
DOWNLOAD_HEADERS = {
    "User-Agent": "CorteXForge/0.1 (+https://github.com/Andreaj42/CorteXForge)",
    "Accept": "*/*",
}
logger = logging.getLogger(__name__)


def _load_registry() -> dict:
    with REGISTRY_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def _resolve_registry_entry(name: str, version: str | None) -> tuple[str, dict]:
    registry = _load_registry()

    if name not in registry:
        raise ValueError(f"Unknown dataset: {name}")

    dataset_entry = registry[name]
    resolved_version = version or dataset_entry["latest"]
    versions = dataset_entry.get("versions", {})

    if resolved_version not in versions:
        raise ValueError(f"Unknown version '{resolved_version}' for dataset '{name}'")

    return resolved_version, versions[resolved_version]


def _sha256_hex(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def _format_size(size_bytes: int | float) -> str:
    value = float(size_bytes)
    units = ["B", "KB", "MB", "GB", "TB"]

    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024

    return f"{int(size_bytes)} B"


def _render_progress_bar(
    downloaded_bytes: int,
    total_bytes: int | None,
    width: int = 28,
) -> str:
    if not total_bytes or total_bytes <= 0:
        return f"[{'?' * width}] {_format_size(downloaded_bytes)}"

    ratio = min(downloaded_bytes / total_bytes, 1.0)
    filled = min(int(ratio * width), width)
    bar = "#" * filled + "-" * (width - filled)
    percent = int(ratio * 100)
    return (
        f"[{bar}] {percent:3d}% "
        f"({_format_size(downloaded_bytes)}/{_format_size(total_bytes)})"
    )


def _update_progress_line(message: str) -> None:
    sys.stderr.write(f"\r{message}")
    sys.stderr.flush()


def _finish_progress_line(message: str) -> None:
    sys.stderr.write(f"\r{message}\n")
    sys.stderr.flush()


def _download_file(url: str, destination: Path, chunk_size: int = 1024 * 1024) -> None:
    request = Request(url, headers=DOWNLOAD_HEADERS)
    with urlopen(request) as response, destination.open("wb") as f:
        total_bytes_header = response.headers.get("Content-Length")
        total_bytes = int(total_bytes_header) if total_bytes_header else None
        downloaded_bytes = 0
        last_logged_percent = -1
        started_at = time.monotonic()

        if total_bytes:
            _update_progress_line(
                f"Download progress: {_render_progress_bar(0, total_bytes)}"
            )
        else:
            _update_progress_line("Download progress: starting, total size unknown")

        while True:
            chunk = response.read(chunk_size)
            if not chunk:
                break

            f.write(chunk)
            downloaded_bytes += len(chunk)

            if total_bytes:
                percent = int((downloaded_bytes / total_bytes) * 100)
                if (
                    percent >= last_logged_percent + 5
                    or downloaded_bytes == total_bytes
                ):
                    elapsed = max(time.monotonic() - started_at, 1e-9)
                    speed = downloaded_bytes / elapsed
                    _update_progress_line(
                        "Download progress: "
                        f"{_render_progress_bar(downloaded_bytes, total_bytes)} "
                        f"at {_format_size(speed)}/s"
                    )
                    last_logged_percent = percent
            else:
                if (
                    downloaded_bytes == len(chunk)
                    or downloaded_bytes % (50 * chunk_size) == 0
                ):
                    elapsed = max(time.monotonic() - started_at, 1e-9)
                    speed = downloaded_bytes / elapsed
                    _update_progress_line(
                        "Download progress: "
                        f"{_format_size(downloaded_bytes)} downloaded "
                        f"at {_format_size(speed)}/s"
                    )

        elapsed = max(time.monotonic() - started_at, 1e-9)
        speed = downloaded_bytes / elapsed
        _finish_progress_line(
            "Download completed: "
            f"{_format_size(downloaded_bytes)} in {elapsed:.1f}s "
            f"at {_format_size(speed)}/s"
        )


def _extract_archive_with_tar(archive_path: Path, root: Path) -> None:
    subprocess.run(
        ["tar", "-xf", str(archive_path.resolve()), "-C", str(root.resolve())],
        check=True,
        capture_output=True,
        text=True,
    )


def _extract_archive_with_external_zstd(archive_path: Path, root: Path) -> None:
    decompressor = shutil.which("unzstd")
    command = None

    if decompressor:
        command = [decompressor, "-c", str(archive_path.resolve())]
    else:
        zstd = shutil.which("zstd")
        if zstd:
            command = [zstd, "-d", "-c", str(archive_path.resolve())]

    if command is None:
        raise RuntimeError(
            "Could not extract .tar.zst archive because no compatible zstd "
            "decompressor was found in PATH. Install 'zstd' or 'unzstd'."
        )

    decompress_process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
    )
    tar_process = subprocess.Popen(
        ["tar", "-xf", "-", "-C", str(root.resolve())],
        stdin=decompress_process.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
    )

    if decompress_process.stdout is not None:
        decompress_process.stdout.close()

    tar_stdout, tar_stderr = tar_process.communicate()
    _, decompress_stderr = decompress_process.communicate()

    if decompress_process.returncode != 0:
        stderr_text = decompress_stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(
            "Failed to decompress dataset archive with zstd. "
            f"Command: {' '.join(command)}. Error: {stderr_text or 'unknown error'}"
        )

    if tar_process.returncode != 0:
        stderr_text = tar_stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(
            "Failed to extract decompressed tar archive. "
            f"Error: {stderr_text or 'unknown error'}"
        )


def _extract_archive(archive_path: Path, root: Path) -> None:
    try:
        _extract_archive_with_tar(archive_path, root)
        return
    except subprocess.CalledProcessError as exc:
        tar_error = (exc.stderr or exc.stdout or "").strip()
        logger.warning(
            "Direct tar extraction failed for %s: %s",
            archive_path.resolve(),
            tar_error or f"exit code {exc.returncode}",
        )

    if archive_path.suffix == ".zst" and archive_path.name.endswith(".tar.zst"):
        logger.info("Retrying archive extraction with external zstd decompressor")
        _extract_archive_with_external_zstd(archive_path, root)
        return

    raise RuntimeError(f"Could not extract archive: {archive_path.resolve()}")


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


def download_dataset(
    name: str,
    root: str | Path,
    version: str | None = None,
    force: bool = False,
):
    root = Path(root)
    resolved_version, archive_entry = _resolve_registry_entry(name, version)
    dataset_dir = root / archive_entry["root_dir"]
    manifest_path = dataset_dir / "manifest.json"
    resolved_root = root.resolve()
    resolved_dataset_dir = dataset_dir.resolve()

    if manifest_path.exists() and not force:
        logger.info(
            "Dataset %s:%s already available at %s",
            name,
            resolved_version,
            resolved_dataset_dir,
        )
        return load_manifest(manifest_path)

    archive_name = archive_entry["archive_name"]
    archive_path = root / archive_name
    url = archive_entry["url"]
    expected_sha256 = archive_entry["sha256"]

    root.mkdir(parents=True, exist_ok=True)

    if dataset_dir.exists() and force:
        logger.info(
            "Removing existing dataset %s:%s from %s",
            name,
            resolved_version,
            resolved_dataset_dir,
        )
        shutil.rmtree(dataset_dir)

    logger.info("Download timeline for %s:%s", name, resolved_version)
    logger.info("1/4 Resolve target directory: %s", resolved_root)
    logger.info("2/4 Download archive from %s", url)

    try:
        _download_file(url, archive_path)

        logger.info("3/4 Verify archive checksum: %s", archive_path.resolve())
        actual_sha256 = _sha256_hex(archive_path)
        if actual_sha256 != expected_sha256:
            raise ValueError(
                "Downloaded archive checksum mismatch for "
                f"{name}:{resolved_version}. Expected {expected_sha256}, got {actual_sha256}"
            )

        logger.info("4/4 Extract archive into %s", resolved_root)
        _extract_archive(archive_path, root)
    finally:
        archive_path.unlink(missing_ok=True)

    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Dataset archive for {name}:{resolved_version} did not contain {manifest_path}"
        )

    logger.info(
        "Dataset %s:%s installed in %s",
        name,
        resolved_version,
        resolved_dataset_dir,
    )

    return load_manifest(manifest_path)


def list_datasets(root: str | Path | None = None) -> list[str]:
    del root
    registry = _load_registry()
    return sorted(registry.keys())


def list_versions(name: str, root: str | Path | None = None) -> list[str]:
    del root
    registry = _load_registry()

    if name not in registry:
        raise ValueError(f"Unknown dataset: {name}")

    versions = registry[name].get("versions", {})
    return sorted(versions.keys())


def list_datasets_with_versions(root: str | Path | None = None) -> dict[str, list[str]]:
    del root
    registry = _load_registry()
    return {
        dataset_name: sorted(dataset_entry.get("versions", {}).keys())
        for dataset_name, dataset_entry in sorted(registry.items())
    }


def list_registry_datasets(root: str | Path | None = None) -> list[dict]:
    del root
    registry = _load_registry()
    result = []

    for dataset_name, dataset_entry in sorted(registry.items()):
        latest = dataset_entry["latest"]
        latest_entry = dataset_entry.get("versions", {}).get(latest, {})
        result.append(
            {
                "name": dataset_name,
                "latest": latest,
                "versions": sorted(dataset_entry.get("versions", {}).keys()),
                "description": latest_entry.get("description", ""),
                "size_bytes": latest_entry.get("size_bytes"),
                "root_dir": latest_entry.get("root_dir"),
            }
        )

    return result
