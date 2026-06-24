from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from PySide6.QtWidgets import QApplication

from ..controller.capture_pipeline import CapturePipeline
from ..models.capture_result import CaptureResult

log = logging.getLogger(__name__)


class MainController:
    """
    Kopplar UI:t till CapturePipeline.

    Ansvar:
    - Hantera användarens sökning efter företag
    - Starta capture-flödet
    - Uppdatera resultat, status och logg i GUI
    - Hantera kopiera/öppna/rensa-åtgärder
    """

    DEFAULT_TIMEFRAMES = ["1W", "1D", "4H", "45M"]

    def __init__(self, view: Any | None = None) -> None:
        self.view: Any | None = None
        self.capture_pipeline = CapturePipeline(log_callback=self._append_log)
        self.company_service = self.capture_pipeline.company_service
        self._company_cache: list[Any] = []
        self._company_cache_loaded = False

        if view is not None:
            self.bind_view(view)

    # -------------------------------------------------------------------------
    # View binding
    # -------------------------------------------------------------------------

    def bind_view(self, view: Any) -> None:
        """
        Binder controller till ett MainWindow-liknande view-objekt.
        """
        self.view = view
        self._connect_signals()
        self.refresh_connection_status()
        self._refresh_company_results_from_current_text()

    def _connect_signals(self) -> None:
        """
        Kopplar signaler om de finns på view:t.
        """
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

    # -------------------------------------------------------------------------
    # Safe view helpers
    # -------------------------------------------------------------------------

    def _call_view(
        self, method_name: str, *args: Any, default: Any = None, **kwargs: Any
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

    # -------------------------------------------------------------------------
    # Logging / status helpers
    # -------------------------------------------------------------------------

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

    # -------------------------------------------------------------------------
    # Company search
    # -------------------------------------------------------------------------

    def _company_data_path(self) -> Path:
        return Path(__file__).resolve().parents[1] / "data" / "companies.json"

    def _load_company_cache(self) -> list[Any]:
        if self._company_cache_loaded:
            return self._company_cache

        self._company_cache_loaded = True
        cache: list[Any] = []

        # 1) Försök från CompanyService om den har någon list-/iter-metod.
        cache = self._load_company_cache_from_service()
        if cache:
            self._company_cache = cache
            return cache

        # 2) Fallback till JSON-filen.
        cache = self._load_company_cache_from_json()
        self._company_cache = cache
        return cache

    def _load_company_cache_from_service(self) -> list[Any]:
        service = self.company_service
        if service is None:
            return []

        candidate_methods = (
            "iter_companies",
            "all_companies",
            "get_all",
            "get_all_companies",
            "list",
            "all",
            "items",
        )

        for method_name in candidate_methods:
            method = getattr(service, method_name, None)
            if not callable(method):
                continue

            try:
                result = method()
            except TypeError:
                continue
            except Exception as exc:
                log.debug("CompanyService.%s misslyckades: %s", method_name, exc)
                continue

            if result is None:
                continue

            try:
                return list(result)
            except TypeError:
                return [result]

        direct_attrs = (
            "companies",
            "_companies",
            "catalog",
            "_catalog",
            "records",
            "_records",
        )

        for attr_name in direct_attrs:
            value = getattr(service, attr_name, None)
            if value is None:
                continue

            if isinstance(value, dict):
                return list(value.values())

            if isinstance(value, (list, tuple, set)):
                return list(value)

        return []

    def _load_company_cache_from_json(self) -> list[Any]:
        path = self._company_data_path()
        if not path.exists():
            return []

        try:
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception as exc:
            log.debug("Kunde inte läsa companies.json: %s", exc)
            return []

        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            if isinstance(data.get("companies"), list):
                return list(data["companies"])

            values = list(data.values())
            if values:
                return values

        return []

    def _entry_name(self, entry: Any) -> str:
        if isinstance(entry, dict):
            for key in ("name", "company_name", "title", "display_name"):
                value = entry.get(key)
                if value:
                    return str(value).strip()
            ticker = entry.get("ticker") or entry.get("symbol")
            if ticker:
                return str(ticker).strip()
            return ""

        for attr in ("name", "company_name", "title", "display_name"):
            value = getattr(entry, attr, None)
            if value:
                return str(value).strip()

        ticker = getattr(entry, "ticker", None) or getattr(entry, "symbol", None)
        if ticker:
            return str(ticker).strip()

        return ""

    def _entry_ticker(self, entry: Any) -> str:
        if isinstance(entry, dict):
            for key in ("ticker", "symbol"):
                value = entry.get(key)
                if value:
                    return str(value).strip()
            return ""

        for attr in ("ticker", "symbol"):
            value = getattr(entry, attr, None)
            if value:
                return str(value).strip()

        return ""

    def _entry_aliases(self, entry: Any) -> list[str]:
        aliases: list[str] = []

        if isinstance(entry, dict):
            for key in ("aliases", "alias", "names", "search_terms"):
                value = entry.get(key)
                if isinstance(value, (list, tuple, set)):
                    aliases.extend(str(item).strip() for item in value if item)
                elif value:
                    aliases.append(str(value).strip())
        else:
            for attr in ("aliases", "alias", "names", "search_terms"):
                value = getattr(entry, attr, None)
                if isinstance(value, (list, tuple, set)):
                    aliases.extend(str(item).strip() for item in value if item)
                elif value:
                    aliases.append(str(value).strip())

        return [alias for alias in aliases if alias]

    def _entry_label(self, entry: Any) -> str:
        name = self._entry_name(entry)
        ticker = self._entry_ticker(entry)

        if name and ticker and ticker.casefold() not in name.casefold():
            return f"{name} ({ticker})"

        if name:
            return name

        if ticker:
            return ticker

        return ""

    def _normalize_company_name(self, text: str) -> str:
        cleaned = text.strip()

        if " (" in cleaned and cleaned.endswith(")"):
            cleaned = cleaned.rsplit(" (", 1)[0].strip()

        return cleaned

    def search_companies(self, query: str) -> list[str]:
        """
        Returnerar matchande företag som strängar att visa i UI.
        """
        needle = query.strip().casefold()
        if len(needle) < 2:
            return []

        results: list[str] = []
        seen: set[str] = set()

        for entry in self._load_company_cache():
            label = self._entry_label(entry)
            if not label:
                continue

            name = self._entry_name(entry)
            ticker = self._entry_ticker(entry)
            aliases = self._entry_aliases(entry)

            haystack_parts = [label, name, ticker, *aliases]
            haystack = " ".join(part for part in haystack_parts if part).casefold()

            if needle in haystack:
                if label not in seen:
                    seen.add(label)
                    results.append(label)

        return results[:25]

    def _refresh_company_results_from_current_text(self) -> None:
        text = self.current_company_text()
        self._update_company_results_for_query(text)

    def _update_company_results_for_query(self, query: str) -> None:
        results = self.search_companies(query)
        self._call_view("set_company_results", results)

    def current_company_text(self) -> str:
        value = self._call_view("current_company_text", default="")
        return str(value or "").strip()

    def selected_timeframes(self) -> list[str]:
        value = self._call_view("selected_timeframes", default=None)
        if isinstance(value, list):
            timeframes = [str(item).strip() for item in value if str(item).strip()]
            return timeframes or list(self.DEFAULT_TIMEFRAMES)
        return list(self.DEFAULT_TIMEFRAMES)

    # -------------------------------------------------------------------------
    # Connection status
    # -------------------------------------------------------------------------

    def refresh_connection_status(self) -> None:
        """
        Uppdaterar statusraden för TradingView-anslutning utan att starta appen.
        """
        window = self.capture_pipeline.window
        result = window.find()

        if result.ok:
            title = window.title() or "ansluten"
            self._set_connection_status(f"TradingView Desktop: {title}")
        else:
            self._set_connection_status("TradingView Desktop: väntar på anslutning")

    # -------------------------------------------------------------------------
    # Signal handlers
    # -------------------------------------------------------------------------

    def handle_search_text_changed(self, text: str) -> None:
        self._update_company_results_for_query(text)

    def handle_company_selected(self, company_text: str) -> None:
        normalized = self._normalize_company_name(company_text)
        self._call_view("set_company_text", normalized)
        self._set_status(f"Valt bolag: {normalized}")

    def handle_capture_requested(self) -> None:
        company_text = self._normalize_company_name(self.current_company_text())

        if not company_text:
            self._show_error("Skriv ett företagsnamn först.")
            return

        timeframes = self.selected_timeframes()

        self._set_busy(True)
        self._set_status("Arbetar...")
        self._set_progress(5)
        self._append_log(f"Startar capture för {company_text} ...")
        self._process_events()

        try:
            result = self.capture_pipeline.capture_company(company_text, timeframes)
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

    def handle_copy_zip_requested(self) -> None:
        path_text = str(self._call_view("selected_zip_path", default="") or "").strip()

        if not path_text:
            self._show_error("Ingen ZIP att kopiera än.")
            return

        try:
            app = QApplication.instance()
            if app is None:
                raise RuntimeError("Qt-applikationen saknas.")
            app.clipboard().setText(path_text)
            self._show_success(f"ZIP-kopierad till urklipp: {path_text}")
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

    # -------------------------------------------------------------------------
    # Compatibility helpers
    # -------------------------------------------------------------------------

    def start(self) -> None:
        """
        Bakåtkompatibel startmetod om appen vill kalla explicit start.
        """
        self.refresh_connection_status()
        self._refresh_company_results_from_current_text()
