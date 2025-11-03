from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QStyle, QWidget, QGraphicsDropShadowEffect
from PySide6.QtGui import QPixmap
from pathlib import Path


# Palette tokens
PRIMARY_ACCENT = "#FF2D55"
SECONDARY = "#8E8E93"
SURFACE = "#F7F7FA"
TEXT_PRIMARY = "#1C1C1E"
TEXT_SECONDARY = "#4A4A4A"
BORDER = "#E6E6EE"

# Glassmorphism tokens
GLASS_BG = "rgba(255,255,255,0.10)"
GLASS_BG_INPUT = "rgba(255,255,255,0.12)"
GLASS_BORDER = "rgba(255,255,255,0.35)"
GLASS_BORDER_SOFT = "rgba(255,255,255,0.18)"
GLASS_SHADOW = "rgba(0,0,0,0.20)"


def apply_qss(app: QApplication) -> None:
    """Apply a global QSS for a soft, modern liquid-glass UI."""
    font_stack = "SF Pro Text, -apple-system, system-ui, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial, sans-serif"
    qss = f"""
    /* Global */
    * {{
        font-family: {font_stack};
        color: {TEXT_PRIMARY};
    }}
    QWidget {{
        background: transparent;
        font-size: 14px;
    }}
    /* App canvas gradient (set via objectName=AppRoot) */
    #AppRoot {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #F5F7FF, stop:1 #FDEBFF);
    }}
    /* Header gradient (opt-in via objectName=Header) */
    #Header {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FF2D55, stop:1 #AF52DE);
        padding: 16px;
        border-bottom: 1px solid {GLASS_BORDER_SOFT};
    }}
    /* Glass containers (use glass(widget) helper for shadow) */
    QWidget[class="Glass"] {{
        background: {GLASS_BG};
        border: 1px solid {GLASS_BORDER};
        border-radius: 18px;
    }}
    /* Cards (legacy helper) */
    QWidget[class="Card"] {{
        background: rgba(255,255,255,0.85);
        border: 1px solid {BORDER};
        border-radius: 18px;
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
        color: {SECONDARY};
    }}
    QPushButton {{
        background: {GLASS_BG_INPUT};
        border: 1px solid {GLASS_BORDER_SOFT};
        border-radius: 10px;
        padding: 8px 14px;
    }}
    QPushButton:hover {{
        background: rgba(255,255,255,0.18);
        border-color: {PRIMARY_ACCENT};
    }}
    QPushButton:pressed {{
        background: rgba(255,255,255,0.22);
    }}
    QPushButton[accent="true"] {{
        background: {PRIMARY_ACCENT};
        color: white;
        border: 1px solid {PRIMARY_ACCENT};
    }}
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background: {GLASS_BG_INPUT};
        border: 1px solid {GLASS_BORDER_SOFT};
        border-radius: 10px;
        padding: 8px 10px;
    }}
    /* Sidebar */
    QListWidget#Sidebar {{
        background: {GLASS_BG};
        border: 1px solid {GLASS_BORDER};
        border-radius: 14px;
        padding: 6px;
    }}
    QListWidget#Sidebar::item {{
        padding: 8px 10px;
        margin: 2px 4px;
        border-radius: 8px;
    }}
    QListWidget#Sidebar::item:selected {{
        background: rgba(255,255,255,0.30);
        color: {TEXT_PRIMARY};
    }}
    QListWidget#Sidebar::item:hover {{
        background: rgba(255,255,255,0.20);
    }}
    /* Splitter */
    QSplitter::handle {{
        background: transparent;
        width: 10px;
    }}
    QSplitter::handle:hover {{
        background: rgba(0,0,0,0.03);
    }}
    /* StatusBar */
    QStatusBar {{
        background: rgba(255,255,255,0.06);
        border-top: 1px solid {GLASS_BORDER_SOFT};
        color: {TEXT_SECONDARY};
    }}
    """
    app.setStyleSheet(qss)


def card(widget: QWidget, radius: int = 18, blur: float = 20.0, dx: float = 0.0, dy: float = 2.0) -> None:
    """Apply rounded card styling and a soft drop shadow to the widget."""
    current = widget.objectName()
    if not current:
        widget.setObjectName("CardInstance")
    widget.setProperty("class", "Card")
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(dx, dy)
    effect.setColor(Qt.black)
    widget.setGraphicsEffect(effect)
    # Also ensure the widget has the .Card style class
    widget.setStyleSheet(f"border-radius: {radius}px;")


def glass(widget: QWidget, radius: int = 18, blur: float = 30.0, dx: float = 0.0, dy: float = 2.0) -> None:
    """Apply glassmorphism styling and a soft shadow to the widget."""
    current = widget.objectName()
    if not current:
        widget.setObjectName("GlassInstance")
    widget.setProperty("class", "Glass")
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(dx, dy)
    effect.setColor(Qt.black)
    widget.setGraphicsEffect(effect)
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


