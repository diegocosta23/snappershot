from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from ..controller.main_controller import MainController
from ..ui.main_window import MainWindow
from ..ui.styles import STYLE


def run() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)

    window = MainWindow()
    controller = MainController(window)
    window.controller = controller  # type: ignore[attr-defined]

    app.aboutToQuit.connect(controller.shutdown)

    window.show()
    sys.exit(app.exec())
