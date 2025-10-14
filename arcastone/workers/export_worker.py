from __future__ import annotations

from pathlib import Path
from typing import Iterable, Dict

from PySide6.QtCore import QThread, Signal

from ..core.export import export_digests


class ExportWorker(QThread):
    progress = Signal(int, int)
    finished_ok = Signal(dict)  # Dict[str, str] digest->path
    error = Signal(str)

    def __init__(self, digests: Iterable[str], destination: Path):
        super().__init__()
        self._digests = list(digests)
        self._destination = destination

    def run(self) -> None:
        try:
            exported = export_digests(self._digests, self._destination)
            self.finished_ok.emit({k: str(v) for k, v in exported.items()})
        except Exception as exc:  # pragma: no cover
            self.error.emit(str(exc))


