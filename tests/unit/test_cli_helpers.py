"""Unit tests for the CLI helper functions."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console
from yt2audi.cli.helpers import (
    BatchProgressManager,
    create_download_progress,
    create_convert_progress,
    process_single_video,
    print_header,
    print_summary,
)
from yt2audi.models.profile import Profile

@pytest.fixture
def mock_console():
    """Fixture for a mock console."""
    # Use real console for some tests as rich.Progress needs internal methods
    return Console(quiet=True)

class TestCLIHelpers:
    """Test suite for CLI helper functions."""

    def test_batch_progress_manager_callback(self, mock_console):
        """Test BatchProgressManager callback generation and updating."""
        manager = BatchProgressManager(mock_console)
        callback = manager.get_callback()
        
        # Simulate a progress update
        callback("https://youtube.com/watch?v=12345678", 50.0, "Testing")
        
        # Verify task was added and updated
        assert "https://youtube.com/watch?v=12345678" in manager.tasks
        
    def test_create_download_progress(self):
        """Test download progress creation."""
        progress, hook = create_download_progress()
        assert progress is not None
        assert callable(hook)
        
        # Test hook
        hook({"status": "downloading", "downloaded_bytes": 50, "total_bytes": 100})

    def test_create_convert_progress(self):
        """Test convert progress creation."""
        progress, hook = create_convert_progress()
        assert progress is not None
        assert callable(hook)
        
        # Test hook
        hook(50.0, "Converting")

    @patch("yt2audi.cli.helpers.HistoryManager")
    @patch("yt2audi.cli.helpers.USBManager")
    @patch("yt2audi.cli.helpers.Splitter.handle_size_exceed")
    def test_process_single_video_success(self, mock_split, mock_usb, mock_history_class, sample_profile, tmp_path):
        """Test full single video processing flow."""
        mock_history = mock_history_class.return_value
        mock_history.is_processed.return_value = False
        
        mock_dl = MagicMock()
        mock_dl.extract_info.return_value = {"id": "test_id", "title": "Test Title"}
        mock_dl.download_video.return_value = (tmp_path / "dl.mp4", {"id": "test_id"})
        
        mock_conv = MagicMock()
        mock_conv.get_output_path.return_value = tmp_path / "out.mp4"
        mock_conv.convert_video.return_value = tmp_path / "out.mp4"
        
        mock_split.return_value = [tmp_path / "out.mp4"]
        
        # DON'T touch the file yet, as we want to trigger the full flow
        out_file = tmp_path / "out.mp4"
        
        # But we need it to exist AFTER convert_video for stat() calls in handle_size_exceed or reporting
        def side_effect_convert(*args, **kwargs):
            out_file.touch()
            return out_file
        mock_conv.convert_video.side_effect = side_effect_convert
        
        with patch("yt2audi.cli.helpers.console") as mock_console:
            results = process_single_video(
                "url", sample_profile, tmp_path, mock_dl, mock_conv, show_progress=False
            )
            
            assert results == [out_file]
            mock_dl.download_video.assert_called_once()
            mock_conv.convert_video.assert_called_once()
            mock_history.mark_completed.assert_called_with("test_id")

    @patch("yt2audi.cli.helpers.HistoryManager")
    def test_process_single_video_skip_history(self, mock_history_class, sample_profile, tmp_path):
        """Test skipping video already in history."""
        mock_history = mock_history_class.return_value
        mock_history.is_processed.return_value = True
        
        mock_dl = MagicMock()
        mock_dl.extract_info.return_value = {"id": "old_id"}
        mock_conv = MagicMock()
        mock_conv.get_output_path.return_value = tmp_path / "already_done.mp4"
        
        with patch("yt2audi.cli.helpers.console"):
            results = process_single_video(
                "url", sample_profile, tmp_path, mock_dl, mock_conv, show_progress=False
            )
            assert len(results) == 1
            assert results[0].name == "already_done.mp4"
            mock_dl.download_video.assert_not_called()

    def test_print_header(self):
        """Test printing standardized header."""
        with patch("yt2audi.cli.helpers.console") as mock_console:
            print_header("Test Mode", "1.0", "My Profile", "Some extra info")
            assert mock_console.print.call_count >= 3

    def test_print_summary(self):
        """Test printing summary info."""
        with patch("yt2audi.cli.helpers.console") as mock_console:
            print_summary(10, 8, 2)
            assert mock_console.print.call_count >= 4
