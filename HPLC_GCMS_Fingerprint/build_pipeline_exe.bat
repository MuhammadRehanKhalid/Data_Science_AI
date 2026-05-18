@echo off
setlocal

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_pipeline_exe.ps1"

endlocal