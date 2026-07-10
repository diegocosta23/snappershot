import unittest

from src.snappershot.services.financial_snapshot_builder import FinancialSnapshotBuilder


class FinancialSnapshotBuilderTests(unittest.TestCase):
    def test_builds_required_sections_with_value_source_pairs(self) -> None:
        builder = FinancialSnapshotBuilder()

        payload = builder.build(
            search_name="Investor B",
            resolved_ticker="INVE-B.ST",
            fmp_data={
                "profile": {
                    "companyName": "Investor AB ser. B",
                    "symbol": "INVE-B.ST",
                    "exchangeShortName": "OMXSTO",
                    "currency": "SEK",
                    "sector": "Financial Services",
                    "industry": "Asset Management",
                    "price": 251.0,
                    "mktCap": 123456,
                    "volAvg": 14000,
                    "lastDiv": 5.8,
                },
                "financial_statements": {
                    "income_statement": {"revenue": 999999, "eps": 12.8},
                    "balance_sheet": {"totalDebt": 300},
                    "cash_flow": {"netCashProvidedByOperatingActivities": 80, "freeCashFlow": 60},
                },
                "ratios": {
                    "returnOnEquity": 0.21,
                    "returnOnAssets": 0.14,
                    "returnOnCapitalEmployed": 0.18,
                    "netDebtToEBITDA": 1.5,
                    "priceEarningsRatio": 17.0,
                    "priceToSalesRatio": 4.2,
                    "priceToBookRatio": 1.8,
                    "grossProfitMargin": 0.4,
                    "operatingProfitMargin": 0.18,
                    "netProfitMargin": 0.13,
                    "debtToEquity": 0.5,
                    "dividendYield": 0.02,
                    "payoutRatio": 0.4,
                    "enterpriseValueMultiple": 15.2,
                },
                "key_metrics": {
                    "eps": 12.8,
                    "revenuePerShare": 54.0,
                    "bookValuePerShare": 88.0,
                    "enterpriseValue": 9000,
                    "netDebt": 300,
                },
                "financial_growth": {
                    "revenueGrowth": 0.08,
                    "epsgrowth": 0.11,
                    "freeCashFlowGrowth": 0.09,
                },
            },
            finnhub_data={
                "profile": {
                    "company_name": "Investor AB ser. B",
                    "symbol": "INVE-B.ST",
                    "exchange": "Nasdaq Stockholm",
                    "currency": "SEK",
                },
                "price": {"current_price": 250.0, "volume": 12345},
                "fundamentals": {
                    "valuation": {"pe": 18.2},
                    "profitability": {
                        "roe": 0.12,
                        "gross_margin": 0.41,
                        "operating_margin": 0.19,
                        "net_margin": 0.15,
                    },
                    "growth": {"revenue_growth": 0.08, "eps_growth": 0.1},
                    "dividend": {"dividend_yield": 0.02, "dividend_rate": 5.5, "payout_ratio": 0.42},
                    "analyst": {
                        "recommendation": {
                            "strong_buy": 2,
                            "buy": 5,
                            "hold": 3,
                            "sell": 1,
                        },
                        "target_price": {"high": 300.0, "average": 270.0, "low": 240.0},
                    },
                },
            },
            yfinance_data={
                "company": {
                    "name": "Investor AB ser. B",
                    "ticker": "INVE-B.ST",
                    "exchange": "Nasdaq Stockholm",
                    "currency": "SEK",
                    "sector": "Financials",
                    "industry": "Asset Management",
                },
                "price": {"current_price": 249.5, "volume": 12000, "eps": 12.3},
                "extra": {"fifty_two_week_high": 280.0, "fifty_two_week_low": 210.0, "average_volume": 15000},
                "fundamentals": {
                    "valuation": {
                        "pe": 17.5,
                        "forward_pe": 16.1,
                        "ps": 4.4,
                        "pb": 1.8,
                        "ev_ebitda": 11.2,
                    },
                    "profitability": {
                        "roe": 0.11,
                        "gross_margin": 0.4,
                        "operating_margin": 0.18,
                        "net_margin": 0.14,
                    },
                    "growth": {"revenue_growth": 0.07, "eps_growth": 0.09},
                    "financial_strength": {"net_debt_to_ebitda": 0.5},
                    "dividend": {"yield": 0.021, "dividend_rate": 5.4, "payout_ratio": 0.4},
                },
            },
        )

        self.assertEqual(payload["metadata"]["search_name"], "Investor B")
        self.assertEqual(payload["metadata"]["resolved_ticker"], "INVE-B.ST")
        self.assertIn("created_at", payload["metadata"])
        self.assertIn("data_sources", payload["metadata"])
        self.assertIn("data_quality", payload["metadata"])
        self.assertEqual(payload["metadata"]["data_sources"], ["fmp", "yfinance", "finnhub"])
        self.assertIn("company", payload)
        self.assertIn("market", payload)
        self.assertIn("key_metrics", payload)
        self.assertIn("profitability", payload)
        self.assertIn("growth", payload)
        self.assertIn("dividend", payload)
        self.assertIn("analyst_consensus", payload)

        for section_name in ["company", "market", "key_metrics", "profitability", "growth", "dividend", "analyst_consensus"]:
            for datapoint in payload[section_name].values():
                self.assertIn("value", datapoint)
                self.assertIn("source", datapoint)

        self.assertEqual(payload["company"]["name"], {"value": "Investor AB ser. B", "source": "fmp"})
        self.assertEqual(payload["market"]["current_price"]["source"], "yfinance")
        self.assertEqual(payload["key_metrics"]["return_on_equity"]["source"], "fmp")
        self.assertEqual(payload["cashflow"]["free_cash_flow"]["source"], "fmp")
        self.assertEqual(payload["analyst_consensus"]["strong_buy"]["source"], "finnhub")
        self.assertNotIn("historical_ohlcv", payload)

    def test_data_quality_counts_real_values_only(self) -> None:
        builder = FinancialSnapshotBuilder()

        payload = builder.build(
            search_name="Empty",
            resolved_ticker="EMPTY.ST",
            finnhub_data={},
            yfinance_data={},
            fmp_data={},
        )

        data_quality = payload["metadata"]["data_quality"]
        self.assertEqual(data_quality["total_fields"], 45)
        self.assertEqual(data_quality["fields_found"], 0)
        self.assertEqual(data_quality["percent_complete"], 0.0)
        self.assertIn("company.name", data_quality["missing_fields"])


if __name__ == "__main__":
    unittest.main()
