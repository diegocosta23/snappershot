from __future__ import annotations

from pathlib import Path
from typing import Any

from .window_manager import WindowManager


class SnapshotEngine:
    """
    Tar riktiga screenshots av TradingView-fönstret.
    """

    def __init__(self) -> None:
        self.window = WindowManager()

    def prepare(self) -> bool:
        """
        Säkerställer att TradingView är redo för capture.
        """
        return self.window.prepare()

    @staticmethod
    def _resolve_output_path(output_path: str | Path) -> Path:
        path = Path(output_path)

        if path.suffix.lower() != ".png":
            path = path.with_suffix(".png")

        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _resolve_window(self, window: Any | None = None) -> Any:
        if window is not None:
            return window

        if not self.window.find() or self.window.window is None:
            raise RuntimeError("TradingView-fönstret hittades inte.")

        return self.window.window

    def capture_window(self, output_path: str | Path, window: Any | None = None) -> Path:
        """
        Tar en screenshot av TradingView-fönstret och sparar den som PNG.
        """
        path = self._resolve_output_path(output_path)
        target_window = self._resolve_window(window)

        try:
            image = target_window.capture_as_image()
        except Exception as exc:
            raise RuntimeError(f"Kunde inte läsa TradingView-fönstret: {exc}") from exc

        if image is None:
            raise RuntimeError("Kunde inte ta screenshot av TradingView-fönstret.")

        if not image.save(str(path)):
            raise RuntimeError(f"Kunde inte spara screenshoten: {path}")

        return path

    def capture(self, filename: str | Path) -> bool:
        """
        Bakåtkompatibel metod som sparar en screenshot av TradingView-fönstret.
        """
        try:
            self.capture_window(filename)
            return True
        except Exception:
            return False