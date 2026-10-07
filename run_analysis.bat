@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

where py >nul 2>nul
if not errorlevel 1 (
    py -3 "%~dp0voice_analyzer.py" %*
    set "RESULT=%errorlevel%"
    pause
    exit /b !RESULT!
)

where python >nul 2>nul
if not errorlevel 1 (
    python "%~dp0voice_analyzer.py" %*
    set "RESULT=%errorlevel%"
    pause
    exit /b !RESULT!
)

echo Python 3 was not found. Install Python 3.9 or newer and try again.
pause
exit /b 1
