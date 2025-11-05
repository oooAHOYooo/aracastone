from __future__ import annotations

from pathlib import Path
from typing import List, Tuple, Dict
from datetime import datetime, timezone
import shlex
import sqlite3
import json

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QTextCursor, QPalette, QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPlainTextEdit,
    QLineEdit,
    QPushButton,
    QLabel,
)

from ..core.storage import ensure_subdirs
from ..core.manifest import list_documents, get_document_entry
from ..core.index import index_stats, search as idx_search


def _fmt_bytes(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    units = ["KB", "MB", "GB", "TB"]
    x = float(n)
    for u in units:
        x /= 1024.0
        if x < 1024.0:
            return f"{x:.2f} {u}"
    return f"{x:.2f} PB"


def _dos_time(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%m/%d/%Y  %I:%M %p")


class TerminalPanel(QWidget):
    def __init__(self):
        super().__init__()
        subs = ensure_subdirs()
        self.data_root: Path = subs["objects"].parents[0]
        self.cwd: Path = self.data_root
        self.history: List[str] = []
        self.history_idx: int = -1

        layout = QVBoxLayout(self)

        # Output area
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self._apply_dos_theme()

        # Input area
        input_row = QHBoxLayout()
        self.prompt_label = QLabel(self._prompt_text())
        self.prompt_label.setStyleSheet("color: #00ff66;")
        self.input = QLineEdit()
        self.input.returnPressed.connect(self._on_enter)
        self.input.installEventFilter(self)
        self.run_btn = QPushButton("Run")
        self.run_btn.clicked.connect(self._on_enter)
        input_row.addWidget(self.prompt_label)
        input_row.addWidget(self.input)
        input_row.addWidget(self.run_btn)

        # After creating input and prompt, apply monospaced font
        self._set_mono_font()

        layout.addWidget(self.output)
        layout.addLayout(input_row)

        self._write_line("Microsoft MS-DOS-like ArcaShell [Version 1.0]")
        self._write_line("(c) ArcaStone. All rights reserved.")
        self._write_line("")
        self._write_line("Type HELP for a list of commands.")

    def _apply_dos_theme(self) -> None:
        pal = self.output.palette()
        pal.setColor(QPalette.Base, QColor(0, 0, 0))
        pal.setColor(QPalette.Text, QColor(240, 240, 240))
        self.output.setPalette(pal)
        self.output.setStyleSheet("background-color: #000000; color: #f0f0f0;")

    def _set_mono_font(self) -> None:
        f = QFont("Courier New")
        f.setStyleHint(QFont.Monospace)
        f.setFixedPitch(True)
        f.setPointSize(11)
        self.output.setFont(f)
        self.input.setFont(f)
        self.prompt_label.setFont(f)

    def _prompt_text(self) -> str:
        rel = str(self.cwd.relative_to(self.data_root)).replace("/", "\\") if self.cwd != self.data_root else ""
        return f"C:\\{rel}> " if rel else "C:\\> "

    def _write(self, text: str) -> None:
        self.output.moveCursor(QTextCursor.End)
        self.output.insertPlainText(text)
        self.output.moveCursor(QTextCursor.End)

    def _write_line(self, text: str) -> None:
        self._write(text + "\n")

    def _set_prompt(self) -> None:
        self.prompt_label.setText(self._prompt_text())

    def eventFilter(self, obj, event):  # noqa: N802
        # Up/Down for history navigation
        from PySide6.QtCore import QEvent
        if obj is self.input and event.type() == QEvent.KeyPress:
            key = event.key()
            if key == Qt.Key_Up:
                if self.history:
                    self.history_idx = max(0, self.history_idx - 1) if self.history_idx >= 0 else len(self.history) - 1
                    self.input.setText(self.history[self.history_idx])
                    self.input.setCursorPosition(len(self.input.text()))
                    return True
            if key == Qt.Key_Down:
                if self.history:
                    if self.history_idx < len(self.history) - 1:
                        self.history_idx += 1
                        self.input.setText(self.history[self.history_idx])
                    else:
                        self.history_idx = -1
                        self.input.clear()
                    self.input.setCursorPosition(len(self.input.text()))
                    return True
        return super().eventFilter(obj, event)

    def _on_enter(self) -> None:
        cmdline = self.input.text().strip()
        self.input.clear()
        if not cmdline:
            return
        self._write_line(self._prompt_text() + cmdline)
        self.history.append(cmdline)
        self.history_idx = -1
        self._execute(cmdline)

    def _execute(self, cmdline: str) -> None:
        try:
            parts = shlex.split(cmdline)
        except ValueError:
            parts = cmdline.split()
        if not parts:
            return
        cmd = parts[0].lower()
        args = parts[1:]
        handler = getattr(self, f"_cmd_{cmd}", None)
        if handler is None:
            self._write_line(f"'{cmd}' is not recognized as an internal or external command.")
            return
        try:
            handler(args)
        except Exception as exc:
            self._write_line(f"Error: {exc}")
        finally:
            self._set_prompt()

    # Commands
    def _cmd_help(self, args: List[str]) -> None:
        self._write_line("Available commands:")
        self._write_line("  HELP                 Show this help")
        self._write_line("  CLS                  Clear the screen")
        self._write_line("  VER                  Show version")
        self._write_line("  DIR [path]           List directory contents under DATA")
        self._write_line("  CD [path]            Change directory (use \\ for root)")
        self._write_line("  PWD                  Show current directory")
        self._write_line("  STATS                Show index/catalog stats")
        self._write_line("  DOCS [filter]        List documents from manifest")
        self._write_line("  SHOW <digest>        Show a document by digest")
        self._write_line("  SEARCH \"q\" [k]       Search indexed chunks")
        self._write_line("  TLOG [n]             Show last n activity events")

    def _cmd_cls(self, args: List[str]) -> None:
        self.output.clear()

    def _cmd_clear(self, args: List[str]) -> None:
        self._cmd_cls(args)

    def _cmd_ver(self, args: List[str]) -> None:
        self._write_line("ArcaShell version 1.0 (MS-DOS style)")

    def _resolve_path(self, arg: str | None) -> Path:
        if not arg or arg.strip() == "":
            return self.cwd
        p = arg.replace("\\", "/")
        if p.startswith("/"):
            # absolute within data root
            return (self.data_root / p.lstrip("/")).resolve()
        if p == "\\":
            return self.data_root
        return (self.cwd / p).resolve()

    def _cmd_dir(self, args: List[str]) -> None:
        target = self._resolve_path(args[0] if args else None)
        try:
            target.relative_to(self.data_root)
        except Exception:
            self._write_line("Access denied.")
            return
        if not target.exists():
            self._write_line("File Not Found")
            return
        if target.is_file():
            stat = target.stat()
            self._write_line(f"{_dos_time(stat.st_mtime)}           {_fmt_bytes(stat.st_size):>12} {target.name}")
            return
        self._write_line(f" Volume in drive C has no label.")
        rel_path = str(target.relative_to(self.data_root)).replace("/", "\\") if target != self.data_root else ""
        self._write_line(f" Directory of C:\\{rel_path}")
        self._write_line("")
        files = 0
        bytes_total = 0
        dirs = 0
        for entry in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            st = entry.stat()
            t = _dos_time(st.st_mtime)
            if entry.is_dir():
                self._write_line(f"{t}    <DIR>          {entry.name}")
                dirs += 1
            else:
                self._write_line(f"{t}           {_fmt_bytes(st.st_size):>12} {entry.name}")
                files += 1
                bytes_total += st.st_size
        self._write_line(f"             {files} File(s)      {_fmt_bytes(bytes_total)}")
        self._write_line(f"             {dirs} Dir(s)")

    def _cmd_cd(self, args: List[str]) -> None:
        target = self._resolve_path(args[0] if args else "")
        try:
            target.relative_to(self.data_root)
        except Exception:
            self._write_line("Access denied.")
            return
        if not target.exists() or not target.is_dir():
            self._write_line("The system cannot find the path specified.")
            return
        self.cwd = target

    def _cmd_pwd(self, args: List[str]) -> None:
        self._write_line(self._prompt_text().strip())

    def _cmd_stats(self, args: List[str]) -> None:
        s = index_stats()
        self._write_line("Index/Catalog Stats:")
        self._write_line(f"  Files:         {s.get('files', 0)}")
        self._write_line(f"  Chunks:        {s.get('chunks', 0)}")
        self._write_line(f"  FAISS Vectors: {s.get('faiss_vectors', 0)}")
        self._write_line(f"  Last Updated:  {datetime.fromtimestamp(s.get('last_updated_epoch', 0)).strftime('%Y-%m-%d %H:%M:%S') if s.get('last_updated_epoch', 0) else '—'}")

    def _cmd_docs(self, args: List[str]) -> None:
        docs = list_documents()
        filt = args[0].lower() if args else None
        self._write_line("Documents:")
        for d in docs:
            name = str(d.get("original_filename", ""))
            digest = str(d.get("digest", ""))
            pages = int(d.get("pages_count", 0))
            sizeb = int(d.get("size_bytes", 0))
            if filt and filt not in name.lower() and (filt not in digest.lower()):
                continue
            self._write_line(f"  {name}  ({pages}p, {_fmt_bytes(sizeb)})  [{digest}]")

    def _cmd_show(self, args: List[str]) -> None:
        if not args:
            self._write_line("Usage: SHOW <digest>")
            return
        d = get_document_entry(args[0])
        if not d:
            self._write_line("Not found.")
            return
        self._write_line(json.dumps(d, indent=2, ensure_ascii=False))

    def _cmd_search(self, args: List[str]) -> None:
        if not args:
            self._write_line("Usage: SEARCH \"query\" [k]")
            return
        query = args[0]
        try:
            k = int(args[1]) if len(args) > 1 else 5
        except Exception:
            k = 5
        results = idx_search(query, top_k=max(1, min(10, k)))
        if not results:
            self._write_line("No results.")
            return
        for i, r in enumerate(results, start=1):
            score = f"{float(r.get('score', 0.0)):.3f}"
            file = str(r.get("file", ""))
            page = int(r.get("page", 0))
            snip = str(r.get("snippet", ""))
            self._write_line(f"{i}. [{score}] {file} (p.{page}) - {snip}")

    def _cmd_tlog(self, args: List[str]) -> None:
        try:
            n = int(args[0]) if args else 50
        except Exception:
            n = 50
        subs = ensure_subdirs()
        rows: List[Tuple[str, str]] = []
        # New events.log
        events = subs["tlog"] / "events.log"
        if events.exists():
            try:
                with events.open("r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            obj = json.loads(line)
                            t = obj.get("time", "")
                            ev = obj.get("event", {})
                            rows.append((t, json.dumps(ev, ensure_ascii=False)))
                        except Exception:
                            pass
            except Exception:
                pass
        # Legacy
        legacy = subs["tlog"].parents[0] / "tlog.jsonl"
        if legacy.exists():
            try:
                with legacy.open("r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            obj = json.loads(line)
                            t = obj.get("time", "")
                            rows.append((t, json.dumps(obj, ensure_ascii=False)))
                        except Exception:
                            pass
            except Exception:
                pass
        rows = rows[-n:]
        if not rows:
            self._write_line("No activity.")
            return
        for t, e in rows:
            self._write_line(f"{t}  {e}")


