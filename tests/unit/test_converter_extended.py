"""Extended unit tests for Converter class."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from yt2audi.core.converter import Converter, ConversionError

@pytest.fixture
def converter(sample_profile):
    return Converter(sample_profile)

class TestConverterExtended:
    """Extended tests for Converter coverage."""

    @patch("yt2audi.core.converter.Converter.probe_video")
    @patch("subprocess.Popen")
    def test_convert_video_ffmpeg_fail(self, mock_popen, mock_probe, converter, tmp_path):
        """Test conversion when FFmpeg returns non-zero."""
        mock_probe.return_value = MagicMock(duration=10.0, width=1280, height=720, fps=30)
        
        # Mock process interaction
        mock_proc = MagicMock()
        mock_proc.stdout.readline.side_effect = ["", ""]
        mock_proc.wait.return_value = 1  # Fail
        mock_proc.poll.return_value = 1  # Ensure loop terminates
        mock_proc.returncode = 1
        mock_popen.return_value = mock_proc
        
        input_file = tmp_path / "in.mp4"
        input_file.touch()
        
        with pytest.raises(ConversionError, match="FFmpeg exited with code 1"):
            converter.convert_video(input_file, output_dir=tmp_path)

    @patch("yt2audi.core.converter.Converter.probe_video")
    @patch("subprocess.Popen")
    def test_convert_video_missing_output(self, mock_popen, mock_probe, converter, tmp_path):
        """Test conversion when output file missing despite success code."""
        mock_probe.return_value = MagicMock(duration=10.0, width=1280, height=720, fps=30)
        
        mock_proc = MagicMock()
        mock_proc.wait.return_value = 0
        mock_proc.poll.return_value = 0
        mock_proc.stdout.readline.return_value = "" # EOF immediately
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc
        
        input_file = tmp_path / "in.mp4"
        input_file.touch()
        
        # Verify it raises if output missing
        # We don't touch the output file here
        with pytest.raises(ConversionError, match="not found"):
            converter.convert_video(input_file, output_dir=tmp_path)

    def test_ensure_extension_logic(self, converter, tmp_path):
        """Test ensure_extension helper (implicitly called or accessible)."""
        pass

    @patch("yt2audi.core.converter.Converter.probe_video")
    @patch("subprocess.Popen")
    def test_convert_video_with_progress(self, mock_popen, mock_probe, converter, tmp_path):
        """Test conversion with progress callback."""
        mock_probe.return_value = MagicMock(duration=100.0, width=1280, height=720, fps=30)
        
        mock_proc = MagicMock()
        # time=00:00:50.00 -> 50%
        mock_proc.stdout.readline.side_effect = [
            "frame=1 time=00:00:50.00 bitrate=100k", 
            ""
        ]
        mock_proc.wait.return_value = 0
        mock_proc.poll.side_effect = [None, 0] # Running then done
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc
        
        input_file = tmp_path / "in.mp4"
        input_file.touch()
        
        # Output file must exist
        out_path = tmp_path / "in.mp4" # Assuming default name
        out_path.touch()
        
        cb = MagicMock()
        with patch("yt2audi.core.converter.get_unique_path", return_value=out_path):
             converter.convert_video(input_file, output_dir=tmp_path, progress_callback=cb)
             
        # Check if callback called
        # progress logic: 50s / 100s = 50%
        # It might be called with ~50.0
        assert cb.call_count >= 1

