from __future__ import annotations

import logging
import zipfile
from pathlib import Path
from typing import Callable

from PySide6.QtWidgets import QMessageBox

from ..models.capture_result import CaptureResult
from ..services.company_service import CompanyService
from ..services.storage_service import StorageService
from ..services.zip_service import ZipService
from ..tradingview.search import TradingViewSearch
from ..tradingview.snapshot import SnapshotEngine
from ..tradingview.timeframe import TimeframeController
from ..tradingview.window_manager import WindowManager

log = logging.getLogger(__name__)


class CapturePipeline:
    """
    Kör hela capture-processen för ett företag.

    Flöde:
        1. Hitta företag
        2. Förbered TradingView
        3. Öppna Symbol Search
        4. Vänta på att användaren väljer aktie
        5. Byt timeframe och ta screenshots
        6. Skapa ZIP
    """

    DEFAULT_TIMEFRAMES = [
        "1W",
        "1D",
        "4H",
        "45M",
    ]

    def __init__(self, log_callback: Callable[[str], None] | None = None) -> None:
        self.company_service = CompanyService()
        self.storage_service = StorageService()
        self.zip_service = ZipService()

        self.window = WindowManager()
        self.search = TradingViewSearch(self.window)
        self.timeframe = TimeframeController(self.window)
        self.snapshot = SnapshotEngine(self.window)

        self._log_callback = log_callback

    def _log(self, message: str) -> None:
        log.info(message)
        if self._log_callback is not None:
            try:
                self._log_callback(message)
            except Exception:
                pass

    def _show_symbol_selection_dialog(self) -> bool:
        """
        Visar dialogen som låter användaren fortsätta när symbolen är vald.
        """
        dialog = QMessageBox()
        dialog.setWindowTitle("SnapperShot")
        dialog.setIcon(QMessageBox.Icon.Information)
        dialog.setText("Välj aktie i TradingView.")
        dialog.setInformativeText("När grafen har laddat klart klickar du Fortsätt.")

        continue_button = dialog.addButton(
            "Fortsätt",
            QMessageBox.ButtonRole.AcceptRole,
        )
        cancel_button = dialog.addButton(
            "Avbryt",
            QMessageBox.ButtonRole.RejectRole,
        )

        dialog.setDefaultButton(continue_button)
        dialog.setEscapeButton(cancel_button)

        dialog.exec()

        return dialog.clickedButton() == continue_button

    def capture_company(
        self,
        company_name: str,
        timeframes: list[str] | None = None,
    ) -> CaptureResult:
        """
        Kör hela capture-processen för ett företag.
        """
        self._log(f"Söker företag: {company_name}")

        company = self.company_service.find(company_name)

        if company is None:
            return CaptureResult.failed(
                "Company not found.",
                company_name=company_name,
            )

        self._log(f"Hittade bolag: {company.name} ({company.ticker})")

        self._log("Förbereder TradingView...")
        ready = self.window.prepare()
        if not ready.ok:
            return CaptureResult.failed(
                f"TradingView Desktop not ready: {ready.message}",
                company_name=company.name,
            )

        self._log("Öppnar Symbol Search...")
        search_result = self.search.open_symbol_search()
        if not search_result.ok:
            return CaptureResult.failed(
                f"Could not open Symbol Search: {search_result.message}",
                company_name=company.name,
            )

        self._log("Väntar på att du väljer aktie...")
        if not self._show_symbol_selection_dialog():
            return CaptureResult.failed(
                "Capture cancelled.",
                company_name=company.name,
            )

        selected_timeframes = list(timeframes or self.DEFAULT_TIMEFRAMES)
        output_folder = self.storage_service.create_capture_folder(company.name)
        self._log(f"Sparar till: {output_folder}")

        screenshots: list[Path] = []

        for timeframe in selected_timeframes:
            self._log(f"Byter timeframe till {timeframe}...")

            timeframe_result = self.timeframe.set(timeframe)
            if not timeframe_result.ok:
                return CaptureResult.failed(
                    f"Failed to set timeframe {timeframe}: {timeframe_result.message}",
                    company_name=company.name,
                )

            screenshot_path = output_folder / f"{timeframe}.png"
            self._log(f"Tar screenshot: {screenshot_path.name}")

            capture_result = self.snapshot.capture(screenshot_path, label=timeframe)
            if not capture_result.ok:
                return CaptureResult.failed(
                    f"Failed to capture timeframe {timeframe}: {capture_result.message}",
                    company_name=company.name,
                )

            captured_path = capture_result.data
            if isinstance(captured_path, Path):
                screenshots.append(captured_path)
            else:
                screenshots.append(screenshot_path)

            self._log(f"✓ Klar: {timeframe}")

        zip_path = self.storage_service.zip_path(company.name)
        self._log(f"Skapar ZIP: {zip_path.name}")

        try:
            created_zip = self.zip_service.create_zip(zip_path, screenshots)
        except Exception as exc:
            return CaptureResult.failed(
                f"Could not create ZIP: {exc}",
                company_name=company.name,
            )

        if not created_zip.exists():
            return CaptureResult.failed(
                "ZIP filen skapades inte.",
                company_name=company.name,
            )

        try:
            if created_zip.stat().st_size <= 0:
                return CaptureResult.failed(
                    "ZIP filen är tom.",
                    company_name=company.name,
                )
        except Exception as exc:
            return CaptureResult.failed(
                f"Could not verify ZIP: {exc}",
                company_name=company.name,
            )

        if not zipfile.is_zipfile(created_zip):
            return CaptureResult.failed(
                "ZIP filen är korrupt.",
                company_name=company.name,
            )

        self._log(f"✓ ZIP klar: {created_zip.name}")

        return CaptureResult.completed(
            company_name=company.name,
            output_folder=output_folder,
            screenshots=screenshots,
            zip_path=created_zip,
        )
