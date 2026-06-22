from __future__ import annotations

from typing import Any

from pywinauto import Desktop


class WindowManager:
    """
    Ansvarar för att hitta och aktivera TradingView Desktop.
    """

    def __init__(self) -> None:
        self.window: Any | None = None

    def find(self) -> bool:
        """
        Hittar TradingView-fönstret.
        """

        desktop = Desktop(backend="uia")

        for window in desktop.windows():

            title = window.window_text()

            if "TradingView" in title:
                self.window = window
                return True

        self.window = None
        return False

    def prepare(self) -> bool:
        """
        Säkerställ att TradingView är redo.
        """

        if not self.find():
            return False

        assert self.window is not None

        try:
            self.window.restore()
        except Exception:
            pass

        try:
            self.window.maximize()
        except Exception:
            pass

        try:
            self.window.set_focus()
        except Exception:
            pass

        return True

    def activate(self) -> bool:
        """
        Fokusera TradingView.
        """
        return self.prepare()

    def maximize(self) -> bool:

        if self.window is None:
            if not self.find():
                return False

        assert self.window is not None

        try:
            self.window.maximize()
            return True
        except Exception:
            return False

    def restore(self) -> bool:

        if self.window is None:
            if not self.find():
                return False

        assert self.window is not None

        try:
            self.window.restore()
            return True
        except Exception:
            return False

    def title(self) -> str:

        if self.window is None:
            return ""

        return self.window.window_text()