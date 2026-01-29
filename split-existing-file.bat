@echo off
:: Split an existing large video file into FAT32-compatible parts

cls
echo ================================================================================
echo                      Split Existing Video File
echo ================================================================================
echo.
echo This tool splits a large video file into parts under 3.9GB each.
echo.

:: Get the file path
echo Enter the path to the large video file:
set /p video_file="File path: "

if "%video_file%"=="" (
    echo.
    echo Error: No file specified.
    pause
    exit /b 1
)

if not exist "%video_file%" (
    echo.
    echo Error: File not found: %video_file%
    pause
    exit /b 1
)

echo.
echo File: %video_file%
echo.
echo This will split the file into parts and save them in the same folder.
echo.
pause

echo.
echo Splitting video...
echo.

cd /d "%~dp0src"
python -c "from pathlib import Path; from yt2audi.core.splitter import Splitter; from yt2audi.models.profile import OnSizeExceed; parts = Splitter.handle_size_exceed(Path(r'%video_file%'), 3.9, OnSizeExceed.SPLIT); print(f'\nCreated {len(parts)} parts:'); [print(f'  {p}') for p in parts]"

set exit_code=%errorlevel%
cd /d "%~dp0"

echo.
if %exit_code% equ 0 (
    echo ================================================================================
    echo SUCCESS! Video split into parts.
    echo ================================================================================
) else (
    echo ================================================================================
    echo ERROR! Split failed.
    echo ================================================================================
)

echo.
pause
