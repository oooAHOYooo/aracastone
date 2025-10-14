from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from PySide6.QtCore import QObject, QThread, Signal

from ..core.storage import store_file
from ..core.pdf import count_pages
from ..core.manifest import DocumentEntry, add_document_entry
from ..core.manifest import _utcnow_iso  # internal but OK for worker use


@dataclass
class IngestResult:
    digest: str
    filename: str
    pages: int
    size_bytes: int


class IngestWorker(QThread):
    progress = Signal(int, int)  # processed, total
    item_done = Signal(object)  # IngestResult
    finished_all = Signal(list)  # List[IngestResult]
    error = Signal(str)

    def __init__(self, files: List[Path]):
        super().__init__()
        self.files = files

    def run(self) -> None:
        results: List[IngestResult] = []
        total = len(self.files)
        for i, path in enumerate(self.files, start=1):
            try:
                info = store_file(path)
                digest = info["hash"].split(":", 1)[1]
                pages = count_pages(path)
                add_document_entry(
                    DocumentEntry(
                        digest=digest,
                        original_filename=path.name,
                        size_bytes=int(info["size"]),
                        added_at=_utcnow_iso(),
                        pages_count=pages,
                    )
                )
                result = IngestResult(digest, path.name, pages, int(info["size"]))
                results.append(result)
                self.item_done.emit(result)
            except Exception as exc:  # pragma: no cover - GUI thread surface
                self.error.emit(f"Failed ingest {path.name}: {exc}")
            finally:
                self.progress.emit(i, total)
        self.finished_all.emit(results)


