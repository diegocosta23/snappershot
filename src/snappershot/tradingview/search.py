from __future__ import annotations

import logging
import time

import pyautogui
import win32gui

from ..models.step_result import StepOutcome
from .window_manager import WindowManager

log = logging.getLogger(__name__)


class TradingViewSearch:
    """
    Öppnar TradingViews Symbol Search.

    V1-beteende:
    - Programmet öppnar bara sökrutan.
    - Användaren väljer aktie manuellt i TradingView.
    - Sedan klickar användaren Fortsätt i SnapperShot.
    """

    SEARCH_DELAY_SECONDS = 0.60
    RETRY_DELAY_SECONDS = 0.35
    MAX_RETRIES = 2

    def __init__(self, window: WindowManager | None = None) -> None:
        self.window = window or WindowManager()

    def prepare(self) -> StepOutcome:
        """
        Säkerställer att TradingView är redo.
        """
        return self.window.prepare()

    def _foreground_hwnd(self) -> int | None:
        try:
            return win32gui.GetForegroundWindow()
        except Exception as exc:
            log.debug("Kunde inte läsa foreground hwnd: %s", exc)
            return None

    def _is_expected_foreground(self) -> bool:
        hwnd = self.window.hwnd
        if hwnd is None:
            return False

        foreground = self._foreground_hwnd()
        return foreground == hwnd

    def _open_shortcut(self) -> StepOutcome:
        """
        Skickar kortkommandot som öppnar Symbol Search.
        """
        try:
            pyautogui.press("/")
            log.debug("TradingViewSearch: skickade '/'")
            return StepOutcome.success("Kortkommando skickat.")
        except Exception as exc:
            log.warning("Kunde inte skicka '/': %s", exc)
            return StepOutcome.fail(f"Kunde inte skicka '/' : {exc}")

    def open_symbol_search(self) -> StepOutcome:
        """
        Öppnar TradingViews Symbol Search.

        Returnerar StepOutcome:
            SUCCESS - sökgenvägen skickades och TradingView behöll fokus
            RETRY   - fokus tappades eller TradingView var inte redo
            FAIL    - kunde inte förbereda eller skicka kortkommandot
        """
        for attempt in range(1, self.MAX_RETRIES + 1):
            log.info(
                "TradingViewSearch.open_symbol_search: försök %d/%d",
                attempt,
                self.MAX_RETRIES,
            )

            ready = self.prepare()
            if not ready.ok:
                log.warning(
                    "TradingViewSearch: prepare() misslyckades: %s",
                    ready.message,
                )

                if ready.should_retry and attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_DELAY_SECONDS)
                    continue

                return StepOutcome.fail(
                    f"Kunde inte förbereda TradingView: {ready.message}"
                )

            hwnd = self.window.hwnd
            if hwnd is None:
                return StepOutcome.fail("TradingView-fönster saknas.")

            if not self._is_expected_foreground():
                focus = self.window.focus()
                if not focus.ok:
                    log.warning(
                        "TradingViewSearch: fokus kunde inte bekräftas: %s",
                        focus.message,
                    )

                    if focus.should_retry and attempt < self.MAX_RETRIES:
                        time.sleep(self.RETRY_DELAY_SECONDS)
                        continue

                    return StepOutcome.fail(
                        f"Kunde inte fokusera TradingView: {focus.message}"
                    )

            shortcut = self._open_shortcut()
            if not shortcut.ok:
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_DELAY_SECONDS)
                    continue
                return StepOutcome.fail(
                    f"Kunde inte öppna Symbol Search: {shortcut.message}"
                )

            time.sleep(self.SEARCH_DELAY_SECONDS)

            if not self._is_expected_foreground():
                log.warning(
                    "TradingView tappade fokus efter öppning av Symbol Search."
                )

                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_DELAY_SECONDS)
                    continue

                return StepOutcome.retry(
                    "TradingView tappade fokus efter att Symbol Search skulle öppnas."
                )

            log.info("Symbol Search öppnad.")
            return StepOutcome.success(
                "Symbol Search öppnad. Välj aktie i TradingView och klicka Fortsätt.",
                data=hwnd,
            )

        return StepOutcome.fail(
            f"Kunde inte öppna Symbol Search efter {self.MAX_RETRIES} försök."
        )

    def search(self, ticker: str) -> StepOutcome:
        _ = ticker
        return self.open_symbol_search()

    def search_and_select_first(self, ticker: str) -> StepOutcome:
        _ = ticker
        return self.open_symbol_search()
