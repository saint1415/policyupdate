@echo off
title PolicyUpdate - Install Dependencies
echo ============================================
echo  PolicyUpdate Dependency Installer
echo ============================================
echo.

REM Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    echo Please install Python 3.9+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo Python found. Installing dependencies...
echo.

REM Install core dependencies
pip install pyyaml python-docx markdown jinja2

echo.
echo ============================================
echo  Optional dependencies for full features:
echo ============================================
echo.

REM Ask about optional dependencies
set /p INSTALL_PDF="Install PDF export support (weasyprint)? [y/N]: "
if /i "%INSTALL_PDF%"=="y" (
    pip install weasyprint
)

set /p INSTALL_WEB="Install web interface (Flask)? [y/N]: "
if /i "%INSTALL_WEB%"=="y" (
    pip install flask flask-login
)

echo.
echo ============================================
echo  Installation Complete!
echo ============================================
echo.
echo To launch PolicyUpdate:
echo   - Double-click PolicyUpdate.pyw
echo   - Or run: launch_gui.bat
echo.
pause
