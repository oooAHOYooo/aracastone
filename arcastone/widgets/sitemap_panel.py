from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QFileDialog,
)

from ..core.sitemap import build_sitemap, export_sitemap_markdown


class SitemapPanel(QWidget):
    addToExport = Signal(str)  # digest

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        controls = QHBoxLayout()
        self.filter = QLineEdit()
        self.filter.setPlaceholderText("Filter by filename…")
        self.refresh_btn = QPushButton("Refresh")
        self.export_md_btn = QPushButton("Export Markdown…")
        controls.addWidget(self.filter)
        controls.addWidget(self.refresh_btn)
        controls.addWidget(self.export_md_btn)
        layout.addLayout(controls)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Document", "Pages", "Digest"])
        layout.addWidget(self.tree)

        self.refresh_btn.clicked.connect(self.refresh)
        self.filter.textChanged.connect(self._apply_filter)
        self.export_md_btn.clicked.connect(self._export_md)
        self.tree.itemDoubleClicked.connect(self._add_selected)

        self.refresh()

    def refresh(self) -> None:
        self.tree.clear()
        for node in build_sitemap():
            it = QTreeWidgetItem([node.title, str(node.pages), node.digest])
            self.tree.addTopLevelItem(it)
        self.tree.resizeColumnToContents(0)
        self._apply_filter()

    def _apply_filter(self) -> None:
        text = self.filter.text().strip().lower()
        for i in range(self.tree.topLevelItemCount()):
            it = self.tree.topLevelItem(i)
            visible = text in it.text(0).lower() if text else True
            it.setHidden(not visible)

    def _add_selected(self) -> None:
        it = self.tree.currentItem()
        if not it:
            return
        digest = it.text(2)
        if digest:
            self.addToExport.emit(digest)

    def _export_md(self) -> None:
        md = export_sitemap_markdown()
        path, _ = QFileDialog.getSaveFileName(self, "Export Sitemap Markdown", "sitemap.md", "Markdown (*.md)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(md)


