"""Market data providers for METI."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd
import yfinance as yf

from meti.config import Settings, get_settings

logger = logging.getLogger(__name__)


def _extract_close_series(data: pd.DataFrame) -> pd.Series | None:
    """Robustly extract a 1-D Close series from yfinance output."""
    if data is None or data.empty:
        return None

    # Newer yfinance sometimes returns MultiIndex columns even for one ticker
    if isinstance(data.columns, pd.MultiIndex):
        # Try to pick the Close level
        try:
            if "Close" in data.columns.get_level_values(0):
                closes = data["Close"]
            else:
                closes = data.xs("Close", axis=1, level=0, drop_level=True)
            if isinstance(closes, pd.DataFrame):
                closes = closes.iloc[:, 0]
            return closes.dropna()
        except Exception:
            pass

    # Classic single-level columns
    if "Close" in data.columns:
        return data["Close"].dropna()

    # Last resort: first numeric column
    numeric = data.select_dtypes(include="number")
    if not numeric.empty:
        return numeric.iloc[:, 0].dropna()

    return None


def fetch_price_change(
    ticker: str,
    period: str,
    interval: str,
    lookback_bars: int,
) -> tuple[float, float]:
    """
    Fetch percent change over the last `lookback_bars` bars.

    Returns
    -------
    (percent_change, current_price)
    """
    try:
        data = yf.download(
            ticker,
            period=period,
            interval=interval,
            auto_adjust=False,
            progress=False,
            threads=False,
        )
        closes = _extract_close_series(data)
        if closes is None or len(closes) < 2:
            return 0.0, 0.0

        # Use available bars if fewer than requested
        bars = min(lookback_bars, len(closes) - 1)
        if bars < 1:
            return 0.0, float(closes.iloc[-1])

        start_price = float(closes.iloc[-bars - 1])
        end_price = float(closes.iloc[-1])

        if start_price == 0:
            return 0.0, end_price

        pct = ((end_price - start_price) / start_price) * 100.0
        return pct, end_price

    except Exception as e:
        logger.warning("Failed to fetch %s (%s %s): %s", ticker, period, interval, e)
        return 0.0, 0.0


def get_all_asset_data(settings: Settings | None = None) -> dict[str, Any]:
    """
    Fetch multi-timeframe data for every configured asset.

    Returns a dict:
    {
      "CL=F": {
          "name": "...",
          "current_price": 78.5,
          "changes": {"1h": 0.3, "4h": 1.2, ...},
          "weighted_change": 0.85,
          ...
      },
      ...
    }
    """
    settings = settings or get_settings()
    result: dict[str, Any] = {}

    for ticker, asset in settings.assets.items():
        changes: dict[str, float] = {}
        current_price = 0.0

        for tf_key, tf in settings.timeframes.items():
            pct, price = fetch_price_change(
                ticker=ticker,
                period=tf.period,
                interval=tf.interval,
                lookback_bars=tf.lookback_bars,
            )
            changes[tf_key] = pct
            if price > 0 and current_price == 0.0:
                current_price = price

        # Weighted change across timeframes
        weighted = 0.0
        for tf_key, pct in changes.items():
            weighted += pct * settings.timeframes[tf_key].weight

        result[ticker] = {
            "ticker": ticker,
            "name": asset.name,
            "emoji": asset.emoji,
            "color": asset.color,
            "weight": asset.weight,
            "description": asset.description,
            "current_price": current_price,
            "changes": changes,
            "weighted_change": weighted,
        }

    return result
