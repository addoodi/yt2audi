"""History tracking for completed video processing."""

import os
from pathlib import Path
from typing import Set

import structlog

from yt2audi.config import get_config_dir

logger = structlog.get_logger(__name__)


class HistoryManager:
    """Tracks successfully processed videos to avoid re-processing."""

    def __init__(self, history_file: Path | None = None) -> None:
        """Initialize the history manager.

        Args:
            history_file: Path to the history text file. 
                         Defaults to config_dir/history.txt.
        """
        if history_file is None:
            self.history_file = get_config_dir() / "history.txt"
        else:
            self.history_file = history_file

        self._processed_ids: Set[str] = set()
        self._load_history()

    def _load_history(self) -> None:
        """Load history from disk."""
        if not self.history_file.exists():
            return

        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                self._processed_ids = {line.strip() for line in f if line.strip()}
            logger.debug("history_loaded", entries=len(self._processed_ids))
        except Exception as e:
            logger.warning("history_load_failed", error=str(e))

    def _save_id(self, video_id: str) -> None:
        """Append a single ID to history disk file."""
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.history_file, "a", encoding="utf-8") as f:
                f.write(f"{video_id}\n")
        except Exception as e:
            logger.error("history_save_failed", id=video_id, error=str(e))

    def is_processed(self, video_id: str) -> bool:
        """Check if a video ID has been successfully processed.

        Args:
            video_id: YouTube video ID.

        Returns:
            True if processed, False otherwise.
        """
        return video_id in self._processed_ids

    def mark_completed(self, video_id: str) -> None:
        """Mark a video as successfully processed.

        Args:
            video_id: YouTube video ID.
        """
        if video_id not in self._processed_ids:
            self._processed_ids.add(video_id)
            self._save_id(video_id)
            logger.info("history_updated", id=video_id)

    def clear(self) -> None:
        """Clear the entire history."""
        self._processed_ids.clear()
        if self.history_file.exists():
            try:
                self.history_file.unlink()
            except Exception:
                pass
        logger.info("history_cleared")
