from __future__ import annotations

from typing import List
from pathlib import Path

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QPushButton,
    QFileDialog,
    QAbstractItemView,
    QComboBox,
    QCheckBox,
    QLineEdit,
    QLabel,
    QMessageBox,
)

from ..core.manifest import list_documents


class ExportPanel(QWidget):
    exportRequested = Signal(list, object, str, bool, str)  # digests, dest, format, encrypt, puzzle

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.docs = QListWidget()
        self.docs.setSelectionMode(QAbstractItemView.MultiSelection)
        self.refresh_btn = QPushButton("Refresh")
        # Options row
        opts = QHBoxLayout()
        self.format = QComboBox()
        self.format.addItem("Original files", "originals")
        self.format.addItem("ZIP archive", "zip")
        self.format.addItem("TAR.GZ archive", "tar.gz")
        self.format.addItem("Metadata JSON", "json")
        self.format.addItem("Metadata CSV", "csv")
        self.format.addItem("Catalog SQLite", "sqlite")
        self.format.addItem("Sitemap Markdown", "sitemap-md")
        self.encrypt_cb = QCheckBox("Encrypt with puzzle")
        self.puzzle = QLineEdit()
        self.puzzle.setPlaceholderText("Enter your puzzle/passphrase…")
        self.puzzle.setEnabled(False)
        self.encrypt_cb.toggled.connect(self.puzzle.setEnabled)
        opts.addWidget(QLabel("Format:"))
        opts.addWidget(self.format)
        opts.addWidget(self.encrypt_cb)
        opts.addWidget(self.puzzle)
        self.export_btn = QPushButton("Export…")
        self._selected_from_search: set[str] = set()

        layout.addWidget(self.docs)
        layout.addWidget(self.refresh_btn)
        layout.addLayout(opts)
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
            # auto-select items previously toggled in Search
            if d["digest"] in self._selected_from_search:
                item.setSelected(True)

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
            fmt = str(self.format.currentData())
            enc = bool(self.encrypt_cb.isChecked())
            puzzle = self.puzzle.text().strip() if enc else ""
            if enc and not puzzle:
                QMessageBox.warning(self, "Missing Puzzle", "Please enter a puzzle/passphrase for encryption.")
                return
            self.exportRequested.emit(digests, Path(dest), fmt, enc, puzzle)

    def toggle_digest(self, digest: str, selected: bool) -> None:
        if selected:
            self._selected_from_search.add(digest)
        else:
            self._selected_from_search.discard(digest)
        # sync selection state in the list if item exists
        for i in range(self.docs.count()):
            it = self.docs.item(i)
            if it.data(Qt.UserRole) == digest:
                it.setSelected(selected)
                break


