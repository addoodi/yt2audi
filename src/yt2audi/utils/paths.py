"""Path utilities."""

import re
import tempfile
from pathlib import Path


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """Sanitize filename to remove problematic characters.

    Args:
        filename: Original filename
        max_length: Maximum filename length

    Returns:
        Sanitized filename safe for all platforms

    Removes:
    - Invalid characters (< > : " / \\ | ? *)
    - Emojis and non-ASCII characters
    - Leading/trailing dots and spaces
    """
    # Remove emojis and non-ASCII characters
    filename = filename.encode("ascii", "ignore").decode("ascii")

    # Remove invalid characters for Windows/Unix
    filename = re.sub(r'[<>:"/\\|?*]', "", filename)

    # Replace multiple spaces with single space
    filename = re.sub(r"\s+", " ", filename)

    # Remove leading/trailing dots and spaces
    filename = filename.strip(". ")

    # Truncate if too long (leave room for extension)
    if len(filename) > max_length:
        filename = filename[: max_length - 10]

    # If empty after sanitization, use a default
    if not filename:
        filename = "video"

    return filename


def get_temp_dir() -> Path:
    """Get temporary directory for downloads.

    Returns:
        Path to temp directory
    """
    temp_dir = Path(tempfile.gettempdir()) / "yt2audi"
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def ensure_extension(path: Path, extension: str) -> Path:
    """Ensure path has the correct extension.

    Args:
        path: Original path
        extension: Desired extension (with or without dot)

    Returns:
        Path with correct extension
    """
    if not extension.startswith("."):
        extension = f".{extension}"

    if path.suffix.lower() != extension.lower():
        return path.with_suffix(extension)

    return path


def get_unique_path(path: Path) -> Path:
    """Get a unique path by appending number if file exists.

    Args:
        path: Desired path

    Returns:
        Unique path (may be same as input if doesn't exist)

    Example:
        video.mp4 → video.mp4 (if doesn't exist)
        video.mp4 → video_1.mp4 (if exists)
        video.mp4 → video_2.mp4 (if video_1.mp4 also exists)
    """
    if not path.exists():
        return path

    counter = 1
    while True:
        new_path = path.with_stem(f"{path.stem}_{counter}")
        if not new_path.exists():
            return new_path
        counter += 1
