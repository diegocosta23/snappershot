from __future__ import annotations

import time

import pyautogui


class TimeframeController:
    """
    Ansvarar för att byta timeframe i TradingView.
    """

    LOAD_DELAY = 1.0

    def set(self, timeframe: str) -> bool:
        """
        Byter timeframe.
        """

        try:
            pyautogui.write(timeframe)
            pyautogui.press("enter")
            time.sleep(self.LOAD_DELAY)
            return True

        except Exception:
            return False

    def cycle(self, timeframes: list[str]) -> bool:
        """
        Byter igenom flera timeframes.
        """

        for timeframe in timeframes:
            if not self.set(timeframe):
                return False

        return True