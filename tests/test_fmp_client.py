import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.snappershot.collectors.fmp_client import FMPClient


class FMPClientTests(unittest.TestCase):
    def test_loads_api_key_from_env_file_when_env_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cwd = Path(tmpdir)
            (cwd / ".env").write_text("FMP_API_KEY=from_env_file\n", encoding="utf-8")

            with patch.dict(os.environ, {}, clear=True):
                old_cwd = Path.cwd()
                try:
                    os.chdir(cwd)
                    client = FMPClient()
                finally:
                    os.chdir(old_cwd)

            self.assertEqual(client.api_key, "from_env_file")

    def test_collects_raw_fmp_fundamentals(self) -> None:
        def fake_get(url, params=None, timeout=None):  # noqa: ANN001
            response = MagicMock()
            if url.endswith("/stable/profile/INVE-B.ST"):
                response.status_code = 200
                response.json.return_value = [
                    {
                        "companyName": "Investor AB ser. B",
                        "symbol": "INVE-B.ST",
                        "exchangeShortName": "OMXSTO",
                        "currency": "SEK",
                        "sector": "Financial Services",
                        "industry": "Asset Management",
                        "price": 250,
                        "mktCap": 1000,
                        "volAvg": 12000,
                        "lastDiv": 5.5,
                    }
                ]
            elif url.endswith("/stable/income-statement/INVE-B.ST"):
                response.status_code = 200
                response.json.return_value = [
                    {"revenue": 100, "eps": 12.3, "freeCashFlow": 50}
                ]
            elif url.endswith("/stable/balance-sheet-statement/INVE-B.ST"):
                response.status_code = 200
                response.json.return_value = [{"totalDebt": 30}]
            elif url.endswith("/stable/cash-flow-statement/INVE-B.ST"):
                response.status_code = 200
                response.json.return_value = [
                    {"netCashProvidedByOperatingActivities": 80, "freeCashFlow": 50}
                ]
            elif url.endswith("/stable/ratios/INVE-B.ST"):
                response.status_code = 200
                response.json.return_value = [
                    {
                        "returnOnEquity": 0.21,
                        "returnOnAssets": 0.14,
                        "returnOnCapitalEmployed": 0.18,
                        "netDebtToEBITDA": 1.5,
                        "priceEarningsRatio": 17.0,
                        "priceToSalesRatio": 4.2,
                        "priceToBookRatio": 1.8,
                        "grossProfitMargin": 0.4,
                        "operatingProfitMargin": 0.18,
                        "netProfitMargin": 0.13,
                        "debtToEquity": 0.5,
                        "dividendYield": 0.02,
                        "payoutRatio": 0.4,
                        "enterpriseValueOverEBIT": 15.2,
                    }
                ]
            elif url.endswith("/stable/key-metrics/INVE-B.ST"):
                response.status_code = 200
                response.json.return_value = [
                    {
                        "eps": 12.3,
                        "revenuePerShare": 54.0,
                        "bookValuePerShare": 88.0,
                        "enterpriseValue": 9000,
                        "netDebt": 300,
                    }
                ]
            elif url.endswith("/stable/financial-growth/INVE-B.ST"):
                response.status_code = 200
                response.json.return_value = [
                    {
                        "revenueGrowth": 0.08,
                        "epsgrowth": 0.11,
                        "freeCashFlowGrowth": 0.09,
                    }
                ]
            else:
                response.status_code = 404
                response.text = "not found"
                response.json.return_value = []
            return response

        with (
            patch.dict(os.environ, {"FMP_API_KEY": "test-key"}, clear=True),
            patch(
                "src.snappershot.collectors.fmp_client.requests.get",
                side_effect=fake_get,
            ),
        ):
            client = FMPClient()
            payload = client.collect("INVE-B.ST")

        self.assertEqual(payload["profile"]["companyName"], "Investor AB ser. B")
        self.assertEqual(payload["ratios"]["returnOnEquity"], 0.21)
        self.assertEqual(payload["key_metrics"]["enterpriseValue"], 9000)
        self.assertEqual(payload["financial_growth"]["revenueGrowth"], 0.08)


if __name__ == "__main__":
    unittest.main()
