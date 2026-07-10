from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any
from datetime import datetime, timezone

from .collectors.finnhub_client import FinnhubClient
from .collectors.yfinance_client import YahooFinanceClient
from .database.sqlite_store import SQLiteStore
from .exports.package_export import build_analysis_package
from .services.storage_service import StorageService

log = logging.getLogger(__name__)


class CaptureEngine:
    """Coordinate fundamental research collection and persistence."""

    def __init__(self) -> None:
        self.storage_service = StorageService()
        self.finnhub = FinnhubClient()
        self.yfinance = YahooFinanceClient()
        self.store = SQLiteStore()

    def _safe_number(self, value: Any) -> Any:
        return value if value not in (None, "", {}, []) else None

    def _merge_first_non_empty(self, primary: Any, fallback: Any) -> Any:
        if self._safe_number(primary) not in (None, {}, []) and primary != {}:
            return primary
        return fallback

    def _has_meaningful_data(self, data: Any) -> bool:
        if not isinstance(data, dict):
            return self._safe_number(data) is not None
        for value in data.values():
            if self._safe_number(value) is not None:
                return True
            if isinstance(value, dict) and any(self._safe_number(item) is not None for item in value.values()):
                return True
        return False

    def _build_analysis_payload(
        self,
        ticker: str,
        finnhub_data: dict[str, Any],
        yfinance_data: dict[str, Any],
        screenshots: list[Path | str] | None = None,
    ) -> dict[str, Any]:
        profile = finnhub_data.get("profile", {}) if isinstance(finnhub_data, dict) else {}
        fundamentals = finnhub_data.get("fundamentals", {}) if isinstance(finnhub_data, dict) else {}
        valuation = fundamentals.get("valuation", {}) if isinstance(fundamentals, dict) else {}
        profitability = fundamentals.get("profitability", {}) if isinstance(fundamentals, dict) else {}
        growth = fundamentals.get("growth", {}) if isinstance(fundamentals, dict) else {}
        strength = fundamentals.get("financial_strength", {}) if isinstance(fundamentals, dict) else {}
        dividend = fundamentals.get("dividend", {}) if isinstance(fundamentals, dict) else {}
        analyst = fundamentals.get("analyst", {}) if isinstance(fundamentals, dict) else {}

        yfinance_company = yfinance_data.get("company", {}) if isinstance(yfinance_data, dict) else {}
        yfinance_fundamentals = yfinance_data.get("fundamentals", {}) if isinstance(yfinance_data, dict) else {}
        yfinance_valuation = yfinance_fundamentals.get("valuation", {}) if isinstance(yfinance_fundamentals, dict) else {}
        yfinance_profitability = yfinance_fundamentals.get("profitability", {}) if isinstance(yfinance_fundamentals, dict) else {}
        yfinance_growth = yfinance_fundamentals.get("growth", {}) if isinstance(yfinance_fundamentals, dict) else {}
        yfinance_strength = yfinance_fundamentals.get("financial_strength", {}) if isinstance(yfinance_fundamentals, dict) else {}
        yfinance_cashflow = yfinance_fundamentals.get("cashflow", {}) if isinstance(yfinance_fundamentals, dict) else {}
        yfinance_dividend = yfinance_fundamentals.get("dividend", {}) if isinstance(yfinance_fundamentals, dict) else {}
        yfinance_analyst = yfinance_fundamentals.get("analyst", {}) if isinstance(yfinance_fundamentals, dict) else {}

        recommendation = self._merge_first_non_empty(analyst.get("recommendation", {}), yfinance_analyst.get("recommendation", {}))
        target_value = self._merge_first_non_empty(
            self._safe_number(analyst.get("target_price")) if not isinstance(analyst.get("target_price"), dict) else self._safe_number(analyst.get("target_price", {}).get("targetPrice")),
            self._safe_number(yfinance_analyst.get("target_price")),
        )

        company_source = "finnhub" if self._safe_number(profile.get("company_name") or profile.get("name")) is not None else "yfinance"
        valuation_source = "finnhub" if self._safe_number(valuation.get("pe")) is not None else "yfinance"
        profitability_source = "finnhub" if self._safe_number(profitability.get("gross_margin")) is not None else "yfinance"
        growth_source = "finnhub" if self._safe_number(growth.get("revenue_growth")) is not None else "yfinance"
        strength_source = "finnhub" if self._safe_number(strength.get("debt_to_equity")) is not None else "yfinance"
        cashflow_source = "finnhub" if self._safe_number(fundamentals.get("cashflow", {}).get("operating_cash_flow")) is not None else "yfinance"
        dividend_source = "finnhub" if self._safe_number(dividend.get("dividend_yield")) is not None else "yfinance"
        analyst_source = "finnhub" if self._safe_number(analyst.get("recommendation")) is not None else "yfinance"

        data_sources = []
        if self._has_meaningful_data(finnhub_data):
            data_sources.append("finnhub")
        if self._has_meaningful_data(yfinance_data):
            data_sources.append("yfinance")

        return {
            "search_name": ticker,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "data_sources": data_sources,
            "yahoo_collected_dataset": yfinance_data,
            "ticker": ticker,
            "company": {
                "name": self._merge_first_non_empty(profile.get("company_name") or profile.get("name") or None, yfinance_company.get("name") or ticker),
                "ticker": self._merge_first_non_empty(ticker, yfinance_company.get("ticker") or ticker),
                "exchange": self._merge_first_non_empty(profile.get("exchange"), yfinance_company.get("exchange")),
                "sector": self._merge_first_non_empty(profile.get("sector") or profile.get("industry"), yfinance_company.get("sector")),
                "industry": self._merge_first_non_empty(profile.get("industry"), yfinance_company.get("industry")),
                "country": self._merge_first_non_empty(profile.get("country"), yfinance_company.get("country")),
                "market_cap": self._merge_first_non_empty(profile.get("market_capitalization"), yfinance_company.get("market_cap")),
                "source": company_source,
                "currency": self._merge_first_non_empty(profile.get("currency"), yfinance_company.get("currency")),
                "reported_currency": self._merge_first_non_empty(profile.get("currency"), yfinance_company.get("reported_currency")),
            },
            "valuation": {
                "pe": self._merge_first_non_empty(self._safe_number(valuation.get("pe")), self._safe_number(yfinance_valuation.get("pe"))),
                "forward_pe": self._merge_first_non_empty(self._safe_number(valuation.get("forward_pe")), self._safe_number(yfinance_valuation.get("forward_pe"))),
                "peg": self._merge_first_non_empty(self._safe_number(valuation.get("peg")), self._safe_number(yfinance_valuation.get("peg"))),
                "pb": self._merge_first_non_empty(self._safe_number(valuation.get("pb")), self._safe_number(yfinance_valuation.get("pb"))),
                "ps": self._merge_first_non_empty(self._safe_number(valuation.get("ps")), self._safe_number(yfinance_valuation.get("ps"))),
                "ev_ebitda": self._merge_first_non_empty(self._safe_number(valuation.get("ev_ebitda")), self._safe_number(yfinance_valuation.get("ev_ebitda"))),
                "source": valuation_source,
                "currency": self._merge_first_non_empty(profile.get("currency"), yfinance_company.get("currency")),
                "reported_currency": self._merge_first_non_empty(profile.get("currency"), yfinance_company.get("reported_currency")),
            },
            "profitability": {
                "gross_margin": self._merge_first_non_empty(self._safe_number(profitability.get("gross_margin")), self._safe_number(yfinance_profitability.get("gross_margin"))),
                "operating_margin": self._merge_first_non_empty(self._safe_number(profitability.get("operating_margin")), self._safe_number(yfinance_profitability.get("operating_margin"))),
                "net_margin": self._merge_first_non_empty(self._safe_number(profitability.get("net_margin")), self._safe_number(yfinance_profitability.get("net_margin"))),
                "roe": self._merge_first_non_empty(self._safe_number(profitability.get("roe")), self._safe_number(yfinance_profitability.get("roe"))),
                "roic": self._merge_first_non_empty(self._safe_number(profitability.get("roi")), self._safe_number(yfinance_profitability.get("roic"))),
                "source": profitability_source,
                "currency": self._merge_first_non_empty(profile.get("currency"), yfinance_company.get("currency")),
                "reported_currency": self._merge_first_non_empty(profile.get("currency"), yfinance_company.get("reported_currency")),
            },
            "growth": {
                "revenue_growth": self._merge_first_non_empty(self._safe_number(growth.get("revenue_growth")), self._safe_number(yfinance_growth.get("revenue_growth"))),
                "eps_growth": self._merge_first_non_empty(self._safe_number(growth.get("eps_growth")), self._safe_number(yfinance_growth.get("eps_growth"))),
                "source": growth_source,
                "currency": self._merge_first_non_empty(profile.get("currency"), yfinance_company.get("currency")),
                "reported_currency": self._merge_first_non_empty(profile.get("currency"), yfinance_company.get("reported_currency")),
            },
            "financial_strength": {
                "cash": self._merge_first_non_empty(self._safe_number(strength.get("cash")), self._safe_number(yfinance_strength.get("cash"))),
                "debt": self._merge_first_non_empty(self._safe_number(strength.get("debt")), self._safe_number(yfinance_strength.get("debt"))),
                "debt_to_equity": self._merge_first_non_empty(self._safe_number(strength.get("debt_to_equity")), self._safe_number(yfinance_strength.get("debt_to_equity"))),
                "current_ratio": self._merge_first_non_empty(self._safe_number(strength.get("current_ratio")), self._safe_number(yfinance_strength.get("current_ratio"))),
                "source": strength_source,
                "currency": self._merge_first_non_empty(profile.get("currency"), yfinance_company.get("currency")),
                "reported_currency": self._merge_first_non_empty(profile.get("currency"), yfinance_company.get("reported_currency")),
            },
            "cashflow": {
                "operating_cash_flow": self._merge_first_non_empty(self._safe_number(strength.get("operating_cashflow")), self._safe_number(yfinance_cashflow.get("operating_cash_flow"))),
                "free_cash_flow": self._merge_first_non_empty(self._safe_number(strength.get("free_cashflow")), self._safe_number(yfinance_cashflow.get("free_cash_flow"))),
                "source": cashflow_source,
                "currency": self._merge_first_non_empty(profile.get("currency"), yfinance_company.get("currency")),
                "reported_currency": self._merge_first_non_empty(profile.get("currency"), yfinance_company.get("reported_currency")),
            },
            "dividend": {
                "yield": self._merge_first_non_empty(self._safe_number(dividend.get("dividend_yield")), self._safe_number(yfinance_dividend.get("yield"))),
                "payout_ratio": self._merge_first_non_empty(self._safe_number(dividend.get("payout_ratio")), self._safe_number(yfinance_dividend.get("payout_ratio"))),
                "source": dividend_source,
                "currency": self._merge_first_non_empty(profile.get("currency"), yfinance_company.get("currency")),
                "reported_currency": self._merge_first_non_empty(profile.get("currency"), yfinance_company.get("reported_currency")),
            },
            "analyst": {
                "recommendation": recommendation,
                "target_price": target_value,
                "source": analyst_source,
                "currency": self._merge_first_non_empty(profile.get("currency"), yfinance_company.get("currency")),
                "reported_currency": self._merge_first_non_empty(profile.get("currency"), yfinance_company.get("reported_currency")),
            },
            "screenshots": [str(path.name if hasattr(path, 'name') else path) for path in (screenshots or [])],
        }

    async def run(self, ticker: str, screenshots: list[Path | str] | None = None) -> dict[str, Any]:
        output_folder = self.storage_service.create_capture_folder(ticker)
        screenshots = screenshots or []

        try:
            log.info("Finnhub -> %s", ticker)
            finnhub_task = asyncio.to_thread(self.finnhub.collect, ticker)
            log.info("Yahoo -> %s", ticker)
            yfinance_task = asyncio.to_thread(self.yfinance.collect, ticker)

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
