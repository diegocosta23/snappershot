from __future__ import annotations

import time

import pyautogui

from .validator import TradingViewValidator


class SnapshotEngine:
    """Ansvarar för timeframes och snapshots."""

    TIMEFRAMES = (
        "1W",
        "1D",
        "4H",
        "45M",
    )

    LOAD_DELAY = 1.6

    def __init__(self) -> None:
        self.validator = TradingViewValidator()

    def change_timeframe(self, timeframe: str) -> bool:
        """Byter timeframe."""
        try:
            pyautogui.write(timeframe)
            pyautogui.press("enter")
            self.validator.wait_after_timeframe()
            time.sleep(self.LOAD_DELAY)
            return True
        except Exception:
            return False

    def snapshot(self) -> bool:
        """TradingViews inbyggda Snapshot."""
        try:
            pyautogui.hotkey("ctrl", "shift", "s")
            time.sleep(1.2)
            return True
        except Exception:
            return False

    def capture_timeframe(self, timeframe: str) -> bool:
        """Byt timeframe och ta snapshot."""
        if not self.change_timeframe(timeframe):
            return False
        return self.snapshot()

    def capture_timeframes(self, timeframes: list[str] | None = None) -> bool:
        """Ta snapshots för en lista av timeframes."""
        sequence = timeframes or list(self.TIMEFRAMES)

        for timeframe in sequence:
            if not self.capture_timeframe(timeframe):
                return False

        return True

    def capture_all(self) -> bool:
        return self.capture_timeframes()


if __name__ == "__main__":
    print("SnapshotEngine är laddad. Använd capture_all() när TradingView är aktivt.")
