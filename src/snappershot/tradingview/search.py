from __future__ import annotations

import time

import pyautogui
import pyperclip


class TradingViewSearch:
    """
    Ansvarar för sökning i TradingView Desktop.
    """

    SEARCH_DELAY = 0.35

    def open_search(self) -> bool:
        """
        Öppna TradingViews sökruta.
        """

        try:

            pyautogui.hotkey("ctrl", "k")
            time.sleep(self.SEARCH_DELAY)

            return True

        except Exception:

            return False

    def clear(self) -> None:
        """
        Töm sökfältet.
        """

        pyautogui.hotkey("ctrl", "a")
        pyautogui.press("backspace")

    def write(self, company: str) -> bool:
        """
        Skriver företagsnamnet.
        """

        try:

            self.clear()

            pyperclip.copy(company)

            pyautogui.hotkey("ctrl", "v")

            time.sleep(self.SEARCH_DELAY)

            return True

        except Exception:

            return False

    def press_enter(self) -> None:

        pyautogui.press("enter")

    def search(self, company: str) -> bool:
        """
        Öppnar sökrutan och skriver företaget.
        """

        if not self.open_search():
            return False

        return self.write(company)