"""Unit tests for path utilities."""

import pytest
from pathlib import Path
from yt2audi.utils.paths import (
    sanitize_filename,
    get_temp_dir,
    ensure_extension,
    get_unique_path
)

class TestPaths:
    """Test suite for path utilities."""

    def test_sanitize_filename(self):
        """Test filename sanitization."""
        assert sanitize_filename("safe_name.mp4") == "safe_name.mp4"
        assert sanitize_filename("invalid/name:?*") == "invalidname"
        assert sanitize_filename("  spaces and dots.  ") == "spaces_and_dots"
        assert sanitize_filename("🚀 emoji 🚀") == "emoji"
        assert sanitize_filename("") == "video"

    def test_get_temp_dir(self):
        """Test getting temp directory."""
        temp_dir = get_temp_dir()
        assert isinstance(temp_dir, Path)
        assert temp_dir.name == "yt2audi"
        assert temp_dir.exists()

    def test_ensure_extension(self):
        """Test extension enforcement."""
        path = Path("video.mkv")
        assert ensure_extension(path, "mp4") == Path("video.mp4")
        assert ensure_extension(path, ".mp4") == Path("video.mp4")
        assert ensure_extension(Path("video.mp4"), "mp4") == Path("video.mp4")

    def test_get_unique_path(self, tmp_path):
        """Test unique path generation."""
        base_path = tmp_path / "video.mp4"
        
        # Doesn't exist yet
        assert get_unique_path(base_path) == base_path
        
        # Exists once
        base_path.touch()
        unique1 = get_unique_path(base_path)
        assert unique1 == tmp_path / "video_1.mp4"
        
        # Exists twice
        unique1.touch()
        assert get_unique_path(base_path) == tmp_path / "video_2.mp4"
