from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class CaptureResult:
    """
    Resultatet av en komplett capture-session.
    """

    success: bool
    company_name: str

    zip_path: Path | None = None

    screenshots: list[Path] = field(default_factory=list)

    message: str = ""

    @property
    def screenshot_count(self) -> int:
        return len(self.screenshots)