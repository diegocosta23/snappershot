from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class FinancialSnapshotBuilder:
    def _safe_value(self, value: Any) -> Any:
        return value if value not in (None, "", {}, []) else None

    def _point(self, primary_value: Any, primary_source: str, fallback_value: Any = None, fallback_source: str | None = None) -> dict[str, Any]:
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
                if value.get("source") == source and self._has_real_value(value.get("value")):
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
            if isinstance(datapoint, dict) and self._has_real_value(datapoint.get("value")):
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

    def build(
        self,
        search_name: str,
        resolved_ticker: str,
        finnhub_data: dict[str, Any],
        yfinance_data: dict[str, Any],
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
            "name": self._point(self._deep_get(yfinance_company, "name"), "yfinance", self._deep_get(profile, "company_name") or self._deep_get(profile, "name"), "finnhub"),
            "ticker": self._point(self._deep_get(yfinance_company, "ticker"), "yfinance", self._deep_get(profile, "symbol"), "finnhub"),
            "exchange": self._point(self._deep_get(yfinance_company, "exchange"), "yfinance", self._deep_get(profile, "exchange"), "finnhub"),
            "currency": self._point(self._deep_get(yfinance_company, "currency"), "yfinance", self._deep_get(profile, "currency"), "finnhub"),
            "sector": self._point(self._deep_get(yfinance_company, "sector"), "yfinance", self._deep_get(profile, "sector"), "finnhub"),
            "industry": self._point(self._deep_get(yfinance_company, "industry"), "yfinance", self._deep_get(profile, "industry"), "finnhub"),
        }

        market = {
            "current_price": self._point(self._deep_get(yfinance_data, "price", "current_price"), "yfinance", self._deep_get(finnhub_data, "price", "current_price"), "finnhub"),
            "market_cap": self._point(self._deep_get(yfinance_company, "market_cap"), "yfinance", self._deep_get(profile, "market_capitalization"), "finnhub"),
            "volume": self._point(self._deep_get(yfinance_data, "price", "volume"), "yfinance", self._deep_get(finnhub_data, "price", "volume"), "finnhub"),
            "average_volume": self._point(self._deep_get(yfinance_data, "extra", "average_volume"), "yfinance", self._deep_get(finnhub_data, "extra", "average_volume"), "finnhub"),
            "52_week_high": self._point(self._deep_get(yfinance_data, "extra", "fifty_two_week_high") or self._deep_get(yfinance_data, "extra", "fiftyTwoWeekHigh"), "yfinance", self._deep_get(finnhub_data, "extra", "fifty_two_week_high"), "finnhub"),
            "52_week_low": self._point(self._deep_get(yfinance_data, "extra", "fifty_two_week_low") or self._deep_get(yfinance_data, "extra", "fiftyTwoWeekLow"), "yfinance", self._deep_get(finnhub_data, "extra", "fifty_two_week_low"), "finnhub"),
        }

        key_metrics = {
            "earnings_per_share": self._point(
                self._deep_get(yfinance_data, "price", "eps") or self._deep_get(yfinance_fundamentals, "financial_statements", "income_statement", "eps") or self._deep_get(yfinance_fundamentals, "eps"),
                "yfinance",
                self._deep_get(finnhub_data, "fundamentals", "profitability", "eps"),
                "finnhub",
            ),
            "revenue_per_share": self._point(self._deep_get(yfinance_company, "revenue_per_share"), "yfinance", self._deep_get(finnhub_profitability, "revenue_per_share") or self._deep_get(profile, "revenue_per_share"), "finnhub"),
            "return_on_equity": self._point(self._deep_get(yfinance_profitability, "roe"), "yfinance", self._deep_get(finnhub_profitability, "roe"), "finnhub"),
            "net_debt_to_ebitda": self._point(self._deep_get(yfinance_fundamentals, "financial_strength", "net_debt_to_ebitda") or self._deep_get(yfinance_fundamentals, "financial_strength", "debt_to_ebitda"), "yfinance", self._deep_get(finnhub_data, "fundamentals", "financial_strength", "net_debt_to_ebitda") or self._deep_get(finnhub_data, "fundamentals", "financial_strength", "debt_to_ebitda"), "finnhub"),
            "pe_ratio": self._point(self._deep_get(yfinance_valuation, "pe"), "yfinance", self._deep_get(valuation, "pe"), "finnhub"),
            "forward_pe": self._point(self._deep_get(yfinance_valuation, "forward_pe"), "yfinance", self._deep_get(valuation, "forward_pe"), "finnhub"),
            "ps_ratio": self._point(self._deep_get(yfinance_valuation, "ps"), "yfinance", self._deep_get(valuation, "ps"), "finnhub"),
            "pb_ratio": self._point(self._deep_get(yfinance_valuation, "pb"), "yfinance", self._deep_get(valuation, "pb"), "finnhub"),
            "ev_to_ebit": self._point(self._deep_get(yfinance_valuation, "ev_ebit"), "yfinance", self._deep_get(valuation, "ev_to_ebit") or self._deep_get(valuation, "ev_ebit"), "finnhub"),
            "ev_to_ebitda": self._point(self._deep_get(yfinance_valuation, "ev_ebitda"), "yfinance", self._deep_get(valuation, "ev_ebitda"), "finnhub"),
        }

        profitability = {
            "gross_margin": self._point(self._deep_get(yfinance_profitability, "gross_margin"), "yfinance", self._deep_get(finnhub_profitability, "gross_margin"), "finnhub"),
            "operating_margin": self._point(self._deep_get(yfinance_profitability, "operating_margin"), "yfinance", self._deep_get(finnhub_profitability, "operating_margin"), "finnhub"),
            "profit_margin": self._point(self._deep_get(yfinance_profitability, "net_margin"), "yfinance", self._deep_get(finnhub_profitability, "net_margin"), "finnhub"),
        }

        growth = {
            "revenue_growth": self._point(self._deep_get(yfinance_growth, "revenue_growth"), "yfinance", self._deep_get(finnhub_growth, "revenue_growth"), "finnhub"),
            "earnings_growth": self._point(self._deep_get(yfinance_growth, "eps_growth"), "yfinance", self._deep_get(finnhub_growth, "eps_growth"), "finnhub"),
        }

        dividend = {
            "dividend_yield": self._point(self._deep_get(yfinance_dividend, "yield") or self._deep_get(yfinance_data, "extra", "dividendYield"), "yfinance", self._deep_get(finnhub_dividend, "dividend_yield"), "finnhub"),
            "dividend_rate": self._point(self._deep_get(yfinance_dividend, "dividend_rate") or self._deep_get(yfinance_data, "extra", "dividendRate"), "yfinance", self._deep_get(finnhub_dividend, "dividend_rate"), "finnhub"),
            "payout_ratio": self._point(self._deep_get(yfinance_dividend, "payout_ratio"), "yfinance", self._deep_get(finnhub_dividend, "payout_ratio"), "finnhub"),
        }

        analyst_consensus = {
            "strong_buy": self._point(self._deep_get(finnhub_analyst, "recommendation", "strong_buy"), "finnhub", self._deep_get(yfinance_analyst, "recommendation", "strong_buy"), "yfinance"),
            "buy": self._point(self._deep_get(finnhub_analyst, "recommendation", "buy"), "finnhub", self._deep_get(yfinance_analyst, "recommendation", "buy"), "yfinance"),
            "hold": self._point(self._deep_get(finnhub_analyst, "recommendation", "hold"), "finnhub", self._deep_get(yfinance_analyst, "recommendation", "hold"), "yfinance"),
            "sell": self._point(self._deep_get(finnhub_analyst, "recommendation", "sell"), "finnhub", self._deep_get(yfinance_analyst, "recommendation", "sell"), "yfinance"),
            "target_high_price": self._point(self._deep_get(finnhub_analyst, "target_price", "high") or self._deep_get(finnhub_analyst, "targetHighPrice"), "finnhub", self._deep_get(yfinance_analyst, "target_price", "high") or self._deep_get(yfinance_analyst, "targetHighPrice"), "yfinance"),
            "target_mean_price": self._point(self._deep_get(finnhub_analyst, "target_price", "average") or self._deep_get(finnhub_analyst, "targetMeanPrice"), "finnhub", self._deep_get(yfinance_analyst, "target_price", "average") or self._deep_get(yfinance_analyst, "targetMeanPrice") or self._deep_get(yfinance_analyst, "target_price"), "yfinance"),
            "target_low_price": self._point(self._deep_get(finnhub_analyst, "target_price", "low") or self._deep_get(finnhub_analyst, "targetLowPrice"), "finnhub", self._deep_get(yfinance_analyst, "target_price", "low") or self._deep_get(yfinance_analyst, "targetLowPrice"), "yfinance"),
        }

        payload = {
            "metadata": {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "search_name": search_name,
                "resolved_ticker": resolved_ticker,
                "data_sources": [
                    source
                    for source in ("yfinance", "finnhub")
                    if self._section_has_source(company, source)
                    or self._section_has_source(market, source)
                    or self._section_has_source(key_metrics, source)
                    or self._section_has_source(profitability, source)
                    or self._section_has_source(growth, source)
                    or self._section_has_source(dividend, source)
                    or self._section_has_source(analyst_consensus, source)
                ],
            },
            "company": company,
            "market": market,
            "key_metrics": key_metrics,
            "profitability": profitability,
            "growth": growth,
            "dividend": dividend,
            "analyst_consensus": analyst_consensus,
        }
        payload["metadata"]["data_quality"] = self._build_data_quality(payload)
        return payload
