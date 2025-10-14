from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List
import shutil

from .storage import resolve_object
from .manifest import get_document_entry


def _unique_destination(dest_dir: Path, desired_name: str) -> Path:
    base = Path(desired_name).stem
    ext = Path(desired_name).suffix
    candidate = dest_dir / f"{base}{ext}"
    i = 1
    while candidate.exists():
        candidate = dest_dir / f"{base}_{i}{ext}"
        i += 1
    return candidate


def export_digests(digests: Iterable[str], destination: Path) -> Dict[str, Path]:
    """Copy selected blobs to destination using original filenames.

    Returns mapping of digest to exported file path.
    """
    destination.mkdir(parents=True, exist_ok=True)
    exported: Dict[str, Path] = {}
    for digest in digests:
        src = resolve_object(digest)
        if not src.exists():
            continue
        entry = get_document_entry(digest)
        name = entry.get("original_filename", digest + ".pdf") if entry else digest + ".pdf"
        dest = _unique_destination(destination, name)
        shutil.copy2(src, dest)
        exported[digest] = dest
    return exported


# New API per spec
def validate_out_dir(out_dir: Path) -> Path:
    """Ensure the output directory exists and is writable; return its resolved path.

    Raises a ValueError with a friendly message if not writable.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    if not out_dir.is_dir():
        raise ValueError(f"Output path is not a directory: {out_dir}")
    test_file = out_dir / ".arcastone_write_test"
    try:
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
    except Exception as exc:  # pragma: no cover - FS dependent
        raise ValueError(f"Cannot write to output directory: {out_dir}: {exc}") from exc
    return out_dir.resolve()


def export_items(items: List[Dict[str, object]], out_dir: Path) -> Dict[str, int]:
    """Copy stored objects to out_dir using original filenames when known.

    items: list like [{"hash": "b3:<hex>"}, ...]
    Falls back to "<hash>.pdf" when original name is unknown.
    Returns summary {"count": n, "bytes": total}.
    """
    out_dir = validate_out_dir(out_dir)
    count = 0
    total_bytes = 0
    for item in items:
        h = str(item.get("hash", ""))
        if not h:
            continue
        try:
            src = resolve_object(h)
        except Exception:
            continue
        if not src.exists():
            continue
        # Determine name preference: manifest original_filename, then provided name, then hash.pdf
        digest = h.split(":", 1)[1] if ":" in h else h
        entry = get_document_entry(digest)
        name = (entry.get("original_filename") if entry else None) or str(item.get("name") or f"{digest}.pdf")
        dest = _unique_destination(out_dir, name)
        shutil.copy2(src, dest)
        count += 1
        try:
            total_bytes += int(dest.stat().st_size)
        except Exception:
            pass
    return {"count": count, "bytes": total_bytes}

