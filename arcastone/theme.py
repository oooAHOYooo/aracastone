from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QStyle, QWidget, QGraphicsDropShadowEffect


# Palette tokens (CleanMyMac-adjacent)
PRIMARY_ACCENT = "#FF2D55"
SECONDARY = "#8E8E93"
SURFACE = "#F7F7FA"
TEXT_PRIMARY = "#1C1C1E"
TEXT_SECONDARY = "#4A4A4A"
BORDER = "#E6E6EE"


def apply_qss(app: QApplication) -> None:
    """Apply a global QSS for a soft, friendly, CleanMyMac-style UI."""
    font_stack = "SF Pro Text, -apple-system, system-ui, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial, sans-serif"
    qss = f"""
    /* Global */
    * {{
        font-family: {font_stack};
        color: {TEXT_PRIMARY};
    }}
    QWidget {{
        background: white;
        font-size: 14px;
    }}
    /* Header gradient (opt-in via objectName=Header) */
    #Header {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FF2D55, stop:1 #AF52DE);
        padding: 16px;
        border-bottom: 1px solid {BORDER};
    }}
    /* Cards (use card(widget) helper for shadow) */
    .Card {{
        background: {SURFACE};
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
    QLabel["secondary"="true"] {{
        color: {SECONDARY};
    }}
    QPushButton {{
        background: white;
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 8px 14px;
    }}
    QPushButton:hover {{ border-color: {PRIMARY_ACCENT}; }}
    QPushButton:pressed {{ background: #f0f0f5; }}
    QPushButton["accent"="true"] {{
        background: {PRIMARY_ACCENT};
        color: white;
        border: 1px solid {PRIMARY_ACCENT};
    }}
    QLineEdit, QTextEdit, QListWidget {{
        background: white;
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 8px 10px;
    }}
    QStatusBar {{
        background: {SURFACE};
        border-top: 1px solid {BORDER};
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


# Backwards compatibility: keep the old name as a no-op wrapper
def apply_dark_theme(app: QApplication) -> None:
    apply_qss(app)


