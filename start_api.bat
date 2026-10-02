@echo off
title NSE Positional Indicators - API Server

echo ============================================================
echo   NSE Positional Indicators - API Server
echo ============================================================
echo.

:: Install dependencies if not already installed
echo [1/2] Installing dependencies...
pip install -r requirements_api.txt --quiet

echo.
echo [2/2] Starting Flask API server on http://localhost:5000
echo.
echo   Health   : http://localhost:5000/health
echo   Analyze  : http://localhost:5000/analyze?symbol=RELIANCE.NS
echo   Watchlist: http://localhost:5000/watchlist?symbols=RELIANCE.NS,INFY.NS
echo.
echo   Press Ctrl+C to stop the server.
echo ============================================================
echo.

python api.py

pause
