from __future__ import annotations

import asyncio
import logging
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable

import pyautogui
import win32gui
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
        5. Stabilisera chart-läget
        6. Byt timeframe och ta screenshots
        7. Skapa ZIP
    """

    DEFAULT_TIMEFRAMES = [
        "1W",
        "1D",
        "4H",
        "45M",
    ]
    SCREENSHOT_DELAY_SECONDS = 3.0

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

    def _stabilize_chart_state(self, company_name: str) -> CaptureResult | None:
        """
        Försöker få TradingView tillbaka till chart-läge efter att användaren
        har valt rätt aktie i Symbol Search.
        """
        focus = self.window.focus()
        if not focus.ok:
            return CaptureResult.failed(
                f"Could not focus TradingView before chart stabilization: {focus.message}",
                company_name=company_name,
            )

        time.sleep(0.20)

        try:
            pyautogui.press("escape")
            time.sleep(0.10)
            pyautogui.press("escape")
            time.sleep(0.10)
        except Exception as exc:
            return CaptureResult.failed(
                f"Could not clear TradingView overlays: {exc}",
                company_name=company_name,
            )

        hwnd = self.window.hwnd
        if hwnd is not None:
            try:
                client_left, client_top, client_right, client_bottom = (
                    win32gui.GetClientRect(hwnd)
                )
                center_client_x = (client_right - client_left) // 2
                center_client_y = (client_bottom - client_top) // 2

                center_x, center_y = win32gui.ClientToScreen(
                    hwnd,
                    (center_client_x, center_client_y),
                )

                pyautogui.click(center_x, center_y)
                time.sleep(0.10)
                pyautogui.press("escape")
            except Exception:
                pass

        return None

    def capture_company(
        self,
        company_name: str,
        timeframes: list[str] | None = None,
    ) -> CaptureResult:
        """
        Kör hela capture-processen för ett företag.
        """
        self._log(f"Förbereder capture för: {company_name}")

        self._log("Förbereder TradingView...")
        ready = self.window.prepare()
        if not ready.ok:
            return CaptureResult.failed(
                f"TradingView Desktop not ready: {ready.message}",
                company_name=company_name,
            )

        self._log("Öppnar Symbol Search...")
        search_result = self.search.open_symbol_search()
        if not search_result.ok:
            return CaptureResult.failed(
                f"Could not open Symbol Search: {search_result.message}",
                company_name=company_name,
            )

        self._log("Väntar på att du väljer aktie...")
        if not self._show_symbol_selection_dialog():
            return CaptureResult.failed(
                "Capture cancelled.",
                company_name=company_name,
            )

        chart_state = self._stabilize_chart_state(company_name)
        if chart_state is not None:
            return chart_state

        selected_timeframes = list(timeframes or self.DEFAULT_TIMEFRAMES)
        output_folder = self.storage_service.create_capture_folder(company_name)
        self._log(f"Sparar till: {output_folder}")

        screenshots: list[Path] = []

        from ..capture_engine import CaptureEngine

        capture_engine = CaptureEngine()
        with ThreadPoolExecutor(max_workers=2) as executor:
            finnhub_future = executor.submit(capture_engine.finnhub.collect, company_name)
            yfinance_future = executor.submit(capture_engine.yfinance.collect, company_name)

            for timeframe in selected_timeframes:
                self._log(f"Byter timeframe till {timeframe}...")

                timeframe_result = self.timeframe.set(timeframe)
                if not timeframe_result.ok:
                    return CaptureResult.failed(
                        f"Failed to set timeframe {timeframe}: {timeframe_result.message}",
                        company_name=company_name,
                    )

                time.sleep(self.SCREENSHOT_DELAY_SECONDS)

                screenshot_path = output_folder / f"{timeframe}.png"
                self._log(f"Tar screenshot: {screenshot_path.name}")

                capture_result = self.snapshot.capture(screenshot_path, label=timeframe)
                if not capture_result.ok:
                    return CaptureResult.failed(
                        f"Failed to capture timeframe {timeframe}: {capture_result.message}",
                        company_name=company_name,
                    )

                captured_path = capture_result.data
                if isinstance(captured_path, Path):
                    screenshots.append(captured_path)
                else:
                    screenshots.append(screenshot_path)

                self._log(f"✓ Klar: {timeframe}")

            try:
                finnhub_data = finnhub_future.result(timeout=60)
            except Exception as exc:
                self._log(f"Finnhub collection warning: {exc}")
                finnhub_data = {}

            try:
                yfinance_data = yfinance_future.result(timeout=60)
            except Exception as exc:
                self._log(f"Yahoo Finance collection warning: {exc}")
                yfinance_data = {}

        try:
            self._log("Startar insamling av rå fundamentdata...")
            asyncio.run(
                capture_engine.run(
                    company_name,
                    screenshots=screenshots,
                )
            )
            self._log("Rådata-paket sparat.")
        except Exception as exc:
            self._log(f"Stock intelligence collection warning: {exc}")

        zip_path = self.storage_service.zip_path(company_name)
        self._log(f"Skapar ZIP: {zip_path.name}")

        try:
            created_zip = self.zip_service.create_zip(zip_path, screenshots)
        except Exception as exc:
            return CaptureResult.failed(
                f"Could not create ZIP: {exc}",
                company_name=company_name,
            )

        if not created_zip.exists():
            return CaptureResult.failed(
                "ZIP filen skapades inte.",
                company_name=company_name,
            )

        try:
            if created_zip.stat().st_size <= 0:
                return CaptureResult.failed(
                    "ZIP filen är tom.",
                    company_name=company_name,
                )
        except Exception as exc:
            return CaptureResult.failed(
                f"Could not verify ZIP: {exc}",
                company_name=company_name,
            )

        if not zipfile.is_zipfile(created_zip):
            return CaptureResult.failed(
                "ZIP filen är korrupt.",
                company_name=company_name,
            )

        self._log(f"✓ ZIP klar: {created_zip.name}")

        return CaptureResult.completed(
            company_name=company_name,
            output_folder=output_folder,
            screenshots=screenshots,
            zip_path=created_zip,
        )
