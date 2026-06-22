from __future__ import annotations

import time

from .search import TradingViewSearch
from .snapshot import SnapshotEngine
from .timeframe import TimeframeController
from .window_manager import WindowManager


class ScreenshotEngine:
    """
    Central motor för SnapperShot.

    Ansvar:

        • aktivera TradingView
        • söka ticker
        • byta timeframe
        • ta screenshots
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

    def search_company(self, ticker: str) -> bool:
        """
        Söker efter en ticker.

        Exempel:

            INVE B
            SWED A
            ABB
            SAND
        """

        if not self.prepare():
            return False

        print(f"[ENGINE] Searching {ticker}")

        return self.search.search(ticker)

    def change_timeframe(self, timeframe: str) -> bool:

        print(f"[ENGINE] Timeframe {timeframe}")

        return self.timeframe.set(timeframe)

    def capture(self, filename: str) -> bool:

        print(f"[ENGINE] Screenshot {filename}")

        return self.snapshot.capture(filename)

    def wait_chart(self, seconds: float = 1.5) -> None:

        time.sleep(seconds)