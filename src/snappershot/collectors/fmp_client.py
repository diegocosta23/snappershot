from __future__ import annotations

import logging
import os
from typing import Any

import requests
from dotenv import load_dotenv

from ..utils.runtime_paths import env_file_candidates

log = logging.getLogger(__name__)


class FMPClient:
    """Collect company fundamentals from Financial Modeling Prep's stable API."""

    _ENDPOINTS = (
        "profile",
        "income-statement",
        "balance-sheet-statement",
        "cash-flow-statement",
        "ratios",
        "key-metrics",
        "financial-growth",
    )

    def __init__(self, api_key: str | None = None, timeout: int = 20) -> None:
        for env_file in env_file_candidates():
            load_dotenv(env_file, override=False)

        self.api_key = api_key or os.getenv("FMP_API_KEY", "")
        self.timeout = timeout
        self.base_url = "https://financialmodelingprep.com/stable"
        self.last_diagnostics = self._new_diagnostics()
        log.info("FMP enabled: %s", "YES" if self.enabled else "NO")

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def _new_diagnostics(self, symbol: str = "") -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "symbol": symbol,
            "api_response_keys": 0,
            "response_count": 0,
            "fields_collected": 0,
            "errors": [],
        }

    @staticmethod
    def _count_fields(value: Any) -> int:
        if isinstance(value, dict):
            return sum(FMPClient._count_fields(item) for item in value.values())
        if isinstance(value, list):
            return sum(FMPClient._count_fields(item) for item in value)
        return int(value not in (None, ""))

    def _record_error(self, endpoint: str, reason: str) -> None:
        errors = self.last_diagnostics["errors"]
        message = f"{endpoint}: {reason}"
        if message not in errors:
            errors.append(message)

    def _safe_reason(self, response: requests.Response) -> str:
        text = str(getattr(response, "text", "") or "").replace("\n", " ").strip()
        if self.api_key:
            text = text.replace(self.api_key, "[redacted]")
        return text[:180] or f"HTTP {response.status_code}"

    def _request(self, endpoint: str, symbol: str) -> list[dict[str, Any]]:
        if not self.enabled:
            self._record_error(endpoint, "FMP_API_KEY is not configured")
            return []

        try:
            response = requests.get(
                f"{self.base_url}/{endpoint}",
                params={"symbol": symbol, "apikey": self.api_key, "limit": 1},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            reason = f"request failed ({type(exc).__name__})"
            self._record_error(endpoint, reason)
            log.warning("FMP %s %s", endpoint, reason)
            return []

        if response.status_code >= 400:
            reason = f"HTTP {response.status_code}: {self._safe_reason(response)}"
            self._record_error(endpoint, reason)
            log.warning("FMP %s failed: HTTP %s", endpoint, response.status_code)
            return []

        try:
            payload = response.json()
        except ValueError:
            self._record_error(endpoint, "invalid JSON response")
            log.warning("FMP %s returned invalid JSON", endpoint)
            return []

        if isinstance(payload, dict):
            error_message = (
                payload.get("Error Message")
                or payload.get("message")
                or payload.get("error")
            )
            if error_message:
                self._record_error(endpoint, str(error_message)[:180])
                return []
            records = [payload]
        elif isinstance(payload, list):
            records = [item for item in payload if isinstance(item, dict)]
        else:
            self._record_error(endpoint, "unexpected response format")
            return []

        self.last_diagnostics["response_count"] += 1
        self.last_diagnostics["api_response_keys"] += sum(
            len(record) for record in records
        )
        return records

    def collect(self, symbol: str) -> dict[str, Any]:
        self.last_diagnostics = self._new_diagnostics(symbol)

        if not self.enabled:
            self._record_error("configuration", "FMP_API_KEY is not configured")
            return self._empty_payload()

        responses = {
            endpoint: self._request(endpoint, symbol) for endpoint in self._ENDPOINTS
        }

        payload = {
            "profile": self._first_record(responses["profile"]),
            "financial_statements": {
                "income_statement": self._first_record(responses["income-statement"]),
                "balance_sheet": self._first_record(
                    responses["balance-sheet-statement"]
                ),
                "cash_flow": self._first_record(responses["cash-flow-statement"]),
            },
            "ratios": self._first_record(responses["ratios"]),
            "key_metrics": self._first_record(responses["key-metrics"]),
            "financial_growth": self._first_record(responses["financial-growth"]),
        }
        self.last_diagnostics["fields_collected"] = self._count_fields(payload)
        return payload

    @staticmethod
    def _first_record(records: list[dict[str, Any]]) -> dict[str, Any]:
        return records[0] if records else {}

    @staticmethod
    def _empty_payload() -> dict[str, Any]:
        return {
            "profile": {},
            "financial_statements": {
                "income_statement": {},
                "balance_sheet": {},
                "cash_flow": {},
            },
            "ratios": {},
            "key_metrics": {},
            "financial_growth": {},
        }
