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

    def _build_news(self, news_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        processed: list[dict[str, Any]] = []
        for item in news_items[:8]:
            title = item.get("headline") or item.get("title") or ""
            summary = item.get("summary") or ""
            date = item.get("date") or item.get("datetime")
            processed.append(
                {
                    "title": title,
                    "date": date,
                    "source": item.get("source") or "",
                    "summary": summary,
                    "sentiment": "neutral",
                }
            )
        return processed

    def _build_risks(self, finnhub_data: dict[str, Any], yfinance_data: dict[str, Any]) -> dict[str, Any]:
        fundamentals = finnhub_data.get("fundamentals", {}) if isinstance(finnhub_data, dict) else {}
        valuation = fundamentals.get("valuation", {}) if isinstance(fundamentals, dict) else {}
        profitability = fundamentals.get("profitability", {}) if isinstance(fundamentals, dict) else {}
        growth = fundamentals.get("growth", {}) if isinstance(fundamentals, dict) else {}
        strength = fundamentals.get("financial_strength", {}) if isinstance(fundamentals, dict) else {}
        dividend = fundamentals.get("dividend", {}) if isinstance(fundamentals, dict) else {}
        balance_sheet = yfinance_data.get("financial_statements", {}).get("balance_sheet", {}) if isinstance(yfinance_data, dict) else {}

        valuation_risk = "high" if self._safe_number(valuation.get("pe")) is None or self._safe_number(valuation.get("forward_pe")) is None else "medium"
        debt_risk = "high" if self._safe_number(strength.get("debt_to_equity")) is None else "medium" if self._safe_number(strength.get("debt_to_equity")) and self._safe_number(strength.get("debt_to_equity")) > 1 else "low"
        growth_risk = "high" if self._safe_number(growth.get("revenue_growth")) is None else "medium" if self._safe_number(growth.get("revenue_growth")) and self._safe_number(growth.get("revenue_growth")) < 0 else "low"
        margin_risk = "high" if self._safe_number(profitability.get("net_margin")) is None else "medium" if self._safe_number(profitability.get("net_margin")) and self._safe_number(profitability.get("net_margin")) < 0 else "low"

        return {
            "valuation_risk": valuation_risk,
            "debt_risk": debt_risk,
            "growth_risk": growth_risk,
            "margin_risk": margin_risk,
        }

    def _build_analysis_payload(
        self,
        ticker: str,
        finnhub_data: dict[str, Any],
        yfinance_data: dict[str, Any],
        screenshots: list[Path] | None = None,
    ) -> dict[str, Any]:
        profile = finnhub_data.get("profile", {}) if isinstance(finnhub_data, dict) else {}
        fundamentals = finnhub_data.get("fundamentals", {}) if isinstance(finnhub_data, dict) else {}
        valuation = fundamentals.get("valuation", {}) if isinstance(fundamentals, dict) else {}
        profitability = fundamentals.get("profitability", {}) if isinstance(fundamentals, dict) else {}
        growth = fundamentals.get("growth", {}) if isinstance(fundamentals, dict) else {}
        strength = fundamentals.get("financial_strength", {}) if isinstance(fundamentals, dict) else {}
        dividend = fundamentals.get("dividend", {}) if isinstance(fundamentals, dict) else {}
        analyst = fundamentals.get("analyst", {}) if isinstance(fundamentals, dict) else {}
        price = yfinance_data.get("price", {}) if isinstance(yfinance_data, dict) else {}
        finance = yfinance_data.get("financial_statements", {}) if isinstance(yfinance_data, dict) else {}
        balance_sheet = finance.get("balance_sheet", {}) if isinstance(finance, dict) else {}
        cash_flow = finance.get("cash_flow", {}) if isinstance(finance, dict) else {}
        extra = yfinance_data.get("extra", {}) if isinstance(yfinance_data, dict) else {}
        news_items = finnhub_data.get("news", []) if isinstance(finnhub_data, dict) else []

        recommendation = analyst.get("recommendation", {}) or {}
        target_price = analyst.get("target_price", {}) or {}
        target_value = self._safe_number(target_price.get("targetPrice")) if isinstance(target_price, dict) else None
        current_price = self._safe_number(price.get("current_price"))
        upside = None
        if current_price and target_value:
            upside = ((target_value - current_price) / current_price) * 100 if current_price else None

        return {
            "ticker": ticker,
            "company": {
                "name": profile.get("company_name") or profile.get("name") or ticker,
                "sector": profile.get("sector") or profile.get("industry"),
                "industry": profile.get("industry"),
                "country": profile.get("country"),
                "currency": profile.get("currency"),
                "market_cap": profile.get("market_capitalization"),
            },
            "fundamental": {
                "company_profile": {
                    "company_name": profile.get("company_name"),
                    "sector": profile.get("sector"),
                    "industry": profile.get("industry"),
                    "country": profile.get("country"),
                    "currency": profile.get("currency"),
                    "market_cap": profile.get("market_capitalization"),
                },
                "cash": balance_sheet.get("cash"),
                "total_debt": balance_sheet.get("debt"),
                "operating_cashflow": cash_flow.get("operating_cashflow"),
                "free_cashflow": cash_flow.get("free_cashflow"),
            },
            "valuation": {
                "pe": self._safe_number(valuation.get("pe")),
                "forward_pe": self._safe_number(valuation.get("forward_pe")),
                "pb": self._safe_number(valuation.get("pb")),
                "ps": self._safe_number(valuation.get("ps")),
                "ev_ebitda": self._safe_number(valuation.get("ev_ebitda")),
                "peg_ratio": self._safe_number(valuation.get("peg")),
            },
            "quality": {
                "cash": self._safe_number(balance_sheet.get("cash")),
                "total_debt": self._safe_number(balance_sheet.get("debt")),
                "debt_to_equity": self._safe_number(strength.get("debt_to_equity")),
                "current_ratio": self._safe_number(strength.get("current_ratio")),
                "gross_margin": self._safe_number(profitability.get("gross_margin")),
                "operating_margin": self._safe_number(profitability.get("operating_margin")),
                "net_margin": self._safe_number(profitability.get("net_margin")),
                "roe": self._safe_number(profitability.get("roe")),
                "roic": self._safe_number(profitability.get("roi")),
            },
            "growth": {
                "revenue_growth_yoy": self._safe_number(growth.get("revenue_growth")),
                "eps_growth": self._safe_number(growth.get("eps_growth")),
                "earnings_trend": self._safe_number(growth.get("earnings_growth")),
            },
            "cashflow": {
                "operating_cashflow": self._safe_number(cash_flow.get("operating_cashflow")),
                "free_cashflow": self._safe_number(cash_flow.get("free_cashflow")),
                "fcf_margin": None,
            },
            "dividend": {
                "dividend_yield": self._safe_number(dividend.get("dividend_yield")) if dividend else self._safe_number(extra.get("dividend_yield")),
                "payout_ratio": self._safe_number(dividend.get("payout_ratio")) if dividend else self._safe_number(extra.get("payout_ratio")),
                "dividend_growth": None,
            },
            "analyst": {
                "recommendation": recommendation,
                "target_price": target_value,
                "upside_percent": upside,
            },
            "news": self._build_news(news_items),
            "risks": self._build_risks(fundamentals, yfinance_data),
            "screenshots": [str(path.name if hasattr(path, 'name') else path) for path in (screenshots or [])],
        }

    async def run(self, ticker: str, screenshots: list[Path] | None = None) -> dict[str, Any]:
        output_folder = self.storage_service.create_capture_folder(ticker)
        screenshots = screenshots or []

        try:
            finnhub_task = asyncio.to_thread(self.finnhub.collect, ticker)
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
