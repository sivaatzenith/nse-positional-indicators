"""
nse_positional_indicators
~~~~~~~~~~~~~~~~~~~~~~~~~
A lightweight Python library that fetches NSE stock data via yfinance and
computes positional trading indicators (SMA50/200, RSI, MACD, ADX, OBV)
together with a simple BUY / SELL / HOLD recommendation.

Quickstart
----------
>>> from nse_positional_indicators import get_data, calculate_indicators, latest_values, advisor
>>> df = get_data("RELIANCE.NS")
>>> df = calculate_indicators(df)
>>> latest = latest_values(df)
>>> print(advisor(latest))
'BUY'

For a full JSON report use :func:`build_report`::

    from nse_positional_indicators import get_data, calculate_indicators, latest_values, build_report
    df = get_data("INFY.NS")
    df = calculate_indicators(df)
    latest = latest_values(df)
    print(build_report("INFY.NS", latest))
"""

from .indicators import (
    get_data,
    calculate_indicators,
    latest_values,
    advisor,
    build_report,
)

__all__ = [
    "get_data",
    "calculate_indicators",
    "latest_values",
    "advisor",
    "build_report",
]

__version__ = "1.0.0"
__author__ = "NSE Positional Indicators"
