@echo off
chcp 65001 >nul
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" run.py setup
) else (
  where py >nul 2>&1
  if errorlevel 1 (
    python run.py setup
  ) else (
    py -3.12 run.py setup
  )
)
set DEMO_EXIT=%ERRORLEVEL%
pause
exit /b %DEMO_EXIT%
