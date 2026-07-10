import unittest
from unittest.mock import MagicMock, patch

from src.snappershot.controller.main_controller import MainController


class _ViewStub:
    def __init__(self) -> None:
        self.results = None

    def set_company_results(self, results) -> None:
        self.results = results


class MainControllerSearchTests(unittest.TestCase):
    def test_search_text_changed_uses_symbol_resolver(self) -> None:
        view = _ViewStub()

        with patch("src.snappershot.controller.main_controller.CapturePipeline") as pipeline_cls, patch(
            "src.snappershot.controller.main_controller.SymbolResolver"
        ) as resolver_cls:
            pipeline = MagicMock()
            pipeline.company_service = MagicMock()
            pipeline.window = MagicMock()
            pipeline_cls.return_value = pipeline

            resolver = MagicMock()
            resolver.search.return_value = [
                {"name": "Investor AB ser. B", "symbol": "INVE-B.ST", "exchange": "Nasdaq Stockholm"}
            ]
            resolver_cls.return_value = resolver

            controller = MainController(view)
            controller.handle_search_text_changed("Investor b")

        self.assertEqual(
            view.results,
            ["Investor AB ser. B\nINVE-B.ST\nNasdaq Stockholm"],
        )


if __name__ == "__main__":
    unittest.main()
