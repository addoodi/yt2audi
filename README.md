# YT2Audi
**Cross-platform YouTube downloader and converter optimized for Audi MMI systems.**

[![CI](https://github.com/addoodi/yt2audi/actions/workflows/ci.yml/badge.svg)](https://github.com/addoodi/yt2audi/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 📋 Project Status & Documentation

> **Current Status:** Phase 2 (Performance & Testing) - Active Development

- 📅 **[Roadmap & Way Forward](ROADMAP.md)** - Future plans and development phases
- 📊 **[Implementation Progress](baseline_metrics/implementation_progress.md)** - Current stage and completed improvements
- 📑 **[Project Analysis & Plan](https://github.com/addoodi/yt2audi/wiki)** - Detailed implementation plan (Wiki)
- 📝 **[Session Summaries](docs/sessions/)** - detailed record of changes

## Features

- ✅ **Smart Download Optimization** - Downloads 720p instead of 4K (10-20x faster, same quality!)
- ✅ **100% Audi Q5 Spec Compliant** - Based on official 2019 manual (720×576, 2 Mbps, 25fps)
- ✅ **Interactive Batch Files** - No command line knowledge needed (Windows)
- ✅ **Hardware-accelerated conversion** - NVIDIA NVENC, AMD AMF, Intel QuickSync
- ✅ **exFAT/NTFS support** - No file splitting needed (Audi Q5 supports all formats!)
- ✅ **FAT32 auto-split** - Automatic splitting for FAT32 USB drives
- ✅ **Multiple profiles** - Default, Long Videos, exFAT/NTFS
- ✅ **Playlist & batch support** - Download entire playlists or batch from file
- ✅ **Cross-platform** - Windows, macOS, Linux

## Quick Start

### Easiest Way (Windows)

1. Run: `install.bat` (installs dependencies)
2. Double-click: `yt2audi-interactive.bat` (interactive menu)
3. Choose option [1] Download Single Video
4. Paste YouTube URL and go!

**See [GETTING_STARTED.md](GETTING_STARTED.md) for complete beginner's guide.**

### Prerequisites

1. **Python 3.11+**
2. **FFmpeg** with hardware encoding support
   - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html)
   - macOS: `brew install ffmpeg`
   - Linux: `apt install ffmpeg` or compile from source

### Installation

```bash
# Windows: Just run install.bat
install.bat

# Or manually:
pip install pydantic tomli tomli-w structlog yt-dlp ffmpeg-python typer[all] rich tenacity

# Or use requirements.txt
pip install -r requirements.txt
```

### Basic Usage

#### Download Single Video

```bash
python -m yt2audi download "https://youtube.com/watch?v=dQw4w9WgXcQ"
```

#### Download Playlist

```bash
python -m yt2audi playlist "https://youtube.com/playlist?list=..."
```

#### Batch Download from File

Create `urls.txt`:
```
https://youtube.com/watch?v=video1
https://youtube.com/watch?v=video2
https://youtube.com/watch?v=video3
```

Then run:
```bash
python -m yt2audi batch urls.txt
```

#### Use Different Profile

```bash
python -m yt2audi download "URL" --profile high_quality
```

#### List Available Profiles

```bash
python -m yt2audi profiles
```

## Configuration

### Profiles

Profiles are located in `configs/profiles/`:

- `audi_q5_mmi.toml` - Default Audi Q5 profile (720x540, FAT32-safe)
- `high_quality.toml` - High quality for exFAT USB drives (1080p)

### Create Custom Profile

```toml
# ~/.config/yt2audi/profiles/my_profile.toml

[profile]
name = "My Custom Profile"
description = "Custom settings"
version = "1.0.0"

[video]
max_width = 1280
max_height = 720
codec = "h264"
# ... (see existing profiles for all options)
```

## Command Reference

### `download` - Download Single Video

```bash
python -m yt2audi download URL [OPTIONS]

Options:
  -p, --profile TEXT      Profile to use (default: audi_q5_mmi)
  -o, --output PATH       Output directory
  --skip-conversion       Download only, skip conversion
  --help                  Show help
```

### `batch` - Batch Download

```bash
python -m yt2audi batch URLS_FILE [OPTIONS]

Options:
  -p, --profile TEXT      Profile to use
  -o, --output PATH       Output directory
  --help                  Show help
```

### `playlist` - Download Playlist

```bash
python -m yt2audi playlist URL [OPTIONS]

Options:
  -p, --profile TEXT      Profile to use
  -o, --output PATH       Output directory
  --help                  Show help
```

### `profiles` - List Profiles

```bash
python -m yt2audi profiles
```

## Output Specifications (Audi Q5 Profile)

| Setting | Value |
|---------|-------|
| Max Resolution | 720x540 |
| Video Codec | H.264 Main Profile, Level 4.0 |
| Audio Codec | AAC, 128kbps, 44.1kHz, Stereo |
| Container | MP4 with faststart |
| Max File Size | 3.9GB (FAT32 limit) |
| FPS Cap | 25 fps |
| GPU Acceleration | Auto-detect (NVENC/AMF/QuickSync/CPU) |

## FAT32 File Size Handling

When a video exceeds 3.9GB, the tool can:

1. **Split** (default) - Automatically split into multiple parts
2. **Compress** - Reduce quality to fit under limit
3. **Warn** - Keep original, show warning
4. **Skip** - Don't process file

Configure in profile:
```toml
[output]
max_file_size_gb = 3.9
on_size_exceed = "split"  # or "compress", "warn", "skip"
```

## GPU Acceleration

The tool automatically detects and uses available hardware encoders:

**Priority:** NVIDIA NVENC → AMD AMF → Intel QuickSync → CPU (libx264)

**Check detection:**
```bash
python test_foundation.py
```

## Troubleshooting

### "FFmpeg not found"

Ensure FFmpeg is installed and in your PATH:
```bash
ffmpeg -version
```

### "No module named 'yt_dlp'"

Install yt-dlp:
```bash
pip install yt-dlp
```

### Videos won't play on Audi MMI

- Verify USB drive is FAT32 or exFAT
- Use default `audi_q5_mmi` profile
- Check file size is under 4GB for FAT32

### Conversion is slow

- Verify GPU encoding is working (check test_foundation.py output)
- Install GPU-specific drivers
- For AMD: Install latest Adrenalin drivers
- For NVIDIA: Install latest GeForce/Studio drivers

## Development

### Run Tests

```bash
python test_foundation.py
```

### Project Structure

```
yt2audi/
├── src/yt2audi/
│   ├── cli/           # CLI interface (Typer)
│   ├── core/          # Core logic (Downloader, Converter, Splitter)
│   ├── models/        # Pydantic data models
│   ├── config/        # Configuration management
│   └── utils/         # Utilities
├── configs/
│   └── profiles/      # Output profiles
└── tests/             # Unit tests
```

### Type Checking

```bash
python -m mypy src/yt2audi
```

## License

MIT License

## Credits

- **yt-dlp** - YouTube download engine
- **FFmpeg** - Video conversion
- **Typer** - CLI framework
- **Rich** - Terminal UI

## Version

Current version: **2.0.0**

---

**Made with ❤️ for Audi enthusiasts**
