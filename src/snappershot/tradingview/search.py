from __future__ import annotations

import time

import pyautogui

from .window_manager import WindowManager


class TradingViewSearch:
    """
    Hanterar endast öppning av TradingViews Symbol Search.

    Den här klassen väljer INTE symbol.
    Användaren gör symbolvalet manuellt i TradingView.
    """

    SEARCH_DELAY = 0.30

    def __init__(self) -> None:
        self.window = WindowManager()

    def prepare(self) -> bool:
        """
        Hittar TradingView Desktop och ger fönstret fokus.
        """
        return self.window.prepare()

    def open_symbol_search(self) -> bool:
        """
        Öppnar TradingViews officiella Symbol Search.

        Returnerar True om TradingView kunde fokuseras.
        """

        if not self.prepare():
            return False

        pyautogui.press("/")

        time.sleep(self.SEARCH_DELAY)

        return True