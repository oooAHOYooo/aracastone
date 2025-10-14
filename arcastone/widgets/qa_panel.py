from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QTextEdit, QPushButton, QLabel


class QAPanel(QWidget):
    ask = Signal(str)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Ask a question about your vault…")
        self.ask_btn = QPushButton("Ask")
        self.answer = QTextEdit()
        self.answer.setReadOnly(True)
        self.sources = QLabel("")
        self.sources.setAlignment(Qt.AlignLeft)

        layout.addWidget(self.input)
        layout.addWidget(self.ask_btn)
        layout.addWidget(QLabel("Answer"))
        layout.addWidget(self.answer)
        layout.addWidget(QLabel("Sources"))
        layout.addWidget(self.sources)

        self.ask_btn.clicked.connect(self._submit)
        self.input.returnPressed.connect(self._submit)

    def _submit(self) -> None:
        text = self.input.text().strip()
        if text:
            self.ask.emit(text)

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


