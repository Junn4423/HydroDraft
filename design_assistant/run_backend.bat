@echo off
title HydroDraft - Backend Only
chcp 65001 >nul
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║          🌊 HYDRODRAFT - BACKEND SERVER                      ║
echo ╠══════════════════════════════════════════════════════════════╣
echo ║  Server:   http://localhost:8000                             ║
echo ║  API Docs: http://localhost:8000/docs                        ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0backend"

echo Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)

echo.
echo Installing/updating dependencies...
pip install -r requirements.txt -q

echo.
echo Starting backend server...
echo Press Ctrl+C to stop.
echo.

REM Open API docs
timeout /t 2 >nul
start "" "http://localhost:8000/docs"

python main.py

pause
