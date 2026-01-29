# YT2Audi - Quick Start Guide

Get started with YT2Audi in 5 minutes!

---

## Choose Your Interface

YT2Audi offers two ways to use it:

### Option A: Interactive Menu (Easiest) ⭐ RECOMMENDED

Double-click `yt2audi-interactive.bat` for a user-friendly menu interface:
- No command line knowledge needed
- Step-by-step guided process
- Automatic input validation
- Perfect for beginners

**Features:**
```
================================================================================
                          YT2Audi Interactive Launcher
================================================================================

Select an option:

  [1] Download Single Video
  [2] Download Batch (from URL list file)
  [3] Download Playlist
  [4] Download Only (skip conversion)
  [5] Convert Only (existing video file)
  [6] View/Edit Settings
  [7] Update yt-dlp
  [8] Run Tests
  [0] Exit

Enter your choice (0-8):
```

### Option B: Quick Download (Fastest)

Double-click `quick-download.bat` for simple one-URL downloads:
- Just paste URL and go
- Uses default Audi Q5 MMI settings
- Saves to `.\output\` folder
- Perfect for quick one-off downloads

### Option C: Command Line (Advanced)

Use the Python CLI for full control (see below):
- Automation and scripting
- Custom parameters
- Integration with other tools

---

## Step 1: Install Dependencies

### Automated Installation (Recommended)

Double-click `install.bat` or run in Command Prompt:

```bash
install.bat
```

This will automatically install all required Python packages.

### Manual Installation

```bash
pip install -r requirements.txt
```

### Verify FFmpeg

Make sure FFmpeg is installed:

```bash
ffmpeg -version
```

If not installed, download from: https://ffmpeg.org/download.html

---

## Step 2: Test the Installation

Run the foundation test:

```bash
python test_foundation.py
```

You should see all tests pass:
```
[OK] All imports successful
[OK] YT2Audi version: 2.0.0
[OK] Loaded profile: Audi Q5 MMI
[OK] Validation works
[OK] GPU detection ran successfully
```

---

## Step 3: Your First Download

### Download a Single Video

```bash
cd src
python -m yt2audi download "https://youtube.com/watch?v=dQw4w9WgXcQ"
```

This will:
1. Download the video from YouTube
2. Convert it to Audi Q5 MMI format (720x540, H.264, AAC)
3. Save to `./output/` directory
4. Automatically split if >3.9GB (FAT32 safe)

### Check Available Profiles

```bash
cd src
python -m yt2audi profiles
```

Output:
```
Available profiles:

  audi_q5_mmi
    Optimized for Audi Q5 MMI/MIB2/3 systems with FAT32 USB support

  high_quality
    Maximum quality for exFAT USB drives (no file size limit)
```

---

## Step 4: Common Use Cases

### Download with High Quality Profile

```bash
cd src
python -m yt2audi download "YOUTUBE_URL" --profile high_quality
```

### Download to Custom Directory

```bash
cd src
python -m yt2audi download "YOUTUBE_URL" --output D:\Videos
```

### Download Entire Playlist

```bash
cd src
python -m yt2audi playlist "https://youtube.com/playlist?list=PLxxxxxx"
```

### Batch Download from File

1. Create `urls.txt` in project root:
   ```
   https://youtube.com/watch?v=video1
   https://youtube.com/watch?v=video2
   https://youtube.com/watch?v=video3
   ```

2. Run batch command:
   ```bash
   cd src
   python -m yt2audi batch ..\urls.txt
   ```

---

## Step 5: Transfer to USB

1. Format USB drive as **FAT32** (for <32GB) or **exFAT** (for >32GB)
2. Copy converted videos from `output/` folder to USB
3. Insert USB into Audi Q5 MMI system
4. Navigate to Media → USB in MMI

**FAT32 File Size Limit:** 4GB max (YT2Audi auto-splits larger files)

---

## Troubleshooting

### "No module named 'yt2audi'"

**Solution:** Make sure you're in the `src/` directory:
```bash
cd C:\Users\AAlmana\Documents\YT2Audi\src
python -m yt2audi --help
```

### "FFmpeg not found"

**Solution:** Install FFmpeg and add to PATH
- Download: https://ffmpeg.org/download.html
- Extract to `C:\ffmpeg\`
- Add `C:\ffmpeg\bin\` to system PATH

### "No module named 'yt_dlp'"

**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
```

### Videos won't play on Audi MMI

**Check:**
1. USB is formatted as FAT32 or exFAT
2. Video file is <4GB (or split parts are <4GB each)
3. Using `audi_q5_mmi` profile (default)
4. Video file has `.mp4` extension

### Slow conversion speed

**Check GPU detection:**
```bash
python test_foundation.py
```

Look for:
```
Selected encoder: h264_amf (or h264_nvenc or h264_qsv)
```

If it says `libx264`, GPU encoding isn't working. Update GPU drivers.

---

## Command Reference

### Get Help

```bash
cd src
python -m yt2audi --help
```

### Command List

| Command | Description |
|---------|-------------|
| `download URL` | Download single video |
| `batch FILE` | Download multiple videos from file |
| `playlist URL` | Download entire playlist |
| `profiles` | List available profiles |
| `--version` | Show version |

### Options

| Option | Description |
|--------|-------------|
| `-p, --profile NAME` | Use specific profile |
| `-o, --output DIR` | Output directory |
| `--skip-conversion` | Download only (no conversion) |

---

## Example Workflow

**Goal:** Download 10 car review videos for a road trip

1. **Create URL list:**
   ```
   # car_reviews.txt
   https://youtube.com/watch?v=review1
   https://youtube.com/watch?v=review2
   https://youtube.com/watch?v=review3
   # ... 7 more
   ```

2. **Download and convert:**
   ```bash
   cd src
   python -m yt2audi batch ..\car_reviews.txt
   ```

3. **Wait for completion** (watch progress bars)

4. **Check output:**
   ```bash
   dir ..\output
   ```

5. **Copy to USB:**
   ```bash
   xcopy ..\output\*.mp4 E:\ /Y
   ```
   (Assuming E: is your USB drive)

6. **Plug into Audi and enjoy!**

---

## Next Steps

- Read full [README.md](README.md) for advanced features
- Read [CLAUDE.md](CLAUDE.md) for technical details
- Read [MVP_COMPLETE.md](MVP_COMPLETE.md) for feature list
- Create custom profiles in `configs/profiles/`

---

## Need Help?

- Check [README.md](README.md) for detailed documentation
- Run `python -m yt2audi --help` for command help
- Report issues on GitHub (if repository exists)

---

**Enjoy your Audi-optimized videos!** 🚗🎬
