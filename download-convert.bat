@echo off
setlocal EnableDelayedExpansion
:: Force UTF-8 encoding
chcp 65001 >nul

:: ============================================================================
:: AUTOMATED YOUTUBE DOWNLOADER & CONVERTER FOR AUDI Q5 (MMI / MIB2/3)
:: ============================================================================
:: Requirements: 
:: 1. FFmpeg and FFprobe on system PATH.
:: 2. yt-dlp.exe (in this folder or on PATH).
:: 3. NVIDIA GPU with NVENC support.
:: ============================================================================

:: --- CONFIGURATION ---

set "OVERWRITE=y"
set "NVENC_CQ=24"
set "AUDIO_BITRATE=128k"
set "AUDIO_SAMPLERATE=44100"

:: ============================================================================

echo.
echo ========================================================
echo   Audi Q5 MMI Downloader ^& Converter
echo ========================================================
echo.

:: 0. CHECK FOR YT-DLP AND URLS
:: ----------------------------------------------------------------------------
if exist "urls.txt" (
    echo [Check] 'urls.txt' found. Checking for yt-dlp...
    
    where yt-dlp >nul 2>nul
    if !errorlevel! NEQ 0 (
        if not exist "yt-dlp.exe" (
            echo [WARNING] 'urls.txt' exists but 'yt-dlp.exe' was not found.
            echo           Skipping download phase.
            goto :StartConversion
        )
    )

    echo [DOWNLOAD] Downloading videos from urls.txt...
    echo.
    
    :: Logic:
    :: --restrict-filenames: Ensures no emojis/weird chars in raw download
    :: --merge-output-format mp4: Ensures we get an MP4 container
    :: -o: Naming structure
    
    for /F "usebackq tokens=*" %%A in ("urls.txt") do (
        if "%%A" NEQ "" (
            echo    Downloading: %%A
            yt-dlp --restrict-filenames -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" --merge-output-format mp4 -o "%%(title)s.%%(ext)s" "%%A"
            echo.
        )
    )
    
    echo [DOWNLOAD] Batch download complete. Proceeding to conversion...
    echo --------------------------------------------------------
) else (
    echo [INFO] No 'urls.txt' found. Processing local files only.
)

:StartConversion

:: 1. Create Output Directory
if not exist "output" (
    echo [INFO] Creating 'output' directory...
    mkdir "output"
)

:: 2. Loop through supported extensions
for %%I in (*.mp4 *.mkv *.m4a *.webm) do (
    call :ProcessFile "%%~fI"
)

echo.
echo ========================================================
echo   Job Complete.
echo ========================================================
pause
exit /b

:: ============================================================================
:: SUBROUTINE: Process Single File
:: ============================================================================
:ProcessFile
    set "INPUT_FILE=%~1"
    
    :: Output filename (ensure it ends in .mp4 regardless of input)
    set "OUTPUT_FILE=%~dp1output\%~n1.mp4"
    set "FILENAME=%~nx1"
    
    :: TEMP WORK FILE (Safe Container)
    set "TEMP_WORK_FILE=%~dp1output\audi_temp_encode.mp4"
    
    :: Scale Filter (Max 720x540)
    set "SCALE_FILTER=scale=w=min(720\,iw):h=min(540\,ih):force_original_aspect_ratio=decrease:force_divisible_by=2"

    echo.
    echo --------------------------------------------------------
    echo Processing: "!FILENAME!"

    :: Check overwrite policy
    if /I "!OVERWRITE!"=="n" (
        if exist "!OUTPUT_FILE!" (
            echo [SKIP] Output file already exists.
            goto :eof
        )
    )

    :: COPY STEP: Safe Copy
    echo [COPY] Copying to temp file to ensure safe filename...
    copy /y "!INPUT_FILE!" "!TEMP_WORK_FILE!" >nul
    
    if not exist "!TEMP_WORK_FILE!" (
        echo [ERROR] Copy failed. Skipping file.
        goto :eof
    )

    :: ------------------------------------------------------
    :: PROBE STEP
    :: ------------------------------------------------------
    
    set "FPS_RAW="
    set "FPS_INT=0"
    set "FFMPEG_FPS_ARG="
    set "INPUT_BITRATE="
    set "FFMPEG_BITRATE_ARG="
    
    set "PROBE_TEMP=%TEMP%\audi_probe_!RANDOM!.txt"
    
    ffprobe -v 0 -select_streams v:0 -show_entries stream=r_frame_rate,bit_rate -of default=noprint_wrappers=1 "!TEMP_WORK_FILE!" > "!PROBE_TEMP!" 2>nul
    
    if exist "!PROBE_TEMP!" (
        for /f "tokens=1,2 delims==" %%A in ('type "!PROBE_TEMP!"') do (
            if "%%A"=="r_frame_rate" set "FPS_RAW=%%B"
            if "%%A"=="bit_rate" set "INPUT_BITRATE=%%B"
        )
        del "!PROBE_TEMP!"
    )

    if not defined FPS_RAW goto ModeAudio

    :: ------------------------------------------------------
    :: OPTIMIZATION: Bitrate Logic
    :: ------------------------------------------------------
    
    if defined INPUT_BITRATE (
        if "!INPUT_BITRATE!"=="N/A" (
             echo [INFO] Input bitrate unknown. Using default safety cap.
             set "FFMPEG_BITRATE_ARG=-maxrate 2000k -bufsize 2000k"
        ) else (
             echo [OPTIMIZE] Input Bitrate detected: !INPUT_BITRATE! bps
             echo [OPTIMIZE] Limiting output maxrate to input bitrate.
             set "FFMPEG_BITRATE_ARG=-maxrate !INPUT_BITRATE! -bufsize !INPUT_BITRATE!"
        )
    ) else (
        set "FFMPEG_BITRATE_ARG=-maxrate 2000k -bufsize 2000k"
    )

    :: ------------------------------------------------------
    :: FPS CALCULATION
    :: ------------------------------------------------------
    
    for /f "tokens=1,2 delims=/" %%A in ("!FPS_RAW!") do (
        set "NUM=%%A"
        set "DEN=%%B"
    )
    
    if "!DEN!"=="" set "DEN=1"
    if "!DEN!"=="0" set "DEN=1"
    
    set /a FPS_INT=!NUM!/!DEN!
    
    if !FPS_INT! GTR 25 (
        echo [LOGIC] Capping FPS to 25.
        set "FFMPEG_FPS_ARG=-r 25"
    ) else if !FPS_INT! LSS 1 (
        echo [LOGIC] FPS too low/invalid. Defaulting to 25.
        set "FFMPEG_FPS_ARG=-r 25"
    ) else (
        set "FFMPEG_FPS_ARG="
    )

    goto ModeVideo

:ModeAudio
    echo [INFO] Audio-only mode detected.
    ffmpeg -y -i "!TEMP_WORK_FILE!" ^
    -vn ^
    -c:a aac -b:a !AUDIO_BITRATE! -ac 2 -ar !AUDIO_SAMPLERATE! ^
    -map_metadata -1 -map_chapters -1 ^
    -movflags +faststart ^
    "!OUTPUT_FILE!"
    goto CheckResult

:ModeVideo
    ffmpeg -y -i "!TEMP_WORK_FILE!" ^
    -c:v h264_nvenc -preset p4 -rc vbr -cq !NVENC_CQ! !FFMPEG_BITRATE_ARG! -profile:v main -level 4.0 ^
    -pix_fmt yuv420p ^
    -vf "!SCALE_FILTER!" ^
    !FFMPEG_FPS_ARG! -fps_mode cfr ^
    -c:a aac -b:a !AUDIO_BITRATE! -ac 2 -ar !AUDIO_SAMPLERATE! ^
    -sn -dn -map_chapters -1 -map_metadata -1 ^
    -movflags +faststart ^
    "!OUTPUT_FILE!"
    goto CheckResult

:CheckResult
    if !errorlevel! NEQ 0 (
        echo [ERROR] FFmpeg failed for file: "!FILENAME!"
    ) else (
        echo [SUCCESS] Converted: "!FILENAME!"
    )
    
    if exist "!TEMP_WORK_FILE!" del "!TEMP_WORK_FILE!"
    
    goto :eof