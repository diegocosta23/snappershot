from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .provider_manager import ProviderManager


class FinancialSnapshotBuilder:
    def __init__(self) -> None:
        self.provider_manager = ProviderManager()

    def _safe_value(self, value: Any) -> Any:
        return value if value not in (None, "", {}, []) else None

    def _point(
        self,
        primary_value: Any,
        primary_source: str,
        fallback_value: Any = None,
        fallback_source: str | None = None,
    ) -> dict[str, Any]:
        if self._safe_value(primary_value) is not None:
            return {"value": primary_value, "source": primary_source}
        if self._safe_value(fallback_value) is not None:
            return {"value": fallback_value, "source": fallback_source}
        return {"value": None, "source": None}

    @staticmethod
    def _deep_get(mapping: Any, *keys: str) -> Any:
        current = mapping
        for key in keys:
            if not isinstance(current, dict):
                return None
            current = current.get(key)
        return current

    def _has_real_value(self, value: Any) -> bool:
        return self._safe_value(value) is not None

    def _pick_source(self, primary_value: Any, fallback_value: Any) -> str | None:
        if self._has_real_value(primary_value):
            return "yfinance"
        if self._has_real_value(fallback_value):
            return "finnhub"
        return None

    def _section_has_source(self, section: Any, source: str) -> bool:
        if not isinstance(section, dict):
            return False
        for value in section.values():
            if isinstance(value, dict):
                if value.get("source") == source and self._has_real_value(
                    value.get("value")
                ):
                    return True
            elif source is None and self._has_real_value(value):
                return True
        return False

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
            ("market", "enterprise_value"),
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
            ("balance", "total_debt"),
            ("balance", "net_debt"),
            ("balance", "debt_equity"),
            ("balance", "net_debt_ebitda"),
            ("cashflow", "operating_cash_flow"),
            ("cashflow", "free_cash_flow"),
            ("cashflow", "fcf_margin"),
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
            if isinstance(datapoint, dict) and self._has_real_value(
                datapoint.get("value")
            ):
                fields_found += 1
            else:
                missing_fields.append(f"{section}.{field}")

        total_fields = len(field_paths)
        percent_complete = (
            round((fields_found / total_fields) * 100, 2) if total_fields else 0.0
        )
        return {
            "total_fields": total_fields,
            "fields_found": fields_found,
            "percent_complete": percent_complete,
            "missing_fields": missing_fields,
        }

    def build(
        self,
        search_name: str,
        resolved_ticker: str,
        finnhub_data: dict[str, Any],
        yfinance_data: dict[str, Any],
        fmp_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        fmp_data = fmp_data or {}
        merged = self.provider_manager.build(
            yahoo_data=yfinance_data, fmp_data=fmp_data, finnhub_data=finnhub_data
        )
        company = merged["company"]
        market = merged["market"]
        key_metrics = merged["key_metrics"]
        profitability = merged["profitability"]
        growth = merged["growth"]
        balance = merged["balance"]
        cashflow = merged["cashflow"]
        dividend = merged["dividend"]
        analyst_consensus = merged["analyst_consensus"]

        payload = {
            "metadata": {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "search_name": search_name,
                "resolved_ticker": resolved_ticker,
                "data_sources": [
                    source
                    for source in ("fmp", "yfinance", "finnhub")
                    if self._section_has_source(company, source)
                    or self._section_has_source(market, source)
                    or self._section_has_source(key_metrics, source)
                    or self._section_has_source(profitability, source)
                    or self._section_has_source(growth, source)
                    or self._section_has_source(balance, source)
                    or self._section_has_source(cashflow, source)
                    or self._section_has_source(dividend, source)
                    or self._section_has_source(analyst_consensus, source)
                ],
            },
            "company": company,
            "market": market,
            "key_metrics": key_metrics,
            "profitability": profitability,
            "growth": growth,
            "balance": balance,
            "cashflow": cashflow,
            "dividend": dividend,
            "analyst_consensus": analyst_consensus,
        }
        payload["metadata"]["data_quality"] = self._build_data_quality(payload)
        return payload
