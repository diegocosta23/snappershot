from __future__ import annotations

import logging
from typing import Any

import os
import requests
from dotenv import load_dotenv
from ..utils.runtime_paths import env_file_candidates

log = logging.getLogger(__name__)


class FinnhubClient:
    """Collect raw company fundamentals from Finnhub."""

    def __init__(self, api_key: str | None = None, timeout: int = 15) -> None:
        for env_file in env_file_candidates():
            load_dotenv(env_file, override=False)
        self.api_key = api_key or os.getenv("FINNHUB_API_KEY", "")
        self.timeout = timeout
        self.base_url = "https://finnhub.io/api/v1"
        self.last_diagnostics = self._new_diagnostics()
        log.info("Finnhub enabled: %s", "YES" if self.api_key else "NO")

    def _new_diagnostics(self, symbol: str = "") -> dict[str, Any]:
        return {
            "enabled": bool(self.api_key),
            "symbol": symbol,
            "response_count": 0,
            "fields_collected": 0,
            "errors": [],
        }

    @staticmethod
    def _count_fields(value: Any) -> int:
        if isinstance(value, dict):
            return sum(FinnhubClient._count_fields(item) for item in value.values())
        if isinstance(value, list):
            return sum(FinnhubClient._count_fields(item) for item in value)
        return int(value not in (None, ""))

    def _record_error(self, endpoint: str, reason: str) -> None:
        message = f"{endpoint}: {reason}"
        if message not in self.last_diagnostics["errors"]:
            self.last_diagnostics["errors"].append(message)

    def _request(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        if not self.api_key:
            self._record_error("configuration", "FINNHUB_API_KEY is not configured")
            raise RuntimeError("FINNHUB_API_KEY is not configured.")

        try:
            response = requests.get(
                f"{self.base_url}{endpoint}",
                params={**(params or {}), "token": self.api_key},
                timeout=self.timeout,
            )
            if response.status_code == 403:
                self._record_error(endpoint, "HTTP 403 (unsupported market or plan)")
                log.warning("Finnhub %s returned 403 (unsupported market); continuing with fallback data", endpoint)
                return {}
            if response.status_code >= 400:
                self._record_error(endpoint, f"HTTP {response.status_code}")
                log.warning("Finnhub %s failed: %s %s", endpoint, response.status_code, response.text[:300])
                return {}
            payload = response.json()
            self.last_diagnostics["response_count"] += 1
            return payload
        except requests.RequestException as exc:
            self._record_error(endpoint, f"request failed ({type(exc).__name__})")
            log.warning("Finnhub request failed for %s: %s", endpoint, type(exc).__name__)
            return {}

    def get_company_profile(self, symbol: str) -> dict[str, Any]:
        data = self._request("/stock/profile2", {"symbol": symbol})
        if not isinstance(data, dict):
            data = {}
        return {
            "symbol": data.get("ticker") or symbol,
            "company_name": data.get("name"),
            "exchange": data.get("exchange"),
            "country": data.get("country"),
            "currency": data.get("currency"),
            "sector": data.get("finnhubIndustry"),
            "industry": data.get("finnhubIndustry"),
            "market_capitalization": data.get("marketCapitalization"),
            "shares_outstanding": data.get("shareOutstanding"),
        }

    def get_fundamental_metrics(self, symbol: str) -> dict[str, Any]:
        data = self._request("/stock/metric", {"symbol": symbol, "metric": "all"})
        if not isinstance(data, dict):
            data = {}
        metric_payload = data.get("metric", {})
        recommendation_trends = self._request("/stock/recommendation", {"symbol": symbol})
        rec = recommendation_trends[0] if isinstance(recommendation_trends, list) and recommendation_trends else {}
        return {
            "valuation": {
                "pe": metric_payload.get("peBasicExclExtraTTM"),
                "forward_pe": metric_payload.get("peExclExtraTTM"),
                "peg": metric_payload.get("pegRatio"),
                "ps": metric_payload.get("psTTM"),
                "pb": metric_payload.get("pbTTM"),
                "ev": metric_payload.get("enterpriseValue"),
                "ev_ebitda": metric_payload.get("evEbitda"),
                "ev_to_ebit": metric_payload.get("evEbitTTM"),
            },
            "profitability": {
                "roe": metric_payload.get("roeTTM"),
                "roa": metric_payload.get("roaTTM"),
                "roi": metric_payload.get("roiTTM"),
                "gross_margin": metric_payload.get("grossMarginTTM"),
                "operating_margin": metric_payload.get("operatingMarginTTM"),
                "net_margin": metric_payload.get("netMarginTTM"),
                "eps": metric_payload.get("epsBasicExclExtraTTM") or metric_payload.get("epsNormalizedAnnual"),
                "revenue_per_share": metric_payload.get("revenuePerShareTTM"),
            },
            "growth": {
                "revenue_growth": metric_payload.get("revenueGrowthTTM"),
                "eps_growth": metric_payload.get("epsGrowthTTM"),
                "earnings_growth": metric_payload.get("earningsGrowth"),
            },
            "financial_strength": {
                "debt_to_equity": metric_payload.get("debtToEquity"),
                "current_ratio": metric_payload.get("currentRatioTTM"),
                "quick_ratio": metric_payload.get("quickRatioTTM"),
                "net_debt_to_ebitda": metric_payload.get("netDebtToEBITDATTM") or metric_payload.get("netDebtToEbitdaTTM"),
            },
            "dividend": {
                "dividend_yield": metric_payload.get("dividendYieldIndicatedAnnual"),
                "payout_ratio": metric_payload.get("payoutRatio"),
            },
            "analyst": {
                "recommendation": {
                    "strong_buy": rec.get("strongBuy"),
                    "buy": rec.get("buy"),
                    "hold": rec.get("hold"),
                    "sell": rec.get("sell"),
                },
                "target_price": {
                    "high": data.get("targetPrice", {}).get("targetHigh") if isinstance(data.get("targetPrice"), dict) else None,
                    "average": data.get("targetPrice", {}).get("targetMean") if isinstance(data.get("targetPrice"), dict) else None,
                    "low": data.get("targetPrice", {}).get("targetLow") if isinstance(data.get("targetPrice"), dict) else None,
                },
            },
        }

    def collect(self, symbol: str) -> dict[str, Any]:
        self.last_diagnostics = self._new_diagnostics(symbol)
        profile = self.get_company_profile(symbol)
        fundamentals = self.get_fundamental_metrics(symbol)
        payload = {
            "profile": profile,
            "fundamentals": fundamentals,
        }
        self.last_diagnostics["fields_collected"] = self._count_fields(payload)
        return payload
