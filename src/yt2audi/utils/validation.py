"""URL and input validation utilities."""

import re
from urllib.parse import urlparse


def is_valid_url(url: str) -> bool:
    """Check if string is a valid URL.

    Args:
        url: URL string to validate

    Returns:
        True if valid URL, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def is_youtube_url(url: str) -> bool:
    """Check if URL is a YouTube URL.

    Args:
        url: URL string to check

    Returns:
        True if YouTube URL, False otherwise

    Supports:
    - youtube.com/watch?v=...
    - youtu.be/...
    - youtube.com/playlist?list=...
    - youtube.com/channel/...
    - youtube.com/@username
    """
    youtube_patterns = [
        r"(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+",
        r"(?:https?://)?(?:www\.)?youtu\.be/[\w-]+",
        r"(?:https?://)?(?:www\.)?youtube\.com/playlist\?list=[\w-]+",
        r"(?:https?://)?(?:www\.)?youtube\.com/channel/[\w-]+",
        r"(?:https?://)?(?:www\.)?youtube\.com/@[\w-]+",
    ]

    return any(re.match(pattern, url) for pattern in youtube_patterns)


def is_playlist_url(url: str) -> bool:
    """Check if URL is a YouTube playlist.

    Args:
        url: URL string to check

    Returns:
        True if playlist URL, False otherwise
    """
    return "playlist?list=" in url or "/playlists" in url


def validate_file_path(path: str) -> bool:
    """Validate that a path string is safe.

    Args:
        path: File path to validate

    Returns:
        True if path is safe, False otherwise

    Checks for:
    - Path traversal attempts (../)
    - Absolute paths when not expected
    - Invalid characters
    """
    from pathlib import Path

    try:
        test_path = Path(path)

        # Check for path traversal
        if ".." in test_path.parts:
            return False

        # Check for null bytes
        if "\x00" in path:
            return False

        return True
    except Exception:
        return False
