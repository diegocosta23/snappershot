from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class CaptureResult:
    """
    Representerar resultatet av en komplett capture-session.
    """

    success: bool

    company_name: str

    message: str = ""

    output_folder: Path | None = None

    zip_path: Path | None = None

    screenshots: list[Path] = field(default_factory=list)

    @property
    def screenshot_count(self) -> int:
        """
        Antal skapade screenshots.
        """
        return len(self.screenshots)

    @property
    def has_zip(self) -> bool:
        """
        True om ZIP skapades.
        """
        return self.zip_path is not None

    @property
    def has_screenshots(self) -> bool:
        """
        True om minst en screenshot finns.
        """
        return bool(self.screenshots)

    @classmethod
    def failed(
        cls,
        message: str,
        company_name: str = "",
    ) -> "CaptureResult":
        return cls(
            success=False,
            company_name=company_name,
            message=message,
        )

    @classmethod
    def completed(
        cls,
        company_name: str,
        output_folder: Path,
        screenshots: list[Path],
        zip_path: Path | None = None,
    ) -> "CaptureResult":
        return cls(
            success=True,
            company_name=company_name,
            output_folder=output_folder,
            screenshots=screenshots,
            zip_path=zip_path,
            message="Capture completed.",
        )