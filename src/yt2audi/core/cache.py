"""Metadata caching for YouTube video information."""

import json
import time
from pathlib import Path
from typing import Any, Optional

import structlog

from yt2audi.config import get_config_dir

logger = structlog.get_logger(__name__)


class MetadataCache:
    """Caches yt-dlp info dictionaries to avoid redundant network requests."""

    def __init__(self, cache_file: Optional[Path] = None, expiration_days: int = 7) -> None:
        """Initialize the cache.

        Args:
            cache_file: Path to the JSON cache file. Defaults to config_dir/cache/metadata.json.
            expiration_days: How many days before a cache entry is considered stale.
        """
        if cache_file is None:
            self.cache_dir = get_config_dir() / "cache"
            self.cache_file = self.cache_dir / "metadata.json"
        else:
            self.cache_file = cache_file
            self.cache_dir = self.cache_file.parent

        self.expiration_seconds = expiration_days * 24 * 60 * 60
        self._cache: dict[str, dict[str, Any]] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        """Load cache from disk."""
        if not self.cache_file.exists():
            self._cache = {}
            return

        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                self._cache = json.load(f)
            logger.debug("cache_loaded", entries=len(self._cache))
        except Exception as e:
            logger.warning("cache_load_failed", error=str(e))
            self._cache = {}

    def _save_cache(self) -> None:
        """Save cache to disk."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2)
            logger.debug("cache_saved", entries=len(self._cache))
        except Exception as e:
            logger.error("cache_save_failed", error=str(e))

    def get(self, url: str) -> Optional[dict[str, Any]]:
        """Get a cached entry if it exists and is not expired.

        Args:
            url: The video URL to look up.

        Returns:
            The info dictionary or None if not found or expired.
        """
        entry = self._cache.get(url)
        if not entry:
            return None

        # Check expiration
        cached_time = entry.get("_cached_at", 0)
        if time.time() - cached_time > self.expiration_seconds:
            logger.debug("cache_expired", url=url)
            del self._cache[url]
            return None

        logger.info("cache_hit", url=url)
        return entry.get("data")

    def set(self, url: str, info: dict[str, Any]) -> None:
        """Store an entry in the cache.

        Args:
            url: The video URL.
            info: The info dictionary from yt-dlp.
        """
        # We only store a subset of fields to keep cache size manageable
        # but enough for our prediction and metadata embedding
        essential_info = {
            "id": info.get("id"),
            "title": info.get("title"),
            "uploader": info.get("uploader"),
            "artist": info.get("artist"),
            "album": info.get("album"),
            "upload_date": info.get("upload_date"),
            "duration": info.get("duration"),
            "ext": info.get("ext"),
            # Add any other fields used by Converter.get_output_path or Converter.build_ffmpeg_command
        }
        
        self._cache[url] = {
            "data": info, # For now store full info as requested by Downloader.extract_info
            "_cached_at": time.time()
        }
        self._save_cache()

    def clear(self) -> None:
        """Clear the entire cache."""
        self._cache = {}
        if self.cache_file.exists():
            try:
                self.cache_file.unlink()
            except Exception:
                pass
        logger.info("cache_cleared")
