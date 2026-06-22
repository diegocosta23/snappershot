from __future__ import annotations

import time

import pyautogui


class SnapshotEngine:
    """
    Ansvarar för timeframes och snapshots.
    """

    TIMEFRAMES = (
        "1W",
        "1D",
        "4H",
        "45",
    )

    LOAD_DELAY = 1.6

    def change_timeframe(self, timeframe: str) -> bool:
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

    def snapshot(self) -> bool:
        """
        TradingViews inbyggda Snapshot.
        """

        try:

            pyautogui.hotkey(
                "ctrl",
                "shift",
                "s",
            )

            time.sleep(1.2)

            return True

        except Exception:

            return False

    def capture_timeframe(
        self,
        timeframe: str,
    ) -> bool:

        if not self.change_timeframe(timeframe):
            return False

        return self.snapshot()

    def capture_all(self) -> bool:

        for timeframe in self.TIMEFRAMES:

            if not self.capture_timeframe(timeframe):

                return False

        return True