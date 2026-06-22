from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QGuiApplication


class ScreenshotService:
    """Tar skärmdumpar av hela skrivbordet via Qt."""

    def capture_desktop(self, output_path: str | Path) -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        screen = QGuiApplication.primaryScreen()
        if screen is None:
            raise RuntimeError("Ingen skärm hittades för skärmdump.")

        pixmap = screen.grabWindow(0)
        if pixmap.isNull():
            raise RuntimeError("Kunde inte ta skärmdump.")

        if not pixmap.save(str(output_path)):
            raise RuntimeError(f"Kunde inte spara skärmdumpen: {output_path}")

        return output_path
