@echo off
title HydroDraft - Quick Start
chcp 65001 >nul
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║          🌊 HYDRODRAFT v2.0 - PROFESSIONAL                   ║
echo ║        Environmental Engineering Design Platform             ║
echo ╠══════════════════════════════════════════════════════════════╣
echo ║                                                              ║
echo ║   [1] Run Development Mode (Frontend + Backend)              ║
echo ║   [2] Run Backend Only (API Server)                          ║
echo ║   [3] Build Production Package                               ║
echo ║   [4] Run Tests                                              ║
echo ║   [5] Exit                                                   ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

choice /c 12345 /n /m "Select option [1-5]: "

if errorlevel 5 exit /b 0
if errorlevel 4 goto tests
if errorlevel 3 goto build
if errorlevel 2 goto backend
if errorlevel 1 goto dev

:dev
echo.
echo Starting Development Mode...
call "%~dp0run_test_app.bat"
goto end

:backend
echo.
echo Starting Backend Only...
call "%~dp0run_backend.bat"
goto end

:build
echo.
echo Starting Production Build...
call "%~dp0build_production.bat"
goto end

:tests
echo.
echo Running Tests...
cd /d "%~dp0backend"
python -m pytest -v
python test_sprint4_bim.py
pause
goto end

:end
