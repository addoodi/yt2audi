"""Unit tests for the HistoryManager class."""

from pathlib import Path
from unittest.mock import patch

import pytest
from yt2audi.core.history import HistoryManager

class TestHistoryManager:
    """Test suite for HistoryManager class."""

    def test_init_load(self, tmp_path):
        """Test history loading on initialization."""
        h_file = tmp_path / "history.txt"
        h_file.write_text("id1\nid2\n\n  id3  ")
        
        hm = HistoryManager(h_file)
        assert hm.is_processed("id1")
        assert hm.is_processed("id2")
        assert hm.is_processed("id3")
        assert not hm.is_processed("id4")

    def test_mark_completed(self, tmp_path):
        """Test marking a video as completed."""
        h_file = tmp_path / "history.txt"
        hm = HistoryManager(h_file)
        
        hm.mark_completed("new_id")
        assert hm.is_processed("new_id")
        
        # Verify it was appended to file
        content = h_file.read_text()
        assert "new_id" in content

    def test_clear(self, tmp_path):
        """Test clearing the history."""
        h_file = tmp_path / "history.txt"
        h_file.write_text("some_id")
        hm = HistoryManager(h_file)
        
        hm.clear()
        assert hm._processed_ids == set()
        assert not h_file.exists()

    @patch("yt2audi.core.history.get_config_dir")
    def test_default_path(self, mock_get_config, tmp_path):
        """Test default history file path."""
        mock_get_config.return_value = tmp_path
        hm = HistoryManager()
        assert hm.history_file == tmp_path / "history.txt"
