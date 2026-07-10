import unittest

from src.snappershot.capture_engine import CaptureEngine


class CaptureEnginePayloadTests(unittest.TestCase):
    def _assert_point(self, point: dict, value, source) -> None:
        self.assertEqual(point["value"], value)
        self.assertEqual(point["source"], source)

    def test_every_metric_has_value_source_structure(self) -> None:
        engine = CaptureEngine()
        payload = engine._build_analysis_payload(
            ticker="ABB.ST",
            finnhub_data={
                "profile": {
                    "name": "ABB Ltd",
                    "symbol": "ABB.ST",
                    "exchange": "STO",
                    "currency": "SEK",
                    "sector": "Industrials",
                    "industry": "Engineering",
                    "market_capitalization": 1000000000,
                },
                "fundamentals": {
                    "valuation": {
                        "pe": 20,
                        "forward_pe": 18,
                        "ps": 2.0,
                        "pb": 2.5,
                        "ev_ebit": 11,
                        "ev_ebitda": 12,
                    },
                    "profitability": {
                        "gross_margin": 0.4,
                        "operating_margin": 0.2,
                        "net_margin": 0.15,
                        "roe": 0.18,
                    },
                    "growth": {
                        "revenue_growth": 0.12,
                        "earnings_growth": 0.08,
                    },
                    "dividend": {
                        "dividend_yield": 0.03,
                        "dividend_rate": 6.0,
                        "payout_ratio": 0.4,
                    },
                    "analyst": {
                        "recommendation": {
                            "strong_buy": 1,
                            "buy": 2,
                            "hold": 3,
                            "sell": 4,
                        },
                        "target_price": {
                            "high": 280,
                            "average": 260,
                            "low": 240,
                        },
                    },
                },
            },
            yfinance_data={
                "price": {
                    "current_price": 200,
                    "volume": 123456,
                },
                "company": {
                    "name": "ABB Ltd",
                    "ticker": "ABB.ST",
                    "exchange": "STO",
                    "currency": "SEK",
                    "sector": "Industrials",
                    "industry": "Engineering",
                    "market_cap": 1000000000,
                },
                "fundamentals": {
                    "valuation": {
                        "pe": 19,
                        "forward_pe": 17,
                        "ps": 1.8,
                        "pb": 2.2,
                        "ev_ebit": 10,
                        "ev_ebitda": 11,
                    },
                    "profitability": {
                        "gross_margin": 0.41,
                        "operating_margin": 0.21,
                        "net_margin": 0.16,
                        "roe": 0.17,
                    },
                    "growth": {
                        "revenue_growth": 0.11,
                        "eps_growth": 0.09,
                    },
                    "dividend": {
                        "yield": 0.031,
                        "dividend_rate": 6.2,
                        "payout_ratio": 0.41,
                    },
                },
                "extra": {
                    "dividendYield": 0.031,
                    "dividendRate": 6.2,
                    "average_volume": 100000,
                    "fifty_two_week_high": 250,
                    "fifty_two_week_low": 150,
                },
            },
        )

        for section_name in ("company", "market", "key_metrics", "profitability", "growth", "dividend", "analyst_consensus"):
            section = payload[section_name]
            for field_name, point in section.items():
                self.assertIn("value", point, f"{section_name}.{field_name}")
                self.assertIn("source", point, f"{section_name}.{field_name}")

        self._assert_point(payload["company"]["name"], "ABB Ltd", "yfinance")
        self._assert_point(payload["company"]["ticker"], "ABB.ST", "yfinance")
        self._assert_point(payload["market"]["current_price"], 200, "yfinance")
        self._assert_point(payload["market"]["market_cap"], 1000000000, "yfinance")
        self._assert_point(payload["market"]["volume"], 123456, "yfinance")
        self._assert_point(payload["market"]["average_volume"], 100000, "yfinance")
        self._assert_point(payload["market"]["52_week_high"], 250, "yfinance")
        self._assert_point(payload["market"]["52_week_low"], 150, "yfinance")
        self._assert_point(payload["key_metrics"]["earnings_per_share"], None, None)
        self._assert_point(payload["key_metrics"]["revenue_per_share"], None, None)
        self._assert_point(payload["key_metrics"]["return_on_equity"], 0.17, "yfinance")
        self._assert_point(payload["key_metrics"]["net_debt_to_ebitda"], None, None)
        self._assert_point(payload["key_metrics"]["pe_ratio"], 19, "yfinance")
        self._assert_point(payload["key_metrics"]["forward_pe"], 17, "yfinance")
        self._assert_point(payload["key_metrics"]["ps_ratio"], 1.8, "yfinance")
        self._assert_point(payload["key_metrics"]["pb_ratio"], 2.2, "yfinance")
        self._assert_point(payload["key_metrics"]["ev_to_ebit"], 10, "yfinance")
        self._assert_point(payload["key_metrics"]["ev_to_ebitda"], 11, "yfinance")
        self._assert_point(payload["profitability"]["gross_margin"], 0.41, "yfinance")
        self._assert_point(payload["profitability"]["operating_margin"], 0.21, "yfinance")
        self._assert_point(payload["profitability"]["profit_margin"], 0.16, "yfinance")
        self._assert_point(payload["growth"]["revenue_growth"], 0.11, "yfinance")
        self._assert_point(payload["growth"]["earnings_growth"], 0.09, "yfinance")
        self._assert_point(payload["dividend"]["dividend_yield"], 0.031, "yfinance")
        self._assert_point(payload["dividend"]["dividend_rate"], 6.2, "yfinance")
        self._assert_point(payload["dividend"]["payout_ratio"], 0.41, "yfinance")
        self._assert_point(payload["analyst_consensus"]["strong_buy"], 1, "finnhub")
        self._assert_point(payload["analyst_consensus"]["buy"], 2, "finnhub")
        self._assert_point(payload["analyst_consensus"]["hold"], 3, "finnhub")
        self._assert_point(payload["analyst_consensus"]["sell"], 4, "finnhub")
        self._assert_point(payload["analyst_consensus"]["target_high_price"], 280, "finnhub")
        self._assert_point(payload["analyst_consensus"]["target_mean_price"], 260, "finnhub")
        self._assert_point(payload["analyst_consensus"]["target_low_price"], 240, "finnhub")
        self.assertNotIn("historical_ohlcv", payload)
        self.assertNotIn("raw_financial_data", payload)

    def test_missing_fields_are_detected(self) -> None:
        engine = CaptureEngine()
        payload = engine._build_analysis_payload(
            ticker="ABB.ST",
            finnhub_data={},
            yfinance_data={},
        )

        self.assertEqual(payload["data_quality"]["fields_found"], 0)
        self.assertGreater(payload["data_quality"]["total_fields"], 0)
        self.assertEqual(payload["data_quality"]["percent_complete"], 0.0)
        self.assertIn("company.name", payload["data_quality"]["missing_fields"])
        self.assertIn("analyst_consensus.target_mean_price", payload["data_quality"]["missing_fields"])

    def test_data_quality_percentage_calculation_works(self) -> None:
        engine = CaptureEngine()
        payload = engine._build_analysis_payload(
            ticker="ABB.ST",
            finnhub_data={},
            yfinance_data={
                "company": {"name": "ABB Ltd"},
                "price": {"current_price": 200},
                "fundamentals": {"valuation": {"pe": 19}},
            },
        )

        total = payload["data_quality"]["total_fields"]
        found = payload["data_quality"]["fields_found"]
        self.assertEqual(payload["data_quality"]["percent_complete"], round((found / total) * 100, 2))
        self.assertEqual(found, 3)


if __name__ == "__main__":
    unittest.main()
