# Getting Started with YT2Audi

**Welcome!** This guide will help you start using YT2Audi in less than 5 minutes.

---

## Quick Start (3 Steps)

### Step 1: Install Dependencies

Double-click: **`install.bat`**

This installs all required Python packages automatically.

---

### Step 2: Test Installation (Optional)

Double-click: **`test_foundation.py`** or run:
```
python test_foundation.py
```

You should see: `[OK] All tests passed!`

---

### Step 3: Download Your First Video

**Easiest method:**

Double-click: **`quick-download.bat`**
- Paste YouTube URL
- Press Enter
- Done!

**OR, for more control:**

Double-click: **`yt2audi-interactive.bat`**
- Choose option [1] Download Single Video
- Follow the prompts
- Done!

---

## File Overview

Here's what each file does:

### 🚀 Quick Start Files (Double-click these!)

| File | Purpose | When to Use |
|------|---------|-------------|
| **install.bat** | Install dependencies | First time setup |
| **quick-download.bat** | Download one video | Quick single downloads |
| **yt2audi-interactive.bat** | Full menu interface | All features, guided setup |

### 📖 Documentation

| File | Content |
|------|---------|
| **GETTING_STARTED.md** | This file - start here! |
| **QUICKSTART.md** | 5-minute guide with examples |
| **BATCH_FILES_GUIDE.md** | Complete batch file reference |
| **README.md** | Full documentation |
| **DOWNLOAD_OPTIMIZATION.md** | How download optimization works |

### 🧪 Test Files

| File | Purpose |
|------|---------|
| **test_foundation.py** | Verify installation |
| **test_download_optimization.py** | Test download optimizer |

### ⚙️ Configuration

| Location | Purpose |
|----------|---------|
| **configs/profiles/** | Output profiles (Audi Q5, high quality, etc.) |
| **urls.txt** | Your URL list for batch downloads (create this) |

---

## Common Tasks

### Task: Download a Single Video

**Method 1 (Quickest):**
```
1. Double-click: quick-download.bat
2. Paste URL
3. Press Enter
```

**Method 2 (More options):**
```
1. Double-click: yt2audi-interactive.bat
2. Select [1] Download Single Video
3. Enter URL
4. Choose output folder
5. Done!
```

---

### Task: Download Multiple Videos

**Preparation:**
Create a file called `urls.txt` with your video URLs (one per line):
```
https://youtube.com/watch?v=video1
https://youtube.com/watch?v=video2
https://youtube.com/watch?v=video3
```

**Steps:**
```
1. Double-click: yt2audi-interactive.bat
2. Select [2] Download Batch
3. Press Enter (uses urls.txt by default)
4. Wait for completion
```

---

### Task: Download Entire Playlist

```
1. Double-click: yt2audi-interactive.bat
2. Select [3] Download Playlist
3. Paste playlist URL
4. Press Enter for defaults
5. Wait for completion
```

---

### Task: Convert Existing Video File

```
1. Double-click: yt2audi-interactive.bat
2. Select [5] Convert Only
3. Enter path to your video file
4. Choose output folder
5. Done!
```

---

### Task: Adjust Quality Settings

```
1. Double-click: yt2audi-interactive.bat
2. Select [6] View/Edit Settings
3. Select [1] Open profile in notepad
4. Edit quality_cq value (18=high quality, 28=small files)
5. Save and close
```

---

## Where Are My Videos?

By default, converted videos are saved to:
```
C:\Users\YourName\Documents\YT2Audi\output\
```

You can change this:
- In interactive menu: enter custom path when prompted
- In settings: edit `output_dir` in profile config

---

## Transfer to Audi USB

After downloading:

1. **Format USB:**
   - For drives <32GB: Use **FAT32**
   - For drives >32GB: Use **exFAT**

2. **Copy videos:**
   - Go to `output\` folder
   - Copy all `.mp4` files to USB

3. **Play in Audi:**
   - Insert USB into Audi MMI
   - Navigate to: Media → USB
   - Enjoy!

---

## Understanding the Output

### File Names

Videos are named using the pattern:
```
Video_Title_videoID.mp4
```

Example:
```
How_To_Drive_Manual_Transmission_dQw4w9WgXcQ.mp4
```

### File Splitting

If a video is >3.9GB, it's automatically split:
```
Long_Movie_part001.mp4
Long_Movie_part002.mp4
Long_Movie_part003.mp4
```

This ensures FAT32 compatibility (4GB file limit).

---

## Troubleshooting

### "Python not found"

**Fix:** Install Python 3.11+ from python.org

### "FFmpeg not found"

**Fix:** Install FFmpeg:
1. Download: https://ffmpeg.org/download.html
2. Extract to `C:\ffmpeg\`
3. Add to PATH: `C:\ffmpeg\bin\`

### "No module named yt2audi"

**Fix:** Run `install.bat` again

### Videos won't play in Audi

**Check:**
- USB formatted as FAT32 or exFAT
- Files are `.mp4` format
- Files are <4GB each (or split)
- Using default Audi Q5 MMI profile

### Very slow downloads

**Check your internet speed** - Large videos (4K) can be 10-20GB.

**Tip:** The new download optimization now downloads 720p instead of 4K by default, making downloads 10-20x faster! (See DOWNLOAD_OPTIMIZATION.md)

---

## Performance Tips

### ⚡ Speed Up Downloads (NEW!)

YT2Audi now **automatically optimizes downloads** to match your output quality!

For Audi Q5 (720x540 output):
- ❌ Old: Downloads 4K (~17GB) → converts to 720p (~1.5GB)
- ✅ New: Downloads 720p (~1.2GB) → converts to 720p (~1.5GB)
- 💡 **Result: 10-20x faster downloads, same quality!**

This is enabled by default. See DOWNLOAD_OPTIMIZATION.md for details.

### ⚡ Speed Up Conversions

**Check GPU encoding:**
```
python test_foundation.py
```

If you see `libx264` instead of `h264_nvenc/amf/qsv`:
1. Update your GPU drivers
2. Restart computer
3. Test again

GPU encoding is **3-5x faster** than CPU encoding!

---

## What's Next?

### Beginner Path
1. ✅ Download a few test videos
2. ✅ Try batch download
3. ✅ Experiment with settings
4. 📖 Read BATCH_FILES_GUIDE.md for advanced features

### Advanced Path
1. 📖 Read QUICKSTART.md for command line usage
2. 📖 Read README.md for all features
3. ⚙️ Create custom profiles
4. 🔧 Explore CLAUDE.md for technical details

---

## Support

- **Questions:** Check the FAQ in README.md
- **Issues:** Run tests to diagnose problems
- **Updates:** Use interactive menu option [7] to update yt-dlp

---

## Features Overview

✅ Download single videos
✅ Download batches (multiple videos)
✅ Download entire playlists
✅ Automatic Audi MMI optimization (720x540, H.264, AAC)
✅ Smart download optimization (10-20x faster!)
✅ Auto-split for FAT32 (>3.9GB files)
✅ GPU hardware acceleration (NVIDIA/AMD/Intel)
✅ Subtitle embedding
✅ Automatic retry on errors
✅ Resume interrupted downloads
✅ User-friendly batch files (no CLI knowledge needed!)

---

**Ready to start?**

1. Run `install.bat`
2. Double-click `quick-download.bat`
3. Paste a YouTube URL
4. Enjoy your Audi-optimized videos! 🚗🎬

---

*Last Updated: 2025-12-25*
*Version: 2.0.0*
