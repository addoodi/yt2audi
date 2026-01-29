@echo off
REM YT2Audi Installation Script
REM This script installs all required dependencies

echo ====================================
echo YT2Audi v2.0 - Installation
echo ====================================
echo.

echo Checking Python installation...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found! Please install Python 3.11+ first.
    pause
    exit /b 1
)
echo.

echo Checking FFmpeg installation...
ffmpeg -version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] FFmpeg not found! Download from: https://ffmpeg.org/download.html
    echo You need FFmpeg for video conversion to work.
    echo.
) else (
    echo [OK] FFmpeg is installed
    echo.
)

echo Installing Python dependencies...
echo This may take a few minutes...
echo.

pip install --upgrade pip
pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Installation failed!
    pause
    exit /b 1
)

echo.
echo ====================================
echo Installation Complete!
echo ====================================
echo.
echo To use YT2Audi:
echo   cd src
echo   python -m yt2audi --help
echo.
echo Quick start:
echo   python -m yt2audi download "YOUTUBE_URL"
echo.
echo See README.md for more examples.
echo.
pause
