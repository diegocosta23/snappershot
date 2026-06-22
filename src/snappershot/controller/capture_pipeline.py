from __future__ import annotations

from pathlib import Path

from ..services.company_service import CompanyService
from ..tradingview.engine import ScreenshotEngine


class CapturePipeline:
    """
    Kör hela capture-processen för ett företag.
    """

    DEFAULT_TIMEFRAMES = [
        "1W",
        "1D",
        "4H",
        "45M",
    ]

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

        if not self.engine.prepare():
            print("TradingView Desktop not found.")
            return False

        #
        # Öppna TradingViews Symbol Search.
        #
        if not self.engine.open_symbol_search():
            print("Could not open Symbol Search.")
            return False

        print()
        print("=" * 60)
        print("SELECT THE COMPANY INSIDE TRADINGVIEW")
        print("WHEN THE CHART HAS LOADED PRESS ENTER HERE")
        print("=" * 60)

        input()

        selected_timeframes = timeframes or self.DEFAULT_TIMEFRAMES

        output_folder = Path("captures") / company.name
        output_folder.mkdir(parents=True, exist_ok=True)

        for timeframe in selected_timeframes:

            print(f"Capturing {timeframe}")

            if not self.engine.capture_timeframe(
                timeframe,
                output_folder / f"{timeframe}.png",
            ):
                print(f"Failed on {timeframe}")
                return False

        print("Capture completed.")

        return True