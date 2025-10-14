from __future__ import annotations

from PySide6.QtWidgets import QStatusBar, QLabel, QProgressBar


class StatusBar(QStatusBar):
    def __init__(self):
        super().__init__()
        self.message_label = QLabel("")
        self.progress = QProgressBar()
        self.progress.setFixedWidth(160)
        self.progress.setRange(0, 100)
        self.progress.hide()
        self.addPermanentWidget(self.progress)
        self.addPermanentWidget(self.message_label)

    def info(self, text: str) -> None:
        self.message_label.setText(text)
        self.showMessage(text, 4000)

    def start_progress(self, maximum: int) -> None:
        self.progress.setRange(0, max(1, int(maximum)))
        self.progress.setValue(0)
        self.progress.show()

    def set_progress(self, value: int) -> None:
        self.progress.setValue(max(0, int(value)))

    def stop_progress(self) -> None:
        self.progress.hide()


