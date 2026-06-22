from __future__ import annotations

from typing import Any

from pywinauto import Desktop


class TradingViewDesktop:
    """
    Hanterar TradingView Desktop-fönstret.

    Ansvar:
        • hitta TradingView
        • fokusera TradingView
        • maximera TradingView
        • returnera aktuell titel
    """

    def __init__(self) -> None:
        self.window: Any | None = None

    def connect(self) -> bool:
        """
        Hitta TradingView Desktop.
        """

        try:

            windows = Desktop(backend="uia").windows()

            for window in windows:

                title = window.window_text()

                if "TradingView" in title:

                    self.window = window
                    return True

            self.window = None
            return False

        except Exception:

            self.window = None
            return False

    def is_running(self) -> bool:
        """
        Returnerar True om TradingView hittades.
        """

        return self.connect()

    def activate(self) -> bool:
        """
        Fokuserar TradingView.
        """

        if self.window is None:

            if not self.connect():
                return False

        try:

            assert self.window is not None
            self.window.set_focus()
            return True

        except Exception:

            return False

    def maximize(self) -> bool:
        """
        Maximerar fönstret.
        """

        if self.window is None:

            if not self.connect():
                return False

        try:

            assert self.window is not None
            self.window.maximize()
            return True

        except Exception:

            return False

    def restore(self) -> bool:
        """
        Återställer om fönstret är minimerat.
        """

        if self.window is None:

            if not self.connect():
                return False

        try:

            assert self.window is not None
            self.window.restore()
            return True

        except Exception:

            return False

    def title(self) -> str:
        """
        Returnerar fönstrets titel.
        """

        if self.window is None:
            return ""

        try:

            assert self.window is not None
            return self.window.window_text()

        except Exception:
            return ""

    def ready(self) -> bool:
        """
        Säkerställer att TradingView är redo.
        """

        return (
            self.connect()
            and self.restore()
            and self.maximize()
            and self.activate()
        )


if __name__ == "__main__":

    tv = TradingViewDesktop()

    print("TradingView hittad:", tv.connect())

    if tv.window:
        print("Titel:", tv.title())
        print("Redo:", tv.ready())
    else:
        print("TradingView Desktop är inte igång.")