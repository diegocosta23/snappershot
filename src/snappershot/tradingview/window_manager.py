from __future__ import annotations

import ctypes
import glob
import logging
import os
import time
from ctypes import wintypes
from pathlib import Path
from typing import Any

import win32con
import win32gui
import win32process
from pywinauto import Desktop

from snappershot.models.step_result import StepOutcome

log = logging.getLogger(__name__)

# =============================================================================
# Win32 setup
# =============================================================================

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
user32 = ctypes.WinDLL("user32", use_last_error=True)

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

kernel32.OpenProcess.argtypes = [
    wintypes.DWORD,
    wintypes.BOOL,
    wintypes.DWORD,
]
kernel32.OpenProcess.restype = wintypes.HANDLE

kernel32.QueryFullProcessImageNameW.argtypes = [
    wintypes.HANDLE,
    wintypes.DWORD,
    wintypes.LPWSTR,
    ctypes.POINTER(wintypes.DWORD),
]
kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL

kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL

user32.AttachThreadInput.argtypes = [
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.BOOL,
]
user32.AttachThreadInput.restype = wintypes.BOOL

# =============================================================================
# Konstanter
# =============================================================================

DEFAULT_WAIT_SECONDS = 20.0
POLL_INTERVAL_SECONDS = 0.50

FOCUS_RETRIES = 3
FOCUS_DELAY = 0.40
ACTION_DELAY = 0.25

MIN_WINDOW_WIDTH = 800
MIN_WINDOW_HEIGHT = 600


class WindowManager:
    """
    Ansvarar för att hitta, verifiera och aktivera TradingView Desktop.

    Behåller ett bool-kompatibelt API via StepOutcome:
        - SUCCESS => truthy
        - RETRY/FAIL => falsy
    """

    def __init__(self) -> None:
        self._hwnd: int | None = None
        self._window: Any | None = None

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def hwnd(self) -> int | None:
        """
        Returnerar cachad HWND om den fortfarande lever.
        """
        if self._is_cached_window_alive():
            return self._hwnd
        return None

    @property
    def window(self) -> Any | None:
        """
        Returnerar en pywinauto-wrapper för TradingView-fönstret.

        Behålls för bakåtkompatibilitet med befintlig kod som använder
        self.window.capture_as_image().
        """
        hwnd = self.hwnd
        if hwnd is None:
            self._window = None
            return None

        if self._window is not None:
            try:
                handle = getattr(self._window, "handle", None)
                if handle == hwnd:
                    return self._window
            except Exception:
                pass

        wrapper = self._resolve_wrapper(hwnd)
        self._window = wrapper
        return wrapper

    # -------------------------------------------------------------------------
    # Cache / validation helpers
    # -------------------------------------------------------------------------

    def _invalidate_cache(self) -> None:
        self._hwnd = None
        self._window = None

    def _is_cached_window_alive(self) -> bool:
        if self._hwnd is None:
            return False

        try:
            if not win32gui.IsWindow(self._hwnd):
                return False

            if not win32gui.IsWindowVisible(self._hwnd):
                return False

            return True
        except Exception:
            return False

    def _resolve_wrapper(self, hwnd: int) -> Any | None:
        """
        Försöker skapa en pywinauto-wrapper från HWND.
        """
        try:
            desktop = Desktop(backend="uia")
            spec = desktop.window(handle=hwnd)
            wrapper = spec.wrapper_object()
            return wrapper
        except Exception as exc:
            log.debug("Kunde inte skapa wrapper för hwnd=%s: %s", hwnd, exc)
            return None

    def _process_name(self, hwnd: int) -> str:
        """
        Returnerar exe-namn för processen som äger hwnd.
        """
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)

            handle = kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION,
                False,
                pid,
            )

            if not handle:
                return ""

            try:
                size = wintypes.DWORD(1024)
                buffer = ctypes.create_unicode_buffer(size.value)

                ok = kernel32.QueryFullProcessImageNameW(
                    handle,
                    0,
                    buffer,
                    ctypes.byref(size),
                )

                if not ok:
                    return ""

                return Path(buffer.value).name.lower()

            finally:
                kernel32.CloseHandle(handle)

        except Exception as exc:
            log.debug("Kunde inte läsa processnamn för hwnd=%s: %s", hwnd, exc)
            return ""

    def _process_id(self, hwnd: int) -> int:
        """
        Returnerar PID för fönstret.
        """
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            return int(pid)
        except Exception:
            return 0

    def _window_title(self, hwnd: int) -> str:
        try:
            return str(win32gui.GetWindowText(hwnd) or "")
        except Exception:
            return ""

    def _window_class(self, hwnd: int) -> str:
        try:
            return str(win32gui.GetClassName(hwnd) or "")
        except Exception:
            return ""

    def _window_rect(self, hwnd: int) -> tuple[int, int, int, int] | None:
        try:
            rect = win32gui.GetWindowRect(hwnd)
            left, top, right, bottom = rect
            if right <= left:
                return None
            if bottom <= top:
                return None
            return left, top, right, bottom
        except Exception:
            return None

    def _window_area(self, hwnd: int) -> int:
        rect = self._window_rect(hwnd)
        if rect is None:
            return 0
        left, top, right, bottom = rect
        return max(0, (right - left) * (bottom - top))

    def _is_tradingview_window(self, hwnd: int) -> bool:
        """
        Returnerar True om hwnd tillhör TradingView Desktop.
        """
        if not win32gui.IsWindow(hwnd):
            return False

        if not win32gui.IsWindowVisible(hwnd):
            return False

        if win32gui.GetParent(hwnd):
            return False

        title = self._window_title(hwnd).lower()
        process = self._process_name(hwnd)

        if process == "tradingview.exe":
            return True

        if "tradingview" in title:
            return True

        return False

    def _window_score(self, hwnd: int) -> tuple[int, int, int]:
        """
        Returnerar en sorteringsnyckel:
            (score, area, hwnd)

        Högre score = bättre kandidat.
        """
        title = self._window_title(hwnd).lower()
        process = self._process_name(hwnd)
        cls = self._window_class(hwnd).lower()
        area = self._window_area(hwnd)

        score = 0

        if process == "tradingview.exe":
            score += 1000

        if "tradingview" in title:
            score += 250

        if "tradingview" in cls:
            score += 50

        if area >= MIN_WINDOW_WIDTH * MIN_WINDOW_HEIGHT:
            score += min(area // 1000, 500)

        if win32gui.IsIconic(hwnd):
            score -= 150

        if "splash" in title:
            score -= 400

        if "update" in title:
            score -= 200

        return score, area, hwnd

    def _scan_windows(self) -> list[int]:
        """
        Hittar alla kandidater som ser ut att vara TradingView.
        """
        candidates: list[int] = []

        def callback(hwnd: int, _: Any) -> bool:
            try:
                if self._is_tradingview_window(hwnd):
                    candidates.append(hwnd)
            except Exception as exc:
                log.debug("EnumWindows callback misslyckades för hwnd=%s: %s", hwnd, exc)
            return True

        win32gui.EnumWindows(callback, None)

        if not candidates:
            return []

        candidates.sort(key=self._window_score, reverse=True)
        return candidates

    def _candidate_executables(self) -> list[Path]:
        """
        Försöker hitta TradingView.exe utan hårdkodad versionssökväg.
        """
        candidates: list[Path] = []

        env = os.environ.get("SNAPPERSHOT_TRADINGVIEW_EXE", "").strip()
        if env:
            candidates.append(Path(env))

        patterns = [
            r"C:\Program Files\WindowsApps\TradingView.Desktop_*_x64_*\TradingView.exe",
            str(Path.home() / "AppData" / "Local" / "Microsoft" / "WindowsApps" / "TradingView.exe"),
        ]

        for pattern in patterns:
            for exe in glob.glob(pattern):
                path = Path(exe)
                if path.exists():
                    candidates.append(path)

        unique: list[Path] = []
        seen: set[str] = set()
        for path in candidates:
            key = str(path).lower()
            if key not in seen:
                seen.add(key)
                unique.append(path)

        return unique

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def find(self) -> StepOutcome:
        """
        Söker efter TradingView Desktop och cachar fönstret.
        """
        if self._is_cached_window_alive():
            hwnd = self._hwnd
            if hwnd is not None:
                title = self._window_title(hwnd)
                log.debug("TradingView hittad via cache: hwnd=%s title=%s", hwnd, title)
                if self._window is None:
                    self._window = self._resolve_wrapper(hwnd)
                return StepOutcome.success(
                    f"TradingView redan hittad: {title}",
                    data=hwnd,
                )

        self._invalidate_cache()

        windows = self._scan_windows()

        if not windows:
            return StepOutcome.fail("TradingView Desktop hittades inte.")

        hwnd = windows[0]
        self._hwnd = hwnd
        self._window = self._resolve_wrapper(hwnd)

        title = self._window_title(hwnd)
        pid = self._process_id(hwnd)
        process = self._process_name(hwnd)
        cls = self._window_class(hwnd)
        rect = self._window_rect(hwnd)

        log.info(
            "TradingView hittad hwnd=%s pid=%s process=%s class=%s title=%s rect=%s",
            hwnd,
            pid,
            process,
            cls,
            title,
            rect,
        )

        return StepOutcome.success(
            f"Hittade TradingView: {title}",
            data=hwnd,
        )

    def launch(self) -> StepOutcome:
        """
        Försöker starta TradingView Desktop.
        """
        for executable in self._candidate_executables():
            try:
                os.startfile(str(executable))
                log.info("Startade TradingView: %s", executable)
                return StepOutcome.success(
                    f"Startade TradingView ({executable.name})",
                    data=executable,
                )
            except Exception as exc:
                log.warning("Kunde inte starta %s: %s", executable, exc)

        return StepOutcome.fail("Ingen TradingView-installation hittades.")

    def ensure_running(self) -> StepOutcome:
        """
        Säkerställer att TradingView körs och att fönstret går att hitta.
        """
        result = self.find()
        if result.ok:
            return result

        launch = self.launch()
        if not launch.ok:
            return launch

        deadline = time.monotonic() + DEFAULT_WAIT_SECONDS

        while time.monotonic() < deadline:
            time.sleep(POLL_INTERVAL_SECONDS)
            result = self.find()
            if result.ok:
                return result

        return StepOutcome.fail("TradingView startade aldrig.")

    def restore(self) -> StepOutcome:
        """
        Återställer TradingView-fönstret.
        """
        result = self.find()
        if not result.ok:
            return result

        hwnd = self.hwnd
        if hwnd is None:
            return StepOutcome.fail("TradingView-fönster saknas.")

        try:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            time.sleep(ACTION_DELAY)
            return StepOutcome.success("TradingView återställd.", data=hwnd)
        except Exception as exc:
            log.exception("Kunde inte återställa fönstret: %s", exc)
            return StepOutcome.fail(f"Kunde inte återställa fönstret: {exc}")

    def maximize(self) -> StepOutcome:
        """
        Maximerar TradingView-fönstret.
        """
        result = self.find()
        if not result.ok:
            return result

        hwnd = self.hwnd
        if hwnd is None:
            return StepOutcome.fail("TradingView-fönster saknas.")

        try:
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            time.sleep(ACTION_DELAY)
            return StepOutcome.success("TradingView maximerad.", data=hwnd)
        except Exception as exc:
            log.exception("Kunde inte maximera fönstret: %s", exc)
            return StepOutcome.fail(f"Kunde inte maximera fönstret: {exc}")

    def focus(self) -> StepOutcome:
        """
        Försöker ge TradingView fokus och verifierar att det lyckades.
        """
        ready = self.ensure_running()
        if not ready.ok:
            return ready

        hwnd = self.hwnd
        if hwnd is None:
            return StepOutcome.fail("TradingView-fönster saknas.")

        try:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            time.sleep(0.10)
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            time.sleep(0.10)
        except Exception:
            pass

        for attempt in range(1, FOCUS_RETRIES + 1):
            current_tid = 0
            target_tid = 0
            attached = False

            try:
                foreground = win32gui.GetForegroundWindow()
                current_tid, _ = win32process.GetWindowThreadProcessId(foreground)
                target_tid, _ = win32process.GetWindowThreadProcessId(hwnd)

                if current_tid and target_tid and current_tid != target_tid:
                    try:
                        attached = bool(user32.AttachThreadInput(current_tid, target_tid, True))
                    except Exception:
                        attached = False

                try:
                    win32gui.BringWindowToTop(hwnd)
                except Exception:
                    pass

                try:
                    win32gui.SetForegroundWindow(hwnd)
                except Exception:
                    pass

                try:
                    win32gui.SetActiveWindow(hwnd)
                except Exception:
                    pass

                try:
                    win32gui.SetFocus(hwnd)
                except Exception:
                    pass

                time.sleep(FOCUS_DELAY)

                active = win32gui.GetForegroundWindow()
                if active == hwnd:
                    log.info("TradingView har fokus (försök %d).", attempt)
                    return StepOutcome.success("TradingView har fokus.", data=hwnd)

                log.warning(
                    "Fokusförsök %d misslyckades: active=%s expected=%s",
                    attempt,
                    active,
                    hwnd,
                )

            except Exception as exc:
                log.exception("Fokusförsök %d misslyckades: %s", attempt, exc)

            finally:
                try:
                    if attached and current_tid and target_tid and current_tid != target_tid:
                        user32.AttachThreadInput(current_tid, target_tid, False)
                except Exception:
                    pass

            time.sleep(0.40)

        self._invalidate_cache()
        return StepOutcome.retry("TradingView kunde inte få fokus.")

    def prepare(self) -> StepOutcome:
        """
        Komplett förberedelse innan automation.
        """
        running = self.ensure_running()
        if not running.ok:
            return running

        restored = self.restore()
        if not restored.ok:
            return restored

        maximized = self.maximize()
        if not maximized.ok:
            return maximized

        focused = self.focus()
        if not focused.ok:
            return focused

        return StepOutcome.success("TradingView är redo.", data=self.hwnd)

    def activate(self) -> StepOutcome:
        """
        Bakåtkompatibel alias för prepare().
        """
        return self.prepare()

    def title(self) -> str:
        """
        Returnerar TradingViews fönstertitel.
        """
        hwnd = self.hwnd
        if hwnd is None:
            return ""

        try:
            return str(win32gui.GetWindowText(hwnd) or "")
        except Exception:
            return ""

    def get_rect(self) -> tuple[int, int, int, int] | None:
        """
        Returnerar fönstrets koordinater.
        """
        hwnd = self.hwnd
        if hwnd is None:
            return None

        try:
            if win32gui.IsIconic(hwnd):
                return None

            left, top, right, bottom = win32gui.GetWindowRect(hwnd)

            if right <= left or bottom <= top:
                return None

            width = right - left
            height = bottom - top

            if width < MIN_WINDOW_WIDTH or height < MIN_WINDOW_HEIGHT:
                return None

            return left, top, right, bottom

        except Exception as exc:
            log.debug("Kunde inte hämta fönsterkoordinater: %s", exc)
            return None