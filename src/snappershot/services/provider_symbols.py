from __future__ import annotations


class ProviderSymbolMapper:
    def translate(self, resolved_ticker: str) -> dict[str, str]:
        yahoo_symbol = str(resolved_ticker or "").strip()
        finnhub_symbol = yahoo_symbol.split(".", 1)[0] if "." in yahoo_symbol else yahoo_symbol
        return {
            "yahoo_symbol": yahoo_symbol,
            "finnhub_symbol": finnhub_symbol,
        }
