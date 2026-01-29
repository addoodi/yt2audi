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


def sanitize_path(path: str) -> str:
    """Sanitize a file path to prevent injection attacks.

    Args:
        path: File path to sanitize

    Returns:
        Sanitized path string

    Raises:
        ValueError: If path contains dangerous characters or patterns

    This function prevents:
    - Command injection via shell metacharacters
    - Path traversal attacks
    - Null byte injection
    - Dangerous filenames (e.g., '/dev/null', 'CON', 'NUL')
    """
    from pathlib import Path

    # Check for null bytes
    if "\x00" in path:
        raise ValueError(f"Path contains null bytes: {path}")

    # Check for shell metacharacters (command injection prevention)
    dangerous_chars = ['&', '|', ';', '$', '`', '\n', '\r', '<', '>']
    for char in dangerous_chars:
        if char in path:
            raise ValueError(
                f"Path contains dangerous shell metacharacter '{char}': {path}"
            )

    # Convert to Path object for normalization
    try:
        normalized_path = Path(path).resolve()
    except (ValueError, OSError) as e:
        raise ValueError(f"Invalid path: {path}") from e

    # Check for path traversal after normalization
    path_str = str(normalized_path)
    if ".." in Path(path_str).parts:
        raise ValueError(f"Path traversal detected: {path}")

    # Check for dangerous filenames (Windows reserved names)
    dangerous_names = {
        'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
        'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2',
        'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    path_parts = normalized_path.parts
    for part in path_parts:
        clean_part = part.upper().split('.')[0]  # Remove extension
        if clean_part in dangerous_names:
            raise ValueError(f"Path contains reserved filename: {part}")

    # Check for Unix special files
    unix_dangerous = {'/dev/null', '/dev/zero', '/dev/random'}
    if path_str in unix_dangerous:
        raise ValueError(f"Path is a dangerous Unix special file: {path_str}")

    return str(normalized_path)
