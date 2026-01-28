@echo off
REM ===================================
REM Script chạy cả Backend và Frontend - HydroDraft Design Assistant
REM ===================================

echo.
echo ==========================================
echo   HydroDraft - Khởi động Full Stack
echo ==========================================
echo.
echo [INFO] Đang khởi động Backend và Frontend...
echo.

REM Khởi động Backend trong cửa sổ mới
echo [INFO] Khởi động Backend (Port 8000)...
start "HydroDraft Backend" cmd /k "cd /d "%~dp0" && call run_backend.bat"

REM Đợi 3 giây cho Backend khởi động
echo [INFO] Đợi Backend khởi động...
timeout /t 3 /nobreak > nul

REM Khởi động Frontend trong cửa sổ mới  
echo [INFO] Khởi động Frontend (Port 3000)...
start "HydroDraft Frontend" cmd /k "cd /d "%~dp0" && call run_frontend.bat"

echo.
echo ==========================================
echo   Các services đang chạy:
echo   - Backend API:  http://localhost:8000
echo   - API Docs:     http://localhost:8000/docs
echo   - Frontend:     http://localhost:3000
echo ==========================================
echo.
echo [INFO] Đóng cửa sổ này sẽ KHÔNG dừng các services
echo [INFO] Để dừng, đóng từng cửa sổ Backend/Frontend
echo.

pause
