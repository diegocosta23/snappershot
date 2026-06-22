from __future__ import annotations

from .window_manager import WindowManager


class TradingViewEngine:
    """Central motor som håller ihop all TradingView-logik."""

    def __init__(self) -> None:
        self.window = WindowManager()

    def prepare(self) -> bool:
        """Säkerställ att TradingView Desktop är igång och redo."""
        return self.window.prepare()

    def is_ready(self) -> bool:
        """Returnerar True om TradingView Desktop är igång."""
        return self.prepare()

    def search_company(self, company_name: str) -> None:
        print(f"[ENGINE] Search company: {company_name}")

    def select_first_result(self) -> None:
        print("[ENGINE] Select first search result")

    def change_timeframe(self, timeframe: str) -> None:
        print(f"[ENGINE] Change timeframe -> {timeframe}")

    def capture(self, filename: str) -> None:
        print(f"[ENGINE] Capture -> {filename}")
