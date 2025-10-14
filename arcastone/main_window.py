from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QMessageBox,
)

from .widgets.drop_ingest import DropIngest
from .widgets.search_panel import SearchPanel
from .widgets.export_panel import ExportPanel
from .widgets.status_bar import StatusBar
from .workers.ingest_worker import IngestWorker
from .workers.index_worker import IndexWorker
from .workers.search_worker import SearchWorker
from .workers.export_worker import ExportWorker
from .core.config import ensure_directories


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        ensure_directories()
        self.setWindowTitle("ArcaStone")
        self.resize(1100, 720)

        self.sidebar = QListWidget()
        self.sidebar.addItem(QListWidgetItem("Home"))
        self.sidebar.addItem(QListWidgetItem("Search"))
        self.sidebar.addItem(QListWidgetItem("Export"))
        self.sidebar.setFixedWidth(160)

        self.home = DropIngest()
        self.search = SearchPanel()
        self.export = ExportPanel()

        self.stack = QWidget()
        self.stack_layout = QVBoxLayout(self.stack)
        self.stack_layout.setContentsMargins(12, 12, 12, 12)
        self.stack_layout.addWidget(self.home)
        self.stack_layout.addWidget(self.search)
        self.stack_layout.addWidget(self.export)
        self.search.hide()
        self.export.hide()

        split = QSplitter()
        split.addWidget(self.sidebar)
        split.addWidget(self.stack)
        split.setStretchFactor(1, 1)

        self.status = StatusBar()
        self.setStatusBar(self.status)
        container = QWidget()
        root = QVBoxLayout(container)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(split)
        self.setCentralWidget(container)

        # Signals
        self.sidebar.currentRowChanged.connect(self._switch)
        self.home.filesDropped.connect(self._ingest_files)
        self.home.indexRequested.connect(self._start_index)
        self.search.querySubmitted.connect(self._start_search)
        self.export.exportRequested.connect(self._start_export)

        self._pending_files: list[Path] = []

    def _switch(self, row: int) -> None:
        self.home.setVisible(row == 0)
        self.search.setVisible(row == 1)
        self.export.setVisible(row == 2)

    def _ingest_files(self, files: list[Path]) -> None:
        self._pending_files.extend(files)
        self.status.info(f"Queued {len(self._pending_files)} file(s) for ingest…")
        worker = IngestWorker(self._pending_files.copy())
        self._pending_files.clear()

        def progress(processed: int, total: int) -> None:
            self.status.info(f"Ingest {processed}/{total}")

        def done_item(res) -> None:
            self.status.info(f"Ingested {res.filename} ({res.pages}p)")

        def finished_all(_list) -> None:
            self.status.info("Ingest finished — ready to index")
            self.home.index_btn.setEnabled(True)

        def err(msg: str) -> None:
            QMessageBox.critical(self, "Ingest Error", msg)

        worker.progress.connect(progress)
        worker.item_done.connect(done_item)
        worker.finished_all.connect(finished_all)
        worker.error.connect(err)
        worker.start()

    def _start_index(self) -> None:
        worker = IndexWorker()

        def progress(p):
            self.status.info(f"Indexing {p.processed_docs}/{p.total_docs}")

        def finished(n: int) -> None:
            self.status.info(f"Index built with {n} vectors")
            self.sidebar.setCurrentRow(1)

        def err(msg: str) -> None:
            QMessageBox.critical(self, "Index Error", msg)

        worker.progress.connect(progress)
        worker.finished_ok.connect(finished)
        worker.error.connect(err)
        worker.start()

    def _start_search(self, query: str) -> None:
        worker = SearchWorker(query)

        def results(items):
            self.search.show_results(items)
            self.status.info(f"Found {len(items)} results")

        def err(msg: str) -> None:
            QMessageBox.critical(self, "Search Error", msg)

        worker.results.connect(results)
        worker.error.connect(err)
        worker.start()

    def _start_export(self, digests: list[str], dest: Path) -> None:
        worker = ExportWorker(digests, dest)

        def finished(mapping: dict[str, str]) -> None:
            self.status.info(f"Exported {len(mapping)} file(s)")

        def err(msg: str) -> None:
            QMessageBox.critical(self, "Export Error", msg)

        worker.finished_ok.connect(finished)
        worker.error.connect(err)
        worker.start()


