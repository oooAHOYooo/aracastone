from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QThread, Signal

from ..core.rag import generate_answer, QAResult


class QAWorker(QThread):
    finished_ok = Signal(object)  # QAResult
    error = Signal(str)

    def __init__(self, question: str, top_k: int = 5, max_new_tokens: int = 128):
        super().__init__()
        self.question = question
        self.top_k = top_k
        self.max_new_tokens = max_new_tokens

    def run(self) -> None:
        try:
            res: QAResult = generate_answer(
                self.question, top_k=self.top_k, max_new_tokens=self.max_new_tokens
            )
            self.finished_ok.emit(res)
        except Exception as exc:  # pragma: no cover
            self.error.emit(str(exc))


