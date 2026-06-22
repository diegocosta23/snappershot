from __future__ import annotations

from pathlib import Path

from ..models.capture_result import CaptureResult
from ..services.company_service import CompanyService
from ..services.storage_service import StorageService
from ..services.zip_service import ZipService
from ..tradingview.engine import ScreenshotEngine


class CapturePipeline:
    """
    Kör hela capture-processen för ett företag.

    Ansvar:
        - hitta bolag
        - öppna TradingViews symbol search
        - vänta på manuellt symbolval
        - ta screenshots för vald timeframe-sekvens
        - skapa ZIP
        - returnera ett CaptureResult
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
        self.storage_service = StorageService()
        self.zip_service = ZipService()

    def capture_company(
        self,
        company_name: str,
        timeframes: list[str] | None = None,
    ) -> CaptureResult:
        company = self.company_service.find(company_name)

        if company is None:
            return CaptureResult.failed("Company not found.", company_name=company_name)

        if not self.engine.prepare():
            return CaptureResult.failed(
                "TradingView Desktop not found.",
                company_name=company.name,
            )

        if not self.engine.open_symbol_search():
            return CaptureResult.failed(
                "Could not open Symbol Search.",
                company_name=company.name,
            )

        print()
        print("=" * 60)
        print("SELECT THE COMPANY INSIDE TRADINGVIEW")
        print("WHEN THE CHART HAS LOADED PRESS ENTER HERE")
        print("=" * 60)

        self.engine.wait_for_symbol_selection()

        selected_timeframes = timeframes or self.DEFAULT_TIMEFRAMES
        output_folder = self.storage_service.create_capture_folder(company.name)

        screenshots: list[Path] = []

        for timeframe in selected_timeframes:
            screenshot_path = output_folder / f"{timeframe}.png"

            if not self.engine.capture_timeframe(timeframe, screenshot_path):
                return CaptureResult.failed(
                    f"Failed to capture timeframe {timeframe}.",
                    company_name=company.name,
                )

            screenshots.append(screenshot_path)

        zip_path = self.storage_service.zip_path(company.name)

        try:
            self.zip_service.create_zip(zip_path, screenshots)
        except Exception as exc:
            return CaptureResult.failed(
                f"Could not create ZIP: {exc}",
                company_name=company.name,
            )

        return CaptureResult.completed(
            company_name=company.name,
            output_folder=output_folder,
            screenshots=screenshots,
            zip_path=zip_path,
        )