from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from yfinance.search import Search

log = logging.getLogger(__name__)


class SymbolResolver:
    def __init__(self, cache_path: str | Path | None = None) -> None:
        self.cache_path = Path(cache_path or Path(__file__).resolve().parent / "symbol_cache.json")
        self.cache: dict[str, dict[str, Any]] = {}
        self._load_cache()

    @staticmethod
    def _preferred_symbol(symbol: str) -> str:
        ticker = str(symbol or "").strip()
        if not ticker:
            return ticker
        if ticker.endswith(".ST") or "." in ticker:
            return ticker
        return f"{ticker}.ST"

    def _load_cache(self) -> None:
        if not self.cache_path.exists():
            return
        try:
            with self.cache_path.open(encoding="utf-8") as handle:
                data = json.load(handle)
                if isinstance(data, dict):
                    self.cache = data
        except (OSError, ValueError, json.JSONDecodeError):
            self.cache = {}

    def _save_cache(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with self.cache_path.open("w", encoding="utf-8") as handle:
            json.dump(self.cache, handle, indent=2, ensure_ascii=False)

    @staticmethod
    def _normalize_query(text: str) -> str:
        return " ".join(str(text).strip().split()).casefold()

    @staticmethod
    def _build_known_mapping(query: str) -> dict[str, Any] | None:
        known: dict[str, dict[str, Any]] = {
            "investor b": {"name": "Investor B", "symbol": "INVE-B.ST", "exchange": "STO", "currency": "SEK"},
            "lifco b": {"name": "Lifco AB ser. B", "symbol": "LIFCO-B.ST", "exchange": "STO", "currency": "SEK"},
            "atlas copco b": {"name": "Atlas Copco AB ser. B", "symbol": "ATCO-B.ST", "exchange": "STO", "currency": "SEK"},
            "abb": {"name": "ABB Ltd", "symbol": "ABB.ST", "exchange": "STO", "currency": "SEK"},
            "sandvik": {"name": "Sandvik AB", "symbol": "SAND.ST", "exchange": "STO", "currency": "SEK"},
            "swedbank a": {"name": "Swedbank AB ser. A", "symbol": "SWED-A.ST", "exchange": "STO", "currency": "SEK"},
        }
        return known.get(SymbolResolver._normalize_query(query))

    def search(self, query: str) -> list[dict[str, Any]]:
        lookup = self._normalize_query(query)
        if not lookup:
            return []

        cached = self.cache.get(lookup)
        if cached:
            log.info("Cache hit for %s -> %s", query, cached.get("yahoo_symbol"))
            return [
                {
                    "name": cached.get("name"),
                    "symbol": cached.get("yahoo_symbol"),
                    "exchange": cached.get("exchange"),
                    "currency": cached.get("currency"),
                }
            ]

        known_match = self._build_known_mapping(query)
        if known_match:
            log.info("Searching symbol: %s", query)
            log.info("Found: %s", known_match["symbol"])
            return [known_match]

        try:
            log.info("Searching symbol: %s", query)
            results = Search(lookup, max_results=5)
            matches: list[dict[str, Any]] = []
            for item in getattr(results, "quotes", []) or []:
                symbol = item.get("symbol")
                if not symbol:
                    continue
                matches.append(
                    {
                        "name": item.get("longname") or item.get("shortname") or query,
                        "symbol": self._preferred_symbol(symbol),
                        "exchange": item.get("exchange"),
                        "currency": item.get("currency"),
                    }
                )
            if matches:
                log.info("Found: %s", matches[0]["symbol"])
            return matches
        except Exception as exc:  # pragma: no cover - defensive path
            log.warning("Symbol search failed for %s: %s", query, exc)
            return []

    def resolve(self, query: str) -> str:
        lookup = self._normalize_query(query)
        if not lookup:
            return query

        cached = self.cache.get(lookup)
        if cached:
            resolved_symbol = cached.get("yahoo_symbol") or query
            if resolved_symbol and resolved_symbol != query:
                log.info("Resolved %s -> %s", query, resolved_symbol)
            return resolved_symbol

        matches = self.search(query)
        if matches:
            selected = matches[0]
            self.cache[lookup] = {
                "name": selected.get("name"),
                "yahoo_symbol": selected.get("symbol"),
                "exchange": selected.get("exchange"),
                "currency": selected.get("currency"),
            }
            self._save_cache()
            log.info("Cache saved")
            return selected.get("symbol") or query

        return query
