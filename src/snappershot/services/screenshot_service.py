from __future__ import annotations

from pathlib import Path

import pyautogui


class ScreenshotService:
    """
    Hanterar skärmdumpar.
    """

    def capture_desktop(self, output_path: Path) -> bool:
        """
        Tar en skärmdump av hela skrivbordet.
        """

        output_path.parent.mkdir(parents=True, exist_ok=True)

        image = pyautogui.screenshot()

        image.save(output_path)

        return True
