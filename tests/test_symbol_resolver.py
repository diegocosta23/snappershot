import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.snappershot.symbols.symbol_resolver import SymbolResolver


class SymbolResolverTests(unittest.TestCase):
    def test_uses_cache_before_search(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "symbol_cache.json"
            resolver = SymbolResolver(cache_path=cache_path)
            resolver.cache = {
                "lifco": {
                    "name": "Lifco AB ser B",
                    "yahoo_symbol": "LIFCO-B.ST",
                    "exchange": "STO",
                    "currency": "SEK",
                }
            }
            resolver._save_cache()

            matches = resolver.search("Lifco")

            self.assertEqual(matches[0]["symbol"], "LIFCO-B.ST")

    def test_falls_back_to_original_query_when_search_has_no_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "symbol_cache.json"
            resolver = SymbolResolver(cache_path=cache_path)

            with patch("src.snappershot.symbols.symbol_resolver.Search") as search_cls:
                search_cls.return_value.quotes = []
                resolved = resolver.resolve("Totally Unknown Company")

            self.assertEqual(resolved, "Totally Unknown Company")


if __name__ == "__main__":
    unittest.main()
