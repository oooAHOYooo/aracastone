from __future__ import annotations

from pathlib import Path
from typing import Dict
import shutil
import blake3


class StorageError(Exception):
    """Raised for storage-related failures with user-friendly messages."""


def get_repo_root() -> Path:
    """Return the repository root and ensure the `data/` directory exists.

    The repo root is inferred from this file location assuming standard layout.
    """
    root = Path(__file__).resolve().parents[2]
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return root


def ensure_subdirs() -> Dict[str, Path]:
    """Ensure storage subdirectories exist and return their paths.

    Returns keys:
    - objects: content-addressed object store root
    - manifests: directory for JSON manifests
    - tlog: directory for append-only logs
    - index: directory for FAISS and related index files
    - catalog: path to SQLite metadata database
    """
    root = get_repo_root()
    data_dir = root / "data"
    objects = data_dir / "objects"
    manifests = data_dir / "manifests"
    tlog = data_dir / "tlog"
    index = data_dir / "index"
    catalog = data_dir / "catalog.sqlite"
    for p in (objects, manifests, tlog, index):
        p.mkdir(parents=True, exist_ok=True)
    return {
        "objects": objects,
        "manifests": manifests,
        "tlog": tlog,
        "index": index,
        "catalog": catalog,
    }


def blake3_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Compute the BLAKE3 hex digest of a file by streaming its contents."""
    if not path.exists() or not path.is_file():
        raise StorageError(f"Path does not exist or is not a file: {path}")
    hasher = blake3.blake3()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def _object_path_for(hex_digest: str) -> Path:
    subs = ensure_subdirs()
    prefix = hex_digest[:2]
    return subs["objects"] / prefix / hex_digest


def store_file(path: Path) -> Dict[str, object]:
    """Store a file into the content-addressed object store.

    - Computes BLAKE3 digest
    - Stores at `objects/<b3[:2]>/<b3>`
    - Returns a dict: {"hash": "b3:<hex>", "size": int, "name": filename, "src": source_path}
    """
    digest = blake3_file(path)
    dest = _object_path_for(digest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        try:
            shutil.copy2(path, dest)
        except Exception as exc:  # pragma: no cover - filesystem dependent
            raise StorageError(f"Failed to store file: {path} -> {dest}: {exc}") from exc
    size = dest.stat().st_size
    return {"hash": f"b3:{digest}", "size": int(size), "name": path.name, "src": str(path)}


def resolve_object(hash_hex: str) -> Path:
    """Resolve a stored object (by hex or b3:<hex>) to its filesystem path.

    Raises StorageError if the object is not found.
    """
    digest = hash_hex
    if ":" in digest:
        algo, _, value = digest.partition(":")
        if algo.lower() != "b3":
            raise StorageError(f"Unsupported hash algorithm: {algo}")
        digest = value
    if len(digest) < 6:
        raise StorageError("Invalid digest string")
    path = _object_path_for(digest)
    if not path.exists():
        raise StorageError(f"Object not found for digest: {digest}")
    return path


# Backwards-compatibility helpers for existing callers
def compute_blake3(path: Path, chunk_size: int = 1024 * 1024) -> str:
    return blake3_file(path, chunk_size=chunk_size)


