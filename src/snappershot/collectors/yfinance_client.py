from __future__ import annotations

import logging
from typing import Any

import yfinance as yf

log = logging.getLogger(__name__)


class YahooFinanceClient:
    """Collect OHLCV, statements, and extra market data from Yahoo Finance."""

    def __init__(self, timeout: int = 20) -> None:
        self.timeout = timeout

    def _safe_get(self, info: dict[str, Any], key: str, default: Any = None) -> Any:
        return info.get(key, default) if isinstance(info, dict) else default

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
        ticker = yf.Ticker(symbol)
        info = getattr(ticker, "info", {}) or {}

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
        }
