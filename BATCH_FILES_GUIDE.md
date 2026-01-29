# YT2Audi Batch Files Guide

This guide explains the interactive batch files included with YT2Audi for Windows users.

---

## Available Batch Files

### 1. `yt2audi-interactive.bat` - Full Interactive Menu

**Description:** Comprehensive menu-driven interface with all features.

**When to use:**
- You're new to YT2Audi
- You want guided step-by-step process
- You need to access advanced features (playlists, custom profiles, etc.)

**How to use:**
1. Double-click `yt2audi-interactive.bat`
2. Select option from menu (1-8)
3. Follow the prompts
4. Watch progress and wait for completion

**Features:**
- Download single video
- Download batch from URL file
- Download entire playlists
- Download-only mode (skip conversion)
- Convert existing video files
- View/edit settings
- Update yt-dlp
- Run tests

---

### 2. `quick-download.bat` - Simple One-Click Download

**Description:** Fastest way to download a single video with default settings.

**When to use:**
- You just want to download one video quickly
- You're happy with default Audi Q5 MMI settings
- You don't need custom output folders

**How to use:**
1. Double-click `quick-download.bat`
2. Paste YouTube URL
3. Press Enter
4. Wait for completion

**Settings:**
- Profile: `audi_q5_mmi` (720x540, H.264, AAC)
- Output: `.\output\` folder
- Auto-split: Enabled (for FAT32 compatibility)

---

## Interactive Menu Walkthrough

### Example 1: Download Single Video

```
Step 1: Launch yt2audi-interactive.bat

Step 2: Select [1] Download Single Video

Step 3: Enter YouTube URL
  URL: https://youtube.com/watch?v=dQw4w9WgXcQ

Step 4: Enter output folder (or press Enter for default)
  Output folder: D:\Audi Videos

Step 5: Select profile
  [1] Audi Q5 MMI (Default)
  [2] Custom profile
  Choice: 1

Step 6: Review summary and press any key to start

Step 7: Wait for download and conversion

Step 8: Find your video in D:\Audi Videos
```

---

### Example 2: Download Batch from File

**Preparation:**
1. Create `urls.txt` with one URL per line:
   ```
   https://youtube.com/watch?v=video1
   https://youtube.com/watch?v=video2
   https://youtube.com/watch?v=video3
   ```

**Steps:**
```
Step 1: Launch yt2audi-interactive.bat

Step 2: Select [2] Download Batch

Step 3: Enter file path (or press Enter for default urls.txt)
  URLs file: urls.txt

Step 4: Enter output folder
  Output folder: (press Enter for default)

Step 5: Select profile
  Choice: 1

Step 6: Press any key to start batch download

Step 7: Watch progress for all videos

Step 8: All videos saved to .\output\
```

---

### Example 3: Download Entire Playlist

```
Step 1: Launch yt2audi-interactive.bat

Step 2: Select [3] Download Playlist

Step 3: Enter playlist URL
  URL: https://youtube.com/playlist?list=PLxxxxxx

Step 4: Enter output folder
  Output folder: (press Enter for default)

Step 5: Enter range (optional)
  Start from video number: 1
  End at video number: (press Enter for all)

Step 6: Select profile
  Choice: 1

Step 7: Press any key to start

Step 8: All playlist videos downloaded and converted
```

---

### Example 4: Convert Existing Video

```
Step 1: Launch yt2audi-interactive.bat

Step 2: Select [5] Convert Only

Step 3: Enter video file path
  Video file: C:\Downloads\myvideo.mp4

Step 4: Enter output folder
  Output folder: (press Enter for default)

Step 5: Select profile
  Choice: 1

Step 6: Press any key to start conversion

Step 7: Converted video saved to .\output\
```

---

## Settings Management

### View Current Settings

```
Launch yt2audi-interactive.bat
→ Select [6] View/Edit Settings
→ Select [2] View current settings
```

This displays your current profile configuration (resolution, codecs, etc.).

### Edit Settings

```
Launch yt2audi-interactive.bat
→ Select [6] View/Edit Settings
→ Select [1] Open profile in notepad
```

This opens `audi_q5_mmi.toml` in Notepad where you can edit:
- Video resolution and quality
- Audio bitrate
- File size limits
- Download preferences
- And more...

**Common Settings to Change:**

```toml
# Increase quality (larger files)
[video]
quality_cq = 18  # Lower = better quality (default: 24)

# Disable file splitting
[output]
on_size_exceed = "warn"  # Options: "split", "compress", "warn", "skip"

# Change output directory
[output]
output_dir = "D:\\Audi Videos"

# Limit download speed (in Mbps)
[download]
rate_limit_mbps = 5.0  # 5 Mbps limit
```

---

## Update yt-dlp

YouTube frequently changes their API. Keep yt-dlp updated:

```
Launch yt2audi-interactive.bat
→ Select [7] Update yt-dlp
→ Confirm update
→ Wait for completion
```

**Recommended:** Update yt-dlp monthly or if downloads start failing.

---

## Testing Features

### Download Optimization Test

```
Launch yt2audi-interactive.bat
→ Select [8] Run Tests
→ Select [1] Download optimization test
```

Shows how the optimizer matches download quality to your profile settings.

### Foundation Tests

```
Launch yt2audi-interactive.bat
→ Select [8] Run Tests
→ Select [2] Foundation tests
```

Verifies:
- All dependencies installed
- GPU detection working
- Profile loading correctly
- FFmpeg available

---

## Troubleshooting Batch Files

### "python is not recognized"

**Problem:** Python not in PATH

**Solution:**
1. Add Python to system PATH, OR
2. Edit batch file to use full Python path:
   ```batch
   C:\Python311\python.exe -m yt2audi ...
   ```

### "No module named 'yt2audi'"

**Problem:** Script running from wrong directory

**Solution:**
Batch files automatically handle this, but if you see this error:
1. Make sure you're running from YT2Audi main folder
2. Check that `src/` folder exists
3. Run `install.bat` to reinstall dependencies

### Batch file closes immediately

**Problem:** Error occurred before you could read it

**Solution:**
1. Open Command Prompt
2. Drag and drop the .bat file into Command Prompt
3. Press Enter
4. Window will stay open so you can see errors

### "FFmpeg not found"

**Problem:** FFmpeg not installed or not in PATH

**Solution:**
1. Download FFmpeg: https://ffmpeg.org/download.html
2. Extract to `C:\ffmpeg\`
3. Add `C:\ffmpeg\bin\` to system PATH
4. Restart command prompt
5. Test: `ffmpeg -version`

---

## Advanced Usage

### Custom Profiles

Create a new profile:

1. Copy `configs/profiles/audi_q5_mmi.toml`
2. Rename to `my_custom_profile.toml`
3. Edit settings as needed
4. Use in interactive menu by selecting [2] Custom profile

### Silent/Automated Mode

For automation, use command line instead of batch files:

```batch
cd src
python -m yt2audi download "URL" --output "D:\Videos" --profile audi_q5_mmi
```

### Integration with Task Scheduler

Create scheduled downloads:

1. Create a batch file with your download command:
   ```batch
   cd C:\Users\YourName\YT2Audi\src
   python -m yt2audi batch C:\urls.txt --output D:\Videos
   ```

2. Use Windows Task Scheduler to run it daily/weekly

---

## Tips and Best Practices

### For Single Videos
✅ Use `quick-download.bat` - fastest option
✅ Or use interactive menu option [1]

### For Multiple Videos
✅ Create `urls.txt` file
✅ Use interactive menu option [2]
✅ Review summary before starting

### For Playlists
✅ Use interactive menu option [3]
✅ Consider limiting range for large playlists
✅ Check available disk space first

### For Best Quality
✅ Edit profile settings (option [6])
✅ Set `quality_cq = 18` (lower = better)
✅ Use `high_quality` profile

### For Smallest Files
✅ Set `on_size_exceed = "compress"` in profile
✅ Or use lower quality: `quality_cq = 28`
✅ Reduce audio bitrate: `bitrate_kbps = 96`

---

## Comparison: Batch Files vs Command Line

| Feature | Interactive .bat | Quick Download .bat | Command Line |
|---------|-----------------|-------------------|--------------|
| **Ease of Use** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **Speed** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Flexibility** | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Features** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Best For** | Beginners | Quick tasks | Advanced users |

---

## Keyboard Shortcuts

When using interactive batch files:

- **Ctrl+C**: Cancel current operation
- **Ctrl+V**: Paste (right-click also works)
- **Enter**: Accept default value
- **Tab**: Auto-complete file paths (in some contexts)

---

## Next Steps

After mastering the batch files:
1. Learn command line usage (see QUICKSTART.md)
2. Create custom profiles (see configs/profiles/)
3. Read full documentation (see README.md)
4. Explore advanced features (see CLAUDE.md)

---

**Happy downloading!** 🚗🎬
