# nse_positional_indicators

A lightweight Python library that fetches NSE stock data via **yfinance** and computes positional trading indicators with a simple **BUY / SELL / HOLD** advisor.

---

## Features

| Indicator | Description |
|---|---|
| **SMA50** | 50-day Simple Moving Average |
| **SMA200** | 200-day Simple Moving Average |
| **RSI** | 14-day Relative Strength Index (Wilder-smoothed) |
| **MACD** | 12/26-day EMA difference + 9-day signal line |
| **ADX** | 14-day Average Directional Index (Wilder-smoothed) |
| **OBV** | On-Balance Volume |

---

## Installation

### From source (development mode)

```bash
git clone <repo-url>
cd nse_positional_indicators
pip install -e .
```

### Dependencies only

```bash
pip install -r requirements.txt
```

---

## Quick Start

```python
from nse_positional_indicators import (
    get_data,
    calculate_indicators,
    latest_values,
    advisor,
    build_report,
)

# 1. Fetch 1 year of daily OHLCV data
df = get_data("RELIANCE.NS")

# 2. Compute all indicators
df = calculate_indicators(df)

# 3. Extract the latest row as a dict
latest = latest_values(df)
print(latest)
# {
#   'current_price': 2910.45,
#   'SMA50': 2875.12,
#   'SMA200': 2740.80,
#   'RSI': 62.4,
#   'MACD': 18.32,
#   'MACD_Signal': 14.10,
#   'MACD_Hist': 4.22,
#   'ADX': 28.5,
#   'OBV': 94820000
# }

# 4. Get a recommendation
print(advisor(latest))   # → 'BUY'

# 5. Get a full JSON report
print(build_report("RELIANCE.NS", latest))
```

---

## API Reference

### `get_data(symbol, period="1y", interval="1d") → pd.DataFrame`

Fetches OHLCV data from Yahoo Finance.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `symbol` | `str` | — | Yahoo Finance ticker, e.g. `"RELIANCE.NS"` |
| `period` | `str` | `"1y"` | Lookback period (`"6mo"`, `"1y"`, `"2y"`, …) |
| `interval` | `str` | `"1d"` | Bar size (`"1d"`, `"1wk"`, …) |

Returns a `DataFrame` with columns `Open`, `High`, `Low`, `Close`, `Volume`.

---

### `calculate_indicators(df) → pd.DataFrame`

Appends indicator columns to the DataFrame.

New columns: `SMA50`, `SMA200`, `RSI`, `MACD`, `MACD_Signal`, `MACD_Hist`, `ADX`, `OBV`.

---

### `latest_values(df) → dict`

Returns the most recent non-NaN row as a plain dictionary.

```python
{
    "current_price": float,
    "SMA50":         float,
    "SMA200":        float | None,   # None if < 200 bars available
    "RSI":           float,
    "MACD":          float,
    "MACD_Signal":   float,
    "MACD_Hist":     float,
    "ADX":           float,
    "OBV":           int,
}
```

---

### `advisor(latest) → str`

Returns `"BUY"`, `"SELL"`, or `"HOLD"` based on:

| Condition | Signal |
|---|---|
| SMA50 > SMA200 **and** 55 ≤ RSI ≤ 70 | **BUY** |
| RSI > 80 **or** SMA50 < SMA200 | **SELL** |
| All other cases | **HOLD** |

---

### `build_report(symbol, latest) → str`

Returns a pretty-printed JSON string combining the symbol, all indicator values, and the recommendation.

```json
{
  "symbol": "RELIANCE.NS",
  "recommendation": "BUY",
  "current_price": 2910.45,
  "SMA50": 2875.12,
  "SMA200": 2740.80,
  "RSI": 62.4,
  "MACD": 18.3200,
  "MACD_Signal": 14.1000,
  "MACD_Hist": 4.2200,
  "ADX": 28.5,
  "OBV": 94820000
}
```

---

## Example: Multiple Stocks

```python
from nse_positional_indicators import get_data, calculate_indicators, latest_values, advisor

WATCHLIST = ["RELIANCE.NS", "INFY.NS", "TCS.NS", "HDFCBANK.NS", "SBIN.NS"]

for symbol in WATCHLIST:
    try:
        df = get_data(symbol)
        df = calculate_indicators(df)
        latest = latest_values(df)
        rec = advisor(latest)
        print(f"{symbol:<15} Price: {latest['current_price']:>8.2f}  RSI: {latest['RSI']:>5.1f}  → {rec}")
    except Exception as e:
        print(f"{symbol:<15} ERROR: {e}")
```

**Sample output:**

```
RELIANCE.NS     Price:  2910.45  RSI:  62.4  → BUY
INFY.NS         Price:  1425.30  RSI:  58.1  → BUY
TCS.NS          Price:  3780.00  RSI:  72.0  → HOLD
HDFCBANK.NS     Price:  1620.50  RSI:  83.5  → SELL
SBIN.NS         Price:   775.20  RSI:  48.3  → HOLD
```

---

## Project Structure

```
nse_positional_indicators/
├── nse_positional_indicators/
│   ├── __init__.py        # Public API exports
│   └── indicators.py      # Core data fetch + indicator logic
├── requirements.txt
├── setup.py
├── pyproject.toml
└── README.md
```

---

## License

MIT License — free to use and modify.
