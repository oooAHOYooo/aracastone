from __future__ import annotations

from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QLabel



class SearchPanel(QWidget):
    querySubmitted = Signal(str)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Search…")
        self.results = QListWidget()
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
            item = QListWidgetItem(f"{r.get('file','')}  —  p.{r.get('page',0)}  —  {r.get('snippet','')}")
            self.results.addItem(item)


