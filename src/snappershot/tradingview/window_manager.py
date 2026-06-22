from __future__ import annotations

from .desktop import TradingViewDesktop


class WindowManager:
<<<<<<< HEAD
    """
    Ansvarar för TradingView-fönstret.
    """
=======
    """Ansvarar för att hitta och aktivera TradingView Desktop."""
>>>>>>> 65558fc5610a8653dbc268b93a15390093e18eb3

    def __init__(self) -> None:

<<<<<<< HEAD
        self.desktop = TradingViewDesktop()

    def prepare(self) -> bool:
        """
        Säkerställ att TradingView är redo.
        """

        if not self.desktop.connect():
=======
    def find(self) -> bool:
        desktop = Desktop(backend="uia")

        for window in desktop.windows():
            title = window.window_text()
            if "TradingView" in title:
                self.window = window
                return True

        self.window = None
        return False

    def prepare(self) -> bool:
        if not self.find():
>>>>>>> 65558fc5610a8653dbc268b93a15390093e18eb3
            return False

        self.desktop.restore()
        self.desktop.maximize()
        self.desktop.activate()

        return True

    def activate(self) -> bool:
<<<<<<< HEAD
        return self.desktop.activate()

    def maximize(self) -> bool:
        return self.desktop.maximize()

    def restore(self) -> bool:
        return self.desktop.restore()

    def title(self) -> str:
        return self.desktop.title()
=======
        return self.prepare()

    def maximize(self) -> bool:
        if self.window is None and not self.find():
            return False

        assert self.window is not None
        try:
            self.window.maximize()
            return True
        except Exception:
            return False

    def restore(self) -> bool:
        if self.window is None and not self.find():
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
>>>>>>> 65558fc5610a8653dbc268b93a15390093e18eb3
