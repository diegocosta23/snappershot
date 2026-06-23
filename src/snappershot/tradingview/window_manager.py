from __future__ import annotations

import ctypes
import os
import time
from ctypes import wintypes
from pathlib import Path
from typing import Any

from pywinauto import Desktop

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
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


class WindowManager:
    """
    Ansvarar för att hitta, starta och aktivera TradingView Desktop.
    """

    DEFAULT_WAIT_SECONDS = 20.0
    POLL_INTERVAL_SECONDS = 0.5

    def __init__(self) -> None:
        self.window: Any | None = None

    def _candidate_executables(self) -> list[Path]:
        candidates: list[Path] = []

        env_path = os.environ.get("SNAPPERSHOT_TRADINGVIEW_EXE", "").strip()
        if env_path:
            candidates.append(Path(env_path))

        candidates.append(
            Path.home()
            / "AppData"
            / "Local"
            / "Microsoft"
            / "WindowsApps"
            / "TradingView.exe"
        )

        candidates.append(
            Path(
                r"C:\Program Files\WindowsApps\TradingView.Desktop_3.2.0.7916_x64__n534cwy3pjxzj\TradingView.exe"
            )
        )

        return candidates

    def _process_name_from_pid(self, pid: int) -> str:
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return ""

        try:
            buffer_size = wintypes.DWORD(1024)
            buffer = ctypes.create_unicode_buffer(buffer_size.value)

            if kernel32.QueryFullProcessImageNameW(
                handle,
                0,
                buffer,
                ctypes.byref(buffer_size),
            ):
                return Path(buffer.value).name

            return ""
        finally:
            kernel32.CloseHandle(handle)

    def _is_tradingview_window(self, window: Any) -> bool:
        try:
            pid = window.process_id()
            process_name = self._process_name_from_pid(pid).lower()

            if process_name == "tradingview.exe":
                return True
        except Exception:
            pass

        try:
            title = window.window_text().strip()
            if "TradingView" in title:
                return True
        except Exception:
            pass

        return False

    def _iter_windows(self):
        desktop = Desktop(backend="uia")
        return desktop.windows()

    def launch(self) -> bool:
        """
        Försöker starta TradingView Desktop om det inte redan körs.
        """
        for executable in self._candidate_executables():
            try:
                if executable.exists():
                    os.startfile(str(executable))
                    return True
            except Exception:
                continue

        return False

    def find(self) -> bool:
        """
        Hittar TradingView-fönstret.
        """

        for window in self._iter_windows():
            try:
                if self._is_tradingview_window(window):
                    self.window = window
                    return True
            except Exception:
                continue

        self.window = None
        return False

    def ensure_running(self) -> bool:
        """
        Ser till att TradingView finns öppet och väntar in fönstret om det behövs.
        """

        if self.find():
            return True

        self.launch()

        deadline = time.time() + self.DEFAULT_WAIT_SECONDS

        while time.time() < deadline:
            if self.find():
                return True
            time.sleep(self.POLL_INTERVAL_SECONDS)

        return False

    def prepare(self) -> bool:
        """
        Säkerställ att TradingView är redo.
        """

        if not self.ensure_running():
            return False

        assert self.window is not None

        try:
            self.window.restore()
        except Exception:
            pass

        try:
            self.window.maximize()
        except Exception:
            pass

        try:
            self.window.set_focus()
        except Exception:
            pass

        return True

    def activate(self) -> bool:
        """
        Fokusera TradingView.
        """
        return self.prepare()

    def maximize(self) -> bool:
        if self.window is None:
            if not self.find():
                return False

        assert self.window is not None

        try:
            self.window.maximize()
            return True
        except Exception:
            return False

    def restore(self) -> bool:
        if self.window is None:
            if not self.find():
                return False

        assert self.window is not None

        try:
            self.window.restore()
            return True
        except Exception:
            return False

    def title(self) -> str:
        if self.window is None:
            return ""

        return self.window.window_text()