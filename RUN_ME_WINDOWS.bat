@echo off
setlocal
cd /d "%~dp0"
echo.
echo  MedData Forensics - Local Research Workbench
echo  Research only. No clinical diagnosis.
echo.
if not exist ".venv\Scripts\python.exe" (
    echo First launch: installing free Python dependencies...
    powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\Setup-Windows.ps1"
    if errorlevel 1 (
        echo Setup failed. Read docs\WINDOWS_SETUP.md for help.
        pause
        exit /b 1
    )
)
echo.
echo Open http://127.0.0.1:8765 after the server starts.
echo Press Ctrl+C to stop.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\Start-Windows.ps1"
if errorlevel 1 pause
endlocal
