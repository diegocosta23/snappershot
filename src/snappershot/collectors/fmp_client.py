from __future__ import annotations

import logging
import os
from typing import Any

import requests
from dotenv import load_dotenv

from ..utils.runtime_paths import env_file_candidates

log = logging.getLogger(__name__)


class FMPClient:
    def __init__(self, api_key: str | None = None, timeout: int = 20) -> None:
        for env_file in env_file_candidates():
            load_dotenv(env_file, override=False)
        self.api_key = api_key or os.getenv("FMP_API_KEY", "")
        self.timeout = timeout
        self.base_url = "https://financialmodelingprep.com/api"

    def _request(self, endpoint: str, symbol: str) -> list[dict[str, Any]]:
        if not self.api_key:
            log.warning("FMP disabled: NO")
            return []

        url = f"{self.base_url}{endpoint}/{symbol}"
        try:
            response = requests.get(
                url,
                params={"apikey": self.api_key, "limit": 1},
                timeout=self.timeout,
            )
            if response.status_code >= 400:
                log.warning("FMP %s failed: %s %s", endpoint, response.status_code, response.text[:300])
                return []
            data = response.json()
            return data if isinstance(data, list) else []
        except requests.RequestException as exc:
            log.warning("FMP request failed for %s: %s", endpoint, exc)
            return []

    def collect(self, symbol: str) -> dict[str, Any]:
        profile = self._request("/v3/profile", symbol)
        income = self._request("/v3/income-statement", symbol)
        balance = self._request("/v3/balance-sheet-statement", symbol)
        cashflow = self._request("/v3/cash-flow-statement", symbol)
        ratios = self._request("/v3/ratios", symbol)
        key_metrics = self._request("/v3/key-metrics", symbol)
        growth = self._request("/v3/financial-growth", symbol)

        return {
            "profile": profile[0] if profile else {},
            "financial_statements": {
                "income_statement": income[0] if income else {},
                "balance_sheet": balance[0] if balance else {},
                "cash_flow": cashflow[0] if cashflow else {},
            },
            "ratios": ratios[0] if ratios else {},
            "key_metrics": key_metrics[0] if key_metrics else {},
            "financial_growth": growth[0] if growth else {},
        }
