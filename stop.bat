@echo off
title AI News Analyzer — Stop Servers
color 0C

echo Menghentikan semua server AI News Analyzer...
echo.

:: Kill uvicorn (backend)
taskkill /F /IM python.exe /T >nul 2>&1
echo [OK] Backend (Python/uvicorn) dihentikan.

:: Kill node (frontend Vite)
taskkill /F /IM node.exe /T >nul 2>&1
echo [OK] Frontend (Node/Vite) dihentikan.

echo.
echo Semua server telah dihentikan.
timeout /t 2 /nobreak >nul
