from __future__ import annotations

from typing import Any


class ProviderManager:
    def _safe_value(self, value: Any) -> bool:
        return value not in (None, "", {}, [])

    def _point(self, primary_value: Any, primary_source: str, fallback_value: Any = None, fallback_source: str | None = None) -> dict[str, Any]:
        if self._safe_value(primary_value):
            return {"value": primary_value, "source": primary_source}
        if self._safe_value(fallback_value):
            return {"value": fallback_value, "source": fallback_source}
        return {"value": None, "source": None}

    @staticmethod
    def _get(mapping: Any, *keys: str) -> Any:
        current = mapping
        for key in keys:
            if not isinstance(current, dict):
                return None
            current = current.get(key)
        return current

    def build(self, *, yahoo_data: dict[str, Any], fmp_data: dict[str, Any], finnhub_data: dict[str, Any]) -> dict[str, Any]:
        yahoo_company = yahoo_data.get("company", {}) if isinstance(yahoo_data, dict) else {}
        yahoo_fundamentals = yahoo_data.get("fundamentals", {}) if isinstance(yahoo_data, dict) else {}
        yahoo_valuation = yahoo_fundamentals.get("valuation", {}) if isinstance(yahoo_fundamentals, dict) else {}
        yahoo_profitability = yahoo_fundamentals.get("profitability", {}) if isinstance(yahoo_fundamentals, dict) else {}
        yahoo_growth = yahoo_fundamentals.get("growth", {}) if isinstance(yahoo_fundamentals, dict) else {}
        yahoo_dividend = yahoo_fundamentals.get("dividend", {}) if isinstance(yahoo_fundamentals, dict) else {}
        yahoo_strength = yahoo_fundamentals.get("financial_strength", {}) if isinstance(yahoo_fundamentals, dict) else {}

        fmp_profile = fmp_data.get("profile", {}) if isinstance(fmp_data, dict) else {}
        fmp_financials = fmp_data.get("financial_statements", {}) if isinstance(fmp_data, dict) else {}
        fmp_income = fmp_financials.get("income_statement", {}) if isinstance(fmp_financials, dict) else {}
        fmp_balance = fmp_financials.get("balance_sheet", {}) if isinstance(fmp_financials, dict) else {}
        fmp_cashflow = fmp_financials.get("cash_flow", {}) if isinstance(fmp_financials, dict) else {}
        fmp_ratios = fmp_data.get("ratios", {}) if isinstance(fmp_data, dict) else {}
        fmp_key_metrics = fmp_data.get("key_metrics", {}) if isinstance(fmp_data, dict) else {}
        fmp_growth = fmp_data.get("financial_growth", {}) if isinstance(fmp_data, dict) else {}

        finnhub_profile = finnhub_data.get("profile", {}) if isinstance(finnhub_data, dict) else {}
        finnhub_fundamentals = finnhub_data.get("fundamentals", {}) if isinstance(finnhub_data, dict) else {}
        finnhub_valuation = finnhub_fundamentals.get("valuation", {}) if isinstance(finnhub_fundamentals, dict) else {}
        finnhub_profitability = finnhub_fundamentals.get("profitability", {}) if isinstance(finnhub_fundamentals, dict) else {}
        finnhub_growth = finnhub_fundamentals.get("growth", {}) if isinstance(finnhub_fundamentals, dict) else {}
        finnhub_dividend = finnhub_fundamentals.get("dividend", {}) if isinstance(finnhub_fundamentals, dict) else {}
        finnhub_analyst = finnhub_fundamentals.get("analyst", {}) if isinstance(finnhub_fundamentals, dict) else {}

        company = {
            "name": self._point(self._get(fmp_profile, "companyName"), "fmp", self._get(yahoo_company, "name"), "yfinance"),
            "ticker": self._point(self._get(fmp_profile, "symbol"), "fmp", self._get(yahoo_company, "ticker"), "yfinance"),
            "exchange": self._point(self._get(fmp_profile, "exchangeShortName"), "fmp", self._get(yahoo_company, "exchange"), "yfinance"),
            "currency": self._point(self._get(fmp_profile, "currency"), "fmp", self._get(yahoo_company, "currency"), "yfinance"),
            "sector": self._point(self._get(fmp_profile, "sector"), "fmp", self._get(yahoo_company, "sector"), "yfinance"),
            "industry": self._point(self._get(fmp_profile, "industry"), "fmp", self._get(yahoo_company, "industry"), "yfinance"),
        }

        market = {
            "current_price": self._point(self._get(yahoo_data, "price", "current_price"), "yfinance", self._get(fmp_profile, "price"), "fmp"),
            "market_cap": self._point(self._get(yahoo_company, "market_cap"), "yfinance", self._get(fmp_profile, "mktCap"), "fmp"),
            "enterprise_value": self._point(self._get(fmp_key_metrics, "enterpriseValue"), "fmp", self._get(yahoo_fundamentals, "financial_strength", "enterprise_value"), "yfinance"),
            "volume": self._point(self._get(yahoo_data, "price", "volume"), "yfinance", self._get(fmp_profile, "volAvg"), "fmp"),
            "average_volume": self._point(self._get(yahoo_data, "extra", "average_volume"), "yfinance", self._get(fmp_profile, "volAvg"), "fmp"),
        }

        key_metrics = {
            "earnings_per_share": self._point(self._get(fmp_key_metrics, "eps"), "fmp", self._get(yahoo_data, "price", "eps"), "yfinance"),
            "revenue_per_share": self._point(self._get(fmp_key_metrics, "revenuePerShare"), "fmp", self._get(yahoo_company, "revenue_per_share"), "yfinance"),
            "book_value_per_share": self._point(self._get(fmp_key_metrics, "bookValuePerShare"), "fmp", self._get(yahoo_company, "book_value_per_share"), "yfinance"),
            "return_on_equity": self._point(self._get(fmp_ratios, "returnOnEquity"), "fmp", self._get(yahoo_profitability, "roe"), "yfinance"),
            "return_on_assets": self._point(self._get(fmp_ratios, "returnOnAssets"), "fmp", None, None),
            "return_on_invested_capital": self._point(self._get(fmp_ratios, "returnOnCapitalEmployed"), "fmp", self._get(yahoo_profitability, "roic"), "yfinance"),
            "net_debt_to_ebitda": self._point(self._get(fmp_ratios, "netDebtToEBITDA"), "fmp", self._get(yahoo_strength, "net_debt_to_ebitda"), "yfinance"),
            "pe_ratio": self._point(self._get(fmp_ratios, "priceEarningsRatio"), "fmp", self._get(yahoo_valuation, "pe"), "yfinance"),
            "forward_pe": self._point(self._get(fmp_ratios, "priceEarningsToGrowthRatio"), "fmp", self._get(yahoo_valuation, "forward_pe"), "yfinance"),
            "ps_ratio": self._point(self._get(fmp_ratios, "priceToSalesRatio"), "fmp", self._get(yahoo_valuation, "ps"), "yfinance"),
            "pb_ratio": self._point(self._get(fmp_ratios, "priceToBookRatio"), "fmp", self._get(yahoo_valuation, "pb"), "yfinance"),
            "ev_sales": self._point(self._get(fmp_ratios, "enterpriseValueMultiple"), "fmp", None, None),
            "ev_ebit": self._point(self._get(fmp_ratios, "enterpriseValueOverEBIT"), "fmp", self._get(yahoo_valuation, "ev_ebit"), "yfinance"),
            "ev_ebitda": self._point(self._get(fmp_ratios, "enterpriseValueMultiple"), "fmp", self._get(yahoo_valuation, "ev_ebitda"), "yfinance"),
        }

        profitability = {
            "gross_margin": self._point(self._get(fmp_ratios, "grossProfitMargin"), "fmp", self._get(yahoo_profitability, "gross_margin"), "yfinance"),
            "operating_margin": self._point(self._get(fmp_ratios, "operatingProfitMargin"), "fmp", self._get(yahoo_profitability, "operating_margin"), "yfinance"),
            "profit_margin": self._point(self._get(fmp_ratios, "netProfitMargin"), "fmp", self._get(yahoo_profitability, "net_margin"), "yfinance"),
            "roa": self._point(self._get(fmp_ratios, "returnOnAssets"), "fmp", None, None),
            "roic": self._point(self._get(fmp_ratios, "returnOnCapitalEmployed"), "fmp", self._get(yahoo_profitability, "roic"), "yfinance"),
        }

        growth = {
            "revenue_growth": self._point(self._get(fmp_growth, "revenueGrowth"), "fmp", self._get(yahoo_growth, "revenue_growth"), "yfinance"),
            "eps_growth": self._point(self._get(fmp_growth, "epsgrowth"), "fmp", self._get(yahoo_growth, "eps_growth"), "yfinance"),
            "fcf_growth": self._point(self._get(fmp_growth, "freeCashFlowGrowth"), "fmp", None, None),
        }

        balance = {
            "total_debt": self._point(self._get(fmp_balance, "totalDebt"), "fmp", self._get(yahoo_strength, "debt"), "yfinance"),
            "net_debt": self._point(self._get(fmp_key_metrics, "netDebt"), "fmp", None, None),
            "debt_equity": self._point(self._get(fmp_ratios, "debtToEquity"), "fmp", self._get(yahoo_strength, "debt_to_equity"), "yfinance"),
            "net_debt_ebitda": self._point(self._get(fmp_ratios, "netDebtToEBITDA"), "fmp", self._get(yahoo_strength, "net_debt_to_ebitda"), "yfinance"),
        }

        cashflow = {
            "operating_cash_flow": self._point(self._get(fmp_cashflow, "netCashProvidedByOperatingActivities"), "fmp", self._get(yahoo_fundamentals, "cashflow", "operating_cash_flow"), "yfinance"),
            "free_cash_flow": self._point(self._get(fmp_cashflow, "freeCashFlow"), "fmp", self._get(yahoo_fundamentals, "cashflow", "free_cash_flow"), "yfinance"),
            "fcf_margin": self._point(self._get(fmp_ratios, "freeCashFlowPerShare"), "fmp", None, None),
        }

        dividend = {
            "dividend_yield": self._point(self._get(fmp_ratios, "dividendYield"), "fmp", self._get(yahoo_dividend, "yield"), "yfinance"),
            "dividend_rate": self._point(self._get(fmp_profile, "lastDiv"), "fmp", self._get(yahoo_dividend, "dividend_rate"), "yfinance"),
            "payout_ratio": self._point(self._get(fmp_ratios, "payoutRatio"), "fmp", self._get(yahoo_dividend, "payout_ratio"), "yfinance"),
        }

        analyst_consensus = {
            "strong_buy": self._point(self._get(finnhub_analyst, "recommendation", "strong_buy"), "finnhub"),
            "buy": self._point(self._get(finnhub_analyst, "recommendation", "buy"), "finnhub"),
            "hold": self._point(self._get(finnhub_analyst, "recommendation", "hold"), "finnhub"),
            "sell": self._point(self._get(finnhub_analyst, "recommendation", "sell"), "finnhub"),
            "target_high_price": self._point(self._get(finnhub_analyst, "target_price", "high"), "finnhub"),
            "target_mean_price": self._point(self._get(finnhub_analyst, "target_price", "average"), "finnhub"),
            "target_low_price": self._point(self._get(finnhub_analyst, "target_price", "low"), "finnhub"),
        }

        return {
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
