from __future__ import annotations

import logging
import time
from typing import Iterable

import pyautogui
import win32gui

from snappershot.models.step_result import StepOutcome
from snappershot.tradingview.window_manager import WindowManager

log = logging.getLogger(__name__)

VALID_TIMEFRAMES: tuple[str, ...] = ("1W", "1D", "4H", "45M")

OPEN_DELAY_SECONDS = 0.45
LOAD_DELAY_SECONDS = 1.50
RETRY_DELAY_SECONDS = 0.35
MAX_RETRIES = 3
BACKSPACE_COUNT = 6


class TimeframeController:
    """
    Byter tidsram i TradingView Desktop.

    V1-beteende:
    - Använder endast kortkommandot "," för att öppna timeframe-fältet.
    - Rensar innehåll med Backspace, inte Ctrl+A.
    - Verifierar fokus före och efter tangenttryckningar.
    - Returnerar StepOutcome.
    """

    def __init__(self, window: WindowManager | None = None) -> None:
        self.window = window or WindowManager()

    def prepare(self) -> StepOutcome:
        """
        Säkerställer att TradingView är redo för tangentinmatning.
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

    def _press_shortcut(self) -> StepOutcome:
        """
        Skickar kortkommandot som öppnar timeframe-fältet.
        """
        try:
            pyautogui.press(",")
            log.debug("TimeframeController: skickade ','")
            return StepOutcome.success("Kortkommando skickat.")
        except Exception as exc:
            log.warning("Kunde inte skicka ',': %s", exc)
            return StepOutcome.fail(f"Kunde inte skicka ',': {exc}")

    def _clear_field(self) -> StepOutcome:
        """
        Rensar fältet med Backspace.
        """
        try:
            for _ in range(BACKSPACE_COUNT):
                pyautogui.press("backspace")
                time.sleep(0.03)
            return StepOutcome.success("Fält rensat.")
        except Exception as exc:
            log.warning("Kunde inte rensa timeframe-fältet: %s", exc)
            return StepOutcome.fail(f"Kunde inte rensa timeframe-fältet: {exc}")

    def _write_timeframe(self, timeframe: str) -> StepOutcome:
        """
        Skriver in timeframe.
        """
        try:
            pyautogui.write(timeframe, interval=0.05)
            log.debug("TimeframeController: skrev '%s'", timeframe)
            return StepOutcome.success("Timeframe skriven.")
        except Exception as exc:
            log.warning("Kunde inte skriva timeframe '%s': %s", timeframe, exc)
            return StepOutcome.fail(f"Kunde inte skriva timeframe '{timeframe}': {exc}")

    def _press_enter(self) -> StepOutcome:
        """
        Bekräftar valet.
        """
        try:
            pyautogui.press("enter")
            log.debug("TimeframeController: tryckte Enter")
            return StepOutcome.success("Enter skickat.")
        except Exception as exc:
            log.warning("Kunde inte skicka Enter: %s", exc)
            return StepOutcome.fail(f"Kunde inte skicka Enter: {exc}")

    def _attempt_set(self, timeframe: str) -> StepOutcome:
        """
        Ett försök att byta timeframe.
        """
        focus = self.window.focus()
        if not focus.ok:
            return StepOutcome.retry(f"Fokus misslyckades: {focus.message}")

        hwnd = self.window.hwnd
        if hwnd is None:
            return StepOutcome.fail("TradingView-fönster saknas.")

        if not self._is_expected_foreground():
            return StepOutcome.retry(
                "TradingView tappade fokus precis innan timeframe skulle ändras."
            )

        shortcut = self._press_shortcut()
        if not shortcut.ok:
            return shortcut

        time.sleep(OPEN_DELAY_SECONDS)

        if not self._is_expected_foreground():
            return StepOutcome.retry(
                "TradingView tappade fokus efter att timeframe-fältet skulle öppnas."
            )

        cleared = self._clear_field()
        if not cleared.ok:
            return cleared

        written = self._write_timeframe(timeframe)
        if not written.ok:
            return written

        pressed = self._press_enter()
        if not pressed.ok:
            return pressed

        time.sleep(LOAD_DELAY_SECONDS)

        if not self._is_expected_foreground():
            return StepOutcome.retry(
                "TradingView tappade fokus efter att timeframe skulle bytas."
            )

        return StepOutcome.success(
            f"Tidsram satt till {timeframe}.",
            data=timeframe,
        )

    def set(self, timeframe: str) -> StepOutcome:
        """
        Byter till angiven tidsram.

        Tillåtna värden:
        - 1W
        - 1D
        - 4H
        - 45M
        """
        tf = timeframe.strip().upper()

        if tf not in VALID_TIMEFRAMES:
            return StepOutcome.fail(
                f"Ogiltig tidsram: '{timeframe}'. "
                f"Tillåtna värden: {', '.join(VALID_TIMEFRAMES)}"
            )

        for attempt in range(1, MAX_RETRIES + 1):
            log.info(
                "TimeframeController.set: %s (försök %d/%d)",
                tf,
                attempt,
                MAX_RETRIES,
            )

            outcome = self._attempt_set(tf)

            if outcome.ok:
                return outcome

            log.warning(
                "TimeframeController.set: försök %d misslyckades: %s",
                attempt,
                outcome.message,
            )

            if outcome.should_retry and attempt < MAX_RETRIES:
                try:
                    pyautogui.press("escape")
                except Exception:
                    pass
                time.sleep(RETRY_DELAY_SECONDS)
                continue

            return outcome

        return StepOutcome.fail(
            f"Kunde inte byta till tidsram {tf} efter {MAX_RETRIES} försök."
        )

    def cycle(self, timeframes: Iterable[str]) -> StepOutcome:
        """
        Byter tidsramar i ordning.
        """
        for timeframe in timeframes:
            outcome = self.set(timeframe)
            if not outcome.ok:
                return StepOutcome.fail(
                    f"Tidsramsbyte misslyckades vid {timeframe}: {outcome.message}"
                )
        return StepOutcome.success("Alla tidsramar genomförda.")