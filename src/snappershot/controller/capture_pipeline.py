from __future__ import annotations

from ..services.company_service import CompanyService
from ..tradingview.engine import ScreenshotEngine


class CapturePipeline:
    """
    Hela arbetsflödet för SnapperShot.

    Version 1:

        Företag
            ↓
        TradingView Desktop
            ↓
        Sök ticker
            ↓
        Klar

    Timeframes och screenshots kommer i nästa steg.
    """

    def __init__(self) -> None:

        self.company_service = CompanyService()
        self.engine = ScreenshotEngine()

    def capture_company(
        self,
        company_name: str,
        timeframes: list[str] | None = None,
    ) -> bool:

        company = self.company_service.find(company_name)

        if company is None:
            print("Company not found.")
            return False

        print(f"Found company: {company.name}")
        print(f"Ticker: {company.ticker}")

        if not self.engine.prepare():
            print("TradingView Desktop is not ready.")
            return False

        print("TradingView ready.")

        #
        # Viktigt:
        # TradingView ska ALLTID få tickern
        #
        if not self.engine.search_company(company.ticker):
            print("Could not search ticker.")
            return False

        print("Ticker loaded successfully.")

        return True