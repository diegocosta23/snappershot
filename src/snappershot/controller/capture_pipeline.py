from __future__ import annotations

from snappershot.services.company_service import CompanyService
from snappershot.services.screenshot_service import ScreenshotService
from snappershot.services.zip_service import ZipService

from snappershot.tradingview.window_manager import WindowManager
from snappershot.tradingview.engine import ScreenshotEngine


class CapturePipeline:
    """
    Hela arbetsflödet.

    Company
        ↓
    TradingView
        ↓
    Search
        ↓
    Timeframes
        ↓
    Screenshots
        ↓
    ZIP
    """

    def __init__(self):

        self.company_service = CompanyService()
        self.window_manager = WindowManager()
        self.engine = ScreenshotEngine()
        self.screenshot_service = ScreenshotService()
        self.zip_service = ZipService()

    def capture_company(
        self,
        company_name: str,
        timeframes: list[str],
    ) -> bool:

        company = self.company_service.find(company_name)

        if company is None:
            print("Company not found.")
            return False

        print(f"Company: {company.name}")

        if not self.window_manager.prepare():

            print("TradingView not ready.")
            return False

        print("TradingView ready.")

        # Nästa steg:
        # self.engine.search(...)
        # self.engine.change_timeframe(...)
        # self.engine.capture(...)

        return True