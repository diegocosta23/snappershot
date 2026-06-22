from __future__ import annotations

import time

import pyautogui


class TimeframeController:
    """
    Ansvarar för att byta timeframe i TradingView Desktop.
    """

    OPEN_DELAY = 0.20
    LOAD_DELAY = 1.25

    def set(self, timeframe: str) -> bool:
        """
        Byter timeframe via TradingViews snabbkommando.

        Exempel:
            1W
            1D
            4H
            45M
        """

        try:
            #
            # Öppna TradingViews timeframe-dialog.
            #
            pyautogui.press(",")

            time.sleep(self.OPEN_DELAY)

            #
            # Rensa eventuell tidigare text.
            #
            pyautogui.hotkey("ctrl", "a")
            pyautogui.press("backspace")

            #
            # Skriv timeframe.
            #
            pyautogui.write(timeframe, interval=0.02)

            pyautogui.press("enter")

            #
            # Vänta på att grafen laddar.
            #
            time.sleep(self.LOAD_DELAY)

            return True

        except Exception:
            return False

    def cycle(self, timeframes: list[str]) -> bool:
        """
        Kör flera timeframes efter varandra.
        """

        for timeframe in timeframes:

            if not self.set(timeframe):
                return False

        return True