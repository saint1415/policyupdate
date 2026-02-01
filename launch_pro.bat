@echo off
title PolicyUpdate Pro - Professional Edition
echo.
echo  ╔═══════════════════════════════════════════════════════╗
echo  ║         PolicyUpdate Pro - GRC Platform               ║
echo  ║              Professional Edition                      ║
echo  ╚═══════════════════════════════════════════════════════╝
echo.

REM Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.9+
    pause
    exit /b 1
)

echo Starting PolicyUpdate Pro...
pythonw "%~dp0PolicyUpdatePro.pyw" 2>nul
if %errorlevel% neq 0 (
    python "%~dp0PolicyUpdatePro.pyw"
)
