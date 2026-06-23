from __future__ import annotations

from pywinauto import Desktop


class TradingViewDesktop:
    """
    Hittar TradingView Desktop.
    """

    def __init__(self) -> None:
        self.window = None

    def is_running(self) -> bool:
        """
        Returnerar True om TradingView Desktop är öppet.
        """

        try:
            windows = Desktop(backend="uia").windows()

            for window in windows:

                title = window.window_text()

                if "TradingView" in title:
                    self.window = window
                    return True

            return False

        except Exception:
            return False
