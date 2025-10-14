from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from PySide6.QtCore import QThread, Signal

from ..core.index import init_index, index_pdf
from ..core.pdf import extract_text, ocr_if_needed
from ..core.manifest import list_documents
from ..core.storage import resolve_object


@dataclass
class IndexProgress:
    processed_docs: int
    total_docs: int
    last_digest: str | None = None


class IndexWorker(QThread):
    progress = Signal(object)  # IndexProgress
    finished_ok = Signal(int)  # num vectors added
    error = Signal(str)

    def __init__(self):
        super().__init__()

    def run(self) -> None:
        docs = list_documents()
        total = len(docs)
        added_total = 0
        init_index()
        try:
            for idx, d in enumerate(docs, start=1):
                digest = d.get("digest")
                filename = d.get("original_filename")
                if not digest or not filename:
                    continue
                # Resolve stored object by digest
                blob_path = resolve_object(digest)
                if not blob_path.exists():
                    continue
                meta = {
                    "name": filename,
                    "hash": f"b3:{digest}",
                    "size": int(blob_path.stat().st_size),
                    "stored_path": str(blob_path),
                }
                added = index_pdf(blob_path, meta)
                added_total += int(added)
                self.progress.emit(IndexProgress(idx, total, digest))
            self.finished_ok.emit(added_total)
        except Exception as exc:  # pragma: no cover - GUI surface
            self.error.emit(str(exc))


