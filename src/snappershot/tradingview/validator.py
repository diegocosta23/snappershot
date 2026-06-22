from __future__ import annotations

import time

import pyautogui


class TradingViewValidator:
    """
    Säkerställer att TradingView verkligen har
    laddat klart innan nästa steg körs.
    """

    def __init__(self) -> None:
        self.default_wait = 1.5

    def wait(self, seconds: float | None = None) -> None:

        time.sleep(seconds or self.default_wait)

    def wait_for_chart(self) -> bool:
        """
        Första versionen.

        Just nu väntar vi bara.
        Senare kommer vi läsa skärmen
        och verifiera att grafen verkligen
        laddat klart.
        """

        self.wait(2.0)

        return True

    def wait_after_search(self) -> bool:

        self.wait(1.5)

        return True

    def wait_after_timeframe(self) -> bool:

        self.wait(1.5)

        return True

    def escape(self) -> None:

        pyautogui.press("esc")