"""Extended unit tests for CLI helpers."""

import pytest
from unittest.mock import MagicMock, patch
from rich.console import Console
from pathlib import Path
from yt2audi.cli.helpers import process_single_video

class TestCLIHelpersExtended:
    """Extended tests for CLI helpers coverage."""

    @patch("yt2audi.cli.helpers.HistoryManager")
    @patch("yt2audi.cli.helpers.USBManager")
    @patch("yt2audi.cli.helpers.Splitter.handle_size_exceed")
    def test_process_single_video_with_progress(self, mock_split, mock_usb, mock_history_class, sample_profile, tmp_path):
        """Test process_single_video with progress bar enabled."""
        mock_history = mock_history_class.return_value
        mock_history.is_processed.return_value = False
        
        mock_dl = MagicMock()
        mock_dl.extract_info.return_value = {"id": "test_id", "title": "Test Title"}
        mock_dl.download_video.return_value = (tmp_path / "dl.mp4", {"id": "test_id"})
        
        mock_conv = MagicMock()
        mock_conv.get_output_path.return_value = tmp_path / "out.mp4"
        mock_conv.convert_video.return_value = tmp_path / "out.mp4"
        
        mock_split.return_value = [tmp_path / "out.mp4"]
        
        # Ensure output exists
        (tmp_path / "out.mp4").touch()
        
        # Use real console or mock that supports 'status'
        with patch("yt2audi.cli.helpers.console") as mock_console:
            results = process_single_video(
                "url", sample_profile, tmp_path, mock_dl, mock_conv, show_progress=True
            )
            assert results == [tmp_path / "out.mp4"]
            # verify progress contexts were used
            # This is hard to assert with mocks on 'with progress:', but if code ran without error it's good

    @patch("yt2audi.cli.helpers.HistoryManager")
    def test_process_single_video_existing_file(self, mock_history_class, sample_profile, tmp_path):
        """Test valid file on disk skips processing."""
        mock_history = mock_history_class.return_value
        mock_history.is_processed.return_value = False
        
        mock_dl = MagicMock()
        # Returns info
        mock_dl.extract_info.return_value = {"id": "test_id"}
        
        mock_conv = MagicMock()
        # Path exists!
        existing_file = tmp_path / "existing.mp4"
        existing_file.touch()
        mock_conv.get_output_path.return_value = existing_file
        
        with patch("yt2audi.cli.helpers.console"):
            results = process_single_video(
                "url", sample_profile, tmp_path, mock_dl, mock_conv, show_progress=False
            )
            
        assert len(results) == 1
        assert results[0] == existing_file
        mock_dl.download_video.assert_not_called()
        mock_history.mark_completed.assert_called()

    def test_process_single_video_usb_copy(self, sample_profile, tmp_path):
        """Test USB copy logic."""
        sample_profile.transfer.usb_auto_copy = True
        
        mock_conv = MagicMock()
        mock_conv.get_output_path.return_value = tmp_path / "out.mp4"
        mock_dl = MagicMock()
        mock_dl.extract_info.return_value = {"id": "1"}
        mock_dl.download_video.return_value = (tmp_path / "dl.mp4", {})
        
        with patch("yt2audi.cli.helpers.HistoryManager") as MockHistory, \
             patch("yt2audi.cli.helpers.USBManager") as MockUSB, \
             patch("yt2audi.cli.helpers.Splitter.handle_size_exceed") as mock_split, \
             patch("yt2audi.cli.helpers.console") as mock_console:
            
            mock_split.return_value = [tmp_path / "out.mp4"]
            
            MockUSB.find_best_drive.return_value = Path("E:/")
            MockUSB.copy_to_usb.return_value = [Path("E:/Test/out.mp4")]
            
            MockHistory.return_value.is_processed.return_value = False
            
            results = process_single_video(
                "url", sample_profile, tmp_path, mock_dl, mock_conv, show_progress=False
            )
            
            MockUSB.find_best_drive.assert_called()
            MockUSB.copy_to_usb.assert_called()
            
            assert "E:" in str(results[0])
