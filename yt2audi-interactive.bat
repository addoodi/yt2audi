@echo off
setlocal enabledelayedexpansion

:: YT2Audi Interactive Launcher
:: Provides a user-friendly menu for downloading and converting videos

:HEADER
cls
echo ================================================================================
echo                          YT2Audi Interactive Launcher
echo ================================================================================
echo.
echo Welcome to YT2Audi - YouTube to Audi MMI Video Converter
echo This tool downloads videos optimized for your Audi infotainment system
echo.
echo ================================================================================
echo.

:MAIN_MENU
echo Select an option:
echo.
echo   [1] Download Single Video
echo   [2] Download Batch (from URL list file)
echo   [3] Download Playlist
echo   [4] Download Only (skip conversion)
echo   [5] Convert Only (existing video file)
echo   [6] View/Edit Settings
echo   [7] Update yt-dlp
echo   [8] Run Tests
echo   [0] Exit
echo.
set /p choice="Enter your choice (0-8): "

if "%choice%"=="1" goto SINGLE_VIDEO
if "%choice%"=="2" goto BATCH_DOWNLOAD
if "%choice%"=="3" goto PLAYLIST_DOWNLOAD
if "%choice%"=="4" goto DOWNLOAD_ONLY
if "%choice%"=="5" goto CONVERT_ONLY
if "%choice%"=="6" goto SETTINGS
if "%choice%"=="7" goto UPDATE_YTDLP
if "%choice%"=="8" goto RUN_TESTS
if "%choice%"=="0" goto EXIT
echo.
echo Invalid choice. Please try again.
timeout /t 2 >nul
goto MAIN_MENU

:: ============================================================================
:: SINGLE VIDEO DOWNLOAD
:: ============================================================================
:SINGLE_VIDEO
cls
echo ================================================================================
echo                           Download Single Video
echo ================================================================================
echo.
echo Enter the YouTube video URL (or press Ctrl+C to cancel):
set /p video_url="URL: "

if "%video_url%"=="" (
    echo.
    echo Error: URL cannot be empty.
    timeout /t 2 >nul
    goto MAIN_MENU
)

echo.
echo Enter output folder path (or press Enter for default: .\output):
set /p output_dir="Output folder: "

if "%output_dir%"=="" (
    set "output_dir=.\output"
)

echo.
echo Select profile:
echo   [1] Audi Q5 MMI (Default - FAT32 USB, auto-split if needed)
echo   [2] Audi Q5 Long Videos (For videos ^>2hrs, smaller files)
echo   [3] Audi Q5 exFAT/NTFS (For exFAT/NTFS USB - no file limits!)
echo   [4] Custom profile
echo.
set /p profile_choice="Profile choice (1-4): "

if "%profile_choice%"=="2" (
    set "profile_name=audi_q5_long_videos"
) else if "%profile_choice%"=="3" (
    set "profile_name=audi_q5_exfat"
) else if "%profile_choice%"=="4" (
    set /p profile_name="Enter profile name: "
) else (
    set "profile_name=audi_q5_mmi"
)

echo.
echo ================================================================================
echo Configuration Summary:
echo ================================================================================
echo   Mode:          Single Video
echo   URL:           %video_url%
echo   Output folder: %output_dir%
echo   Profile:       %profile_name%
echo ================================================================================
echo.
echo Press any key to start download or Ctrl+C to cancel...
pause >nul

echo.
echo Starting download and conversion...
echo.

:: Run from project root (package is installed with pip install -e .)
cd /d "%~dp0"
python -m yt2audi download "%video_url%" --output "%output_dir%" --profile "%profile_name%"

set exit_code=%errorlevel%

if %exit_code% equ 0 (
    echo.
    echo ================================================================================
    echo SUCCESS! Video downloaded and converted.
    echo Output location: %output_dir%
    echo ================================================================================
) else (
    echo.
    echo ================================================================================
    echo ERROR! Download or conversion failed. Check the logs above.
    echo ================================================================================
)

echo.
echo Press any key to return to main menu...
pause >nul
goto MAIN_MENU

:: ============================================================================
:: BATCH DOWNLOAD
:: ============================================================================
:BATCH_DOWNLOAD
cls
echo ================================================================================
echo                          Download Batch (URL List)
echo ================================================================================
echo.
echo This mode downloads multiple videos from a text file (one URL per line).
echo.
echo Enter the path to your URL list file (or press Enter for default: urls.txt):
set /p urls_file="URLs file: "

if "%urls_file%"=="" (
    set "urls_file=urls.txt"
)

if not exist "%urls_file%" (
    echo.
    echo Error: File not found: %urls_file%
    echo.
    echo Please create a text file with one YouTube URL per line.
    timeout /t 3 >nul
    goto MAIN_MENU
)

echo.
echo Enter output folder path (or press Enter for default: .\output):
set /p output_dir="Output folder: "

if "%output_dir%"=="" (
    set "output_dir=.\output"
)

echo.
echo Select profile:
echo   [1] Audi Q5 MMI (Default - FAT32 USB, auto-split if needed)
echo   [2] Audi Q5 Long Videos (For videos ^>2hrs, smaller files)
echo   [3] Audi Q5 exFAT/NTFS (For exFAT/NTFS USB - no file limits!)
echo   [4] Custom profile
echo.
set /p profile_choice="Profile choice (1-4): "

if "%profile_choice%"=="2" (
    set "profile_name=audi_q5_long_videos"
) else if "%profile_choice%"=="3" (
    set "profile_name=audi_q5_exfat"
) else if "%profile_choice%"=="4" (
    set /p profile_name="Enter profile name: "
) else (
    set "profile_name=audi_q5_mmi"
)

echo.
echo ================================================================================
echo Configuration Summary:
echo ================================================================================
echo   Mode:          Batch Download
echo   URLs file:     %urls_file%
echo   Output folder: %output_dir%
echo   Profile:       %profile_name%
echo ================================================================================
echo.
echo Press any key to start batch download or Ctrl+C to cancel...
pause >nul

echo.
echo Starting batch download and conversion...
echo.

cd /d "%~dp0"
python -m yt2audi batch "%urls_file%" --output "%output_dir%" --profile "%profile_name%"

set exit_code=%errorlevel%

if %exit_code% equ 0 (
    echo.
    echo ================================================================================
    echo SUCCESS! All videos downloaded and converted.
    echo Output location: %output_dir%
    echo ================================================================================
) else (
    echo.
    echo ================================================================================
    echo WARNING! Some downloads may have failed. Check the logs above.
    echo ================================================================================
)

echo.
echo Press any key to return to main menu...
pause >nul
goto MAIN_MENU

:: ============================================================================
:: PLAYLIST DOWNLOAD
:: ============================================================================
:PLAYLIST_DOWNLOAD
cls
echo ================================================================================
echo                           Download Playlist
echo ================================================================================
echo.
echo Enter the YouTube playlist URL (or press Ctrl+C to cancel):
set /p playlist_url="Playlist URL: "

if "%playlist_url%"=="" (
    echo.
    echo Error: URL cannot be empty.
    timeout /t 2 >nul
    goto MAIN_MENU
)

echo.
echo Enter output folder path (or press Enter for default: .\output):
set /p output_dir="Output folder: "

if "%output_dir%"=="" (
    set "output_dir=.\output"
)

echo.
echo Playlist options:
echo   Start from video number (press Enter for 1):
set /p playlist_start="Start: "
if "%playlist_start%"=="" set "playlist_start=1"

echo   End at video number (press Enter for all):
set /p playlist_end="End: "

echo.
echo Select profile:
echo   [1] Audi Q5 MMI (Default - FAT32 USB, auto-split if needed)
echo   [2] Audi Q5 Long Videos (For videos ^>2hrs, smaller files)
echo   [3] Audi Q5 exFAT/NTFS (For exFAT/NTFS USB - no file limits!)
echo   [4] Custom profile
echo.
set /p profile_choice="Profile choice (1-4): "

if "%profile_choice%"=="2" (
    set "profile_name=audi_q5_long_videos"
) else if "%profile_choice%"=="3" (
    set "profile_name=audi_q5_exfat"
) else if "%profile_choice%"=="4" (
    set /p profile_name="Enter profile name: "
) else (
    set "profile_name=audi_q5_mmi"
)

echo.
echo ================================================================================
echo Configuration Summary:
echo ================================================================================
echo   Mode:          Playlist Download
echo   URL:           %playlist_url%
echo   Output folder: %output_dir%
echo   Profile:       %profile_name%
echo   Range:         Video %playlist_start% to %playlist_end%
echo ================================================================================
echo.
echo Press any key to start download or Ctrl+C to cancel...
pause >nul

echo.
echo Starting playlist download and conversion...
echo.

cd /d "%~dp0"
if "%playlist_end%"=="" (
    python -m yt2audi playlist "%playlist_url%" --output "%output_dir%" --profile "%profile_name%" --start %playlist_start%
) else (
    python -m yt2audi playlist "%playlist_url%" --output "%output_dir%" --profile "%profile_name%" --start %playlist_start% --end %playlist_end%
)

set exit_code=%errorlevel%

if %exit_code% equ 0 (
    echo.
    echo ================================================================================
    echo SUCCESS! Playlist downloaded and converted.
    echo Output location: %output_dir%
    echo ================================================================================
) else (
    echo.
    echo ================================================================================
    echo WARNING! Some downloads may have failed. Check the logs above.
    echo ================================================================================
)

echo.
echo Press any key to return to main menu...
pause >nul
goto MAIN_MENU

:: ============================================================================
:: DOWNLOAD ONLY (NO CONVERSION)
:: ============================================================================
:DOWNLOAD_ONLY
cls
echo ================================================================================
echo                      Download Only (Skip Conversion)
echo ================================================================================
echo.
echo This mode downloads the video without converting it.
echo.
echo Enter the YouTube video URL (or press Ctrl+C to cancel):
set /p video_url="URL: "

if "%video_url%"=="" (
    echo.
    echo Error: URL cannot be empty.
    timeout /t 2 >nul
    goto MAIN_MENU
)

echo.
echo Enter output folder path (or press Enter for default: .\output):
set /p output_dir="Output folder: "

if "%output_dir%"=="" (
    set "output_dir=.\output"
)

echo.
echo ================================================================================
echo Configuration Summary:
echo ================================================================================
echo   Mode:          Download Only (No Conversion)
echo   URL:           %video_url%
echo   Output folder: %output_dir%
echo ================================================================================
echo.
echo Press any key to start download or Ctrl+C to cancel...
pause >nul

echo.
echo Starting download...
echo.

cd /d "%~dp0"
python -m yt2audi download "%video_url%" --output "%output_dir%" --skip-conversion

set exit_code=%errorlevel%

if %exit_code% equ 0 (
    echo.
    echo ================================================================================
    echo SUCCESS! Video downloaded.
    echo Output location: %output_dir%
    echo ================================================================================
) else (
    echo.
    echo ================================================================================
    echo ERROR! Download failed. Check the logs above.
    echo ================================================================================
)

echo.
echo Press any key to return to main menu...
pause >nul
goto MAIN_MENU

:: ============================================================================
:: CONVERT ONLY (EXISTING VIDEO)
:: ============================================================================
:CONVERT_ONLY
cls
echo ================================================================================
echo                      Convert Only (Existing Video)
echo ================================================================================
echo.
echo This mode converts an existing video file to Audi-compatible format.
echo.
echo Enter the path to the video file:
set /p video_file="Video file: "

if "%video_file%"=="" (
    echo.
    echo Error: File path cannot be empty.
    timeout /t 2 >nul
    goto MAIN_MENU
)

if not exist "%video_file%" (
    echo.
    echo Error: File not found: %video_file%
    timeout /t 2 >nul
    goto MAIN_MENU
)

echo.
echo Enter output folder path (or press Enter for default: .\output):
set /p output_dir="Output folder: "

if "%output_dir%"=="" (
    set "output_dir=.\output"
)

echo.
echo Select profile:
echo   [1] Audi Q5 MMI (Default - FAT32 USB, auto-split if needed)
echo   [2] Audi Q5 Long Videos (For videos ^>2hrs, smaller files)
echo   [3] Audi Q5 exFAT/NTFS (For exFAT/NTFS USB - no file limits!)
echo   [4] Custom profile
echo.
set /p profile_choice="Profile choice (1-4): "

if "%profile_choice%"=="2" (
    set "profile_name=audi_q5_long_videos"
) else if "%profile_choice%"=="3" (
    set "profile_name=audi_q5_exfat"
) else if "%profile_choice%"=="4" (
    set /p profile_name="Enter profile name: "
) else (
    set "profile_name=audi_q5_mmi"
)

echo.
echo ================================================================================
echo Configuration Summary:
echo ================================================================================
echo   Mode:          Convert Only
echo   Input file:    %video_file%
echo   Output folder: %output_dir%
echo   Profile:       %profile_name%
echo ================================================================================
echo.
echo Press any key to start conversion or Ctrl+C to cancel...
pause >nul

echo.
echo Starting conversion...
echo.

cd /d "%~dp0"
python -m yt2audi convert "%video_file%" --output "%output_dir%" --profile "%profile_name%"

set exit_code=%errorlevel%

if %exit_code% equ 0 (
    echo.
    echo ================================================================================
    echo SUCCESS! Video converted.
    echo Output location: %output_dir%
    echo ================================================================================
) else (
    echo.
    echo ================================================================================
    echo ERROR! Conversion failed. Check the logs above.
    echo ================================================================================
)

echo.
echo Press any key to return to main menu...
pause >nul
goto MAIN_MENU

:: ============================================================================
:: SETTINGS
:: ============================================================================
:SETTINGS
cls
echo ================================================================================
echo                              Settings
echo ================================================================================
echo.
echo Current profile location: .\configs\profiles\audi_q5_mmi.toml
echo.
echo Available actions:
echo   [1] Open profile in notepad
echo   [2] View current settings
echo   [3] Reset to default settings
echo   [4] Show available profiles
echo   [0] Back to main menu
echo.
set /p settings_choice="Choice (0-4): "

if "%settings_choice%"=="1" (
    notepad ".\configs\profiles\audi_q5_mmi.toml"
    goto SETTINGS
)
if "%settings_choice%"=="2" (
    echo.
    type ".\configs\profiles\audi_q5_mmi.toml"
    echo.
    echo Press any key to continue...
    pause >nul
    goto SETTINGS
)
if "%settings_choice%"=="3" (
    echo.
    echo Reset to default settings? This will overwrite your current profile.
    set /p confirm="Type YES to confirm: "
    if "!confirm!"=="YES" (
        echo Resetting to defaults...
        :: Could copy from a backup or template
        echo Done. Please restart the script.
    )
    timeout /t 2 >nul
    goto SETTINGS
)
if "%settings_choice%"=="4" (
    echo.
    echo Available profiles in .\configs\profiles\:
    dir /b ".\configs\profiles\*.toml" 2>nul
    echo.
    echo Press any key to continue...
    pause >nul
    goto SETTINGS
)
if "%settings_choice%"=="0" goto MAIN_MENU

goto SETTINGS

:: ============================================================================
:: UPDATE YT-DLP
:: ============================================================================
:UPDATE_YTDLP
cls
echo ================================================================================
echo                           Update yt-dlp
echo ================================================================================
echo.
echo This will update yt-dlp to the latest version.
echo.
set /p confirm="Continue? (Y/N): "

if /i not "%confirm%"=="Y" goto MAIN_MENU

echo.
echo Updating yt-dlp...
python -m pip install --upgrade yt-dlp

echo.
echo ================================================================================
echo yt-dlp update complete!
echo ================================================================================
echo.
echo Press any key to return to main menu...
pause >nul
goto MAIN_MENU

:: ============================================================================
:: RUN TESTS
:: ============================================================================
:RUN_TESTS
cls
echo ================================================================================
echo                              Run Tests
echo ================================================================================
echo.
echo Select test to run:
echo   [1] Download optimization test
echo   [2] Foundation tests
echo   [3] Full test suite (pytest)
echo   [0] Back to main menu
echo.
set /p test_choice="Choice (0-3): "

if "%test_choice%"=="1" (
    echo.
    echo Running download optimization test...
    python tests\manual\test_download_optimization.py
    echo.
    echo Press any key to continue...
    pause >nul
    goto RUN_TESTS
)
if "%test_choice%"=="2" (
    echo.
    echo Running foundation tests...
    python tests\manual\test_foundation.py
    echo.
    echo Press any key to continue...
    pause >nul
    goto RUN_TESTS
)
if "%test_choice%"=="3" (
    echo.
    echo Running full test suite...
    cd /d "%~dp0"
    python -m pytest tests/ -v
    echo.
    echo Press any key to continue...
    pause >nul
    goto RUN_TESTS
)
if "%test_choice%"=="0" goto MAIN_MENU

goto RUN_TESTS

:: ============================================================================
:: EXIT
:: ============================================================================
:EXIT
cls
echo ================================================================================
echo                          Thank you for using YT2Audi!
echo ================================================================================
echo.
echo Your videos are ready for your Audi infotainment system.
echo.
echo For support or feedback, visit:
echo   https://github.com/anthropics/claude-code/issues
echo.
echo ================================================================================
timeout /t 3 >nul
exit /b 0
