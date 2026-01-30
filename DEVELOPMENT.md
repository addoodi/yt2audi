# YT2Audi Development Documentation

> **Purpose:** This document serves as the single source of truth for the project's development plan, technical analysis, and implementation progress. It consolidates previous roadmaps and status reports.

---

## 1. Project Analysis & Overview

**YT2Audi** is a cross-platform YouTube downloader and video converter optimized for Audi Q5 MMI/MIB2/3 infotainment systems. It focuses on robust performance, hardware acceleration, and specific format compatibility for vehicle media systems.

### 1.1 Technology Stack
- **Language:** Python 3.11+
- **Core Libraries:** `yt-dlp` (Downloader), `ffmpeg-python` (Conversion)
- **CLI Framework:** Typer + Rich
- **Data models:** Pydantic v2
- **Testing:** pytest, coverage
- **Build:** Poetry / pip

### 1.2 Architecture
```
src/yt2audi/
├── cli/           # CLI interface (Typer commands)
├── core/          # Business logic (Downloader, Converter, Splitter)
├── models/        # Data structures (Pydantic)
└── utils/         # Helpers (Path sanitization, Validation)
```

### 1.3 Key Features
- **Smart GPU Detection:** Auto-selects NVENC, AMF, or QuickSync.
- **Profile System:** Pre-tuned configs for Audi MMI (FAT32 splitting, exFAT quality).
- **Security:** Strict path sanitization and pinned dependencies.
- **Resilience:** Automatic retries and specific error handling.

---

## 2. Implementation Plan & Roadmap

This roadmap outlines the development phases.

### Phase 0: Cleanup & Baseline ✅ (COMPLETE)
- [x] Baseline testing (7/7 tests passed)
- [x] Remove build artifacts (~30 MB saved)
- [x] Reorganize project structure
- [x] Record metrics

### Phase 1: Critical Security Fixes ✅ (COMPLETE)
- [x] **SEC-1:** Pin dependency versions (`requirements.txt`)
- [x] **SEC-2:** Add path enforcement (`sanitize_path`)
- [x] **DOC-3:** Create `CONTRIBUTING.md`
- [x] **DEVOPS-1:** GitHub Actions CI/CD (`.github/workflows/ci.yml`)

### Phase 2: Performance & Code Quality 🔄 (IN PROGRESS)
**Goal:** Optimize speed and reliability.

- [x] **CODE-2:** Reduce code duplication (CLI helpers)
- [x] **DEVOPS-2:** Pre-commit hooks
- [x] **BUG-3:** Windows long path support
- [x] **FIX-1:** Fix interactive batch execution (Typer compatibility)
- [x] **FIX-2:** YouTube 403 Bypass (Updated `yt-dlp` & Client Headers)
- [ ] **PERF-1:** Async download pipeline (Concurrent batch downloads) **[NEXT PRIORITY]**
- [ ] **PERF-2:** Resume support for interrupted downloads
- [ ] **TEST-1:** Increase test coverage to 85%

### Phase 3: Enhancements ⏳ (PLANNED)
- [ ] **FEAT-2:** USB Auto-Detection & Copy
- [ ] **PERF-3:** Metadata Caching
- [ ] **DOC-1:** API Documentation (Sphinx)
- [ ] **FEAT-4:** Playlist Tracking (avoid re-downloads)

### Phase 4: Extended Features ⏳ (FUTURE)
- [ ] **FEAT-1:** Web UI Dashboard
- [ ] **FEAT-3:** Subtitle Translation
- [ ] **DEVOPS-3:** Automated Semantic Releases

---

## 3. Implementation Progress Report

**Last Updated Status:** Phase 2 Active

### Recent Accomplishments
1.  **Resolved Critical Bugs:**
    *   Fixed `yt2audi-interactive.bat` crashing due to directory/path issues.
    *   Resolved `UserWarning` regarding Typer/Click versions by updating `pyproject.toml`.
    *   **Fixed YouTube 403 Forbidden errors:** Updated `downloader.py` to use `android`/`ios` client simulation and force IPv4 (`source_address='0.0.0.0'`). Also unpinned `yt-dlp` to ensure latest extraction logic is always available.
    
2.  **GitHub Migration:**
    *   Cleaned repository history of large binaries (~4.5GB removed).
    *   Successfully uploaded project to GitHub (`origin/main`).
    *   Restored and pushed CI workflows.

### Metrics Snapshot
| Metric | Baseline | Current | Target |
|--------|----------|---------|--------|
| **Test Coverage** | ~65% | ~65% | 85% |
| **Security Score** | B | A | A+ |
| **Repo Size** | ~50MB | ~35MB | <50MB |
| **Dependencies** | Vulnerable | Secured | Pinned |

---

## 4. Technical Recommendations (from Analysis)

### Performance Optimizations (PERF)
- **Async Pipeline:** Move from sequential `for` loop to `asyncio.gather`. Use a semaphore to limit concurrency (e.g., 3 downloads) to avoid rate limits while maximizing bandwidth.
- **FFmpeg Flags:** Add `-movflags +faststart` and `-max_muxing_queue_size` for better stability on large files.

### Code Quality (CODE)
- **Type Safety:** Continue using `mypy --strict`.
- **Error Handling:** Ensure `DownloadError` wraps low-level exceptions with user-friendly messages (e.g., "Geo-blocked" instead of HTTP 403).

### Testing (TEST)
- **Integration Tests:** Needs end-to-end test of `Download -> Convert -> Split` on a real small file.
- **Mocking:** Mock `yt_dlp` responses to test edge cases without hitting YouTube (avoid bans during testing).
