# YT2Audi Development Roadmap

**Last Updated:** 2026-01-29  
**Current Status:** Phase 2 (75% complete)  
**Overall Progress:** 40% (8 of 20 major items complete)

---

## Overview

This roadmap outlines planned improvements for YT2Audi across 4 phases. Phases 0, 1, and partial Phase 2 are complete. This document provides a clear path forward for remaining work.

---

## Phase Progress

```
✅ Phase 0: Cleanup & Baseline (100%)   [1 week - COMPLETE]
✅ Phase 1: Critical Fixes (100%)       [1 week - COMPLETE]
🔄 Phase 2: Important (75%)             [2-3 weeks - IN PROGRESS]
⏳ Phase 3: Enhancements (0%)           [4 weeks - PLANNED]
⏳ Phase 4: Nice-to-Have (0%)           [6+ weeks - PLANNED]
```

**Total Estimated Time:** 12-14 weeks  
**Time Invested:** 2 weeks (Phases 0, 1, 2 partial)  
**Remaining:** 10-12 weeks

---

## ✅ Completed Items (Phases 0-2)

### Phase 0: Cleanup & Baseline ✅
- [x] Baseline testing (7/7 tests passed)
- [x] Remove build artifacts (~25 MB saved)
- [x] Reorganize project structure
- [x] Update .gitignore
- [x] Record baseline metrics

**Status:** ✅ Complete (Commit: 4e829ce)

---

### Phase 1: Critical Security Fixes ✅
- [x] **SEC-1:** Pin dependency versions
- [x] **SEC-2:** Add path sanitization (`sanitize_path()`)
- [x] **DOC-3:** Create CONTRIBUTING.md
- [x] **DEVOPS-1:** GitHub Actions CI/CD (9 platforms)

**Status:** ✅ Complete (Commit: 238f7a4)

---

### Phase 2: Code Quality (Partial) 🔄
- [x] **CODE-2:** Reduce code duplication (CLI helpers)
- [x] **DEVOPS-2:** Pre-commit hooks (11 checks)
- [x] **BUG-3:** Windows long path support
- [ ] **PERF-1:** Async download pipeline ⏳
- [ ] **PERF-2:** Resume support ⏳
- [ ] **TEST-1:** Increase coverage to 85% ⏳

**Status:** 🔄 75% Complete (Commit: 158762d)

---

## 🎯 Next Steps: Complete Phase 2

### Priority 1: PERF-1 - Async Download Pipeline

**Goal:** 3-5x performance improvement for batch operations

**Implementation:**

1. **Create async downloader** (`src/yt2audi/core/async_downloader.py`)
   ```python
   import asyncio
   import aiohttp
   from typing import List
   
   class AsyncDownloader:
       async def download_videos(self, urls: List[str]) -> List[Path]:
           """Download multiple videos concurrently."""
           tasks = [self._download_single(url) for url in urls]
           return await asyncio.gather(*tasks)
   ```

2. **Add async CLI command**
   ```bash
   yt2audi batch-async urls.txt --max-concurrent 3
   ```

3. **Implement semaphore** for rate limiting
   ```python
   self.semaphore = asyncio.Semaphore(max_concurrent)
   ```

4. **Add progress aggregation** for multiple concurrent downloads

**Estimated Time:** 4-6 hours  
**Complexity:** High (7/10)  
**Dependencies:** `aiohttp`, `aiofiles` (already installed)

**Success Criteria:**
- [ ] Batch downloads 3-5x faster
- [ ] Concurrent limit configurable (default: 3)
- [ ] Progress bars show all active downloads
- [ ] Error handling per video (don't stop batch on failure)
- [ ] Tests cover async edge cases

---

### Priority 2: PERF-2 - Resume Support

**Goal:** Continue interrupted downloads without restarting

**Implementation:**

1. **Download state tracking** (`.yt2audi.state.json`)
   ```json
   {
     "url": "https://youtube.com/...",
     "downloaded_bytes": 1024000,
     "total_bytes": 5120000,
     "temp_file": "/tmp/video_Abc123.part"
   }
   ```

2. **Resume logic in downloader**
   ```python
   def download_video(self, url: str, resume: bool = True):
       if resume and state_file.exists():
           state = load_state(state_file)
           # Resume from state.downloaded_bytes
       else:
           # Start fresh download
   ```

3. **Add CLI flag**
   ```bash
   yt2audi download URL --resume
   ```

4. **Cleanup state files** on successful completion

**Estimated Time:** 3-4 hours  
**Complexity:** Medium (6/10)  
**Dependencies:** None (standard library)

**Success Criteria:**
- [ ] Interrupted downloads resume from last byte
- [ ] State files cleaned up on success
- [ ] Works with both single and batch downloads
- [ ] CLI flag `--resume` / `--no-resume`
- [ ] Tests verify resume accuracy

---

### Priority 3: TEST-1 - Increase Test Coverage to 85%

**Goal:** Improve reliability and catch regressions

**Current Coverage:** ~65%  
**Target:** 85%+

**Plan:**

1. **Identify gaps** (Run coverage report)
   ```bash
   pytest --cov=yt2audi --cov-report=html
   # Open htmlcov/index.html
   ```

2. **Priority areas:**
   - Core modules: `downloader.py`, `converter.py`, `splitter.py` (90%+)
   - Security: `sanitize_path()`, `validate_file_path()` (100%)
   - CLI helpers: `helpers.py` (80%+)
   - Models: `profile.py` (70%+)

3. **Add missing tests:**
   - Edge cases (empty URLs, invalid profiles)
   - Error paths (network failures, disk full)
   - Integration tests (end-to-end workflows)

4. **Create test fixtures** (`tests/fixtures/`)
   - Sample videos (small, <1MB)
   - Test profiles (various configs)
   - Mock responses

**Estimated Time:** 4-6 hours  
**Complexity:** Medium (5/10)

**Success Criteria:**
- [ ] Overall coverage ≥85%
- [ ] Core modules ≥90%
- [ ] Security functions 100%
- [ ] No untested error paths
- [ ] Integration tests added

---

## 📅 Phase 2 Completion Timeline

| Item | Estimated Time | Status |
|------|---------------|---------|
| **PERF-1:** Async pipeline | 4-6 hours | ⏳ Next |
| **PERF-2:** Resume support | 3-4 hours | ⏳ After PERF-1 |
| **TEST-1:** Coverage to 85% | 4-6 hours | ⏳ Final |
| **Total** | **11-16 hours** | **2-3 sessions** |

**Recommended Schedule:**
- **Session 1 (4-5 hours):** PERF-1 (Async pipeline)
- **Session 2 (3-4 hours):** PERF-2 (Resume support)
- **Session 3 (4-6 hours):** TEST-1 (Coverage)

---

## 🚀 Phase 3: Enhancements (Future)

**Timeline:** Month 2 (after Phase 2 complete)

### Features to Implement

1. **FEAT-2: USB Auto-Detection** (High Priority)
   - Detect connected USB drives
   - Auto-copy completed videos
   - Support multiple drives
   - **Time:** 3-4 hours

2. **PERF-3: Caching** (Medium Priority)
   - Cache video metadata
   - Avoid re-downloading info
   - **Time:** 2-3 hours

3. **DOC-1: API Documentation** (Medium Priority)
   - Sphinx setup
   - Auto-generate from docstrings
   - Host on Read the Docs
   - **Time:** 4-6 hours

4. **FEAT-4: Playlist Tracking** (Low Priority)
   - Track downloaded videos
   - Skip already downloaded
   - **Time:** 3-4 hours

5. **CONFIG-1: Environment Variables** (Low Priority)
   - Support `YT2AUDI_*` env vars
   - Override profile settings
   - **Time:** 2-3 hours

**Phase 3 Total:** 14-20 hours (2-3 weeks)

---

## 🎨 Phase 4: Nice-to-Have (Future)

**Timeline:** Month 3+ (after Phase 3 complete)

### Optional Features

1. **FEAT-1: Web UI Dashboard**
   - FastAPI backend
   - React/Vue frontend
   - Monitor downloads remotely
   - **Time:** 12-16 hours

2. **FEAT-3: Enhanced Subtitle Support**
   - Auto-download subtitles
   - Translation support
   - Burn-in option
   - **Time:** 4-6 hours

3. **FEAT-5: Quality Presets**
   - `--quality ultra|balanced|fast|minimal`
   - Quick selection
   - **Time:** 2-3 hours

4. **TEST-2: Property-Based Testing**
   - Hypothesis integration
   - Fuzz testing
   - **Time:** 4-6 hours

5. **DEVOPS-3: Automated Releases**
   - Semantic versioning
   - Changelog generation
   - GitHub releases
   - **Time:** 3-4 hours

**Phase 4 Total:** 25-35 hours (4-6 weeks)

---

## 📊 Roadmap Metrics

### Progress Tracking

| Phase | Items | Complete | Remaining | % Done |
|-------|-------|----------|-----------|--------|
| **Phase 0** | 5 | 5 | 0 | 100% ✅ |
| **Phase 1** | 4 | 4 | 0 | 100% ✅ |
| **Phase 2** | 6 | 3 | 3 | 50% 🔄 |
| **Phase 3** | 5 | 0 | 5 | 0% ⏳ |
| **Phase 4** | 5 | 0 | 5 | 0% ⏳ |
| **Total** | **25** | **12** | **13** | **48%** |

### Time Investment

| Phase | Estimated | Spent | Remaining |
|-------|-----------|-------|-----------|
| **Phase 0** | 8 hours | 2 hours | ✅ Done |
| **Phase 1** | 12 hours | 3 hours | ✅ Done |
| **Phase 2** | 20 hours | 5 hours | 15 hours |
| **Phase 3** | 20 hours | 0 hours | 20 hours |
| **Phase 4** | 32 hours | 0 hours | 32 hours |
| **Total** | **92 hours** | **10 hours** | **82 hours** |

---

## 🎯 Success Criteria

### Phase 2 Complete When:
- [x] Code duplication eliminated
- [x] Pre-commit hooks configured
- [x] Windows long paths supported
- [ ] Async pipeline implemented (3-5x faster)
- [ ] Resume support working
- [ ] Test coverage ≥85%

### Project Complete When:
- [ ] All security issues resolved ✅ (Phase 1 done)
- [ ] Performance optimized (Phase 2)
- [ ] Test coverage ≥85% (Phase 2)
- [ ] USB auto-detection working (Phase 3)
- [ ] CI/CD fully operational ✅ (Phase 1 done)
- [ ] Documentation comprehensive ✅ (Phase 1-2 done)

---

## 🛡️ Risk Management

### Potential Risks

1. **Async Complexity**
   - **Risk:** Async implementation bugs
   - **Mitigation:** Extensive testing, start simple
   - **Fallback:** Keep sync option available

2. **Resume State Corruption**
   - **Risk:** Partial state files cause errors
   - **Mitigation:** Atomic writes, checksums
   - **Fallback:** Detect corruption, restart download

3. **Test Coverage Difficulty**
   - **Risk:** Hard to test certain edge cases
   - **Mitigation:** Use mocking, fixtures
   - **Fallback:** Document untestable areas

4. **Breaking Changes**
   - **Risk:** New features break existing code
   - **Mitigation:** Regression tests after each change
   - **Fallback:** Git revert, fix forward

---

## 📋 Decision Log

### Key Decisions Made

1. **Async over Threading** (PERF-1)
   - **Reason:** Better I/O concurrency, simpler debugging
   - **Trade-off:** Slightly more complex code
   - **Status:** Planned

2. **JSON State Files** (PERF-2)
   - **Reason:** Human-readable, easy to debug
   - **Alternative:** SQLite (overkill for simple case)
   - **Status:** Planned

3. **85% Coverage Target** (TEST-1)
   - **Reason:** Balance between quality and effort
   - **Alternative:** 100% (diminishing returns)
   - **Status:** Planned

### Deferred Items

1. **Web UI** → Phase 4
   - **Reason:** Not critical for core functionality
   - **Revisit:** After Phase 3 complete

2. **Database Support** → Future
   - **Reason:** File-based state sufficient for now
   - **Revisit:** If users request tracking features

---

## 🔄 Iteration Plan

### After Each Phase

1. **Run regression tests**
   ```bash
   pytest tests/ --cov=yt2audi -v
   mypy src/yt2audi --strict
   ```

2. **Update metrics**
   - Test coverage %
   - Performance benchmarks
   - Code complexity

3. **Commit changes**
   - Detailed commit message
   -Conventional Commits format
   - Reference issues/PRs

4. **Update documentation**
   - CHANGELOG.md
   - This roadmap
   - Session summary

5. **Demo/Review**
   - Show improvements
   - Gather feedback
   - Adjust priorities

---

## 📞 Stakeholder Communication

### Status Updates

**Weekly (During Active Development):**
- Progress on current phase
- Blockers encountered
- Upcoming week's goals

**Monthly (Maintenance Mode):**
- Phase completion status
- Metrics update
- Roadmap adjustments

### Review Points

1. **After Phase 2** → Decide Phase 3 priority
2. **After Phase 3** → Evaluate Phase 4 necessity
3. **Every 3 months** → Reassess roadmap

---

## 🎓 Learning Objectives

### For Team/Contributors

- **Async Programming:** Learn `asyncio` patterns (Phase 2)
- **Testing Best Practices:** Achieve high coverage (Phase 2)
- **Performance Optimization:** Measure and improve (Phase 2-3)
- **API Design:** Build intuitive interfaces (Phase 3-4)
- **DevOps:** Master CI/CD workflows (Phase 1 ✅)

---

## 📚 Resources

### Documentation
- [Project Analysis](../c7a1ddec-425d-4cad-a6a2-f765a847781e/project_analysis.md)
- [Session Summaries](./SESSION_SUMMARY_2026-01-29.md)
- [CONTRIBUTING.md](../CONTRIBUTING.md)

### Tools
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [asyncio Guide](https://docs.python.org/3/library/asyncio.html)
- [pytest Coverage](https://pytest-cov.readthedocs.io/)

### References
- [Audi Q5 Specs](../Audi%20Q5%20(2019)%20Supported%20Media%20&%20Specifications.md)
- [Optimization Summary](../OPTIMIZATION_SUMMARY.md)

---

## ✅ Next Session Checklist

Before starting next session:

- [ ] Review this roadmap
- [ ] Check for any reported issues
- [ ] Ensure dev environment is up to date
- [ ] Run baseline tests to verify current state
- [ ] Choose next priority item (recommend: PERF-1)

---

**Roadmap Maintained By:** Development Team  
**Review Frequency:** After each phase completion  
**Last Review:** 2026-01-29  
**Next Review:** After Phase 2 complete
