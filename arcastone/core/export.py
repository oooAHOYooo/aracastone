from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Tuple
import shutil
import io
import json
import csv
import tarfile
import zipfile
import os
import secrets


from .storage import resolve_object, ensure_subdirs
from .manifest import get_document_entry, list_documents
from .sitemap import export_sitemap_markdown


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


# ====== Enhanced multi-format and encryption exports ======

def _selected_files(digests: Iterable[str]) -> List[Tuple[Path, str]]:
    files: List[Tuple[Path, str]] = []
    for d in digests:
        src = resolve_object(d)
        if not src.exists():
            continue
        entry = get_document_entry(d)
        name = entry.get("original_filename", f"{d}.pdf") if entry else f"{d}.pdf"
        files.append((src, name))
    return files


def _pbkdf2_key(puzzle: str, salt: bytes, length: int = 32, iterations: int = 200_000) -> bytes:
    try:
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes
    except Exception as exc:  # pragma: no cover - optional dep
        raise RuntimeError("Encryption requested but 'cryptography' is not installed.\nInstall with: pip install cryptography") from exc
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=length, salt=salt, iterations=iterations)
    return kdf.derive(puzzle.encode("utf-8"))


def encrypt_bytes(data: bytes, puzzle: str) -> bytes:
    """Encrypt bytes with AES-256-GCM using a key from the puzzle.

    Output framing: b"ARCAENC1" + 16-byte salt + 12-byte nonce + ciphertext
    """
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except Exception as exc:  # pragma: no cover - optional dep
        raise RuntimeError("Encryption requested but 'cryptography' is not installed.\nInstall with: pip install cryptography") from exc
    salt = secrets.token_bytes(16)
    key = _pbkdf2_key(puzzle, salt)
    nonce = secrets.token_bytes(12)
    aes = AESGCM(key)
    ct = aes.encrypt(nonce, data, None)
    return b"ARCAENC1" + salt + nonce + ct


def export_zip(digests: Iterable[str], out_file: Path, puzzle: str | None = None) -> Path:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for src, name in _selected_files(digests):
            zf.write(src, arcname=name)
    data = buf.getvalue()
    if puzzle:
        data = encrypt_bytes(data, puzzle)
        out_file = out_file.with_suffix(out_file.suffix + ".enc")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_bytes(data)
    return out_file


def export_tar_gz(digests: Iterable[str], out_file: Path, puzzle: str | None = None) -> Path:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for src, name in _selected_files(digests):
            tf.add(src, arcname=name)
    data = buf.getvalue()
    if puzzle:
        data = encrypt_bytes(data, puzzle)
        out_file = out_file.with_suffix(out_file.suffix + ".enc")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_bytes(data)
    return out_file


def export_metadata_json(digests: Iterable[str], out_file: Path, puzzle: str | None = None) -> Path:
    docs = []
    for d in digests:
        entry = get_document_entry(d)
        if entry:
            docs.append(entry)
    data = json.dumps({"documents": docs}, indent=2, ensure_ascii=False).encode("utf-8")
    if puzzle:
        data = encrypt_bytes(data, puzzle)
        out_file = out_file.with_suffix(out_file.suffix + ".enc")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_bytes(data)
    return out_file


def export_metadata_csv(digests: Iterable[str], out_file: Path, puzzle: str | None = None) -> Path:
    rows: List[Dict[str, object]] = []
    for d in digests:
        entry = get_document_entry(d)
        if entry:
            rows.append(entry)
    buf = io.StringIO()
    if rows:
        fieldnames = list(rows[0].keys())
        w = csv.DictWriter(buf, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    data = buf.getvalue().encode("utf-8")
    if puzzle:
        data = encrypt_bytes(data, puzzle)
        out_file = out_file.with_suffix(out_file.suffix + ".enc")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_bytes(data)
    return out_file


def export_catalog_sqlite(out_file: Path, puzzle: str | None = None) -> Path:
    subs = ensure_subdirs()
    src = subs["catalog"]
    data = src.read_bytes() if src.exists() else b""
    if puzzle:
        data = encrypt_bytes(data, puzzle)
        out_file = out_file.with_suffix(out_file.suffix + ".enc")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_bytes(data)
    return out_file


def export_sitemap_md(out_file: Path, puzzle: str | None = None) -> Path:
    # Build markdown then optionally encrypt
    md = export_sitemap_markdown()
    data = md.encode("utf-8")
    if puzzle:
        data = encrypt_bytes(data, puzzle)
        out_file = out_file.with_suffix(out_file.suffix + ".enc")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_bytes(data)
    return out_file


def export_originals(digests: Iterable[str], dest_dir: Path, puzzle: str | None = None) -> Dict[str, Path]:
    """Copy originals; if puzzle provided, copy as .enc with encrypted content."""
    dest_dir = validate_out_dir(dest_dir)
    mapping: Dict[str, Path] = {}
    for src, name in _selected_files(digests):
        dest = _unique_destination(dest_dir, name if not puzzle else name + ".enc")
        if puzzle:
            data = src.read_bytes()
            enc = encrypt_bytes(data, puzzle)
            dest.write_bytes(enc)
        else:
            shutil.copy2(src, dest)
        digest = src.name  # src is objects/<prefix>/<digest>
        mapping[digest] = dest
    return mapping


EXPORT_FORMATS = {
    "originals": "Original files",
    "zip": "ZIP archive",
    "tar.gz": "TAR.GZ archive",
    "json": "Metadata JSON",
    "csv": "Metadata CSV",
    "sqlite": "Catalog SQLite",
    "sitemap-md": "Sitemap Markdown",
}


def perform_export(digests: List[str], destination: Path, fmt: str, puzzle: str | None) -> Dict[str, str]:
    """Perform export in the given format. Returns mapping label->path string."""
    destination = destination.resolve()
    if fmt == "originals":
        res = export_originals(digests, destination, puzzle)
        return {k: str(v) for k, v in res.items()}
    # Single-file outputs
    destination.mkdir(parents=True, exist_ok=True)
    label = "output"
    if fmt == "zip":
        out = export_zip(digests, destination / "export.zip", puzzle)
    elif fmt == "tar.gz":
        out = export_tar_gz(digests, destination / "export.tar.gz", puzzle)
    elif fmt == "json":
        out = export_metadata_json(digests, destination / "export.json", puzzle)
    elif fmt == "csv":
        out = export_metadata_csv(digests, destination / "export.csv", puzzle)
    elif fmt == "sqlite":
        out = export_catalog_sqlite(destination / "catalog.sqlite", puzzle)
    elif fmt == "sitemap-md":
        out = export_sitemap_md(destination / "sitemap.md", puzzle)
    else:
        raise ValueError(f"Unknown export format: {fmt}")
    return {label: str(out)}


