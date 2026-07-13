from __future__ import annotations

import logging
from pathlib import Path

from .snapshot import SnapshotEngine
from .timeframe import TimeframeController
from .window_manager import WindowManager

log = logging.getLogger(__name__)


class TradingViewClient:
    """Small adapter for the existing TradingView screenshot flow."""

    def __init__(self, window: WindowManager | None = None) -> None:
        self.window = window or WindowManager()
        self.timeframe = TimeframeController(self.window)
        self.snapshot = SnapshotEngine(self.window)

    def capture_screenshots(
        self, output_folder: str | Path, timeframes: list[str] | None = None
    ) -> list[Path]:
        folder = Path(output_folder)
        folder.mkdir(parents=True, exist_ok=True)
        captured: list[Path] = []

        for timeframe in timeframes or ["1W", "1D", "4H", "45M"]:
            self.timeframe.set(timeframe)
            screenshot_path = folder / f"{timeframe}.png"
            result = self.snapshot.capture(screenshot_path, label=timeframe)
            if result.ok and result.data is not None:
                captured.append(Path(result.data))
            elif screenshot_path.exists():
                captured.append(screenshot_path)

        return captured
