from __future__ import annotations

from datetime import datetime
from pathlib import Path


class StorageService:
    """Bygger sökvägar för skärmdumpar och zip-filer."""

    def __init__(self, base_dir: str | Path | None = None) -> None:
        self.base_dir = Path(base_dir) if base_dir is not None else Path.home() / "Desktop" / "Screenshots to GPT"

    @staticmethod
    def _sanitize(text: str) -> str:
        cleaned = "".join(char for char in text.strip() if char.isalnum() or char in (" ", "_", "-"))
        cleaned = "_".join(part for part in cleaned.split() if part)
        return cleaned or "Untitled"

    @staticmethod
    def timestamp() -> str:
        return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    def artifact_stem(self, company: str, timestamp: str | None = None) -> str:
        return f"{self._sanitize(company)}_{timestamp or self.timestamp()}"

    def company_folder(self, company: str) -> Path:
        folder = self.base_dir / self._sanitize(company)
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def screenshot_path(self, company: str, timestamp: str | None = None) -> Path:
        folder = self.company_folder(company)
        return folder / f"{self.artifact_stem(company, timestamp)}.png"

    def zip_path(self, company: str, timestamp: str | None = None) -> Path:
        folder = self.company_folder(company)
        return folder / f"{self.artifact_stem(company, timestamp)}.zip"
