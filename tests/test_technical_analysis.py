import unittest

from src.snappershot.analysis.technical_analysis import TechnicalAnalysis


class TechnicalAnalysisTests(unittest.TestCase):
    def test_calculates_basic_indicators(self) -> None:
        analyzer = TechnicalAnalysis()
        data = analyzer._build_sample_ohlcv()

        result = analyzer.analyze(data)

        self.assertIn("trend", result)
        self.assertIn("above_sma200", result)
        self.assertGreaterEqual(result["rsi"], 0)
        self.assertIsInstance(result["signals"], list)


if __name__ == "__main__":
    unittest.main()
