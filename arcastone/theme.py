from __future__ import annotations

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QStyle, QWidget
from pathlib import Path


# Classic Windows-esque palette (modernized)
PRIMARY_ACCENT = "#0078D4"  # Fluent blue
SECONDARY = "#5E5E5E"
WINDOW_BG = "#F0F0F0"
SURFACE = "#FFFFFF"
TEXT_PRIMARY = "#111111"
TEXT_SECONDARY = "#333333"
BORDER = "#C6C6C6"


def apply_qss(app: QApplication) -> None:
    """Apply a global QSS for a flat, classic Windows-style UI (no glass/shadows)."""
    font_stack = "Segoe UI, -apple-system, system-ui, Roboto, Ubuntu, Cantarell, Noto Sans, Arial, sans-serif"
    qss = f"""
    /* Global */
    * {{
        font-family: {font_stack};
        color: {TEXT_PRIMARY};
    }}
    QWidget {{
        background: {WINDOW_BG};
        font-size: 14px;
    }}
    /* App root */
    #AppRoot {{
        background: {WINDOW_BG};
    }}
    /* Optional header */
    #Header {{
        background: {PRIMARY_ACCENT};
        color: #ffffff;
        padding: 12px 16px;
        border-bottom: 1px solid {BORDER};
    }}
    /* Flat panels (legacy classes kept for compatibility) */
    QWidget[class="Glass"],
    QWidget[class="Card"] {{
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 4px;
    }}
    QLabel#H1 {{
        font-size: 22px;
        font-weight: 600;
        color: {TEXT_PRIMARY};
    }}
    QLabel#H2 {{
        font-size: 18px;
        font-weight: 600;
        color: {TEXT_PRIMARY};
    }}
    QLabel[secondary="true"] {{
        color: {TEXT_SECONDARY};
    }}
    QPushButton {{
        background: #E6E6E6;
        border: 1px solid {BORDER};
        border-radius: 4px;
        padding: 6px 12px;
    }}
    QPushButton:hover {{
        background: #DCDCDC;
        border-color: {BORDER};
    }}
    QPushButton:pressed {{
        background: #D0D0D0;
    }}
    QPushButton[accent="true"] {{
        background: {PRIMARY_ACCENT};
        color: #ffffff;
        border: 1px solid {PRIMARY_ACCENT};
    }}
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background: #FFFFFF;
        border: 1px solid {BORDER};
        border-radius: 3px;
        padding: 6px 8px;
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border: 1px solid {PRIMARY_ACCENT};
    }}
    /* Sidebar */
    QListWidget#Sidebar {{
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 4px;
        padding: 6px;
    }}
    QListWidget#Sidebar::item {{
        padding: 6px 8px;
        margin: 2px 4px;
        border-radius: 3px;
    }}
    QListWidget#Sidebar::item:selected {{
        background: #D9EFFF;
        color: {TEXT_PRIMARY};
    }}
    QListWidget#Sidebar::item:hover {{
        background: #EEEEEE;
    }}
    /* Splitter */
    QSplitter::handle {{
        background: #DDDDDD;
        width: 8px;
    }}
    QSplitter::handle:hover {{
        background: #CCCCCC;
    }}
    /* GroupBox */
    QGroupBox {{
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 4px;
        margin-top: 12px; /* space for title */
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 6px;
        margin-left: 8px;
        color: {TEXT_PRIMARY};
        background: {SURFACE};
    }}
    /* Scroll areas and viewports */
    QAbstractScrollArea {{
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 4px;
    }}
    QScrollArea {{
        border: none; /* container handles borders */
        background: transparent;
    }}
    QAbstractScrollArea > .viewport {{
        background: {SURFACE};
        border: none;
    }}
    /* Tables and trees */
    QHeaderView::section {{
        background: #EDEDED;
        border: 1px solid {BORDER};
        padding: 4px 6px;
    }}
    QTableWidget, QTreeWidget {{
        gridline-color: {BORDER};
        selection-background-color: #D9EFFF;
        selection-color: {TEXT_PRIMARY};
        alternate-background-color: #F7F7F7;
    }}
    /* StatusBar */
    QStatusBar {{
        background: #EAEAEA;
        border-top: 1px solid {BORDER};
        color: {TEXT_SECONDARY};
    }}
    """
    app.setStyleSheet(qss)


def card(widget: QWidget, radius: int = 4, *_args, **_kwargs) -> None:
    """Apply flat card styling with no shadow (compatibility helper)."""
    current = widget.objectName()
    if not current:
        widget.setObjectName("CardInstance")
    widget.setProperty("class", "Card")
    try:
        widget.setGraphicsEffect(None)
    except Exception:
        pass
    widget.setStyleSheet(f"border-radius: {radius}px;")


def glass(widget: QWidget, radius: int = 4, *_args, **_kwargs) -> None:
    """Apply flat panel styling (no glass/shadow)."""
    current = widget.objectName()
    if not current:
        widget.setObjectName("GlassInstance")
    widget.setProperty("class", "Glass")
    try:
        widget.setGraphicsEffect(None)
    except Exception:
        pass
    widget.setStyleSheet(f"border-radius: {radius}px;")


def get_icon(name: str) -> QIcon:
    """Return a standard Qt icon by friendly name.

    Names: "file", "folder", "open", "save", "trash", "add", "remove", "search", "refresh", "apply", "cancel".
    """
    mapping = {
        "file": QStyle.SP_FileIcon,
        "folder": QStyle.SP_DirIcon,
        "open": QStyle.SP_DialogOpenButton,
        "save": QStyle.SP_DialogSaveButton,
        "trash": QStyle.SP_TrashIcon,
        "add": QStyle.SP_DialogYesButton,
        "remove": QStyle.SP_DialogNoButton,
        "search": QStyle.SP_FileDialogContentsView,
        "refresh": QStyle.SP_BrowserReload,
        "apply": QStyle.SP_DialogApplyButton,
        "cancel": QStyle.SP_DialogCancelButton,
    }
    sp = mapping.get(name.lower(), QStyle.SP_FileIcon)
    style = QApplication.instance().style() if QApplication.instance() else None
    if style is None:
        # Fallback empty icon
        return QIcon()
    return style.standardIcon(sp)


def app_logo_icon() -> QIcon:
    """Return the branded app icon if available."""
    base = Path(__file__).resolve().parents[2]
    svg = base / "assets" / "brand" / "arcastone.svg"
    if svg.exists():
        # Qt can load SVG into QIcon via QPixmap with svg plugin available
        return QIcon(str(svg))
    return QIcon()


# Backwards compatibility: keep the old name as a no-op wrapper
def apply_dark_theme(app: QApplication) -> None:
    apply_qss(app)


