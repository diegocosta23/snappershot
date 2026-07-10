import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

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


if __name__ == "__main__":
    unittest.main()
