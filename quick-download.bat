@echo off
:: YT2Audi Quick Download
:: Simple one-click download interface

cls
echo ================================================================================
echo                     YT2Audi - Quick Download
echo ================================================================================
echo.

:: Get URL from user
echo Paste the YouTube URL and press Enter:
set /p url="URL: "

if "%url%"=="" (
    echo.
    echo Error: No URL provided.
    pause
    exit /b 1
)

:: Use default output directory
set "output_dir=.\output"

echo.
echo Starting download to: %output_dir%
echo Using profile: Audi Q5 MMI (720x540, optimized for FAT32)
echo.
echo Please wait...
echo.

:: Run the download
cd /d "%~dp0src"
python -m yt2audi download "%url%" --output "%output_dir%" --profile audi_q5_mmi

set exit_code=%errorlevel%
cd /d "%~dp0"

echo.
if %exit_code% equ 0 (
    echo ================================================================================
    echo SUCCESS! Video is ready in: %output_dir%
    echo ================================================================================
) else (
    echo ================================================================================
    echo ERROR! Download failed. Check the error messages above.
    echo ================================================================================
)

echo.
pause
