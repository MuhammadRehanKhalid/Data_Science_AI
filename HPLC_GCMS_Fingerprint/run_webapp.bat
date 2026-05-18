@echo off
setlocal

set "ROOT_DIR=%~dp0"

echo Launching PowerShell webapp starter...
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT_DIR%run_webapp.ps1"

echo.
echo The webapp is starting.
echo Backend:  http://localhost:8000
echo Frontend: usually http://localhost:5173
echo.
echo Close the two windows opened by this script to stop the app.
endlocal