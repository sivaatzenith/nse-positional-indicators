@echo off
title NSE API - ngrok Tunnel

echo ============================================================
echo   NSE Positional Indicators - ngrok Public Tunnel
echo ============================================================
echo.
echo   This will expose your local Flask server (port 5000)
echo   to the internet via a public HTTPS URL.
echo.
echo   REQUIREMENTS:
echo   1. Flask server must already be running (run start_api.bat first)
echo   2. ngrok must be installed: https://ngrok.com/download
echo      After install run: ngrok config add-authtoken YOUR_TOKEN
echo.
echo   Once running, copy the https://xxxx.ngrok-free.app URL
echo   and paste it into Power Automate as the HTTP action URI.
echo.
echo   Press Ctrl+C to stop the tunnel.
echo ============================================================
echo.

ngrok http 5000

pause
