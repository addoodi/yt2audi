# Changelog

All notable changes to this project will be documented in this file.

## [2.0.1] - 2025-12-25

### Added
- **Smart Download Optimization** - Automatically matches download quality to output profile
  - Downloads 720p for 720x576 output (instead of 4K/8K)
  - Saves 80-90% bandwidth and download time
  - No quality loss (same final output)
- **Official Audi Q5 Spec Compliance** - Updated profiles based on 2019 user manual
  - Resolution: 720×576 px (official spec)
  - Max bitrate: 2.0 Mbps (official spec)
  - Frame rate: 25 fps (official spec)
- **exFAT/NTFS Profile** - New profile for exFAT/NTFS USB drives
  - No file size limits (Audi Q5 supports exFAT and NTFS!)
  - No splitting needed for large files
- **Interactive Batch Files** (Windows)
  - `yt2audi-interactive.bat` - Full featured menu interface
  - `quick-download.bat` - One-click simple downloads
  - `split-existing-file.bat` - Split large files manually
- **Three Optimized Profiles**
  - `audi_q5_mmi` - Default (FAT32, auto-split)
  - `audi_q5_long_videos` - For videos >2hrs (smaller files)
  - `audi_q5_exfat` - For exFAT/NTFS USB (no limits)
- **Documentation**
  - `OFFICIAL_SPECS_OPTIMIZATION.md` - Complete optimization analysis
  - `OPTIMIZATION_SUMMARY.md` - Quick reference guide
  - `DOWNLOAD_OPTIMIZATION.md` - Download optimization details
  - `PROFILE_COMPARISON.md` - Profile comparison guide
  - `BATCH_FILES_GUIDE.md` - Interactive batch file guide
  - `GETTING_STARTED.md` - Beginner's guide

### Fixed
- **File Splitter Bug** - Fixed format string error when splitting files >3.9GB
  - Error: "Unknown format code 'd' for object of type 'str'"
  - Now correctly generates split files (part000.mp4, part001.mp4, etc.)

### Changed
- **Resolution**: 720×540 → 720×576 (official Audi Q5 spec)
- **Max Bitrate**: "auto" → 2.0 Mbps (official Audi Q5 spec)
  - Results in ~33% smaller files for long videos
  - Ensures compatibility and prevents decoder overload
- **Profile Descriptions** - Updated to reflect official specifications

### Optimized
- **File Sizes** - 33% reduction for long videos due to 2.0 Mbps limit
  - Example: 24-hour video reduced from 9.5GB to 6.3GB
- **Download Speed** - 10-20x faster downloads with smart optimization
  - Example: 17GB 4K download → 3.5GB 720p download

---

## [2.0.0] - 2025-12-24

### Added
- Complete Python rewrite from batch scripts
- Cross-platform support (Windows, macOS, Linux)
- Hardware-accelerated encoding (NVENC, AMF, QuickSync)
- Multiple output profiles
- Playlist support
- Batch processing
- Auto-retry with exponential backoff
- Structured logging (JSON)
- Type-safe code with full type hints
- CLI interface with Typer
- FAT32 file splitting support
- Subtitle embedding

### Initial Features
- Download single videos
- Download batches from URL file
- Download entire playlists
- GPU detection and encoder selection
- Progress tracking with Rich library
- Profile-based configuration (TOML)
- Automatic retry on errors

---

## Format

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

### Categories
- **Added** - New features
- **Changed** - Changes to existing functionality
- **Deprecated** - Soon-to-be removed features
- **Removed** - Removed features
- **Fixed** - Bug fixes
- **Security** - Security fixes
- **Optimized** - Performance improvements
