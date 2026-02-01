"""Unit tests for validation utilities."""

import pytest
from yt2audi.utils.validation import (
    is_valid_url,
    is_youtube_url,
    is_playlist_url,
    validate_file_path,
    sanitize_path
)

class TestValidation:
    """Test suite for validation utilities."""

    def test_is_valid_url(self):
        """Test URL validation."""
        assert is_valid_url("https://google.com") is True
        assert is_valid_url("http://localhost:8080") is True
        assert is_valid_url("not a url") is False
        assert is_valid_url("") is False

    def test_is_youtube_url(self):
        """Test YouTube URL detection."""
        assert is_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") is True
        assert is_youtube_url("https://youtu.be/dQw4w9WgXcQ") is True
        assert is_youtube_url("https://www.youtube.com/playlist?list=PL123") is True
        assert is_youtube_url("https://google.com") is False

    def test_is_playlist_url(self):
        """Test playlist URL detection."""
        assert is_playlist_url("https://youtube.com/playlist?list=123") is True
        assert is_playlist_url("https://youtube.com/watch?v=123") is False

    def test_validate_file_path(self):
        """Test file path safety validation."""
        assert validate_file_path("safe/path.mp4") is True
        assert validate_file_path("../../dangerous") is False
        assert validate_file_path("path/\x00/null") is False

    def test_sanitize_path_success(self):
        """Test path sanitization with valid paths."""
        # Note: sanitize_path calls resolve(), so we should use relative paths
        # that actually exist or just check if it returns a string.
        path = "src/yt2audi"
        sanitized = sanitize_path(path)
        assert isinstance(sanitized, str)
        assert "yt2audi" in sanitized

    def test_sanitize_path_failures(self):
        """Test path sanitization with dangerous inputs."""
        with pytest.raises(ValueError, match="null bytes"):
            sanitize_path("path\x00")
            
        with pytest.raises(ValueError, match="dangerous shell metacharacter"):
            sanitize_path("path; rm -rf /")
            
        with pytest.raises(ValueError, match="reserved filename"):
            sanitize_path("C:/NUL")
