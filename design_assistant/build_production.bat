@echo off
title HydroDraft - Production Build v2.0
chcp 65001 >nul
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║          🌊 HYDRODRAFT - PRODUCTION BUILD                    ║
echo ║              Professional Engineering Platform               ║
echo ╠══════════════════════════════════════════════════════════════╣
echo ║  Sprint 1: Offline Foundation        ✓ Complete              ║
echo ║  Sprint 2: Traceable Engineering     ✓ Complete              ║
echo ║  Sprint 3: Professional CAD          ✓ Complete              ║
echo ║  Sprint 4: BIM ^& Enterprise          ✓ Complete              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

echo [1/6] Checking environment...
echo.
python --version
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

node --version
if errorlevel 1 (
    echo ERROR: Node.js not found!
    echo Please install Node.js 16+ from https://nodejs.org
    pause
    exit /b 1
)

echo.
echo [2/6] Installing Python dependencies...
cd backend
pip install -r requirements.txt -q
pip install pyinstaller -q
if errorlevel 1 (
    echo ERROR: Failed to install Python dependencies!
    pause
    exit /b 1
)

echo.
echo [3/6] Running backend tests...
python test_sprint4_bim.py
if errorlevel 1 (
    echo.
    echo ⚠️  WARNING: Some tests failed.
    echo    Continue anyway? (Y/N)
    choice /c YN /n
    if errorlevel 2 (
        echo Build cancelled.
        pause
        exit /b 1
    )
)

echo.
echo [4/6] Building React frontend...
cd ..\frontend
if exist package.json (
    call npm install --legacy-peer-deps
    if errorlevel 1 (
        echo ERROR: npm install failed!
        pause
        exit /b 1
    )
    
    call npm run build
    if errorlevel 1 (
        echo ERROR: npm build failed!
        pause
        exit /b 1
    )
    
    echo Frontend build complete!
    
    REM Copy build to backend static folder
    if exist ..\backend\static rmdir /s /q ..\backend\static
    mkdir ..\backend\static
    xcopy /e /y build\* ..\backend\static\
    echo Frontend copied to backend\static
) else (
    echo Skipping frontend build - no package.json found
)

echo.
echo [5/6] Building production executable...
cd ..\backend
python build_production.py

if errorlevel 1 (
    echo ERROR: PyInstaller build failed!
    pause
    exit /b 1
)

echo.
echo [6/6] Creating installer package...

REM Create distribution folder
if not exist ..\dist mkdir ..\dist
if exist ..\dist\HydroDraft rmdir /s /q ..\dist\HydroDraft
mkdir ..\dist\HydroDraft

REM Copy PyInstaller output
if exist dist\HydroDraft_build (
    xcopy /e /y dist\HydroDraft_build\* ..\dist\HydroDraft\
)

REM Copy additional files
copy /y ..\HUONG_DAN_CAI_DAT.md ..\dist\HydroDraft\
copy /y ..\README.md ..\dist\HydroDraft\

REM Create run script
echo @echo off > ..\dist\HydroDraft\Run_HydroDraft.bat
echo title HydroDraft Professional >> ..\dist\HydroDraft\Run_HydroDraft.bat
echo echo Starting HydroDraft... >> ..\dist\HydroDraft\Run_HydroDraft.bat
echo cd /d "%%~dp0" >> ..\dist\HydroDraft\Run_HydroDraft.bat
echo start "" HydroDraft_build.exe >> ..\dist\HydroDraft\Run_HydroDraft.bat

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║              ✅ BUILD COMPLETE!                              ║
echo ╠══════════════════════════════════════════════════════════════╣
echo ║  Output: dist\HydroDraft\                                    ║
echo ║  Run:    dist\HydroDraft\Run_HydroDraft.bat                  ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo The application is ready for distribution.
echo Copy the entire HydroDraft folder to the target machine.
echo.
pause
