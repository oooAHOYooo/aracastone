from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .theme import apply_qss, app_logo_icon
from .main_window import MainWindow
from .core.config import ensure_directories, set_offline_model_cache_env


def main() -> int:
    ensure_directories()
    set_offline_model_cache_env()
    app = QApplication(sys.argv)
    apply_qss(app)
    win = MainWindow()
    win.setWindowIcon(app_logo_icon())
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())


