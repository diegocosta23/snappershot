import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd

from src.snappershot.collectors.yfinance_client import YahooFinanceClient
from src.snappershot.symbols.symbol_resolver import SymbolResolver


class YahooFinanceTickerResolutionTests(unittest.TestCase):
    def test_resolves_display_names_before_querying_yfinance(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "symbol_cache.json"
            with patch("src.snappershot.collectors.yfinance_client.yf.Ticker") as ticker_cls:
                ticker_instance = MagicMock()
                ticker_instance.info = {}
                ticker_cls.return_value = ticker_instance

                client = YahooFinanceClient(symbol_resolver=SymbolResolver(cache_path=cache_path))
                client._history_payload = MagicMock(return_value=[])

                client.collect("Investor B")

                ticker_cls.assert_called_once_with("INVE-B.ST")

    def test_collects_raw_financial_data_with_completeness(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "symbol_cache.json"
            with patch("src.snappershot.collectors.yfinance_client.yf.Ticker") as ticker_cls:
                ticker_instance = MagicMock()
                ticker_instance.info = {
                    "longName": "ABB Ltd",
                    "symbol": "ABB.ST",
                    "exchange": "STO",
                    "sector": "Industrials",
                    "industry": "Engineering",
                    "country": "SE",
                    "currency": "SEK",
                    "financialCurrency": "USD",
                    "marketCap": 1000000000,
                    "trailingPE": 20,
                    "grossMargins": 0.4,
                    "revenueGrowth": 0.12,
                    "totalAssets": 9000000,
                    "operatingCashflow": 4000000,
                    "dividendRate": 6.0,
                    "currentPrice": 200,
                    "open": 198,
                    "dayHigh": 205,
                    "dayLow": 195,
                    "previousClose": 199,
                    "volume": 123456,
                    "fiftyTwoWeekHigh": 250,
                    "fiftyTwoWeekLow": 150,
                    "beta": 1.1,
                    "averageVolume": 100000,
                }
                ticker_instance.dividends = pd.Series([1.25, 1.5], index=pd.to_datetime(["2025-01-01", "2025-06-01"]))
                ticker_cls.return_value = ticker_instance

                client = YahooFinanceClient(symbol_resolver=SymbolResolver(cache_path=cache_path))
                client._history_payload = MagicMock(return_value=[])

                payload = client.collect("ABB.ST")

                raw = payload["raw_financial_data"]
                self.assertEqual(raw["company"]["name"], {"value": "ABB Ltd", "source": "yfinance"})
                self.assertEqual(raw["valuation"]["pe"], {"value": 20, "source": "yfinance"})
                self.assertEqual(raw["profitability"]["gross_margin"], {"value": 0.4, "source": "yfinance"})
                self.assertEqual(raw["growth"]["revenue_growth"], {"value": 0.12, "source": "yfinance"})
                self.assertEqual(raw["balance_sheet"]["total_assets"], {"value": 9000000, "source": "yfinance"})
                self.assertEqual(raw["cashflow"]["operating_cash_flow"], {"value": 4000000, "source": "yfinance"})
                self.assertEqual(raw["dividends"]["latest_dividend"], {"value": 1.5, "source": "yfinance"})
                self.assertEqual(raw["market_data"]["current_price"], {"value": 200, "source": "yfinance"})
                self.assertEqual(raw["data_completeness"]["fields_total"], 46)
                self.assertEqual(raw["data_completeness"]["fields_found"], 26)
                self.assertEqual(raw["data_completeness"]["percent"], 56.52)
                self.assertNotIn("historical_ohlcv", payload)

    def test_collect_does_not_export_long_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "symbol_cache.json"
            with patch("src.snappershot.collectors.yfinance_client.yf.Ticker") as ticker_cls:
                ticker_instance = MagicMock()
                ticker_instance.info = {
                    "longName": "ABB Ltd",
                    "symbol": "ABB.ST",
                }
                ticker_cls.return_value = ticker_instance

                client = YahooFinanceClient(symbol_resolver=SymbolResolver(cache_path=cache_path))

                payload = client.collect("ABB")

                self.assertNotIn("historical_ohlcv", payload)


if __name__ == "__main__":
    unittest.main()
