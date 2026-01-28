@echo off
title HydroDraft - Development Mode
chcp 65001 >nul
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║          🌊 HYDRODRAFT - DEVELOPMENT MODE                    ║
echo ║              Frontend + Backend Running                      ║
echo ╠══════════════════════════════════════════════════════════════╣
echo ║  Backend:  http://localhost:8000                             ║
echo ║  Frontend: http://localhost:3000                             ║
echo ║  API Docs: http://localhost:8000/docs                        ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

echo [1/5] Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

echo.
echo [2/5] Checking Node.js...
node --version
if errorlevel 1 (
    echo ERROR: Node.js not found!
    echo Please install Node.js 16+ from https://nodejs.org
    pause
    exit /b 1
)

echo.
echo [3/5] Installing backend dependencies...
cd backend
pip install -r requirements.txt -q
if errorlevel 1 (
    echo WARNING: Some packages may have failed to install
)

echo.
echo [4/5] Installing frontend dependencies...
cd ..\frontend
if not exist node_modules (
    echo Running npm install... (this may take a few minutes)
    call npm install --legacy-peer-deps
) else (
    echo node_modules exists, skipping npm install
)

echo.
echo [5/5] Starting servers...
echo.
echo ═══════════════════════════════════════════════════════════════
echo   Starting Backend server (port 8000)...
echo   Starting Frontend dev server (port 3000)...
echo ═══════════════════════════════════════════════════════════════
echo.
echo   Press Ctrl+C in each window to stop the servers.
echo.

REM Start backend in new window
cd ..\backend
start "HydroDraft Backend" cmd /c "python main.py"

REM Wait for backend to start
timeout /t 3 >nul

REM Start frontend in new window
cd ..\frontend
start "HydroDraft Frontend" cmd /c "npm start"

REM Wait a bit then open browser
timeout /t 5 >nul
start "" "http://localhost:3000"

echo.
echo ═══════════════════════════════════════════════════════════════
echo   Servers are starting...
echo   
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo   API Docs: http://localhost:8000/docs
echo.
echo   Browser will open automatically.
echo   
echo   To stop: Close the Backend and Frontend terminal windows.
echo ═══════════════════════════════════════════════════════════════
echo.
pause
