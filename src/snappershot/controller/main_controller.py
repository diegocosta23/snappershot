from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from PySide6.QtWidgets import QApplication

try:
    import pythoncom
except ImportError:  # pragma: no cover - optional on non-Windows platforms
    pythoncom = None

from ..controller.capture_pipeline import CapturePipeline
from ..models.capture_result import CaptureResult
from ..symbols.symbol_resolver import SymbolResolver

log = logging.getLogger(__name__)


class MainController:
    """
    Kopplar UI:t till CapturePipeline.

    Ansvar:
    - hantera företagssökning
    - starta capture-flödet
    - uppdatera status, progress och resultat i GUI
    - kopiera ZIP, öppna mapp och rensa visningen
    """

    DEFAULT_TIMEFRAMES = ["1W", "1D", "4H", "45M"]

    def __init__(self, view: Any | None = None) -> None:
        self.view: Any | None = None
        self.capture_pipeline = CapturePipeline(log_callback=self._append_log)
        self.company_service = self.capture_pipeline.company_service
        self.symbol_resolver = SymbolResolver()

        if view is not None:
            self.bind_view(view)

    # ---------------------------------------------------------------------
    # View binding
    # ---------------------------------------------------------------------

    def bind_view(self, view: Any) -> None:
        self.view = view
        self._connect_signals()
        self.refresh_connection_status()
        self._refresh_company_results_from_current_text()

    def _connect_signals(self) -> None:
        if self.view is None:
            return

        self._connect_signal("capture_requested", self.handle_capture_requested)
        self._connect_signal("search_text_changed", self.handle_search_text_changed)
        self._connect_signal("company_selected", self.handle_company_selected)
        self._connect_signal("copy_zip_requested", self.handle_copy_zip_requested)
        self._connect_signal("open_folder_requested", self.handle_open_folder_requested)
        self._connect_signal("clear_requested", self.handle_clear_requested)

    def _connect_signal(self, signal_name: str, handler: Any) -> None:
        if self.view is None:
            return

        signal = getattr(self.view, signal_name, None)
        if signal is None:
            return

        try:
            signal.connect(handler)
        except Exception as exc:
            log.debug("Kunde inte koppla signal %s: %s", signal_name, exc)

    # ---------------------------------------------------------------------
    # Safe view helpers
    # ---------------------------------------------------------------------

    def _call_view(
        self,
        method_name: str,
        *args: Any,
        default: Any = None,
        **kwargs: Any,
    ) -> Any:
        if self.view is None:
            return default

        method = getattr(self.view, method_name, None)
        if not callable(method):
            return default

        try:
            return method(*args, **kwargs)
        except Exception as exc:
            log.debug("View-metod %s misslyckades: %s", method_name, exc)
            return default

    def _process_events(self) -> None:
        try:
            app = QApplication.instance()
            if app is not None:
                app.processEvents()
        except Exception:
            pass

    # ---------------------------------------------------------------------
    # Logging / status
    # ---------------------------------------------------------------------

    def _append_log(self, message: str) -> None:
        log.info(message)
        self._call_view("append_log", message)

    def _set_status(self, text: str) -> None:
        self._call_view("set_status", text)

    def _set_connection_status(self, text: str) -> None:
        self._call_view("set_connection_status", text)

    def _set_progress(self, value: int) -> None:
        self._call_view("set_progress", value)

    def _set_busy(self, busy: bool) -> None:
        self._call_view("set_busy", busy)
        self._process_events()

    def _set_result(self, filename: str | None, path: str | None) -> None:
        self._call_view("set_result", filename, path)

    def _show_error(self, message: str) -> None:
        self._call_view("show_error", message)
        self._append_log(message)

    def _show_success(self, message: str) -> None:
        self._call_view("show_success", message)
        self._append_log(message)

    # ---------------------------------------------------------------------
    # Company search
    # ---------------------------------------------------------------------

    def _format_symbol_result(self, result: dict[str, Any]) -> str:
        name = str(result.get("name") or "").strip()
        symbol = str(result.get("symbol") or "").strip()
        exchange = str(result.get("exchange") or "").strip()

        return "\n".join(part for part in (name, symbol, exchange) if part)

    def search_companies(self, query: str) -> list[str]:
        """
        Returnerar matchande företag som strängar för UI:t.
        """
        needle = query.strip()
        if len(needle) < 2:
            return []

        try:
            matches = self.symbol_resolver.search(query)
        except Exception as exc:
            log.debug("SymbolResolver.search misslyckades: %s", exc)
            return []

        results: list[str] = []
        for match in matches:
            label = self._format_symbol_result(match)
            if not label:
                continue
            results.append(label)

        return results[:25]

    def _update_company_results_for_query(self, query: str) -> None:
        self._call_view("set_company_results", self.search_companies(query))

    def _refresh_company_results_from_current_text(self) -> None:
        self._call_view("set_company_results", self.search_companies(self.current_company_text()))

    def current_company_text(self) -> str:
        value = self._call_view("current_company_text", default="")
        return str(value or "").strip()

    def _normalize_company_name(self, text: str) -> str:
        cleaned = text.strip()
        if " (" in cleaned and cleaned.endswith(")"):
            cleaned = cleaned.rsplit(" (", 1)[0].strip()
        return cleaned

    def selected_timeframes(self) -> list[str]:
        value = self._call_view("selected_timeframes", default=None)
        if isinstance(value, list):
            timeframes = [str(item).strip() for item in value if str(item).strip()]
            return timeframes or list(self.DEFAULT_TIMEFRAMES)
        return list(self.DEFAULT_TIMEFRAMES)

    # ---------------------------------------------------------------------
    # Connection status
    # ---------------------------------------------------------------------

    def refresh_connection_status(self) -> None:
        """
        Uppdaterar statusraden för TradingView utan att starta något.
        """
        window = self.capture_pipeline.window
        result = window.find()

        if result.ok:
            title = window.title() or "ansluten"
            self._set_connection_status(f"TradingView Desktop: {title}")
        else:
            self._set_connection_status("TradingView Desktop: väntar på anslutning")

    # ---------------------------------------------------------------------
    # Signal handlers
    # ---------------------------------------------------------------------

    def handle_search_text_changed(self, text: str) -> None:
        self._update_company_results_for_query(text)

    def handle_company_selected(self, company_text: str) -> None:
        normalized = self._normalize_company_name(company_text)
        self._call_view("set_company_text", normalized)

    def handle_capture_requested(self) -> None:
        archive_name = self._normalize_company_name(self.current_company_text())

        if not archive_name:
            self._show_error("Skriv ett ZIP-filnamn först.")
            return

        timeframes = self.selected_timeframes()

        self._set_busy(True)
        self._set_status("Arbetar...")
        self._set_progress(5)
        self._append_log(f"Startar capture med ZIP-filnamn {archive_name} ...")
        self._process_events()

        try:
            result = self.capture_pipeline.capture_company(archive_name, timeframes)
            self._apply_capture_result(result)
        except Exception as exc:
            log.exception("Capture misslyckades med undantag: %s", exc)
            self._set_result(None, None)
            self._set_progress(0)
            self._show_error(f"Capture misslyckades: {exc}")
        finally:
            self._set_busy(False)
            self._process_events()

    def _apply_capture_result(self, result: CaptureResult) -> None:
        if result.success:
            zip_path = result.zip_path

            if zip_path is not None:
                self._set_result(zip_path.name, str(zip_path))
            else:
                self._set_result(None, None)

            self._set_progress(100)
            self._set_status("Klar")
            self._show_success(result.message or "Capture klar.")
            self._append_log(
                f"ZIP skapad för {result.company_name} med {result.screenshot_count} screenshots."
            )
        else:
            self._set_result(None, None)
            self._set_progress(0)
            self._set_status("Fel")
            self._show_error(result.message or "Capture misslyckades.")

    def _copy_text_to_clipboard(self, text: str) -> None:
        if pythoncom is not None:
            pythoncom.CoInitialize()
            try:
                QApplication.clipboard().setText(text)
            finally:
                pythoncom.CoUninitialize()
            return

        QApplication.clipboard().setText(text)

    def handle_copy_zip_requested(self) -> None:
        path_text = str(self._call_view("selected_zip_path", default="") or "").strip()

        if not path_text:
            self._show_error("Ingen ZIP att kopiera än.")
            return

        try:
            self._copy_text_to_clipboard(path_text)
            self._show_success(f"ZIP kopierad till urklipp: {path_text}")
        except Exception as exc:
            self._show_error(f"Kunde inte kopiera ZIP till urklipp: {exc}")

    def handle_open_folder_requested(self) -> None:
        path_text = str(self._call_view("selected_zip_path", default="") or "").strip()

        if not path_text:
            self._show_error("Ingen ZIP-mapp att öppna än.")
            return

        folder = Path(path_text).parent

        if not folder.exists():
            self._show_error(f"Mappen finns inte: {folder}")
            return

        try:
            os.startfile(str(folder))
            self._show_success(f"Öppnade mapp: {folder}")
        except Exception as exc:
            self._show_error(f"Kunde inte öppna mappen: {exc}")

    def handle_clear_requested(self) -> None:
        self._call_view("set_company_text", "")
        self._call_view("set_company_results", [])
        self._set_result(None, None)
        self._set_status("Redo")
        self._set_progress(0)
        self._call_view("clear_log")
        self._set_connection_status("TradingView Desktop: väntar på anslutning")
        self._append_log("Visning rensad.")

    # ---------------------------------------------------------------------
    # Compatibility
    # ---------------------------------------------------------------------

    def start(self) -> None:
        """
        Bakåtkompatibel startmetod.
        """
        self.refresh_connection_status()
        self._refresh_company_results_from_current_text()
