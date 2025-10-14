from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from ..core.index import search as core_search


class SearchWorker(QThread):
    results = Signal(list)  # List[dict]
    error = Signal(str)

    def __init__(self, query: str, k: int = 10):
        super().__init__()
        self.query = query
        self.k = k

    def run(self) -> None:
        try:
            res = core_search(self.query, self.k)
            self.results.emit(res)
        except Exception as exc:  # pragma: no cover
            self.error.emit(str(exc))


