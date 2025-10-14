from __future__ import annotations

from typing import List
from pathlib import Path

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QPushButton, QFileDialog

from ..core.manifest import list_documents


class ExportPanel(QWidget):
    exportRequested = Signal(list, object)  # List[str] digests, Path destination

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.docs = QListWidget()
        self.docs.setSelectionMode(self.docs.MultiSelection)
        self.refresh_btn = QPushButton("Refresh")
        self.export_btn = QPushButton("Export to Folder…")

        layout.addWidget(self.docs)
        layout.addWidget(self.refresh_btn)
        layout.addWidget(self.export_btn)

        self.refresh_btn.clicked.connect(self.refresh)
        self.export_btn.clicked.connect(self._export)
        self.refresh()

    def refresh(self) -> None:
        self.docs.clear()
        for d in list_documents():
            text = f"{d['original_filename']} — {d['pages_count']}p — {d['digest'][:8]}…"
            item = self.docs.addItem(text) if False else None
            # Workaround: QListWidget.addItem returns None; create item explicitly
            from PySide6.QtWidgets import QListWidgetItem
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, d["digest"])  # store full digest
            self.docs.addItem(item)

    def _export(self) -> None:
        items = self.docs.selectedItems()
        if not items:
            return
        digests: List[str] = []
        for item in items:
            digest = item.data(Qt.UserRole)
            if isinstance(digest, str):
                digests.append(digest)
        dest = QFileDialog.getExistingDirectory(self, "Select Destination Folder", str(Path.home()))
        if dest:
            self.exportRequested.emit(digests, Path(dest))


