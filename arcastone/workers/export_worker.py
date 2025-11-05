from __future__ import annotations

from pathlib import Path
from typing import Iterable, Dict

from PySide6.QtCore import QThread, Signal

from ..core.export import perform_export


class ExportWorker(QThread):
    progress = Signal(int, int)
    finished_ok = Signal(dict)  # Dict[str, str] digest->path
    error = Signal(str)

    def __init__(self, digests: Iterable[str], destination: Path, fmt: str, puzzle: str | None):
        super().__init__()
        self._digests = list(digests)
        self._destination = destination
        self._fmt = fmt
        self._puzzle = puzzle

    def run(self) -> None:
        try:
            exported = perform_export(self._digests, self._destination, self._fmt, self._puzzle)
            self.finished_ok.emit(exported)
        except Exception as exc:  # pragma: no cover
            self.error.emit(str(exc))


