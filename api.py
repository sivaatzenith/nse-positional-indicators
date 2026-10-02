"""
api.py
~~~~~~
Flask REST API wrapper for nse_positional_indicators.

Exposes two endpoints that Power Automate (or any HTTP client) can call:

  GET  /analyze?symbol=RELIANCE.NS
  GET  /analyze?symbol=RELIANCE.NS&period=6mo
  POST /analyze          body: {"symbol": "RELIANCE.NS", "period": "1y"}
  GET  /watchlist?symbols=RELIANCE.NS,INFY.NS,TCS.NS
  GET  /health           → liveness check

Run locally
-----------
    python api.py

Run with a custom port
-----------------------
    python api.py --port 8080

Expose to the internet (for Power Automate Cloud)
--------------------------------------------------
    ngrok http 5000
    # Copy the https://xxxxx.ngrok-free.app URL into Power Automate
"""

import argparse
import json
import sys
import os
import logging
from datetime import datetime

from flask import Flask, jsonify, request

# Allow running from the project root without pip install
sys.path.insert(0, os.path.dirname(__file__))

from nse_positional_indicators import (
    get_data,
    calculate_indicators,
    latest_values,
    advisor,
    build_report,
)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = Flask(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _analyze(symbol: str, period: str = "1y") -> dict:
    """Run the full pipeline for one symbol and return a plain dict."""
    df     = get_data(symbol, period=period)
    df     = calculate_indicators(df)
    latest = latest_values(df)
    return json.loads(build_report(symbol, latest))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalise_symbol(symbol: str) -> str:
    """Ensure the symbol carries the .NS suffix required by Yahoo Finance.

    Examples
    --------
    'tcs'        -> 'TCS.NS'
    'TCS'        -> 'TCS.NS'
    'TCS.NS'     -> 'TCS.NS'
    'TCS.BO'     -> 'TCS.BO'   (BSE suffix kept as-is)
    """
    s = symbol.strip().upper()
    # If already has an exchange suffix (e.g. .NS .BO .BSE) leave it alone
    if "." not in s:
        s = s + ".NS"
    return s


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/", methods=["GET"])
def index():
    """Root route — lists all available endpoints."""
    return jsonify({
        "service":   "NSE Positional Indicators API",
        "version":   "1.0.0",
        "status":    "running",
        "endpoints": {
            "GET /health":                                   "Server liveness check",
            "GET /analyze?symbol=RELIANCE.NS":               "Analyse a single NSE stock",
            "GET /analyze?symbol=RELIANCE.NS&period=6mo":    "Analyse with custom period",
            "POST /analyze  body:{symbol,period}":           "Analyse via POST JSON body",
            "GET /watchlist?symbols=RELIANCE.NS,INFY.NS":    "Analyse multiple stocks",
        },
        "valid_periods": ["1mo", "3mo", "6mo", "1y", "2y"],
        "example_nse_symbols": ["RELIANCE.NS", "INFY.NS", "TCS.NS", "HDFCBANK.NS", "SBIN.NS"],
    }), 200


@app.route("/health", methods=["GET"])
def health():
    """Liveness check — Power Automate can poll this to verify the server is up."""
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat() + "Z"}), 200


@app.route("/analyze", methods=["GET", "POST"])
def analyze():
    """
    Analyze a single NSE stock symbol.

    GET  /analyze?symbol=RELIANCE.NS&period=1y
    POST /analyze   JSON body: {"symbol": "RELIANCE.NS", "period": "1y"}

    Returns JSON:
    {
      "symbol":         "RELIANCE.NS",
      "recommendation": "BUY",
      "current_price":  2910.45,
      "SMA50":          2875.12,
      "SMA200":         2740.80,
      "RSI":            62.4,
      "MACD":           18.32,
      "MACD_Signal":    14.10,
      "MACD_Hist":      4.22,
      "ADX":            28.5,
      "OBV":            94820000
    }
    """
    if request.method == "POST":
        data   = request.get_json(silent=True) or {}
        symbol = data.get("symbol", "RELIANCE.NS")
        period = data.get("period", "1y")
    else:
        symbol = request.args.get("symbol", "RELIANCE.NS")
        period = request.args.get("period", "1y")

    symbol = _normalise_symbol(symbol)
    log.info("Analyzing %s  period=%s", symbol, period)

    try:
        report = _analyze(symbol, period)
        return jsonify(report), 200

    except ValueError as e:
        log.warning("Data error for %s: %s", symbol, e)
        return jsonify({"error": str(e), "symbol": symbol}), 404

    except Exception as e:
        log.error("Unexpected error for %s: %s", symbol, e)
        return jsonify({"error": str(e), "symbol": symbol}), 500


@app.route("/watchlist", methods=["GET", "POST"])
def watchlist():
    """
    Analyze multiple NSE symbols in one call.

    GET  /watchlist?symbols=RELIANCE.NS,INFY.NS,TCS.NS&period=1y
    POST /watchlist   JSON body: {"symbols": ["RELIANCE.NS", "INFY.NS"], "period": "1y"}

    Returns JSON array of per-symbol reports (errors are included inline).
    """
    if request.method == "POST":
        data    = request.get_json(silent=True) or {}
        symbols = data.get("symbols", [])
        period  = data.get("period", "1y")
    else:
        raw     = request.args.get("symbols", "RELIANCE.NS")
        symbols = [s.strip() for s in raw.split(",")]
        period  = request.args.get("period", "1y")

    symbols = [_normalise_symbol(s) for s in symbols if s]
    log.info("Watchlist: %s  period=%s", symbols, period)

    results = []
    for sym in symbols:
        try:
            results.append(_analyze(sym, period))
        except Exception as e:
            log.warning("Error for %s: %s", sym, e)
            results.append({"symbol": sym, "error": str(e)})

    return jsonify(results), 200


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NSE Positional Indicators API Server")
    parser.add_argument("--port", type=int, default=5000, help="Port to listen on (default: 5000)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    args = parser.parse_args()

    print(f"""
╔══════════════════════════════════════════════════════╗
║       NSE Positional Indicators — API Server         ║
╠══════════════════════════════════════════════════════╣
║  Health   : http://localhost:{args.port}/health          ║
║  Analyze  : http://localhost:{args.port}/analyze?symbol= ║
║  Watchlist: http://localhost:{args.port}/watchlist?symbols=║
╚══════════════════════════════════════════════════════╝
  To expose publicly: ngrok http {args.port}
""")

    app.run(host=args.host, port=args.port, debug=False)
