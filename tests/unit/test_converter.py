"""Unit tests for the Converter class."""

import asyncio
import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

import pytest
from yt2audi.core.converter import Converter, VideoMetadata
from yt2audi.exceptions import ConversionError

@pytest.fixture
def mock_profile(sample_profile):
    """Fixture for a mock profile."""
    return sample_profile

@pytest.fixture
def converter(mock_profile):
    """Fixture for Converter instance."""
    return Converter(mock_profile)

class TestVideoMetadata:
    """Test suite for VideoMetadata class."""

    def test_metadata_parsing(self):
        """Test parsing FFprobe JSON data."""
        data = {
            "format": {"duration": "60.5", "bit_rate": "1000000", "size": "1048576"},
            "streams": [
                {
                    "codec_type": "video",
                    "width": 1280,
                    "height": 720,
                    "r_frame_rate": "30/1",
                    "codec_name": "h264"
                },
                {
                    "codec_type": "audio",
                    "codec_name": "aac"
                }
            ]
        }
        meta = VideoMetadata(data)
        assert meta.duration == 60.5
        assert meta.bitrate == 1000000
        assert meta.width == 1280
        assert meta.height == 720
        assert meta.fps == 30.0
        assert meta.codec_name == "h264"

    def test_metadata_empty_data(self):
        """Test metadata with missing fields."""
        meta = VideoMetadata({})
        assert meta.duration == 0
        assert meta.width == 0
        assert meta.fps == 0

class TestConverter:
    """Test suite for Converter class."""

    @patch("subprocess.run")
    def test_probe_video_success(self, mock_run, converter, tmp_path):
        """Test successful video probing."""
        input_file = tmp_path / "input.mp4"
        input_file.touch()
        
        mock_stdout = json.dumps({
            "format": {"duration": "10"},
            "streams": [{"codec_type": "video", "width": 100, "height": 100}]
        })
        mock_run.return_value = MagicMock(stdout=mock_stdout, returncode=0)
        
        meta = converter.probe_video(input_file)
        assert meta.duration == 10.0
        assert meta.width == 100

    def test_probe_video_not_found(self, converter):
        """Test probing non-existent file."""
        with pytest.raises(ConversionError, match="Input file not found"):
            converter.probe_video(Path("non_existent.mp4"))

    @patch("subprocess.run")
    def test_probe_video_error(self, mock_run, converter, tmp_path):
        """Test handling of FFprobe error."""
        input_file = tmp_path / "input.mp4"
        input_file.touch()
        mock_run.side_effect = subprocess.CalledProcessError(1, "ffprobe", stderr="Error detail")
        with pytest.raises(ConversionError, match="FFprobe failed"):
            converter.probe_video(input_file)

    def test_get_output_path_template(self, converter, tmp_path):
        """Test output path generation with templates."""
        info = {"title": "My Video", "id": "123", "uploader": "Me"}
        out_dir = tmp_path / "out"
        
        out_dir = tmp_path / "out"
        
        # Determine behavior with standard template
        converter.output_config.filename_template = "{title}.{ext}"
        path = converter.get_output_path(info, out_dir)
        assert path == out_dir / "My_Video.mp4"
        
        # Test with custom template in profile
        converter.output_config.filename_template = "{uploader} - {title} [{id}].{ext}"
        path = converter.get_output_path(info, out_dir)
        # Sanitization applies to components, but template structure (spaces) is preserved
        assert path == out_dir / "Me - My_Video [123].mp4"

    def test_get_output_path_template_error(self, converter, tmp_path):
        """Test fallback when template is invalid."""
        info = {"title": "Safe"}
        converter.output_config.filename_template = "{bad_key}.mp4"
        path = converter.get_output_path(info, tmp_path)
        # Should fallback to f"{title}_{id}.{ext}" or similar
        assert "Safe" in path.name

    def test_build_ffmpeg_command_with_thumbnail(self, converter):
        """Test FFmpeg command with thumbnail inclusion."""
        meta = MagicMock(width=1920, height=1080, fps=30)
        thumb = Path("cover.jpg")
        with patch.object(Path, "exists", return_value=True):
            cmd = converter.build_ffmpeg_command(Path("in.mp4"), Path("out.mp4"), meta, thumbnail_path=thumb)
            assert str(thumb) in cmd
            assert "attached_pic" in cmd

    @patch("subprocess.Popen")
    @patch("yt2audi.core.converter.Converter.probe_video")
    def test_convert_video_sync_success(self, mock_probe, mock_popen, converter, tmp_path):
        """Test successful sync conversion."""
        input_file = tmp_path / "input.mp4"
        input_file.touch()
        
        mock_probe.return_value = MagicMock(duration=10.0, width=1920, height=1080, fps=30)
        
        # Setup mock process
        mock_proc = MagicMock()
        # Simulate some progress lines and then EOF
        mock_proc.stdout.readline.side_effect = ["frame=1 time=00:00:05.00", "frame=2 time=00:00:10.00", ""]
        mock_proc.wait.return_value = 0
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc
        
        output_dir = tmp_path / "out"
        output_dir.mkdir()
        output_path = output_dir / "input.mp4"
        
        with patch("yt2audi.core.converter.get_unique_path", return_value=output_path):
            with patch("yt2audi.core.converter.ensure_extension", return_value=output_path):
                output_path.touch()
                result = converter.convert_video(input_file, output_dir=output_dir)
                assert result == output_path

    @pytest.mark.asyncio
    @patch("asyncio.create_subprocess_exec")
    @patch("yt2audi.core.converter.Converter.probe_video_async")
    async def test_convert_video_async_success(self, mock_probe, mock_exec, converter, tmp_path):
        """Test successful async conversion."""
        input_file = tmp_path / "input.mp4"
        input_file.touch()
        
        mock_probe.return_value = MagicMock(duration=10.0, width=1920, height=1080, fps=30)
        
        # Mock async process
        mock_proc = MagicMock()
        mock_proc.stdout = MagicMock()
        mock_proc.stdout.read = AsyncMock(side_effect=[b"frame=1 time=00:00:05.00", b""])
        mock_proc.wait = AsyncMock(return_value=0)
        mock_exec.return_value = mock_proc

        output_dir = tmp_path / "out"
        output_dir.mkdir()
        output_path = output_dir / "input.mp4"
        
        with patch("yt2audi.core.converter.get_unique_path", return_value=output_path):
            with patch("yt2audi.core.converter.ensure_extension", return_value=output_path):
                output_path.touch()
                result = await converter.convert_video_async(input_file, output_dir=output_dir)
                assert result == output_path

    def test_estimate_output_size(self, converter):
        """Test size estimation."""
        with patch.object(converter, "probe_video") as mock_probe:
            mock_probe.return_value = MagicMock(duration=3600, bitrate=1000000)
            size_gb = converter.estimate_output_size(Path("test.mp4"))
            assert size_gb > 0
            assert isinstance(size_gb, float)

    def test_estimate_output_size_fail(self, converter):
        """Test size estimation when probing fails."""
        with patch.object(converter, "probe_video", side_effect=Exception("Fail")):
            # It re-raises the exception (likely ConversionError wrapping it)
            with pytest.raises(Exception):
                converter.estimate_output_size(Path("test.mp4"))
