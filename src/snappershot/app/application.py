from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from src.snappershot.ui.main_window import MainWindow
from src.snappershot.ui.styles import STYLE


def run() -> None:
    app = QApplication(sys.argv)

    app.setApplicationName("SnapperShot")
    app.setStyleSheet(STYLE)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    run()