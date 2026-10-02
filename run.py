"""
run.py
~~~~~~
Standalone script to fetch NSE stock data, compute positional indicators,
and print a BUY / SELL / HOLD recommendation as a JSON report.

Usage
-----
    python run.py                        # uses default symbol RELIANCE.NS
    python run.py INFY.NS                # pass any NSE ticker as argument
    python run.py INFY.NS TCS.NS SBIN.NS # run a watchlist
"""

import sys
import json
from nse_positional_indicators import (
    get_data,
    calculate_indicators,
    latest_values,
    advisor,
    build_report,
)

# ---------------------------------------------------------------------------
# Default watchlist — override by passing symbols as CLI arguments
# e.g.  python run.py INFY.NS TCS.NS
# ---------------------------------------------------------------------------
DEFAULT_SYMBOLS = ["RELIANCE.NS"]


def run(symbol: str) -> None:
    """Fetch, compute, and print the full JSON report for one symbol."""
    print(f"\n{'='*55}")
    print(f"  {symbol}")
    print(f"{'='*55}")
    try:
        df = get_data(symbol)
        print(f"  Fetched {len(df)} rows of OHLCV data.")

        df = calculate_indicators(df)
        print("  Indicators calculated: SMA50, SMA200, RSI, MACD, ADX, OBV")

        latest = latest_values(df)
        recommendation = advisor(latest)

        report = json.loads(build_report(symbol, latest))
        print(json.dumps(report, indent=2))

    except ValueError as e:
        print(f"  [DATA ERROR] {e}")
    except Exception as e:
        print(f"  [ERROR] {e}")


def main() -> None:
    symbols = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_SYMBOLS
    for symbol in symbols:
        run(symbol.upper())
    print(f"\n{'='*55}\nDone.\n")


if __name__ == "__main__":
    main()
