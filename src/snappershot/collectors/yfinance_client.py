from __future__ import annotations

import logging
from typing import Any

import pandas as pd
import yfinance as yf

from ..symbols.symbol_resolver import SymbolResolver

log = logging.getLogger(__name__)


class YahooFinanceClient:
    """Collect OHLCV, statements, and extra market data from Yahoo Finance."""

    def __init__(self, timeout: int = 20, symbol_resolver: SymbolResolver | None = None) -> None:
        self.timeout = timeout
        self.symbol_resolver = symbol_resolver or SymbolResolver()

    def _resolve_ticker(self, symbol: str) -> str:
        lookup = str(symbol).strip()
        if not lookup:
            return lookup

        resolved = self.symbol_resolver.resolve(lookup)
        if resolved and resolved != lookup:
            log.info("Resolved %s -> %s", lookup, resolved)
            return resolved

        return lookup

    def _safe_get(self, info: dict[str, Any], key: str, default: Any = None) -> Any:
        return info.get(key, default) if isinstance(info, dict) else default

    def _normalize_value(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, float) and pd.isna(value):
            return None
        if isinstance(value, pd.Series):
            return value.iloc[0] if not value.empty else None
        if isinstance(value, pd.DataFrame):
            if value.empty:
                return None
            first_row = value.iloc[0]
            if isinstance(first_row, pd.Series):
                return first_row.iloc[0] if len(first_row) == 1 else first_row.to_dict()
            return first_row
        if hasattr(value, "item") and not isinstance(value, (str, bytes, dict, list, tuple, set)):
            try:
                return value.item()
            except Exception:
                return value
        return value

    def _data_point(self, value: Any) -> dict[str, Any]:
        normalized = self._normalize_value(value)
        return {"value": normalized, "source": "yfinance"}

    def _data_section(self, mapping: dict[str, Any]) -> dict[str, dict[str, Any]]:
        return {key: self._data_point(value) for key, value in mapping.items()}

    def _frame_to_latest_value(self, frame: Any, field: str) -> Any:
        if frame is None:
            return None
        if isinstance(frame, pd.DataFrame):
            if frame.empty or field not in frame.index:
                return None
            series = frame.loc[field]
            if isinstance(series, pd.Series):
                return series.dropna().iloc[0] if not series.dropna().empty else None
            return series
        if isinstance(frame, pd.Series):
            return frame.dropna().iloc[0] if not frame.dropna().empty else None
        if isinstance(frame, dict):
            return frame.get(field)
        return None

    def _latest_dividend(self, dividends: Any) -> Any:
        if dividends is None:
            return None
        if isinstance(dividends, pd.Series):
            return dividends.dropna().iloc[-1] if not dividends.dropna().empty else None
        if isinstance(dividends, list):
            return dividends[-1] if dividends else None
        return dividends

    def _build_raw_dataset(self, ticker: Any, info: dict[str, Any]) -> dict[str, Any]:
        company = self._data_section(
            {
                "name": self._safe_get(info, "longName") or self._safe_get(info, "shortName"),
                "ticker": self._safe_get(info, "symbol"),
                "exchange": self._safe_get(info, "exchange"),
                "sector": self._safe_get(info, "sector"),
                "industry": self._safe_get(info, "industry"),
                "country": self._safe_get(info, "country"),
                "currency": self._safe_get(info, "currency"),
                "reported_currency": self._safe_get(info, "financialCurrency"),
                "market_cap": self._safe_get(info, "marketCap"),
            }
        )

        valuation = self._data_section(
            {
                "pe": self._safe_get(info, "trailingPE"),
                "forward_pe": self._safe_get(info, "forwardPE"),
                "pb": self._safe_get(info, "priceToBook"),
                "ps": self._safe_get(info, "priceToSalesTrailing12Months"),
                "ev_ebitda": self._safe_get(info, "enterpriseToEbitda"),
                "peg": self._safe_get(info, "pegRatio"),
            }
        )

        profitability = self._data_section(
            {
                "gross_margin": self._safe_get(info, "grossMargins"),
                "operating_margin": self._safe_get(info, "operatingMargins"),
                "net_margin": self._safe_get(info, "profitMargins"),
                "roe": self._safe_get(info, "returnOnEquity"),
                "roic": self._safe_get(info, "returnOnCapitalEmployed") or self._safe_get(info, "returnOnAssets"),
            }
        )

        growth = self._data_section(
            {
                "revenue_growth": self._safe_get(info, "revenueGrowth"),
                "eps_growth": self._safe_get(info, "earningsGrowth"),
            }
        )

        balance_sheet = self._data_section(
            {
                "total_assets": self._safe_get(info, "totalAssets"),
                "total_liabilities": self._safe_get(info, "totalLiabilities"),
                "total_equity": self._safe_get(info, "totalStockholderEquity"),
                "cash": self._safe_get(info, "totalCash"),
                "debt": self._safe_get(info, "totalDebt"),
                "current_ratio": self._safe_get(info, "currentRatio"),
                "debt_to_equity": self._safe_get(info, "debtToEquity"),
            }
        )

        cashflow = self._data_section(
            {
                "operating_cash_flow": self._safe_get(info, "operatingCashflow"),
                "free_cash_flow": self._safe_get(info, "freeCashflow"),
                "capital_expenditures": self._safe_get(info, "capitalExpenditures"),
            }
        )

        dividends = self._data_section(
            {
                "dividend_rate": self._safe_get(info, "dividendRate"),
                "dividend_yield": self._safe_get(info, "dividendYield"),
                "payout_ratio": self._safe_get(info, "payoutRatio"),
                "latest_dividend": self._latest_dividend(getattr(ticker, "dividends", None)),
            }
        )

        market_data = self._data_section(
            {
                "current_price": self._safe_get(info, "currentPrice"),
                "open": self._safe_get(info, "open"),
                "high": self._safe_get(info, "dayHigh"),
                "low": self._safe_get(info, "dayLow"),
                "close": self._safe_get(info, "previousClose"),
                "volume": self._safe_get(info, "volume"),
                "fifty_two_week_high": self._safe_get(info, "fiftyTwoWeekHigh"),
                "fifty_two_week_low": self._safe_get(info, "fiftyTwoWeekLow"),
                "beta": self._safe_get(info, "beta"),
                "average_volume": self._safe_get(info, "averageVolume"),
            }
        )

        raw_dataset = {
            "company": company,
            "valuation": valuation,
            "profitability": profitability,
            "growth": growth,
            "balance_sheet": balance_sheet,
            "cashflow": cashflow,
            "dividends": dividends,
            "market_data": market_data,
        }

        fields_total = 0
        fields_found = 0
        for section in raw_dataset.values():
            for datapoint in section.values():
                fields_total += 1
                if datapoint["value"] is not None:
                    fields_found += 1

        raw_dataset["data_completeness"] = {
            "fields_total": fields_total,
            "fields_found": fields_found,
            "percent": round((fields_found / fields_total) * 100, 2) if fields_total else 0.0,
        }
        return raw_dataset

    def _history_payload(self, ticker: Any, interval: str) -> list[dict[str, Any]]:
        history = ticker.history(period="5y", interval=interval, auto_adjust=False)
        if history is None or history.empty:
            return []

        rows: list[dict[str, Any]] = []
        for index, row in history.iterrows():
            rows.append(
                {
                    "date": index.strftime("%Y-%m-%d"),
                    "open": float(row.get("Open", 0.0) or 0.0),
                    "high": float(row.get("High", 0.0) or 0.0),
                    "low": float(row.get("Low", 0.0) or 0.0),
                    "close": float(row.get("Close", 0.0) or 0.0),
                    "volume": int(row.get("Volume", 0) or 0),
                }
            )
        return rows

    def collect(self, symbol: str) -> dict[str, Any]:
        resolved_symbol = self._resolve_ticker(symbol)
        ticker = yf.Ticker(resolved_symbol)
        info = getattr(ticker, "info", {}) or {}
        raw_financial_data = self._build_raw_dataset(ticker, info)

        price = {
            "current_price": self._safe_get(info, "currentPrice"),
            "open": self._safe_get(info, "open"),
            "high": self._safe_get(info, "dayHigh"),
            "low": self._safe_get(info, "dayLow"),
            "close": self._safe_get(info, "previousClose"),
            "volume": self._safe_get(info, "volume"),
        }

        financial_statements = {
            "income_statement": {
                "revenue": self._safe_get(info, "totalRevenue"),
                "gross_profit": self._safe_get(info, "grossProfits"),
                "operating_income": self._safe_get(info, "operatingIncome"),
                "net_income": self._safe_get(info, "netIncomeToCommon"),
                "eps": self._safe_get(info, "trailingEps"),
            },
            "balance_sheet": {
                "assets": self._safe_get(info, "totalAssets"),
                "liabilities": self._safe_get(info, "totalLiabilities"),
                "equity": self._safe_get(info, "totalStockholderEquity"),
                "cash": self._safe_get(info, "cash"),
                "debt": self._safe_get(info, "totalDebt"),
            },
            "cash_flow": {
                "operating_cashflow": self._safe_get(info, "operatingCashflow"),
                "free_cashflow": self._safe_get(info, "freeCashflow"),
                "capex": self._safe_get(info, "capitalExpenditures"),
            },
        }

        extra = {
            "fifty_two_week_high": self._safe_get(info, "fiftyTwoWeekHigh"),
            "fifty_two_week_low": self._safe_get(info, "fiftyTwoWeekLow"),
            "beta": self._safe_get(info, "beta"),
            "dividend_rate": self._safe_get(info, "dividendRate"),
            "dividend_yield": self._safe_get(info, "dividendYield"),
            "payout_ratio": self._safe_get(info, "payoutRatio"),
        }

        company = {
            "name": self._safe_get(info, "longName") or self._safe_get(info, "shortName"),
            "ticker": self._safe_get(info, "symbol"),
            "exchange": self._safe_get(info, "exchange"),
            "sector": self._safe_get(info, "sector"),
            "industry": self._safe_get(info, "industry"),
            "country": self._safe_get(info, "country"),
            "market_cap": self._safe_get(info, "marketCap"),
            "currency": self._safe_get(info, "currency"),
            "reported_currency": self._safe_get(info, "financialCurrency"),
        }

        fundamentals = {
            "valuation": {
                "pe": self._safe_get(info, "trailingPE"),
                "forward_pe": self._safe_get(info, "forwardPE"),
                "pb": self._safe_get(info, "priceToBook"),
                "ps": self._safe_get(info, "priceToSalesTrailing12Months"),
                "ev_ebitda": self._safe_get(info, "enterpriseToEbitda"),
                "peg": self._safe_get(info, "pegRatio"),
            },
            "profitability": {
                "gross_margin": self._safe_get(info, "grossMargins"),
                "operating_margin": self._safe_get(info, "operatingMargins"),
                "net_margin": self._safe_get(info, "profitMargins"),
                "roe": self._safe_get(info, "returnOnEquity"),
                "roic": self._safe_get(info, "returnOnCapitalEmployed") or self._safe_get(info, "returnOnAssets"),
            },
            "growth": {
                "revenue_growth": self._safe_get(info, "revenueGrowth"),
                "eps_growth": self._safe_get(info, "earningsGrowth"),
            },
            "financial_strength": {
                "cash": self._safe_get(info, "totalCash"),
                "debt": self._safe_get(info, "totalDebt"),
                "debt_to_equity": self._safe_get(info, "debtToEquity"),
                "current_ratio": self._safe_get(info, "currentRatio"),
            },
            "cashflow": {
                "operating_cash_flow": self._safe_get(info, "operatingCashflow"),
                "free_cash_flow": self._safe_get(info, "freeCashflow"),
            },
            "dividend": {
                "yield": self._safe_get(info, "dividendYield"),
                "payout_ratio": self._safe_get(info, "payoutRatio"),
            },
            "analyst": {
                "recommendation": self._safe_get(info, "recommendationMean"),
                "target_price": self._safe_get(info, "targetMeanPrice"),
            },
        }

        return {
            "price": price,
            "historical_ohlcv": {
                "1d": self._history_payload(ticker, "1d"),
                "1wk": self._history_payload(ticker, "1wk"),
                "1mo": self._history_payload(ticker, "1mo"),
            },
            "financial_statements": financial_statements,
            "extra": extra,
            "company": company,
            "fundamentals": fundamentals,
            "raw_financial_data": raw_financial_data,
        }
