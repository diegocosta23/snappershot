from __future__ import annotations

from .desktop import TradingViewDesktop


class WindowManager:
    """
    Ansvarar för TradingView-fönstret.
    """

    def __init__(self) -> None:

        self.desktop = TradingViewDesktop()

    def prepare(self) -> bool:
        """
        Säkerställ att TradingView är redo.
        """

        if not self.desktop.connect():
            return False

        self.desktop.restore()
        self.desktop.maximize()
        self.desktop.activate()

        return True

    def activate(self) -> bool:
        return self.desktop.activate()

    def maximize(self) -> bool:
        return self.desktop.maximize()

    def restore(self) -> bool:
        return self.desktop.restore()

    def title(self) -> str:
        return self.desktop.title()