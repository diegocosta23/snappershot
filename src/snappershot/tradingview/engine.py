from __future__ import annotations

from .desktop import TradingViewDesktop


class TradingViewEngine:
    """
    Central motor som håller ihop all TradingView-logik.
    Här kommer senare:
        - sökning
        - timeframe-byte
        - snapshots
        - export
        - felhantering
    """

    def __init__(self) -> None:
        self.desktop = TradingViewDesktop()

    def is_ready(self) -> bool:
        """
        Returnerar True om TradingView Desktop är igång.
        """
        return self.desktop.is_running()