from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QApplication

from ..controller.capture_pipeline import CapturePipeline
from ..services.company_service import CompanyService

if TYPE_CHECKING:
    from ..ui.main_window import MainWindow


class MainController:
    """Kopplar GUI:t till första fungerande printscreen-flödet."""

    def __init__(self, window: MainWindow) -> None:
        self.window = window
        self.pipeline = CapturePipeline()
        self.company_service = CompanyService()
        self.selected_company = ""
        self.latest_zip_path = ""

        self._connect_signals()
        self.window.set_connection_status("🟢 Printscreen redo")
        self.window.set_status("Redo")

    def _connect_signals(self) -> None:
        self.window.search_text_changed.connect(self._on_search_text_changed)
        self.window.company_selected.connect(self._on_company_selected)
        self.window.capture_requested.connect(self._on_capture_requested)
        self.window.copy_zip_requested.connect(self._on_copy_zip_requested)
        self.window.open_folder_requested.connect(self._on_open_folder_requested)
        self.window.clear_requested.connect(self._on_clear_requested)

    def _on_search_text_changed(self, text: str) -> None:
        query = text.strip()

        if len(query) < 2:
            self.window.set_company_results([])
            self.window.set_status("Redo")
            return

        results = self.company_service.search(query)
        names = [company.name for company in results][:8]

        self.window.set_company_results(names)
        self.window.set_status(f"{len(names)} träffar")
        self.window.append_log(f"Sökning: {query} ({len(names)} träffar)")

    def _on_company_selected(self, company: str) -> None:
        company = company.strip()
        if not company:
            return

        self.selected_company = company
        self.window.show_success(f"Vald: {company}")

    def _capture(self, company: str) -> bool:
        company = company.strip()
        if not company:
            self.window.show_error("Skriv eller välj ett företag först.")
            return False

        self.window.set_busy(True)
        self.window.set_progress(10)
        self.window.set_status(f"Tar printscreen: {company}")
        self.window.append_log(f"Startar printscreen för {company}")

        try:
            result = self.pipeline.capture_company(company)

            if not result.success or result.zip_path is None:
                self.window.show_error(result.message or "Capture misslyckades.")
                return False

            self.latest_zip_path = str(result.zip_path)
            self.window.set_progress(55)
            if result.screenshot_path is not None:
                self.window.append_log(f"Sparad bild: {result.screenshot_path}")

            self.window.set_result(result.zip_path.name, str(result.zip_path))
            self.window.set_progress(100)
            self.window.show_success(f"Klart: {result.company_name}")
            self.window.append_log(f"ZIP skapad: {result.zip_path}")
            return True
        except Exception as exc:
            self.window.show_error(str(exc))
            return False
        finally:
            self.window.set_busy(False)

    def capture_company(self, company: str) -> bool:
        self.selected_company = company.strip() or self.selected_company
        return self._capture(self.selected_company)

    def _on_capture_requested(self) -> None:
        company = self.selected_company or self.window.current_company_text()
        self._capture(company)

    def _on_copy_zip_requested(self) -> None:
        if not self.latest_zip_path:
            self.window.show_error("Ingen ZIP-fil finns ännu.")
            return

        QApplication.clipboard().setText(self.latest_zip_path)
        self.window.show_success("ZIP-sökvägen kopierad")

    def _on_open_folder_requested(self) -> None:
        if not self.latest_zip_path:
            self.window.show_error("Ingen ZIP-fil finns ännu.")
            return

        Path(self.latest_zip_path).parent.mkdir(parents=True, exist_ok=True)
        try:
            import os

            os.startfile(Path(self.latest_zip_path).parent)  # type: ignore[attr-defined]
        except Exception as exc:
            self.window.show_error(f"Kunde inte öppna mapp: {exc}")

    def _on_clear_requested(self) -> None:
        self.selected_company = ""
        self.latest_zip_path = ""
        self.window.set_company_text("")
        self.window.set_company_results([])
        self.window.set_result(None, None)
        self.window.clear_log()
        self.window.set_status("Redo")
        self.window.set_connection_status("🟢 Printscreen redo")
        self.window.append_log("Rensat.")

    def shutdown(self) -> None:
        """Framtida städning när appen avslutas."""
        return None
