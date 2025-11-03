from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from ..core.retrieval_chat import retrieve_only_answer


class RetrievalWorker(QThread):
    finished_ok = Signal(object)  # RetrievalAnswer
    error = Signal(str)

    def __init__(self, query: str, top_k: int = 5):
        super().__init__()
        self.query = query
        self.top_k = top_k

    def run(self) -> None:
        try:
            res = retrieve_only_answer(self.query, top_k=self.top_k)
            self.finished_ok.emit(res)
        except Exception as exc:  # pragma: no cover
            self.error.emit(str(exc))


