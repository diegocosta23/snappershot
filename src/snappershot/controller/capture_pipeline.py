from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..models.company import Company
from ..services.company_service import CompanyService


@dataclass(slots=True)
class CaptureResult:
    success: bool
    company_name: str
    screenshot_path: Path | None = None
    zip_path: Path | None = None
    message: str = ""
    company: Company | None = None


class CapturePipeline:
    def __init__(self) -> None:
        self.company_service = CompanyService()

    def resolve_company(self, company_name: str) -> Company | None:
        return self.company_service.find(company_name)
