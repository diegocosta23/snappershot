from __future__ import annotations

from .window_manager import WindowManager


class ScreenshotEngine:
    """
    Ansvarar för all automation inne i TradingView.

    Den här klassen ska senare kunna:

    • söka bolag
    • välja rätt träff
    • byta timeframe
    • ta screenshot
    """

    def __init__(self):

        self.window = WindowManager()

    def prepare(self) -> bool:
        """
        Säkerställ att TradingView är redo.
        """

        return self.window.prepare()

    def search_company(self, company_name: str):

        print(f"[ENGINE] Search company: {company_name}")

    def select_first_result(self):

        print("[ENGINE] Select first search result")

    def change_timeframe(self, timeframe: str):

        print(f"[ENGINE] Change timeframe -> {timeframe}")

    def capture(self, filename: str):

        print(f"[ENGINE] Capture -> {filename}")