from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QLabel,
    QFileDialog,
    QHBoxLayout,
)

from ..core import rag


class QAPanel(QWidget):
    ask = Signal(str)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        # LLM status and setup controls
        status_row = QHBoxLayout()
        self.llm_status = QLabel("LLM: not configured")
        self.set_model_btn = QPushButton("Set Model Path…")
        self.set_model_btn.clicked.connect(self._choose_model_dir)
        status_row.addWidget(self.llm_status)
        status_row.addStretch(1)
        status_row.addWidget(self.set_model_btn)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Ask a question about your vault…")
        self.ask_btn = QPushButton("Ask")
        self.answer = QTextEdit()
        self.answer.setReadOnly(True)
        self.sources = QLabel("")
        self.sources.setAlignment(Qt.AlignLeft)

        layout.addLayout(status_row)
        layout.addWidget(self.input)
        layout.addWidget(self.ask_btn)
        layout.addWidget(QLabel("Answer"))
        layout.addWidget(self.answer)
        layout.addWidget(QLabel("Sources"))
        layout.addWidget(self.sources)

        self.ask_btn.clicked.connect(self._submit)
        self.input.returnPressed.connect(self._submit)
        self._refresh_llm_status()

    def _submit(self) -> None:
        text = self.input.text().strip()
        if text:
            self.ask.emit(text)

    def _choose_model_dir(self) -> None:
        dirname = QFileDialog.getExistingDirectory(self, "Select local LLM model directory")
        if dirname:
            ok = rag.set_local_llm_path(dirname)
            self._refresh_llm_status()

    def _refresh_llm_status(self) -> None:
        available, path = rag.llm_status()
        if available:
            self.llm_status.setText(f"LLM: ready — {path}")
        else:
            self.llm_status.setText("LLM: not configured (uses extractive fallback)")

    def show_answer(self, text: str, files: list[str]) -> None:
        self.answer.setPlainText(text)
        if files:
            unique = []
            seen = set()
            for f in files:
                if f and f not in seen:
                    seen.add(f)
                    unique.append(f)
            self.sources.setText("\n".join(unique))
        else:
            self.sources.setText("(no sources)")


