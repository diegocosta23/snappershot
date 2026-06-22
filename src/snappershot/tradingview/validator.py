from __future__ import annotations

import time

import pyautogui


class TradingViewValidator:
    """Säkerställer att TradingView verkligen har laddat klart."""

    def __init__(self) -> None:
        self.default_wait = 1.5

    def wait(self, seconds: float | None = None) -> None:
        time.sleep(seconds or self.default_wait)

    def wait_for_chart(self) -> bool:
        """Första versionen: vänta bara lite extra."""
        self.wait(2.0)
        return True

    def wait_after_search(self) -> bool:
        self.wait(1.5)
        return True

    def wait_after_timeframe(self) -> bool:
        self.wait(1.5)
        return True

    def wait_for_ready(self) -> bool:
        """Gemensam framtida readiness-check."""
        return self.wait_for_chart()

    def escape(self) -> None:
        pyautogui.press("esc")


if __name__ == "__main__":
    validator = TradingViewValidator()
    print("Validator redo. Använd wait_after_search() och wait_after_timeframe().")
