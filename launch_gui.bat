@echo off
title PolicyUpdate - GRC Policy Management
echo Starting PolicyUpdate...
echo.

REM Check if Python is available
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

REM Launch the GUI
pythonw "%~dp0PolicyUpdate.pyw" 2>nul
if %errorlevel% neq 0 (
    REM If pythonw fails, try python
    python "%~dp0PolicyUpdate.pyw"
)
