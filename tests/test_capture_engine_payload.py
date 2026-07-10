import unittest

from src.snappershot.capture_engine import CaptureEngine


class CaptureEnginePayloadTests(unittest.TestCase):
    def test_builds_fundamental_package_shape(self) -> None:
        engine = CaptureEngine()
        payload = engine._build_analysis_payload(
            ticker="ABB.ST",
            finnhub_data={
                "profile": {
                    "company_name": "ABB Ltd",
                    "sector": "Industrials",
                    "industry": "Engineering",
                    "country": "SE",
                    "currency": "SEK",
                    "market_capitalization": 1000000000,
                },
                "fundamentals": {
                    "valuation": {
                        "pe": 20,
                        "forward_pe": 18,
                        "pb": 2.5,
                        "ps": 2.0,
                        "ev_ebitda": 12,
                        "peg": 1.4,
                    },
                    "profitability": {
                        "gross_margin": 0.4,
                        "operating_margin": 0.2,
                        "net_margin": 0.15,
                        "roe": 0.18,
                        "roi": 0.16,
                    },
                    "growth": {
                        "revenue_growth": 0.12,
                        "eps_growth": 0.1,
                        "earnings_growth": 0.08,
                    },
                    "financial_strength": {
                        "debt_to_equity": 0.5,
                        "current_ratio": 1.4,
                    },
                    "dividend": {
                        "dividend_yield": 0.03,
                        "payout_ratio": 0.4,
                    },
                    "analyst": {
                        "recommendation": {"buy": 1},
                        "target_price": {"targetPrice": 250},
                    },
                },
                "news": [
                    {
                        "headline": "ABB reports strong order intake",
                        "datetime": 1710000000,
                        "source": "Reuters",
                        "summary": "ABB posted a strong quarter.",
                    }
                ],
            },
            yfinance_data={
                "price": {"current_price": 200},
                "company": {"name": "ABB Ltd", "ticker": "ABB.ST"},
                "fundamentals": {
                    "valuation": {"pe": 19, "ps": 1.8, "pb": 2.2, "ev_ebit": 11},
                    "profitability": {"roe": 0.17},
                    "analyst": {"recommendation": {"buy": 3}, "target_price": 260},
                },
                "financial_statements": {
                    "balance_sheet": {"cash": 5000000, "debt": 2000000},
                    "cash_flow": {
                        "operating_cashflow": 4000000,
                        "free_cashflow": 3000000,
                    },
                },
                "extra": {"dividendRate": 6.0, "dividendYield": 0.03, "payoutRatio": 0.4},
            },
            screenshots=["daily.png"],
        )

        self.assertEqual(payload["search_name"], "ABB.ST")
        self.assertIn("created_at", payload)
        self.assertEqual(payload["data_sources"], ["finnhub", "yfinance"])
        self.assertEqual(payload["yahoo_collected_dataset"]["extra"]["dividendRate"], 6.0)
        self.assertEqual(payload["company"]["name"], {"value": "ABB Ltd", "source": "yfinance"})
        self.assertEqual(payload["company"]["ticker"], {"value": "ABB.ST", "source": "yfinance"})
        self.assertEqual(payload["market"]["current_price"], {"value": 200, "source": "yfinance"})
        self.assertEqual(payload["market"]["market_cap"], {"value": 1000000000, "source": "finnhub"})
        self.assertEqual(payload["key_metrics"]["pe_ratio"], {"value": 19, "source": "yfinance"})
        self.assertEqual(payload["key_metrics"]["return_on_equity"], {"value": 0.17, "source": "yfinance"})
        self.assertEqual(payload["analyst_consensus"]["buy"], {"value": 3, "source": "yfinance"})
        self.assertEqual(payload["analyst_consensus"]["target_mean_price"], {"value": 260, "source": "yfinance"})
        self.assertEqual(payload["profitability"]["gross_margin"], {"value": 0.4, "source": "finnhub"})
        self.assertEqual(payload["growth"]["revenue_growth"], {"value": 0.12, "source": "finnhub"})
        self.assertEqual(payload["dividend"]["dividend_yield"], {"value": 0.03, "source": "yfinance"})
        self.assertEqual(payload["dividend"]["dividend_rate"], {"value": 6.0, "source": "yfinance"})
        self.assertNotIn("historical_ohlcv", payload["yahoo_collected_dataset"])
        self.assertNotIn("historical_ohlcv", payload["yahoo_collected_dataset"])

    def test_uses_yfinance_fields_when_finnhub_is_empty(self) -> None:
        engine = CaptureEngine()
        payload = engine._build_analysis_payload(
            ticker="ABB.ST",
            finnhub_data={"profile": {}, "fundamentals": {}},
            yfinance_data={
                "company": {
                    "name": "ABB Ltd",
                    "ticker": "ABB.ST",
                    "exchange": "STO",
                    "sector": "Industrials",
                    "industry": "Engineering",
                    "country": "SE",
                    "market_cap": 1000000000,
                    "currency": "SEK",
                    "reported_currency": "USD",
                },
                "fundamentals": {
                    "valuation": {
                        "pe": 20,
                        "forward_pe": 18,
                        "pb": 2.5,
                        "ps": 2.0,
                        "ev_ebitda": 12,
                        "peg": 1.4,
                    },
                    "profitability": {
                        "gross_margin": 0.4,
                        "operating_margin": 0.2,
                        "net_margin": 0.15,
                        "roe": 0.18,
                        "roic": 0.16,
                    },
                    "growth": {
                        "revenue_growth": 0.12,
                        "eps_growth": 0.1,
                    },
                    "financial_strength": {
                        "cash": 5000000,
                        "debt": 2000000,
                        "debt_to_equity": 0.5,
                        "current_ratio": 1.4,
                    },
                    "cashflow": {
                        "operating_cash_flow": 4000000,
                        "free_cash_flow": 3000000,
                    },
                    "dividend": {
                        "yield": 0.03,
                        "payout_ratio": 0.4,
                    },
                    "analyst": {
                        "recommendation": {"buy": 1},
                        "target_price": 250,
                    },
                },
            },
            screenshots=["daily.png"],
        )

        self.assertEqual(payload["company"]["name"], {"value": "ABB Ltd", "source": "yfinance"})
        self.assertEqual(payload["company"]["currency"], {"value": "SEK", "source": "yfinance"})
        self.assertEqual(payload["market"]["current_price"], {"value": None, "source": None})
        self.assertEqual(payload["key_metrics"]["pe_ratio"], {"value": 20, "source": "yfinance"})
        self.assertEqual(payload["key_metrics"]["pb_ratio"], {"value": 2.5, "source": "yfinance"})
        self.assertEqual(payload["key_metrics"]["ev_to_ebitda"], {"value": 12, "source": "yfinance"})
        self.assertEqual(payload["profitability"]["profit_margin"], {"value": 0.15, "source": "yfinance"})
        self.assertEqual(payload["dividend"]["dividend_yield"], {"value": 0.03, "source": "yfinance"})
        self.assertEqual(payload["analyst_consensus"]["target_mean_price"], {"value": 250, "source": "yfinance"})
        self.assertEqual(payload["data_sources"], ["yfinance"])
        self.assertEqual(payload["key_metrics"]["earnings_per_share"], {"value": None, "source": None})
        self.assertEqual(payload["analyst_consensus"]["target_high_price"], {"value": None, "source": None})

    def test_omits_finnhub_from_data_sources_when_empty(self) -> None:
        engine = CaptureEngine()
        payload = engine._build_analysis_payload(
            ticker="ABB.ST",
            finnhub_data={},
            yfinance_data={
                "company": {"name": "ABB Ltd", "ticker": "ABB.ST"},
                "fundamentals": {},
            },
            screenshots=[],
        )

        self.assertEqual(payload["data_sources"], ["yfinance"])
        self.assertEqual(payload["key_metrics"]["return_on_equity"], {"value": None, "source": None})


if __name__ == "__main__":
    unittest.main()
