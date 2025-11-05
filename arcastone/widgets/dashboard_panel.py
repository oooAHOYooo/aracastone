from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Tuple
import json
import sqlite3
import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QGridLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QTreeWidget,
    QTreeWidgetItem,
)

from ..core.storage import ensure_subdirs
from ..core.manifest import list_documents
from ..core.index import index_stats


def _parse_iso(ts: str) -> datetime:
    try:
        # Supports ISO with trailing Z
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
    except Exception:
        try:
            return datetime.fromisoformat(ts)
        except Exception:
            return datetime.fromtimestamp(0, tz=timezone.utc)


class DashboardPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Controls
        controls = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh)
        controls.addStretch(1)
        controls.addWidget(self.refresh_btn)
        layout.addLayout(controls)

        # Summary group
        summary_group = QGroupBox("Daily Dashboard")
        summary_grid = QGridLayout(summary_group)
        summary_grid.setContentsMargins(10, 8, 10, 10)
        summary_grid.setHorizontalSpacing(12)
        summary_grid.setVerticalSpacing(6)
        self.total_docs = QLabel("0")
        self.today_docs = QLabel("0")
        self.total_pages = QLabel("0")
        self.today_pages = QLabel("0")
        self.total_bytes = QLabel("0")
        self.today_bytes = QLabel("0")
        self.index_files = QLabel("0")
        self.index_chunks = QLabel("0")
        self.index_vectors = QLabel("0")

        row = 0
        summary_grid.addWidget(QLabel("Total Documents:"), row, 0)
        summary_grid.addWidget(self.total_docs, row, 1)
        summary_grid.addWidget(QLabel("Today Documents:"), row, 2)
        summary_grid.addWidget(self.today_docs, row, 3)
        row += 1
        summary_grid.addWidget(QLabel("Total Pages:"), row, 0)
        summary_grid.addWidget(self.total_pages, row, 1)
        summary_grid.addWidget(QLabel("Today Pages:"), row, 2)
        summary_grid.addWidget(self.today_pages, row, 3)
        row += 1
        summary_grid.addWidget(QLabel("Total Bytes:"), row, 0)
        summary_grid.addWidget(self.total_bytes, row, 1)
        summary_grid.addWidget(QLabel("Today Bytes:"), row, 2)
        summary_grid.addWidget(self.today_bytes, row, 3)
        row += 1
        summary_grid.addWidget(QLabel("Catalog Files:"), row, 0)
        summary_grid.addWidget(self.index_files, row, 1)
        summary_grid.addWidget(QLabel("Indexed Chunks:"), row, 2)
        summary_grid.addWidget(self.index_chunks, row, 3)
        row += 1
        summary_grid.addWidget(QLabel("FAISS Vectors:"), row, 0)
        summary_grid.addWidget(self.index_vectors, row, 1)
        layout.addWidget(summary_group)

        # Activity history
        act_group = QGroupBox("Activity History")
        act_layout = QVBoxLayout(act_group)
        act_layout.setContentsMargins(10, 8, 10, 10)
        act_layout.setSpacing(8)
        self.activity_table = QTableWidget(0, 3)
        self.activity_table.setHorizontalHeaderLabels(["Time", "Event", "Details"])
        self.activity_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.activity_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.activity_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.activity_table.setWordWrap(True)
        self.activity_table.setAlternatingRowColors(True)
        act_layout.addWidget(self.activity_table)
        layout.addWidget(act_group)

        # Data positions
        pos_group = QGroupBox("Data Positions")
        pos_layout = QVBoxLayout(pos_group)
        pos_layout.setContentsMargins(10, 8, 10, 10)
        pos_layout.setSpacing(8)
        self.pos_tree = QTreeWidget()
        self.pos_tree.setHeaderLabels(["Item", "Value"]) 
        self.pos_tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.pos_tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        pos_layout.addWidget(self.pos_tree)
        layout.addWidget(pos_group)

        layout.addStretch(1)

        self.refresh()

    def refresh(self) -> None:
        self._load_summary()
        self._load_activity()
        self._load_positions()

    def _load_summary(self) -> None:
        docs = list_documents()
        total_docs = len(docs)
        total_pages = sum(int(d.get("pages_count", 0)) for d in docs)
        total_bytes = sum(int(d.get("size_bytes", 0)) for d in docs)
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_docs = 0
        today_pages = 0
        today_bytes = 0
        for d in docs:
            ts = str(d.get("added_at", ""))
            if ts.startswith(today_str):
                today_docs += 1
                today_pages += int(d.get("pages_count", 0))
                today_bytes += int(d.get("size_bytes", 0))

        idx = index_stats()
        self.total_docs.setText(str(total_docs))
        self.today_docs.setText(str(today_docs))
        self.total_pages.setText(str(total_pages))
        self.today_pages.setText(str(today_pages))
        self.total_bytes.setText(self._fmt_bytes(total_bytes))
        self.today_bytes.setText(self._fmt_bytes(today_bytes))
        self.index_files.setText(str(idx.get("files", 0)))
        self.index_chunks.setText(str(idx.get("chunks", 0)))
        self.index_vectors.setText(str(idx.get("faiss_vectors", 0)))

    def _iter_tlog_rows(self) -> List[Tuple[datetime, str, str]]:
        subs = ensure_subdirs()
        rows: List[Tuple[datetime, str, str]] = []
        # New events.log
        events_log = subs["tlog"] / "events.log"
        if events_log.exists():
            try:
                with events_log.open("r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                            ts = _parse_iso(str(obj.get("time", "")))
                            ev = obj.get("event", {})
                            if isinstance(ev, dict):
                                name = str(ev.get("type", "event"))
                                details = json.dumps(ev, ensure_ascii=False)
                            else:
                                name = "event"
                                details = str(ev)
                            rows.append((ts, name, details))
                        except Exception:
                            pass
            except Exception:
                pass
        # Legacy tlog.jsonl
        legacy = Path(os.path.dirname(subs["tlog"])) / "tlog.jsonl"
        if legacy.exists():
            try:
                with legacy.open("r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                            ts = _parse_iso(str(obj.get("time", "")))
                            name = str(obj.get("event", ""))
                            details = json.dumps(obj.get("data", {}), ensure_ascii=False)
                            rows.append((ts, name, details))
                        except Exception:
                            pass
            except Exception:
                pass
        rows.sort(key=lambda r: r[0], reverse=True)
        return rows

    def _load_activity(self) -> None:
        rows = self._iter_tlog_rows()
        # Limit to recent 200
        rows = rows[:200]
        self.activity_table.setRowCount(len(rows))
        for i, (ts, name, details) in enumerate(rows):
            self.activity_table.setItem(i, 0, QTableWidgetItem(ts.strftime("%Y-%m-%d %H:%M:%S")))
            self.activity_table.setItem(i, 1, QTableWidgetItem(name))
            self.activity_table.setItem(i, 2, QTableWidgetItem(details))
        self.activity_table.resizeRowsToContents()

    def _load_positions(self) -> None:
        self.pos_tree.clear()
        subs = ensure_subdirs()
        data_dir = subs["objects"].parents[0]

        # Root paths
        root_node = QTreeWidgetItem(["Data Root", str(data_dir)])
        self.pos_tree.addTopLevelItem(root_node)
        self.pos_tree.addTopLevelItem(QTreeWidgetItem(["Objects Dir", str(subs["objects"])]))
        self.pos_tree.addTopLevelItem(QTreeWidgetItem(["Index Dir", str(subs["index"])]))
        self.pos_tree.addTopLevelItem(QTreeWidgetItem(["Catalog DB", str(subs["catalog"])]))

        # Index files info
        idx = index_stats()
        faiss_path = (subs["index"] / "faiss.index")
        faiss_size = faiss_path.stat().st_size if faiss_path.exists() else 0
        idx_node = QTreeWidgetItem(["FAISS Index", str(faiss_path)])
        idx_node.addChild(QTreeWidgetItem(["Vectors", str(idx.get("faiss_vectors", 0))]))
        idx_node.addChild(QTreeWidgetItem(["File Size", self._fmt_bytes(faiss_size)]))
        self.pos_tree.addTopLevelItem(idx_node)

        # Catalog: list files (limited)
        files_node = QTreeWidgetItem(["Catalog Files (latest 200)", ""]) 
        self.pos_tree.addTopLevelItem(files_node)
        try:
            conn = sqlite3.connect(str(subs["catalog"]))
            cur = conn.cursor()
            cur.execute("SELECT name, size, stored_path FROM files ORDER BY id DESC LIMIT 200")
            for name, size, stored in cur.fetchall():
                stored_str = str(stored)
                leaf = QTreeWidgetItem([str(name), f"{self._fmt_bytes(int(size))} @ {stored_str}"])
                files_node.addChild(leaf)
        except Exception:
            pass
        finally:
            try:
                conn.close()
            except Exception:
                pass

        for i in range(self.pos_tree.topLevelItemCount()):
            self.pos_tree.topLevelItem(i).setExpanded(True)

    def _fmt_bytes(self, n: int) -> str:
        if n < 1024:
            return f"{n} B"
        units = ["KB", "MB", "GB", "TB"]
        x = float(n)
        for u in units:
            x /= 1024.0
            if x < 1024.0:
                return f"{x:.2f} {u}"
        return f"{x:.2f} PB"



