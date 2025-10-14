from __future__ import annotations

from pathlib import Path
from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QFrame


class DropIngest(QWidget):
    filesDropped = Signal(list)  # List[Path]
    indexRequested = Signal()

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)

        layout = QVBoxLayout(self)

        self.card = QFrame()
        self.card.setFrameShape(QFrame.StyledPanel)
        card_layout = QVBoxLayout(self.card)

        self.title = QLabel("Drop PDFs here")
        self.title.setAlignment(Qt.AlignCenter)
        self.subtitle = QLabel("or click to choose")
        self.subtitle.setAlignment(Qt.AlignCenter)

        self.choose_btn = QPushButton("Choose PDFs…")
        self.index_btn = QPushButton("Index Now")
        self.index_btn.setEnabled(False)

        card_layout.addWidget(self.title)
        card_layout.addWidget(self.subtitle)
        card_layout.addWidget(self.choose_btn)
        card_layout.addWidget(self.index_btn)

        layout.addWidget(self.card)

        self.choose_btn.clicked.connect(self._choose_files)
        self.index_btn.clicked.connect(self.indexRequested.emit)

        self._has_files = False

    def _choose_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(self, "Select PDF files", str(Path.home()), "PDF Files (*.pdf)")
        if files:
            paths = [Path(f) for f in files]
            self._has_files = True
            self.index_btn.setEnabled(True)
            self.filesDropped.emit(paths)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        paths: List[Path] = []
        for u in urls:
            p = Path(u.toLocalFile())
            if p.suffix.lower() == ".pdf" and p.exists():
                paths.append(p)
        if paths:
            self._has_files = True
            self.index_btn.setEnabled(True)
            self.filesDropped.emit(paths)


