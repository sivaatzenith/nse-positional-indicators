"""
indicators.py
~~~~~~~~~~~~~
Core computation engine for NSE positional trading indicators.

Supported indicators
--------------------
- SMA50  : 50-day Simple Moving Average
- SMA200 : 200-day Simple Moving Average
- RSI    : 14-day Relative Strength Index
- MACD   : 12/26-day EMA difference with 9-day signal line
- ADX    : 14-day Average Directional Index
- OBV    : On-Balance Volume
"""

from __future__ import annotations

import json
from typing import Dict, Any

import pandas as pd
import yfinance as yf


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------

def get_data(symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """Fetch daily OHLCV data for an NSE symbol from Yahoo Finance.

    Parameters
    ----------
    symbol : str
        Yahoo Finance ticker symbol, e.g. ``"RELIANCE.NS"`` or ``"INFY.NS"``.
    period : str, optional
        Lookback period understood by yfinance (``"1y"``, ``"2y"``, ``"6mo"``
        …). Default is ``"1y"``.
    interval : str, optional
        Bar interval (``"1d"``, ``"1wk"``…). Default is ``"1d"``.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns ``Open``, ``Close``, ``High``, ``Low``,
        ``Volume`` indexed by date.  Raises ``ValueError`` if no data is
        returned.

    Examples
    --------
    >>> df = get_data("RELIANCE.NS")
    >>> df.shape
    (252, 5)
    """
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval=interval)

    if df.empty:
        raise ValueError(
            f"No data returned for symbol '{symbol}'. "
            "Check the ticker and your internet connection."
        )

    # Keep only canonical OHLCV columns; yfinance may add Dividends / Stock Splits
    df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)
    return df


# ---------------------------------------------------------------------------
# Indicator calculations
# ---------------------------------------------------------------------------

def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Wilder-smoothed RSI."""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, float("nan"))
    return 100 - (100 / (1 + rs))


def _macd(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Return (macd_line, signal_line, histogram)."""
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def _adx(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.Series:
    """Wilder-smoothed ADX."""
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    up_move = high - high.shift(1)
    down_move = low.shift(1) - low

    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)

    atr = tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    plus_di = 100 * (
        plus_dm.ewm(alpha=1 / period, min_periods=period, adjust=False).mean() / atr
    )
    minus_di = 100 * (
        minus_dm.ewm(alpha=1 / period, min_periods=period, adjust=False).mean() / atr
    )

    dx = (100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, float("nan")))
    adx = dx.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    return adx


def _obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """On-Balance Volume."""
    direction = close.diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    return (direction * volume).cumsum()


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Compute all positional indicators and append them as new columns.

    Parameters
    ----------
    df : pd.DataFrame
        OHLCV DataFrame as returned by :func:`get_data`.

    Returns
    -------
    pd.DataFrame
        The same DataFrame with additional columns:

        - ``SMA50``       – 50-day Simple Moving Average of Close
        - ``SMA200``      – 200-day Simple Moving Average of Close
        - ``RSI``         – 14-day Relative Strength Index
        - ``MACD``        – MACD line (12/26 EMA diff)
        - ``MACD_Signal`` – 9-day signal line
        - ``MACD_Hist``   – MACD histogram
        - ``ADX``         – 14-day Average Directional Index
        - ``OBV``         – On-Balance Volume

    Examples
    --------
    >>> df = get_data("INFY.NS")
    >>> df = calculate_indicators(df)
    >>> "SMA50" in df.columns
    True
    """
    df = df.copy()
    close = df["Close"]

    df["SMA50"] = close.rolling(window=50).mean()
    df["SMA200"] = close.rolling(window=200).mean()
    df["RSI"] = _rsi(close)
    df["MACD"], df["MACD_Signal"], df["MACD_Hist"] = _macd(close)
    df["ADX"] = _adx(df["High"], df["Low"], close)
    df["OBV"] = _obv(close, df["Volume"])

    return df


# ---------------------------------------------------------------------------
# Latest values extraction
# ---------------------------------------------------------------------------

def latest_values(df: pd.DataFrame) -> Dict[str, Any]:
    """Extract the most recent row's indicator values as a plain dict.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame produced by :func:`calculate_indicators`.

    Returns
    -------
    dict
        Keys: ``current_price``, ``SMA50``, ``SMA200``, ``RSI``, ``MACD``,
        ``MACD_Signal``, ``MACD_Hist``, ``ADX``, ``OBV``.

    Examples
    --------
    >>> latest = latest_values(df)
    >>> isinstance(latest["RSI"], float)
    True
    """
    last = df.dropna(subset=["SMA50", "RSI", "MACD", "ADX"]).iloc[-1]

    return {
        "current_price": round(float(last["Close"]), 2),
        "SMA50":         round(float(last["SMA50"]), 2),
        "SMA200":        round(float(last["SMA200"]), 2) if pd.notna(last["SMA200"]) else None,
        "RSI":           round(float(last["RSI"]), 2),
        "MACD":          round(float(last["MACD"]), 4),
        "MACD_Signal":   round(float(last["MACD_Signal"]), 4),
        "MACD_Hist":     round(float(last["MACD_Hist"]), 4),
        "ADX":           round(float(last["ADX"]), 2),
        "OBV":           int(last["OBV"]),
    }


# ---------------------------------------------------------------------------
# Advisor
# ---------------------------------------------------------------------------

def advisor(latest: Dict[str, Any]) -> str:
    """Return a simple positional trading recommendation.

    Rules
    -----
    - **BUY**  : SMA50 > SMA200  AND  55 ≤ RSI ≤ 70
    - **SELL** : RSI > 80  OR  SMA50 < SMA200
    - **HOLD** : all other cases

    Parameters
    ----------
    latest : dict
        Dictionary as returned by :func:`latest_values`.

    Returns
    -------
    str
        One of ``"BUY"``, ``"SELL"``, or ``"HOLD"``.

    Examples
    --------
    >>> advisor({"SMA50": 2500, "SMA200": 2400, "RSI": 60})
    'BUY'
    """
    sma50  = latest.get("SMA50")
    sma200 = latest.get("SMA200")
    rsi    = latest.get("RSI")

    if sma50 is None or rsi is None:
        return "HOLD"

    if sma200 is not None:
        if sma50 > sma200 and 55 <= rsi <= 70:
            return "BUY"
        if rsi > 80 or sma50 < sma200:
            return "SELL"
    else:
        # SMA200 not yet available (< 200 bars of data)
        if 55 <= rsi <= 70:
            return "BUY"
        if rsi > 80:
            return "SELL"

    return "HOLD"


# ---------------------------------------------------------------------------
# JSON report helper
# ---------------------------------------------------------------------------

def build_report(symbol: str, latest: Dict[str, Any]) -> str:
    """Serialise indicator values + recommendation to a JSON string.

    Parameters
    ----------
    symbol : str
        The ticker symbol (used as a label in the output).
    latest : dict
        Dictionary as returned by :func:`latest_values`.

    Returns
    -------
    str
        Pretty-printed JSON string.

    Examples
    --------
    >>> print(build_report("RELIANCE.NS", latest))
    {
      "symbol": "RELIANCE.NS",
      ...
    }
    """
    recommendation = advisor(latest)
    report = {"symbol": symbol, "recommendation": recommendation, **latest}
    return json.dumps(report, indent=2)
