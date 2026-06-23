from __future__ import annotations

import time

import pyautogui

from .window_manager import WindowManager


class TradingViewSearch:
    """
    Hanterar TradingViews Symbol Search.

    SnapperShot väljer inte aktien automatiskt.
    Programmet öppnar bara Symbol Search.
    Användaren väljer sedan själv rätt instrument i TradingView.
    """

    SEARCH_DELAY = 0.30

    def __init__(self) -> None:
        self.window = WindowManager()

    def prepare(self) -> bool:
        """
        Ger TradingView fokus.
        """
        return self.window.prepare()

    def open_symbol_search(self) -> bool:
        """
        Öppnar TradingViews Symbol Search med den officiella genvägen "/".
        """

        if not self.prepare():
            return False

        pyautogui.press("/")

        time.sleep(self.SEARCH_DELAY)

        return True

    #
    # Bakåtkompatibel metod.
    #
    def search(self, ticker: str) -> bool:
        _ = ticker
        return self.open_symbol_search()

    def search_and_select_first(self, ticker: str) -> bool:
        _ = ticker
        return self.open_symbol_search()