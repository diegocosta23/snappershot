from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SelectedCompany:
    display_name: str
    yahoo_symbol: str
    tradingview_symbol: str
    finnhub_symbol: str
    exchange: str = ""
    country: str = ""
