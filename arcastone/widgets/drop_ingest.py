from __future__ import annotations

from pathlib import Path
from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QFrame, QListWidget, QListWidgetItem, QProgressBar


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

        self.file_list = QListWidget()
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.hide()

        card_layout.addWidget(self.title)
        card_layout.addWidget(self.subtitle)
        card_layout.addWidget(self.choose_btn)
        card_layout.addWidget(self.index_btn)
        card_layout.addWidget(self.file_list)
        card_layout.addWidget(self.progress)

        layout.addWidget(self.card)

        self.choose_btn.clicked.connect(self._choose_files)
        self.index_btn.clicked.connect(self.indexRequested.emit)

        self._has_files = False
        self._total = 0
        self._processed = 0

    def _choose_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(self, "Select PDF files", str(Path.home()), "PDF Files (*.pdf)")
        if files:
            paths = [Path(f) for f in files]
            self._has_files = True
            self.index_btn.setEnabled(True)
            self._append_files(paths)
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
            self._append_files(paths)
            self.filesDropped.emit(paths)

    def start_progress(self, total: int) -> None:
        self._total = max(1, int(total))
        self._processed = 0
        self.progress.setRange(0, self._total)
        self.progress.setValue(0)
        self.progress.show()

    def set_progress(self, processed: int) -> None:
        self._processed = max(0, int(processed))
        self.progress.setValue(self._processed)
        if self._total and self._processed >= self._total:
            self.progress.hide()

    def _append_files(self, paths: List[Path]) -> None:
        for p in paths:
            item = QListWidgetItem(p.name)
            item.setToolTip(str(p))
            self.file_list.addItem(item)


