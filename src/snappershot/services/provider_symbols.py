from __future__ import annotations


class ProviderSymbolMapper:
    def translate(self, resolved_ticker: str) -> dict[str, str]:
        yahoo_symbol = str(resolved_ticker or "").strip()
        finnhub_symbol = (
            yahoo_symbol.split(".", 1)[0] if "." in yahoo_symbol else yahoo_symbol
        )
        fmp_symbol = yahoo_symbol

        tradingview_symbol = yahoo_symbol
        if yahoo_symbol.endswith(".ST"):
            base = yahoo_symbol.removesuffix(".ST")
            base = base.replace("-", "_")
            tradingview_symbol = f"OMXSTO:{base}"
        elif "." not in yahoo_symbol and yahoo_symbol:
            tradingview_symbol = f"NASDAQ:{yahoo_symbol}"

        return {
            "yahoo_symbol": yahoo_symbol,
            "fmp_symbol": fmp_symbol,
            "finnhub_symbol": finnhub_symbol,
            "tradingview_symbol": tradingview_symbol,
        }
