from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from .collectors.finnhub_client import FinnhubClient
from .collectors.yfinance_client import YahooFinanceClient
from .database.sqlite_store import SQLiteStore
from .exports.package_export import build_analysis_package
from .services.provider_symbols import ProviderSymbolMapper
from .services.financial_snapshot_builder import FinancialSnapshotBuilder
from .services.storage_service import StorageService

log = logging.getLogger(__name__)


class CaptureEngine:
    """Coordinate data collection and snapshot persistence."""

    def __init__(self) -> None:
        self.storage_service = StorageService()
        self.finnhub = FinnhubClient()
        self.yfinance = YahooFinanceClient()
        self.store = SQLiteStore()
        self.snapshot_builder = FinancialSnapshotBuilder()
        self.provider_symbols = ProviderSymbolMapper()

    def _build_analysis_payload(
        self,
        ticker: str,
        finnhub_data: dict[str, Any],
        yfinance_data: dict[str, Any],
        screenshots: list[Path | str] | None = None,
    ) -> dict[str, Any]:
        _ = screenshots
        provider_symbols = self.provider_symbols.translate(self.yfinance._resolve_ticker(ticker))
        return self.snapshot_builder.build(
            search_name=ticker,
            resolved_ticker=provider_symbols["yahoo_symbol"],
            finnhub_data=finnhub_data,
            yfinance_data=yfinance_data,
        )

    async def run(
        self,
        ticker: str,
        screenshots: list[Path | str] | None = None,
        output_folder: Path | None = None,
    ) -> dict[str, Any]:
        output_folder = output_folder or self.storage_service.create_capture_folder(ticker)
        screenshots = screenshots or []

        try:
            provider_symbols = self.provider_symbols.translate(self.yfinance._resolve_ticker(ticker))
            finnhub_task = asyncio.to_thread(self.finnhub.collect, provider_symbols["finnhub_symbol"])
            yfinance_task = asyncio.to_thread(self.yfinance.collect, provider_symbols["yahoo_symbol"])

            finnhub_data, yfinance_data = await asyncio.gather(
                finnhub_task,
                yfinance_task,
                return_exceptions=True,
            )

            if isinstance(finnhub_data, Exception):
                log.warning("Finnhub collection failed: %s", finnhub_data)
                finnhub_data = {}
            if isinstance(yfinance_data, Exception):
                log.warning("Yahoo Finance collection failed: %s", yfinance_data)
                yfinance_data = {}

            payload = self._build_analysis_payload(ticker, finnhub_data, yfinance_data, screenshots)
            export_path = build_analysis_package(payload, output_folder)
            self.store.save_capture(ticker, payload)
            export_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
            return payload
        except Exception as exc:
            log.exception("Capture engine failed: %s", exc)
            raise
