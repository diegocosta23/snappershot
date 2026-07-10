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

        self.assertEqual(payload["ticker"], "ABB.ST")
        self.assertEqual(payload["search_name"], "ABB.ST")
        self.assertIn("created_at", payload)
        self.assertEqual(payload["data_sources"], ["finnhub", "yfinance"])
        self.assertEqual(payload["yahoo_collected_dataset"]["extra"]["dividendRate"], 6.0)
        self.assertEqual(payload["company"]["name"], "ABB Ltd")
        self.assertEqual(payload["company"]["ticker"], "ABB.ST")
        self.assertIn("valuation", payload)
        self.assertIn("profitability", payload)
        self.assertIn("growth", payload)
        self.assertIn("financial_strength", payload)
        self.assertIn("cashflow", payload)
        self.assertIn("dividend", payload)
        self.assertIn("analyst", payload)
        self.assertNotIn("news", payload)
        self.assertNotIn("risks", payload)
        self.assertEqual(payload["screenshots"], ["daily.png"])

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

        self.assertEqual(payload["company"]["name"], "ABB Ltd")
        self.assertEqual(payload["company"]["currency"], "SEK")
        self.assertEqual(payload["company"]["reported_currency"], "USD")
        self.assertEqual(payload["valuation"]["pe"], 20)
        self.assertEqual(payload["valuation"]["pb"], 2.5)
        self.assertEqual(payload["valuation"]["ps"], 2.0)
        self.assertEqual(payload["valuation"]["ev_ebitda"], 12)
        self.assertEqual(payload["profitability"]["roe"], 0.18)
        self.assertEqual(payload["financial_strength"]["debt"], 2000000)
        self.assertEqual(payload["cashflow"]["free_cash_flow"], 3000000)
        self.assertEqual(payload["dividend"]["yield"], 0.03)
        self.assertEqual(payload["analyst"]["target_price"], 250)
        self.assertEqual(payload["data_sources"], ["yfinance"])

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


if __name__ == "__main__":
    unittest.main()
