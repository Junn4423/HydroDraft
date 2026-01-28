@echo off
title HydroDraft - Frontend Only
chcp 65001 >nul
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║          🌊 HYDRODRAFT - FRONTEND DEV SERVER                 ║
echo ╠══════════════════════════════════════════════════════════════╣
echo ║  Dev Server: http://localhost:3000                           ║
echo ║  (Make sure backend is running on port 8000)                 ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0frontend"

echo Checking Node.js...
node --version
if errorlevel 1 (
    echo ERROR: Node.js not found!
    echo Please install from https://nodejs.org
    pause
    exit /b 1
)

echo.
if not exist node_modules (
    echo Installing dependencies... (this may take a few minutes)
    call npm install --legacy-peer-deps
) else (
    echo Dependencies already installed.
)

echo.
echo Starting frontend dev server...
echo Press Ctrl+C to stop.
echo.

npm start

pause
