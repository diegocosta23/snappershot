from __future__ import annotations

from snappershot.tradingview.automation import TradingViewAutomation


class MainController:

    def __init__(self):

        self.engine = TradingViewAutomation()

    def capture_company(
        self,
        company: str,
    ) -> bool:

        company = company.strip()

        if not company:
            return False

        return self.engine.capture(company)