from __future__ import annotations

from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QLabel



class SearchPanel(QWidget):
    querySubmitted = Signal(str)
    toggleExport = Signal(str, bool)  # digest hash, selected

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Search…")
        self.results = QListWidget()
        self.results.itemChanged.connect(self._item_changed)
        self.caption = QLabel("Enter a query to search indexed PDFs")
        self.caption.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.input)
        layout.addWidget(self.results)
        layout.addWidget(self.caption)

        self.input.returnPressed.connect(self._submit)

    def _submit(self) -> None:
        text = self.input.text().strip()
        if text:
            self.querySubmitted.emit(text)

    def show_results(self, results: List[dict]) -> None:
        self.results.clear()
        for r in results:
            digest = str(r.get("hash", ""))
            text = f"{r.get('file','')}  —  p.{r.get('page',0)}  —  {r.get('snippet','')}"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, digest)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEditable)
            item.setCheckState(Qt.Unchecked)
            self.results.addItem(item)

    def _item_changed(self, item: QListWidgetItem) -> None:
        digest = item.data(Qt.UserRole)
        if isinstance(digest, str) and digest:
            self.toggleExport.emit(digest, item.checkState() == Qt.Checked)


