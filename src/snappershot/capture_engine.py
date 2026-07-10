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

    def _select_metric_value(self, yfinance_value: Any, finnhub_value: Any) -> tuple[Any, str]:
        if self._safe_number(yfinance_value) is not None:
            return yfinance_value, "yfinance"
        if self._safe_number(finnhub_value) is not None:
            return finnhub_value, "finnhub"
        return None, None

    def _metric_point(self, yfinance_value: Any, finnhub_value: Any) -> dict[str, Any]:
        value, source = self._select_metric_value(yfinance_value, finnhub_value)
        return {"value": value, "source": source}

    @staticmethod
    def _deep_get(mapping: Any, *keys: str) -> Any:
        current = mapping
        for key in keys:
            if not isinstance(current, dict):
                return None
            current = current.get(key)
        return current

    def _point(self, yfinance_value: Any = None, finnhub_value: Any = None) -> dict[str, Any]:
        return self._metric_point(yfinance_value, finnhub_value)

    def _source_from(self, yfinance_value: Any = None, finnhub_value: Any = None) -> str | None:
        _, source = self._select_metric_value(yfinance_value, finnhub_value)
        return source

    def _primary_point(
        self,
        primary_value: Any,
        primary_source: str,
        fallback_value: Any,
        fallback_source: str,
    ) -> dict[str, Any]:
        if self._is_real_value(primary_value):
            return {"value": primary_value, "source": primary_source}
        if self._is_real_value(fallback_value):
            return {"value": fallback_value, "source": fallback_source}
        return {"value": None, "source": None}

    def _is_real_value(self, value: Any) -> bool:
        return self._safe_number(value) is not None

    def _build_data_quality(self, payload: dict[str, Any]) -> dict[str, Any]:
        field_paths = [
            ("company", "name"),
            ("company", "ticker"),
            ("company", "exchange"),
            ("company", "currency"),
            ("company", "sector"),
            ("company", "industry"),
            ("market", "current_price"),
            ("market", "market_cap"),
            ("market", "volume"),
            ("market", "average_volume"),
            ("market", "52_week_high"),
            ("market", "52_week_low"),
            ("key_metrics", "earnings_per_share"),
            ("key_metrics", "revenue_per_share"),
            ("key_metrics", "return_on_equity"),
            ("key_metrics", "net_debt_to_ebitda"),
            ("key_metrics", "pe_ratio"),
            ("key_metrics", "forward_pe"),
            ("key_metrics", "ps_ratio"),
            ("key_metrics", "pb_ratio"),
            ("key_metrics", "ev_to_ebit"),
            ("key_metrics", "ev_to_ebitda"),
            ("profitability", "gross_margin"),
            ("profitability", "operating_margin"),
            ("profitability", "profit_margin"),
            ("growth", "revenue_growth"),
            ("growth", "earnings_growth"),
            ("dividend", "dividend_yield"),
            ("dividend", "dividend_rate"),
            ("dividend", "payout_ratio"),
            ("analyst_consensus", "strong_buy"),
            ("analyst_consensus", "buy"),
            ("analyst_consensus", "hold"),
            ("analyst_consensus", "sell"),
            ("analyst_consensus", "target_high_price"),
            ("analyst_consensus", "target_mean_price"),
            ("analyst_consensus", "target_low_price"),
        ]

        missing_fields: list[str] = []
        fields_found = 0
        for section, field in field_paths:
            datapoint = self._deep_get(payload, section, field)
            if isinstance(datapoint, dict) and self._is_real_value(datapoint.get("value")):
                fields_found += 1
            else:
                missing_fields.append(f"{section}.{field}")

        total_fields = len(field_paths)
        percent_complete = round((fields_found / total_fields) * 100, 2) if total_fields else 0.0

        return {
            "total_fields": total_fields,
            "fields_found": fields_found,
            "percent_complete": percent_complete,
            "missing_fields": missing_fields,
        }

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
        finnhub_profitability = fundamentals.get("profitability", {}) if isinstance(fundamentals, dict) else {}
        finnhub_growth = fundamentals.get("growth", {}) if isinstance(fundamentals, dict) else {}
        finnhub_dividend = fundamentals.get("dividend", {}) if isinstance(fundamentals, dict) else {}
        finnhub_analyst = fundamentals.get("analyst", {}) if isinstance(fundamentals, dict) else {}

        yfinance_company = yfinance_data.get("company", {}) if isinstance(yfinance_data, dict) else {}
        yfinance_fundamentals = yfinance_data.get("fundamentals", {}) if isinstance(yfinance_data, dict) else {}
        yfinance_valuation = yfinance_fundamentals.get("valuation", {}) if isinstance(yfinance_fundamentals, dict) else {}
        yfinance_profitability = yfinance_fundamentals.get("profitability", {}) if isinstance(yfinance_fundamentals, dict) else {}
        yfinance_growth = yfinance_fundamentals.get("growth", {}) if isinstance(yfinance_fundamentals, dict) else {}
        yfinance_dividend = yfinance_fundamentals.get("dividend", {}) if isinstance(yfinance_fundamentals, dict) else {}
        yfinance_analyst = yfinance_fundamentals.get("analyst", {}) if isinstance(yfinance_fundamentals, dict) else {}

        company = {
            "name": self._point(self._deep_get(yfinance_company, "name"), self._deep_get(profile, "company_name") or self._deep_get(profile, "name")),
            "ticker": self._point(self._deep_get(yfinance_company, "ticker"), self._deep_get(profile, "symbol")),
            "exchange": self._point(self._deep_get(yfinance_company, "exchange"), self._deep_get(profile, "exchange")),
            "currency": self._point(self._deep_get(yfinance_company, "currency"), self._deep_get(profile, "currency")),
            "sector": self._point(self._deep_get(yfinance_company, "sector"), self._deep_get(profile, "sector")),
            "industry": self._point(self._deep_get(yfinance_company, "industry"), self._deep_get(profile, "industry")),
        }

        market = {
            "current_price": self._point(self._deep_get(yfinance_data, "price", "current_price"), self._deep_get(finnhub_data, "price", "current_price")),
            "market_cap": self._point(self._deep_get(yfinance_company, "market_cap"), self._deep_get(profile, "market_capitalization")),
            "volume": self._point(self._deep_get(yfinance_data, "price", "volume"), self._deep_get(finnhub_data, "price", "volume")),
            "average_volume": self._point(self._deep_get(yfinance_data, "extra", "average_volume"), self._deep_get(finnhub_data, "extra", "average_volume")),
            "52_week_high": self._point(self._deep_get(yfinance_data, "extra", "fifty_two_week_high") or self._deep_get(yfinance_data, "extra", "fiftyTwoWeekHigh"), self._deep_get(finnhub_data, "extra", "fifty_two_week_high")),
            "52_week_low": self._point(self._deep_get(yfinance_data, "extra", "fifty_two_week_low") or self._deep_get(yfinance_data, "extra", "fiftyTwoWeekLow"), self._deep_get(finnhub_data, "extra", "fifty_two_week_low")),
        }

        key_metrics = {
            "earnings_per_share": self._point(
                self._deep_get(yfinance_data, "fundamentals", "financial_statements", "income_statement", "eps") or self._deep_get(yfinance_fundamentals, "financial_statements", "income_statement", "eps") or self._deep_get(yfinance_fundamentals, "eps") or self._deep_get(yfinance_data, "price", "eps"),
                self._deep_get(finnhub_data, "fundamentals", "profitability", "eps"),
            ),
            "revenue_per_share": self._point(self._deep_get(yfinance_company, "revenue_per_share"), self._deep_get(profile, "revenue_per_share")),
            "return_on_equity": self._point(self._deep_get(yfinance_profitability, "roe"), self._deep_get(finnhub_profitability, "roe")),
            "net_debt_to_ebitda": self._point(self._deep_get(yfinance_fundamentals, "financial_strength", "net_debt_to_ebitda") or self._deep_get(yfinance_fundamentals, "financial_strength", "debt_to_ebitda"), self._deep_get(finnhub_data, "fundamentals", "financial_strength", "net_debt_to_ebitda") or self._deep_get(finnhub_data, "fundamentals", "financial_strength", "debt_to_ebitda")),
            "pe_ratio": self._point(self._deep_get(yfinance_valuation, "pe"), self._deep_get(valuation, "pe")),
            "forward_pe": self._point(self._deep_get(yfinance_valuation, "forward_pe"), self._deep_get(valuation, "forward_pe")),
            "ps_ratio": self._point(self._deep_get(yfinance_valuation, "ps"), self._deep_get(valuation, "ps")),
            "pb_ratio": self._point(self._deep_get(yfinance_valuation, "pb"), self._deep_get(valuation, "pb")),
            "ev_to_ebit": self._point(self._deep_get(yfinance_valuation, "ev_ebit"), self._deep_get(valuation, "ev_ebit")),
            "ev_to_ebitda": self._point(self._deep_get(yfinance_valuation, "ev_ebitda"), self._deep_get(valuation, "ev_ebitda")),
        }

        profitability = {
            "gross_margin": self._point(self._deep_get(yfinance_profitability, "gross_margin"), self._deep_get(finnhub_profitability, "gross_margin")),
            "operating_margin": self._point(self._deep_get(yfinance_profitability, "operating_margin"), self._deep_get(finnhub_profitability, "operating_margin")),
            "profit_margin": self._point(self._deep_get(yfinance_profitability, "net_margin"), self._deep_get(finnhub_profitability, "net_margin")),
        }

        growth = {
            "revenue_growth": self._point(self._deep_get(yfinance_growth, "revenue_growth"), self._deep_get(finnhub_growth, "revenue_growth")),
            "earnings_growth": self._point(self._deep_get(yfinance_growth, "eps_growth"), self._deep_get(finnhub_growth, "eps_growth")),
        }

        dividend = {
            "dividend_yield": self._point(self._deep_get(yfinance_fundamentals, "dividend", "yield") or self._deep_get(yfinance_data, "extra", "dividendYield"), self._deep_get(finnhub_dividend, "dividend_yield")),
            "dividend_rate": self._point(self._deep_get(yfinance_fundamentals, "dividend", "dividend_rate") or self._deep_get(yfinance_data, "extra", "dividendRate"), self._deep_get(finnhub_dividend, "dividend_rate")),
            "payout_ratio": self._point(self._deep_get(yfinance_fundamentals, "dividend", "payout_ratio"), self._deep_get(finnhub_dividend, "payout_ratio")),
        }

        analyst_consensus = {
            "strong_buy": self._primary_point(self._deep_get(finnhub_analyst, "recommendation", "strong_buy"), "finnhub", self._deep_get(yfinance_analyst, "recommendation", "strong_buy"), "yfinance"),
            "buy": self._primary_point(self._deep_get(finnhub_analyst, "recommendation", "buy"), "finnhub", self._deep_get(yfinance_analyst, "recommendation", "buy"), "yfinance"),
            "hold": self._primary_point(self._deep_get(finnhub_analyst, "recommendation", "hold"), "finnhub", self._deep_get(yfinance_analyst, "recommendation", "hold"), "yfinance"),
            "sell": self._primary_point(self._deep_get(finnhub_analyst, "recommendation", "sell"), "finnhub", self._deep_get(yfinance_analyst, "recommendation", "sell"), "yfinance"),
            "target_high_price": self._primary_point(self._deep_get(finnhub_analyst, "target_price", "high") or self._deep_get(finnhub_analyst, "targetHighPrice"), "finnhub", self._deep_get(yfinance_analyst, "target_price", "high") or self._deep_get(yfinance_analyst, "targetHighPrice"), "yfinance"),
            "target_mean_price": self._primary_point(self._deep_get(finnhub_analyst, "target_price", "average") or self._deep_get(finnhub_analyst, "targetMeanPrice"), "finnhub", self._deep_get(yfinance_analyst, "target_price", "average") or self._deep_get(yfinance_analyst, "targetMeanPrice") or self._deep_get(yfinance_analyst, "target_price"), "yfinance"),
            "target_low_price": self._primary_point(self._deep_get(finnhub_analyst, "target_price", "low") or self._deep_get(finnhub_analyst, "targetLowPrice"), "finnhub", self._deep_get(yfinance_analyst, "target_price", "low") or self._deep_get(yfinance_analyst, "targetLowPrice"), "yfinance"),
        }

        payload = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "data_sources": [
                source
                for source in (
                    "finnhub" if self._has_meaningful_data(finnhub_data) else None,
                    "yfinance" if self._has_meaningful_data(yfinance_data) else None,
                )
                if source
            ],
            "company": company,
            "market": market,
            "key_metrics": key_metrics,
            "profitability": profitability,
            "growth": growth,
            "dividend": dividend,
            "analyst_consensus": analyst_consensus,
        }
        payload["data_quality"] = self._build_data_quality(payload)
        return payload

    async def run(
        self,
        ticker: str,
        screenshots: list[Path | str] | None = None,
        output_folder: Path | None = None,
    ) -> dict[str, Any]:
        output_folder = output_folder or self.storage_service.create_capture_folder(ticker)
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
