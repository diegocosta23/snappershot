from __future__ import annotations

import time

import pyautogui


class TimeframeController:
    """
    Ansvarar för att byta timeframe i TradingView Desktop.
    """

    OPEN_DELAY = 0.20
    LOAD_DELAY = 1.25
    MAX_RETRIES = 2

    VALID_TIMEFRAMES = {
        "1W",
        "1D",
        "4H",
        "45M",
    }

    def set(self, timeframe: str) -> bool:
        """
        Byter timeframe i TradingView.
        """

        timeframe = timeframe.upper()

        if timeframe not in self.VALID_TIMEFRAMES:
            raise ValueError(f"Ogiltigt timeframe: {timeframe}")

        for _ in range(self.MAX_RETRIES):
            try:
                pyautogui.press(",")
                time.sleep(self.OPEN_DELAY)

                pyautogui.hotkey("ctrl", "a")
                pyautogui.press("backspace")

                pyautogui.write(timeframe, interval=0.02)
                pyautogui.press("enter")

                time.sleep(self.LOAD_DELAY)
                return True

            except Exception:
                time.sleep(0.3)

        return False

    def cycle(self, timeframes: list[str]) -> bool:
        """
        Kör flera timeframes efter varandra.
        """

        for timeframe in timeframes:
            if not self.set(timeframe):
                return False

        return True