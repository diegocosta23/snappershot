import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.snappershot.collectors.finnhub_client import FinnhubClient


class FinnhubClientTests(unittest.TestCase):
    def test_loads_api_key_from_env_file_when_env_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cwd = Path(tmpdir)
            (cwd / ".env").write_text("FINNHUB_API_KEY=from_env_file\n", encoding="utf-8")

            with patch.dict(os.environ, {}, clear=True):
                old_cwd = Path.cwd()
                try:
                    os.chdir(cwd)
                    client = FinnhubClient()
                finally:
                    os.chdir(old_cwd)

            self.assertEqual(client.api_key, "from_env_file")

    def test_env_variable_takes_priority_over_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cwd = Path(tmpdir)
            (cwd / ".env").write_text("FINNHUB_API_KEY=from_env_file\n", encoding="utf-8")

            with patch.dict(os.environ, {"FINNHUB_API_KEY": "from_env_var"}, clear=True):
                old_cwd = Path.cwd()
                try:
                    os.chdir(cwd)
                    client = FinnhubClient()
                finally:
                    os.chdir(old_cwd)

            self.assertEqual(client.api_key, "from_env_var")

    def test_collects_analyst_and_fallback_metrics(self) -> None:
        def fake_get(url, params=None, timeout=None):  # noqa: ANN001
            response = MagicMock()
            if url.endswith("/stock/profile2"):
                response.status_code = 200
                response.json.return_value = {
                    "ticker": "INVE-B",
                    "name": "Investor AB ser. B",
                    "exchange": "STO",
                    "country": "SE",
                    "currency": "SEK",
                    "finnhubIndustry": "Financial Services",
                    "marketCapitalization": 1000,
                    "shareOutstanding": 10,
                }
            elif url.endswith("/stock/metric"):
                response.status_code = 200
                response.json.return_value = {
                    "metric": {
                        "revenuePerShareTTM": 12.5,
                        "netDebtToEBITDATTM": 1.7,
                        "evEbitTTM": 15.2,
                    }
                }
            elif url.endswith("/stock/recommendation"):
                response.status_code = 200
                response.json.return_value = [
                    {"strongBuy": 2, "buy": 4, "hold": 3, "sell": 1}
                ]
            else:
                response.status_code = 404
                response.text = "not found"
                response.json.return_value = {}
            return response

        with patch.dict(os.environ, {"FINNHUB_API_KEY": "test-key"}, clear=True), patch(
            "src.snappershot.collectors.finnhub_client.requests.get",
            side_effect=fake_get,
        ):
            client = FinnhubClient()
            payload = client.collect("INVE-B")

        self.assertEqual(payload["fundamentals"]["profitability"]["revenue_per_share"], 12.5)
        self.assertEqual(payload["fundamentals"]["financial_strength"]["net_debt_to_ebitda"], 1.7)
        self.assertEqual(payload["fundamentals"]["valuation"]["ev_to_ebit"], 15.2)
        self.assertEqual(payload["fundamentals"]["analyst"]["recommendation"]["strong_buy"], 2)
        self.assertEqual(payload["fundamentals"]["analyst"]["recommendation"]["buy"], 4)
        self.assertEqual(payload["fundamentals"]["analyst"]["recommendation"]["hold"], 3)
        self.assertEqual(payload["fundamentals"]["analyst"]["recommendation"]["sell"], 1)


if __name__ == "__main__":
    unittest.main()
