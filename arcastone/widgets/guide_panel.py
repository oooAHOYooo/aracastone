from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextBrowser, QLineEdit, QPushButton, QHBoxLayout


class GuidePanel(QWidget):
    ask = Signal(str)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.chat = QTextBrowser()
        controls = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Ask about your vault (no generation, quotes only)…")
        self.send_btn = QPushButton("Send")
        controls.addWidget(self.input)
        controls.addWidget(self.send_btn)

        layout.addWidget(self.chat)
        layout.addLayout(controls)

        self.send_btn.clicked.connect(self._submit)
        self.input.returnPressed.connect(self._submit)

    def _submit(self) -> None:
        text = self.input.text().strip()
        if text:
            self.chat.append(f"<b>You:</b> {text}")
            self.ask.emit(text)

    def show_markdown(self, md: str) -> None:
        # Basic markdown-to-HTML: newlines to <br>, '>' quote to italic block
        # (QTextBrowser supports limited HTML; for brevity, keep simple)
        html = (
            md.replace("&", "&amp;")
              .replace("<", "&lt;")
              .replace("> ", "&gt; ")
              .replace("\n", "<br>")
        )
        self.chat.append(f"<b>Guide:</b><br>{html}")


