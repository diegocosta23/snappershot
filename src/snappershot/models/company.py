from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Company:
    """
    Representerar ett företag som kan öppnas i TradingView.
    """

    name: str
    ticker: str

    @property
    def display_name(self) -> str:
        return f"{self.name} ({self.ticker})"

    def __str__(self) -> str:
        return self.display_name