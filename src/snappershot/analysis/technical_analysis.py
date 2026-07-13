from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


class TechnicalAnalysis:
    """Calculate common technical indicators from OHLCV data."""

    def __init__(self) -> None:
        self.logger = log

    def _ensure_dataframe(self, ohlcv_data: Any) -> pd.DataFrame:
        if isinstance(ohlcv_data, pd.DataFrame):
            return ohlcv_data.copy()

        if isinstance(ohlcv_data, dict):
            if "data" in ohlcv_data and isinstance(ohlcv_data["data"], list):
                records = ohlcv_data["data"]
            else:
                records = ohlcv_data.get("rows", [])
        elif isinstance(ohlcv_data, list):
            records = ohlcv_data
        else:
            records = []

        if not records:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        frame = pd.DataFrame(records)
        standardized = frame.rename(
            columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "volume": "volume",
            }
        )
        for column in ["open", "high", "low", "close", "volume"]:
            if column in standardized.columns:
                standardized[column] = pd.to_numeric(
                    standardized[column], errors="coerce"
                )
        standardized = standardized.dropna(subset=["close"]).sort_index()
        return standardized

    def _calculate_rsi(self, close: pd.Series, window: int = 14) -> float:
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(window=window).mean()
        avg_loss = loss.rolling(window=window).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.dropna().iloc[-1]) if not rsi.dropna().empty else 50.0

    def _calculate_macd(self, close: pd.Series) -> tuple[float, float, float]:
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        histogram = macd - signal
        return (
            float(macd.dropna().iloc[-1]),
            float(signal.dropna().iloc[-1]),
            float(histogram.dropna().iloc[-1]),
        )

    def _calculate_adx(self, frame: pd.DataFrame, window: int = 14) -> float:
        if frame.empty or len(frame) < window + 1:
            return 0.0
        high = frame["high"].astype(float)
        low = frame["low"].astype(float)
        close = frame["close"].astype(float)
        up_move = high.diff()
        down_move = low.diff() * -1
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
        tr1 = pd.Series(high - low)
        tr2 = (pd.Series(abs(high - close.shift()))).abs()
        tr3 = (pd.Series(abs(low - close.shift()))).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        tr_smooth = tr.rolling(window).sum()
        plus_dm_smooth = pd.Series(plus_dm, index=frame.index).rolling(window).sum()
        minus_dm_smooth = pd.Series(minus_dm, index=frame.index).rolling(window).sum()
        plus_di = 100 * (plus_dm_smooth / tr_smooth.replace(0, np.nan))
        minus_di = 100 * (minus_dm_smooth / tr_smooth.replace(0, np.nan))
        dx = (abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan)) * 100
        adx = dx.rolling(window).mean()
        return float(adx.dropna().iloc[-1]) if not adx.dropna().empty else 0.0

    def _calculate_atr(self, frame: pd.DataFrame, window: int = 14) -> float:
        if frame.empty or len(frame) < 2:
            return 0.0
        high = frame["high"].astype(float)
        low = frame["low"].astype(float)
        close = frame["close"].astype(float)
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return (
            float(tr.rolling(window).mean().dropna().iloc[-1])
            if not tr.rolling(window).mean().dropna().empty
            else 0.0
        )

    def analyze(self, ohlcv_data: Any) -> dict[str, Any]:
        frame = self._ensure_dataframe(ohlcv_data)
        if frame.empty:
            return {
                "trend": "neutral",
                "above_sma200": False,
                "golden_cross": False,
                "death_cross": False,
                "signals": [],
                "rsi": 50.0,
            }

        close = frame["close"].astype(float)
        sma20 = self._last_value(close.rolling(20).mean())
        sma50 = self._last_value(close.rolling(50).mean())
        sma100 = self._last_value(close.rolling(100).mean())
        sma200 = self._last_value(close.rolling(200).mean())
        ema20 = self._last_value(close.ewm(span=20, adjust=False).mean())
        ema50 = self._last_value(close.ewm(span=50, adjust=False).mean())
        ema200 = self._last_value(close.ewm(span=200, adjust=False).mean())

        rsi = self._calculate_rsi(close)
        macd, signal, histogram = self._calculate_macd(close)
        adx = self._calculate_adx(frame)
        atr = self._calculate_atr(frame)

        current_close = float(close.iloc[-1])
        average_volume = (
            float(self._last_value(frame["volume"].rolling(20).mean()))
            if "volume" in frame.columns and not frame["volume"].dropna().empty
            else 0.0
        )
        latest_volume = (
            float(self._last_value(frame["volume"].dropna()))
            if "volume" in frame.columns and not frame["volume"].dropna().empty
            else 0.0
        )
        relative_volume = latest_volume / average_volume if average_volume else None

        above_sma200 = current_close > sma200
        golden_cross = sma20 > sma50 > sma100 > sma200
        death_cross = sma20 < sma50 < sma100 < sma200

        trend = (
            "bullish"
            if above_sma200 and rsi > 50
            else "bearish"
            if above_sma200 is False and rsi < 50
            else "neutral"
        )
        if (sma20 > sma50 and sma50 > sma200) or (ema20 > ema50 and ema50 > ema200):
            trend = "bullish"
        if (sma20 < sma50 and sma50 < sma200) or (ema20 < ema50 and ema50 < ema200):
            trend = "bearish"

        signals: list[str] = []
        if above_sma200:
            signals.append("above_sma200")
        if golden_cross:
            signals.append("golden_cross")
        if death_cross:
            signals.append("death_cross")
        if rsi > 70:
            signals.append("overbought")
        if rsi < 30:
            signals.append("oversold")

        return {
            "sma": {
                "sma20": round(float(sma20), 2),
                "sma50": round(float(sma50), 2),
                "sma100": round(float(sma100), 2),
                "sma200": round(float(sma200), 2),
            },
            "ema": {
                "ema20": round(float(ema20), 2),
                "ema50": round(float(ema50), 2),
                "ema200": round(float(ema200), 2),
            },
            "momentum": {
                "rsi14": round(rsi, 2),
                "macd": round(macd, 2),
                "macd_signal": round(signal, 2),
                "macd_histogram": round(histogram, 2),
            },
            "trend": {
                "adx": round(adx, 2),
                "trend": trend,
                "uptrend": trend == "bullish",
                "downtrend": trend == "bearish",
            },
            "volatility": {
                "atr": round(atr, 2),
            },
            "volume": {
                "average_volume_20": round(average_volume, 2),
                "relative_volume": (
                    round(relative_volume, 2) if relative_volume is not None else None
                ),
            },
            "above_sma200": above_sma200,
            "golden_cross": golden_cross,
            "death_cross": death_cross,
            "signals": signals,
            "rsi": round(rsi, 2),
        }

    @staticmethod
    def _last_value(series: pd.Series) -> float:
        values = series.dropna()
        if values.empty:
            return 0.0
        return float(values.iloc[-1])

    def _build_sample_ohlcv(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        close = 100.0
        for index in range(30):
            close += (index % 5) - 2
            rows.append(
                {
                    "open": close - 1,
                    "high": close + 1,
                    "low": close - 2,
                    "close": close,
                    "volume": 1000000 + index * 10000,
                }
            )
        return rows
