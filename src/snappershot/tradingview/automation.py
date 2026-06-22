from __future__ import annotations

from snappershot.tradingview.desktop import TradingViewDesktop
from snappershot.tradingview.search import TradingViewSearch
from snappershot.tradingview.snapshot import SnapshotEngine
from snappershot.tradingview.validator import TradingViewValidator


class TradingViewAutomation:
    """
    Huvudmotorn.

    Kör hela arbetsflödet.

    GUI
        ↓
    Desktop
        ↓
    Search
        ↓
    Validator
        ↓
    Snapshot
    """

    def __init__(self) -> None:

        self.desktop = TradingViewDesktop()
        self.search = TradingViewSearch()
        self.validator = TradingViewValidator()
        self.snapshot = SnapshotEngine()

    def prepare(self) -> bool:
        """
        Säkerställ att TradingView är redo.
        """

        return self.desktop.ready()

    def open_company(
        self,
        company: str,
    ) -> bool:
        """
        Öppna företag.
        """

        if not self.search.search(company):
            return False

        self.search.press_enter()

        return self.validator.wait_after_search()

    def capture(
        self,
        company: str,
    ) -> bool:
        """
        Komplett körning.
        """

        if not self.prepare():
            return False

        if not self.open_company(company):
            return False

        return self.snapshot.capture_all()