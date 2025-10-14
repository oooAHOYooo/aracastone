from __future__ import annotations

from PySide6.QtWidgets import QStatusBar, QLabel


class StatusBar(QStatusBar):
    def __init__(self):
        super().__init__()
        self.message_label = QLabel("")
        self.addPermanentWidget(self.message_label)

    def info(self, text: str) -> None:
        self.message_label.setText(text)
        self.showMessage(text, 4000)


