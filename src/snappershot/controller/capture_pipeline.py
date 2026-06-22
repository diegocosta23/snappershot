from __future__ import annotations

<<<<<<< HEAD
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
=======
from dataclasses import dataclass
from pathlib import Path

from ..models.company import Company
from ..services.company_service import CompanyService
from ..services.screenshot_service import ScreenshotService
from ..services.storage_service import StorageService
from ..services.zip_service import ZipService


@dataclass(slots=True)
class CaptureResult:
    success: bool
    company_name: str
    screenshot_path: Path | None = None
    zip_path: Path | None = None
    message: str = ""
    company: Company | None = None


class CapturePipeline:
    def __init__(self) -> None:
        self.company_service = CompanyService()
        self.screenshot_service = ScreenshotService()
        self.storage_service = StorageService()
        self.zip_service = ZipService()

    def resolve_company(self, company_name: str) -> Company | None:
        return self.company_service.find(company_name)

    def capture_company(self, company_name: str) -> CaptureResult:
        raw_name = company_name.strip()
        if not raw_name:
            return CaptureResult(False, "", message="Skriv eller välj ett företag först.")

        company = self.resolve_company(raw_name)
        resolved_name = company.name if company is not None else raw_name
        timestamp = self.storage_service.timestamp()
        screenshot_path = self.storage_service.screenshot_path(resolved_name, timestamp)
        zip_path = self.storage_service.zip_path(resolved_name, timestamp)

        try:
            self.screenshot_service.capture_desktop(screenshot_path)
            self.zip_service.create_zip(zip_path, [screenshot_path])
            return CaptureResult(
                True,
                resolved_name,
                screenshot_path=screenshot_path,
                zip_path=zip_path,
                message="Capture klar.",
                company=company,
            )
        except Exception as exc:
            return CaptureResult(False, resolved_name, message=str(exc), company=company)
>>>>>>> 65558fc5610a8653dbc268b93a15390093e18eb3
