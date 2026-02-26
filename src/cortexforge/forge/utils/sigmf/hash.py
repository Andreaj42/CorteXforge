from pathlib import Path
import hashlib

def _sha512_hex(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Compute SHA-512 hash of a file and return it as a hex string."""
    h = hashlib.sha512()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()
