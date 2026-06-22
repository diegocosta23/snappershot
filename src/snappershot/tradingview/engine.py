from __future__ import annotations

from .window_manager import WindowManager


<<<<<<< HEAD
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
=======
class TradingViewEngine:
    """Central motor som håller ihop all TradingView-logik."""

    def __init__(self) -> None:
        self.window = WindowManager()

    def prepare(self) -> bool:
        """Säkerställ att TradingView Desktop är igång och redo."""
        return self.window.prepare()

    def is_ready(self) -> bool:
        """Returnerar True om TradingView Desktop är igång."""
        return self.prepare()

    def search_company(self, company_name: str) -> None:
        print(f"[ENGINE] Search company: {company_name}")

    def select_first_result(self) -> None:
        print("[ENGINE] Select first search result")

    def change_timeframe(self, timeframe: str) -> None:
        print(f"[ENGINE] Change timeframe -> {timeframe}")

    def capture(self, filename: str) -> None:
        print(f"[ENGINE] Capture -> {filename}")
>>>>>>> 65558fc5610a8653dbc268b93a15390093e18eb3
