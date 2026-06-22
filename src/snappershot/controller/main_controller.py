from __future__ import annotations

from src.snappershot.tradingview.desktop import TradingViewDesktop


class MainController:
    """
    Huvudkontroller.

    All logik ska gå genom denna klass.
    GUI får aldrig prata direkt med TradingView.
    """

    def __init__(self) -> None:
        self.desktop = TradingViewDesktop()

    def check_connection(self) -> bool:
        """
        Kontrollerar om TradingView Desktop är igång.
        """
        return self.desktop.is_running()