import unittest

from src.snappershot.services.provider_symbols import ProviderSymbolMapper


class ProviderSymbolMapperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mapper = ProviderSymbolMapper()

    def test_investor_symbol_maps_to_tradingview(self) -> None:
        result = self.mapper.translate("INVE-B.ST")
        self.assertEqual(result["yahoo_symbol"], "INVE-B.ST")
        self.assertEqual(result["finnhub_symbol"], "INVE-B")
        self.assertEqual(result["tradingview_symbol"], "OMXSTO:INVE_B")

    def test_swedbank_symbol_maps_to_tradingview(self) -> None:
        result = self.mapper.translate("SWED-A.ST")
        self.assertEqual(result["tradingview_symbol"], "OMXSTO:SWED_A")

    def test_us_symbol_maps_to_nasdaq(self) -> None:
        result = self.mapper.translate("MSFT")
        self.assertEqual(result["tradingview_symbol"], "NASDAQ:MSFT")


if __name__ == "__main__":
    unittest.main()
