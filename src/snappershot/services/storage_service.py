from __future__ import annotations

from datetime import datetime
from pathlib import Path


class StorageService:
    """
    Hanterar alla sökvägar som SnapperShot använder.
    """

    ROOT_FOLDER = Path.home() / "Desktop" / "Screenshots to GPT"

    def __init__(self) -> None:
        self.ROOT_FOLDER.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def sanitize(name: str) -> str:
        """
        Gör ett filnamn säkert för Windows.
        """

        invalid = '<>:"/\\|?*'

        for char in invalid:
            name = name.replace(char, "_")

        return name.strip()

    def create_capture_folder(self, company: str) -> Path:
        """
        Skapar en unik mapp för varje capture.
        """

        company = self.sanitize(company)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        folder = self.ROOT_FOLDER / company / timestamp

        folder.mkdir(parents=True, exist_ok=True)

        return folder

    def timeframe_path(
        self,
        company: str,
        timeframe: str,
    ) -> Path:

        folder = self.create_capture_folder(company)

        return folder / f"{timeframe}.png"

    def zip_path(self, company: str) -> Path:

        company = self.sanitize(company)

        return self.ROOT_FOLDER / f"{company}.zip"