@echo off
title AI News Analyzer — Dev Server
color 0A

echo ============================================
echo   AI News Analyzer — Starting Dev Servers
echo ============================================
echo.

:: ── Activate Python venv and start FastAPI backend ──
echo [1/2] Starting Backend (FastAPI :8000)...
start "Backend - FastAPI" cmd /k "cd /d E:\AI NEWS ANALYZER\ai-news-analyzer\backend && call venv\Scripts\activate && uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

:: Small delay so backend starts first
timeout /t 3 /nobreak >nul

:: ── Start Vite frontend ──
echo [2/2] Starting Frontend (Vite :5173)...
start "Frontend - Vite" cmd /k "cd /d E:\AI NEWS ANALYZER\ai-news-analyzer\frontend && npm run dev"

echo.
echo ============================================
echo   Both servers are starting...
echo   Backend  : http://localhost:8000
echo   Frontend : http://localhost:5173
echo   API Docs : http://localhost:8000/docs
echo ============================================
echo.
echo Press any key to open the app in browser...
pause >nul

start http://localhost:5173
