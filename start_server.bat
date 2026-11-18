@echo off
title NovaStock - Inventory & Sales Management System
color 0B
echo ========================================================
echo   ⚡ NovaStock - Inventory & Sales Management System
echo   Academic Project-Based Learning (PBL) Submission
echo ========================================================
echo.
echo [1/3] Checking Python environment...
py -3.11 --version >nul 2>&1
if %errorlevel% equ 0 (
    set PY_CMD=py -3.11
) else (
    set PY_CMD=python
)
echo       Using: %PY_CMD%
echo.
echo [2/3] Starting web server on http://127.0.0.1:5000...
echo       Press CTRL+C anytime in this window to stop.
echo.
start "" http://127.0.0.1:5000
echo [3/3] Opening browser window...
echo.
%PY_CMD% app.py
pause
