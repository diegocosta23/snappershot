from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QMessageBox

from .search import TradingViewSearch
from .snapshot import SnapshotEngine
from .timeframe import TimeframeController
from .window_manager import WindowManager


class ScreenshotEngine:
    """
    Central motor för SnapperShot.

    Ansvar:
        • aktivera TradingView
        • öppna Symbol Search
        • byta timeframe
        • ta screenshots av TradingView-fönstret
    """

    def __init__(self) -> None:
        self.window = WindowManager()
        self.search = TradingViewSearch()
        self.timeframe = TimeframeController()
        self.snapshot = SnapshotEngine()

    def prepare(self) -> bool:
        """
        Säkerställ att TradingView Desktop är redo.
        """
        return self.window.prepare()

    def is_ready(self) -> bool:
        return self.prepare()

    def open_symbol_search(self) -> bool:
        """
        Öppnar TradingViews officiella Symbol Search.
        """
        if not self.prepare():
            return False

        return self.search.open_symbol_search()

    def search_company(self, ticker: str) -> bool:
        """
        Bakåtkompatibel metod.

        TradingView ska hantera själva symbolvalet manuellt,
        så den här metoden öppnar bara Symbol Search.
        """
        return self.open_symbol_search()

    def wait_for_symbol_selection(self) -> bool:
        """
        Visar en dialog som låter användaren fortsätta när symbolen är vald.
        """
        dialog = QMessageBox()
        dialog.setWindowTitle("SnapperShot")
        dialog.setIcon(QMessageBox.Icon.Information)
        dialog.setText("Välj aktie i TradingView.")
        dialog.setInformativeText("När grafen har laddat klart klickar du Fortsätt.")

        continue_button = dialog.addButton(
            "Fortsätt",
            QMessageBox.ButtonRole.AcceptRole,
        )
        cancel_button = dialog.addButton(
            "Avbryt",
            QMessageBox.ButtonRole.RejectRole,
        )

        dialog.setDefaultButton(continue_button)
        dialog.setEscapeButton(cancel_button)

        dialog.exec()

        return dialog.clickedButton() == continue_button

    def change_timeframe(self, timeframe: str) -> bool:
        """
        Byter timeframe i TradingView.
        """
        if not self.prepare():
            return False

        return self.timeframe.set(timeframe)

    def capture(self, filename: str | Path) -> bool:
        """
        Tar en screenshot av det aktiva TradingView-fönstret.
        """
        if not self.window.find() or self.window.window is None:
            return False

        try:
            self.snapshot.capture_window(filename, window=self.window.window)
            return True
        except Exception:
            return False

    def capture_timeframe(self, timeframe: str, filename: str | Path) -> bool:
        """
        Byter timeframe och tar sedan screenshot.
        """
        if not self.change_timeframe(timeframe):
            return False

        return self.capture(filename)

    def wait_chart(self, seconds: float = 1.5) -> None:
        """
        Tillfällig väntan för laddning av graf.
        """
        import time

        time.sleep(seconds)
