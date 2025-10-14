from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
from datetime import datetime, timezone
import blake3

from .config import MANIFEST_PATH, TLOG_PATH
from .storage import ensure_subdirs


ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime(ISO_FORMAT)


# New API per spec
def hash_json(obj: Any) -> str:
    """Return a BLAKE3 hex digest of the canonical JSON representation."""
    data = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return blake3.blake3(data).hexdigest()


def write_manifest(entries: List[Dict[str, Any]]) -> Path:
    """Write a manifest JSON file under data/manifests/YYYYMMDD/manifest-<hash>.json.

    Entries are simple dicts like: {"hash": "b3:...", "name": "foo.pdf", "size": 123}
    Adds created time, signer, and a simple summary.
    Returns the path to the written file.
    """
    subs = ensure_subdirs()
    manifests_dir = subs["manifests"]
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    day_dir = manifests_dir / today
    day_dir.mkdir(parents=True, exist_ok=True)

    total_size = int(sum(int(e.get("size", 0)) for e in entries))
    manifest_doc = {
        "created": _utcnow_iso(),
        "signer": "local-dev",
        "entries": entries,
        "summary": {
            "count": len(entries),
            "total_size": total_size,
        },
    }
    fname_hash = hash_json(entries)
    out_path = day_dir / f"manifest-{fname_hash}.json"
    out_path.write_text(json.dumps(manifest_doc, indent=2, ensure_ascii=False), encoding="utf-8")
    return out_path


def append_tlog(event: Dict[str, Any]) -> None:
    """Append a JSONL event with time and signer to data/tlog/events.log."""
    subs = ensure_subdirs()
    tlog_dir = subs["tlog"]
    tlog_dir.mkdir(parents=True, exist_ok=True)
    out = tlog_dir / "events.log"
    row = {
        "time": _utcnow_iso(),
        "signer": "local-dev",
        "event": event,
    }
    with out.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


# Existing API kept for compatibility with earlier flow
def _read_manifest() -> Dict[str, Any]:
    if not MANIFEST_PATH.exists():
        return {"documents": []}
    try:
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"documents": []}


def _write_manifest(data: Dict[str, Any]) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def append_tlog_legacy(event: str, data: Dict[str, Any]) -> None:
    entry = {
        "time": _utcnow_iso(),
        "signer": "local-dev",
        "event": event,
        "data": data,
    }
    TLOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TLOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


@dataclass
class DocumentEntry:
    digest: str
    original_filename: str
    size_bytes: int
    added_at: str
    pages_count: int


def add_document_entry(entry: DocumentEntry) -> None:
    manifest = _read_manifest()
    documents: List[Dict[str, Any]] = manifest.get("documents", [])
    documents = [d for d in documents if d.get("digest") != entry.digest]
    documents.append(asdict(entry))
    manifest["documents"] = documents
    _write_manifest(manifest)
    append_tlog_legacy("manifest.add_document", asdict(entry))


def get_document_entry(digest: str) -> Optional[Dict[str, Any]]:
    manifest = _read_manifest()
    for d in manifest.get("documents", []):
        if d.get("digest") == digest:
            return d
    return None


def list_documents() -> List[Dict[str, Any]]:
    manifest = _read_manifest()
    return list(manifest.get("documents", []))


