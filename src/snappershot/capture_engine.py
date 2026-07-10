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
        finnhub_company = profile if isinstance(profile, dict) else {}
        finnhub_valuation = valuation if isinstance(valuation, dict) else {}
        finnhub_profitability = profitability if isinstance(profitability, dict) else {}
        finnhub_growth = growth if isinstance(growth, dict) else {}
        finnhub_strength = strength if isinstance(strength, dict) else {}
        finnhub_dividend = dividend if isinstance(dividend, dict) else {}
        finnhub_analyst = analyst if isinstance(analyst, dict) else {}

        data_sources = []
        if self._has_meaningful_data(finnhub_data):
            data_sources.append("finnhub")
        if self._has_meaningful_data(yfinance_data):
            data_sources.append("yfinance")

        company_name = self._merge_first_non_empty(profile.get("company_name") or profile.get("name") or None, self._merge_first_non_empty(self._deep_get(yfinance_company, "name"), ticker))
        ticker_value = self._merge_first_non_empty(self._deep_get(profile, "symbol"), self._merge_first_non_empty(self._deep_get(yfinance_company, "ticker"), ticker))
        exchange_value = self._merge_first_non_empty(self._deep_get(profile, "exchange"), self._deep_get(yfinance_company, "exchange"))
        currency_value = self._merge_first_non_empty(self._deep_get(profile, "currency"), self._deep_get(yfinance_company, "currency"))
        sector_value = self._merge_first_non_empty(self._deep_get(profile, "sector"), self._deep_get(yfinance_company, "sector"))
        industry_value = self._merge_first_non_empty(self._deep_get(profile, "industry"), self._deep_get(yfinance_company, "industry"))

        current_price = self._metric_point(self._deep_get(yfinance_data, "price", "current_price"), self._deep_get(finnhub_data, "price", "current_price"))
        market_cap = self._metric_point(self._deep_get(yfinance_company, "market_cap"), self._deep_get(profile, "market_capitalization"))
        volume = self._metric_point(self._deep_get(yfinance_data, "price", "volume"), self._deep_get(finnhub_data, "price", "volume"))
        average_volume = self._metric_point(self._deep_get(yfinance_data, "extra", "average_volume"), self._deep_get(finnhub_data, "extra", "average_volume"))
        week_high = self._metric_point(self._deep_get(yfinance_data, "extra", "fifty_two_week_high"), self._deep_get(finnhub_data, "extra", "fifty_two_week_high"))
        week_low = self._metric_point(self._deep_get(yfinance_data, "extra", "fifty_two_week_low"), self._deep_get(finnhub_data, "extra", "fifty_two_week_low"))

        avanza_metrics = {
            "eps": self._metric_point(
                self._deep_get(yfinance_data, "fundamentals", "financial_statements", "income_statement", "eps") or self._deep_get(yfinance_data, "fundamentals", "profitability", "eps"),
                self._deep_get(finnhub_data, "fundamentals", "profitability", "eps"),
            ),
            "revenue_per_share": self._metric_point(
                self._deep_get(yfinance_company, "revenue_per_share") or self._deep_get(yfinance_fundamentals, "revenue_per_share"),
                self._deep_get(finnhub_company, "revenue_per_share"),
            ),
            "roe": self._metric_point(
                yfinance_profitability.get("roe"),
                finnhub_profitability.get("roe"),
            ),
            "net_debt_ebitda": self._metric_point(
                yfinance_strength.get("net_debt_ebitda") or yfinance_strength.get("debt_to_ebitda"),
                finnhub_strength.get("net_debt_ebitda") or finnhub_strength.get("debt_to_ebitda"),
            ),
            "pe": self._metric_point(yfinance_valuation.get("pe"), finnhub_valuation.get("pe")),
            "ps": self._metric_point(yfinance_valuation.get("ps"), finnhub_valuation.get("ps")),
            "pb": self._metric_point(yfinance_valuation.get("pb"), finnhub_valuation.get("pb")),
            "ev_ebit": self._metric_point(
                yfinance_valuation.get("ev_ebit"),
                finnhub_valuation.get("ev_ebit"),
            ),
            "ev_ebitda": self._metric_point(
                yfinance_valuation.get("ev_ebitda"),
                finnhub_valuation.get("ev_ebitda"),
            ),
            "profitability": {
                "gross_margin": self._metric_point(yfinance_profitability.get("gross_margin"), finnhub_profitability.get("gross_margin")),
                "operating_margin": self._metric_point(yfinance_profitability.get("operating_margin"), finnhub_profitability.get("operating_margin")),
                "profit_margin": self._metric_point(yfinance_profitability.get("net_margin"), finnhub_profitability.get("net_margin")),
            },
            "growth": {
                "revenue_growth": self._metric_point(yfinance_growth.get("revenue_growth"), finnhub_profitability.get("revenue_growth")),
                "earnings_growth": self._metric_point(yfinance_growth.get("eps_growth"), finnhub_profitability.get("earnings_growth")),
            },
            "analysts": {
                "strong_buy": self._metric_point(self._deep_get(yfinance_analyst, "recommendation", "strong_buy"), self._deep_get(finnhub_analyst, "recommendation", "strong_buy")),
                "buy": self._metric_point(self._deep_get(yfinance_analyst, "recommendation", "buy"), self._deep_get(finnhub_analyst, "recommendation", "buy")),
                "hold": self._metric_point(self._deep_get(yfinance_analyst, "recommendation", "hold"), self._deep_get(finnhub_analyst, "recommendation", "hold")),
                "sell": self._metric_point(self._deep_get(yfinance_analyst, "recommendation", "sell"), self._deep_get(finnhub_analyst, "recommendation", "sell")),
                "target_high_price": self._metric_point(self._deep_get(yfinance_analyst, "target_price", "high") or yfinance_analyst.get("targetHighPrice"), self._deep_get(finnhub_analyst, "target_price", "high") or finnhub_analyst.get("targetHighPrice")),
                "target_mean_price": self._metric_point(self._deep_get(yfinance_analyst, "target_price", "average") or yfinance_analyst.get("targetMeanPrice"), self._deep_get(finnhub_analyst, "target_price", "average") or finnhub_analyst.get("targetMeanPrice")),
                "target_low_price": self._metric_point(self._deep_get(yfinance_analyst, "target_price", "low"), self._deep_get(finnhub_analyst, "target_price", "low")),
            },
        }

        return {
            "search_name": ticker,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "data_sources": data_sources,
            "yahoo_collected_dataset": yfinance_data,
            "company": {
                "name": {"value": company_name, "source": "yfinance" if self._safe_number(self._deep_get(yfinance_company, "name")) is not None else ("finnhub" if self._safe_number(self._deep_get(profile, "company_name") or self._deep_get(profile, "name")) is not None else None)},
                "ticker": {"value": ticker_value, "source": "yfinance" if self._safe_number(self._deep_get(yfinance_company, "ticker")) is not None else ("finnhub" if self._safe_number(self._deep_get(profile, "symbol")) is not None else None)},
                "exchange": {"value": exchange_value, "source": "yfinance" if self._safe_number(self._deep_get(yfinance_company, "exchange")) is not None else ("finnhub" if self._safe_number(self._deep_get(profile, "exchange")) is not None else None)},
                "currency": {"value": currency_value, "source": "yfinance" if self._safe_number(self._deep_get(yfinance_company, "currency")) is not None else ("finnhub" if self._safe_number(self._deep_get(profile, "currency")) is not None else None)},
                "sector": {"value": sector_value, "source": "yfinance" if self._safe_number(self._deep_get(yfinance_company, "sector")) is not None else ("finnhub" if self._safe_number(self._deep_get(profile, "sector")) is not None else None)},
                "industry": {"value": industry_value, "source": "yfinance" if self._safe_number(self._deep_get(yfinance_company, "industry")) is not None else ("finnhub" if self._safe_number(self._deep_get(profile, "industry")) is not None else None)},
            },
            "market": {
                "current_price": current_price,
                "market_cap": market_cap,
                "volume": volume,
                "average_volume": average_volume,
                "52_week_high": week_high,
                "52_week_low": week_low,
            },
            "key_metrics": {
                "earnings_per_share": avanza_metrics["eps"],
                "revenue_per_share": avanza_metrics["revenue_per_share"],
                "return_on_equity": avanza_metrics["roe"],
                "net_debt_to_ebitda": avanza_metrics["net_debt_ebitda"],
                "pe_ratio": avanza_metrics["pe"],
                "ps_ratio": avanza_metrics["ps"],
                "pb_ratio": avanza_metrics["pb"],
                "ev_to_ebit": avanza_metrics["ev_ebit"],
                "ev_to_ebitda": avanza_metrics["ev_ebitda"],
            },
            "profitability": {
                "gross_margin": self._metric_point(yfinance_profitability.get("gross_margin"), finnhub_profitability.get("gross_margin")),
                "operating_margin": self._metric_point(yfinance_profitability.get("operating_margin"), finnhub_profitability.get("operating_margin")),
                "profit_margin": self._metric_point(yfinance_profitability.get("net_margin"), finnhub_profitability.get("net_margin")),
            },
            "growth": {
                "revenue_growth": self._metric_point(yfinance_growth.get("revenue_growth"), finnhub_growth.get("revenue_growth")),
                "earnings_growth": self._metric_point(yfinance_growth.get("eps_growth"), finnhub_growth.get("eps_growth")),
            },
            "dividend": {
                "dividend_yield": self._metric_point(
                    yfinance_dividend.get("yield") or self._deep_get(yfinance_data, "extra", "dividendYield"),
                    finnhub_dividend.get("dividend_yield"),
                ),
                "dividend_rate": self._metric_point(
                    yfinance_dividend.get("dividend_rate") or self._deep_get(yfinance_data, "extra", "dividendRate"),
                    finnhub_dividend.get("dividend_rate"),
                ),
                "payout_ratio": self._metric_point(yfinance_dividend.get("payout_ratio"), finnhub_dividend.get("payout_ratio")),
            },
            "analyst_consensus": {
                "strong_buy": self._metric_point(self._deep_get(yfinance_analyst, "recommendation", "strong_buy"), self._deep_get(finnhub_analyst, "recommendation", "strong_buy")),
                "buy": self._metric_point(self._deep_get(yfinance_analyst, "recommendation", "buy"), self._deep_get(finnhub_analyst, "recommendation", "buy")),
                "hold": self._metric_point(self._deep_get(yfinance_analyst, "recommendation", "hold"), self._deep_get(finnhub_analyst, "recommendation", "hold")),
                "sell": self._metric_point(self._deep_get(yfinance_analyst, "recommendation", "sell"), self._deep_get(finnhub_analyst, "recommendation", "sell")),
                "target_high_price": self._metric_point(self._deep_get(yfinance_analyst, "target_price", "high") or yfinance_analyst.get("targetHighPrice"), self._deep_get(finnhub_analyst, "target_price", "high") or finnhub_analyst.get("targetHighPrice")),
                "target_mean_price": self._metric_point(
                    yfinance_analyst.get("target_price") if not isinstance(yfinance_analyst.get("target_price"), dict) else self._deep_get(yfinance_analyst, "target_price", "average"),
                    finnhub_analyst.get("target_price") if not isinstance(finnhub_analyst.get("target_price"), dict) else self._deep_get(finnhub_analyst, "target_price", "average"),
                ),
                "target_low_price": self._metric_point(self._deep_get(yfinance_analyst, "target_price", "low") or yfinance_analyst.get("targetLowPrice"), self._deep_get(finnhub_analyst, "target_price", "low") or finnhub_analyst.get("targetLowPrice")),
            },
        }

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
