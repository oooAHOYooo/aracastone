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
from .widgets.about_panel import AboutPanel
from .widgets.status_bar import StatusBar
from .workers.ingest_worker import IngestWorker
from .workers.index_worker import IndexWorker
from .workers.search_worker import SearchWorker
from .workers.export_worker import ExportWorker
from .workers.qa_worker import QAWorker
from .widgets.qa_panel import QAPanel
from .widgets.sitemap_panel import SitemapPanel
from .workers.retrieval_worker import RetrievalWorker
from .widgets.guide_panel import GuidePanel
from .core.config import ensure_directories


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        ensure_directories()
        self.setWindowTitle("ArcaStone")
        self.resize(1100, 720)

        # Keep references to background workers to avoid premature destruction
        self._workers: list = []

        self.sidebar = QListWidget()
        self.sidebar.addItem(QListWidgetItem("Home"))
        self.sidebar.addItem(QListWidgetItem("Search"))
        self.sidebar.addItem(QListWidgetItem("Export"))
        self.sidebar.addItem(QListWidgetItem("Sitemap"))
        self.sidebar.addItem(QListWidgetItem("Guide"))
        self.sidebar.addItem(QListWidgetItem("Q&A"))
        self.sidebar.addItem(QListWidgetItem("About"))
        self.sidebar.setFixedWidth(160)

        self.home = DropIngest()
        self.search = SearchPanel()
        self.export = ExportPanel()
        self.sitemap = SitemapPanel()
        self.guide = GuidePanel()
        self.qa = QAPanel()
        self.about = AboutPanel()

        self.stack = QWidget()
        self.stack_layout = QVBoxLayout(self.stack)
        self.stack_layout.setContentsMargins(12, 12, 12, 12)
        self.stack_layout.addWidget(self.home)
        self.stack_layout.addWidget(self.search)
        self.stack_layout.addWidget(self.export)
        self.stack_layout.addWidget(self.sitemap)
        self.stack_layout.addWidget(self.guide)
        self.stack_layout.addWidget(self.qa)
        self.stack_layout.addWidget(self.about)
        self.search.hide()
        self.export.hide()
        self.sitemap.hide()
        self.guide.hide()
        self.qa.hide()
        self.about.hide()

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
        self.search.toggleExport.connect(self._toggle_export_digest)
        self.qa.ask.connect(self._start_qa)
        self.guide.ask.connect(self._start_retrieval)
        self.sitemap.addToExport.connect(lambda d: self.export.toggle_digest(d, True))
        self.export.exportRequested.connect(self._start_export)

        self._pending_files: list[Path] = []

    def _track_worker(self, worker) -> None:
        """Track worker lifetime and remove on finish."""
        self._workers.append(worker)
        def _cleanup(w=worker):
            if w in self._workers:
                self._workers.remove(w)
        worker.finished.connect(_cleanup)

    def _switch(self, row: int) -> None:
        self.home.setVisible(row == 0)
        self.search.setVisible(row == 1)
        self.export.setVisible(row == 2)
        self.sitemap.setVisible(row == 3)
        self.guide.setVisible(row == 4)
        self.qa.setVisible(row == 5)
        self.about.setVisible(row == 6)

    def _ingest_files(self, files: list[Path]) -> None:
        self._pending_files.extend(files)
        self.status.info(f"Queued {len(self._pending_files)} file(s) for ingest…")
        worker = IngestWorker(self._pending_files.copy())
        self._pending_files.clear()

        def progress(processed: int, total: int) -> None:
            if processed == 1:
                self.status.start_progress(total)
                self.home.start_progress(total)
            self.status.set_progress(processed)
            self.home.set_progress(processed)
            self.status.info(f"Ingest {processed}/{total}")

        def done_item(res) -> None:
            self.status.info(f"Ingested {res.filename} ({res.pages}p)")

        def finished_all(_list) -> None:
            self.status.stop_progress()
            self.home.set_progress(total)
            self.status.info("Ingest finished — ready to index")
            self.home.index_btn.setEnabled(True)

        def err(msg: str) -> None:
            QMessageBox.critical(self, "Ingest Error", msg)

        worker.progress.connect(progress)
        worker.item_done.connect(done_item)
        worker.finished_all.connect(finished_all)
        worker.error.connect(err)
        self._track_worker(worker)
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
        self._track_worker(worker)
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
        self._track_worker(worker)
        worker.start()

    def _start_export(self, digests: list[str], dest: Path) -> None:
        worker = ExportWorker(digests, dest)

        def finished(mapping: dict[str, str]) -> None:
            self.status.info(f"Exported {len(mapping)} file(s)")

        def err(msg: str) -> None:
            QMessageBox.critical(self, "Export Error", msg)

        worker.finished_ok.connect(finished)
        worker.error.connect(err)
        self._track_worker(worker)
        worker.start()

    def _toggle_export_digest(self, digest: str, selected: bool) -> None:
        self.export.toggle_digest(digest, selected)

    def _start_qa(self, question: str) -> None:
        worker = QAWorker(question)

        def finished(res):
            self.qa.show_answer(res.answer, res.used_files)
            self.status.info("Q&A completed")

        def err(msg: str) -> None:
            QMessageBox.critical(self, "Q&A Error", msg)

        self.status.info("Answering…")
        self._track_worker(worker)
        worker.finished_ok.connect(finished)
        worker.error.connect(err)
        worker.start()

    def _start_retrieval(self, question: str) -> None:
        worker = RetrievalWorker(question)

        def finished(res):
            self.guide.show_markdown(res.markdown)
            self.status.info("Guide ready")

        def err(msg: str) -> None:
            QMessageBox.critical(self, "Guide Error", msg)

        self.status.info("Searching…")
        self._track_worker(worker)
        worker.finished_ok.connect(finished)
        worker.error.connect(err)
        worker.start()

    def closeEvent(self, event):  # type: ignore[override]
        # Attempt graceful shutdown of running threads
        for w in list(self._workers):
            if w.isRunning():
                w.quit()
        # Wait briefly for threads to exit
        for w in list(self._workers):
            if w.isRunning():
                w.wait(5000)
        # Force stop any stubborn threads
        for w in list(self._workers):
            if w.isRunning():
                w.terminate()
                w.wait(1000)
        return super().closeEvent(event)


