from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QGridLayout

from ..core.index import index_stats


class IndexPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.title = QLabel("Repository Index")
        self.title.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.title)

        grid = QGridLayout()
        self.files = QLabel("0")
        self.chunks = QLabel("0")
        self.faiss = QLabel("0")
        self.updated = QLabel("—")
        grid.addWidget(QLabel("Files"), 0, 0)
        grid.addWidget(self.files, 0, 1)
        grid.addWidget(QLabel("Chunks"), 1, 0)
        grid.addWidget(self.chunks, 1, 1)
        grid.addWidget(QLabel("Vectors"), 2, 0)
        grid.addWidget(self.faiss, 2, 1)
        grid.addWidget(QLabel("Last Updated"), 3, 0)
        grid.addWidget(self.updated, 3, 1)
        layout.addLayout(grid)

        self.refresh_btn = QPushButton("Refresh Stats")
        layout.addWidget(self.refresh_btn)
        self.refresh_btn.clicked.connect(self.refresh)

        self.refresh()

    def refresh(self) -> None:
        s = index_stats()
        self.files.setText(str(s.get("files", 0)))
        self.chunks.setText(str(s.get("chunks", 0)))
        self.faiss.setText(str(s.get("faiss_vectors", 0)))
        ts = int(s.get("last_updated_epoch", 0) or 0)
        self.updated.setText(datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M") if ts else "—")


