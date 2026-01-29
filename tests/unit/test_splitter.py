"""Unit tests for video file splitter."""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from yt2audi.core.splitter import Splitter
from yt2audi.exceptions import ConversionError
from yt2audi.models.profile import OnSizeExceed


class TestGetFileSize:
    """Test suite for get_file_size_gb method."""

    def test_get_file_size_existing_file(self, temp_dir: Path) -> None:
        """Test getting size of existing file."""
        test_file = temp_dir / "test.mp4"
        # Create a 1MB file
        test_file.write_bytes(b"x" * (1024 * 1024))

        size_gb = Splitter.get_file_size_gb(test_file)

        assert 0.0009 < size_gb < 0.0011  # ~0.001 GB

    def test_get_file_size_nonexistent_file(self, temp_dir: Path) -> None:
        """Test getting size of non-existent file."""
        test_file = temp_dir / "nonexistent.mp4"

        size_gb = Splitter.get_file_size_gb(test_file)

        assert size_gb == 0.0


class TestSplitVideo:
    """Test suite for split_video method."""

    def test_split_not_needed_file_under_limit(self, sample_video_path: Path) -> None:
        """Test that files under size limit are not split."""
        # File is small (< 1GB)
        result = Splitter.split_video(
            input_path=sample_video_path,
            max_size_gb=1.0,
        )

        assert len(result) == 1
        assert result[0] == sample_video_path

    def test_split_input_file_not_found(self, temp_dir: Path) -> None:
        """Test splitting non-existent file raises error."""
        nonexistent = temp_dir / "nonexistent.mp4"

        with pytest.raises(ConversionError, match="Input file not found"):
            Splitter.split_video(nonexistent, max_size_gb=1.0)

    @patch("subprocess.run")
    def test_split_video_success(
        self,
        mock_run: Mock,
        sample_video_path: Path,
        temp_dir: Path,
    ) -> None:
        """Test successful video splitting."""
        # Make file appear large
        with patch.object(Splitter, "get_file_size_gb", return_value=5.0):
            # Mock ffmpeg success
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            # Create fake output files that FFmpeg would create
            part1 = temp_dir / "sample_video_part001.mp4"
            part2 = temp_dir / "sample_video_part002.mp4"
            part1.write_bytes(b"part1")
            part2.write_bytes(b"part2")

            result = Splitter.split_video(
                input_path=sample_video_path,
                max_size_gb=2.0,
                output_dir=temp_dir,
            )

            # Should find the created parts
            assert len(result) == 2
            assert part1 in result
            assert part2 in result
            mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_split_video_ffmpeg_failure(
        self,
        mock_run: Mock,
        sample_video_path: Path,
    ) -> None:
        """Test handling of FFmpeg failure during split."""
        # Make file appear large
        with patch.object(Splitter, "get_file_size_gb", return_value=5.0):
            # Mock ffmpeg failure
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=1,
                cmd=["ffmpeg"],
                stderr="FFmpeg error",
            )

            with pytest.raises(ConversionError, match="FFmpeg splitting failed"):
                Splitter.split_video(sample_video_path, max_size_gb=2.0)

    @patch("subprocess.run")
    def test_split_video_no_output_files(
        self,
        mock_run: Mock,
        sample_video_path: Path,
        temp_dir: Path,
    ) -> None:
        """Test error when no output files are created."""
        # Make file appear large
        with patch.object(Splitter, "get_file_size_gb", return_value=5.0):
            # Mock ffmpeg success but don't create files
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            with pytest.raises(ConversionError, match="no output files found"):
                Splitter.split_video(
                    sample_video_path,
                    max_size_gb=2.0,
                    output_dir=temp_dir,
                )


class TestCompressToSize:
    """Test suite for compress_to_size method."""

    def test_compress_input_not_found(self, temp_dir: Path) -> None:
        """Test compressing non-existent file raises error."""
        nonexistent = temp_dir / "nonexistent.mp4"

        with pytest.raises(ConversionError, match="Input file not found"):
            Splitter.compress_to_size(nonexistent, target_size_gb=1.0)

    @patch("subprocess.run")
    def test_compress_to_size_success(
        self,
        mock_run: Mock,
        sample_video_path: Path,
        temp_dir: Path,
    ) -> None:
        """Test successful video compression."""
        output_path = temp_dir / "compressed.mp4"

        # Mock ffprobe (duration query)
        def run_side_effect(cmd, *args, **kwargs):
            if "ffprobe" in cmd[0]:
                return Mock(returncode=0, stdout="600.0", stderr="")
            # ffmpeg (compression)
            else:
                # Create output file
                output_path.write_bytes(b"compressed video")
                return Mock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = run_side_effect

        result = Splitter.compress_to_size(
            input_path=sample_video_path,
            target_size_gb=2.0,
            reduction_factor=0.8,
            output_path=output_path,
        )

        assert result == output_path
        assert output_path.exists()
        assert mock_run.call_count == 2  # ffprobe + ffmpeg

    @patch("subprocess.run")
    def test_compress_ffprobe_failure(
        self,
        mock_run: Mock,
        sample_video_path: Path,
    ) -> None:
        """Test handling of ffprobe failure."""
        # Mock ffprobe failure
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["ffprobe"],
            stderr="ffprobe error",
        )

        with pytest.raises(ConversionError):
            Splitter.compress_to_size(sample_video_path, target_size_gb=2.0)

    @patch("subprocess.run")
    def test_compress_ffmpeg_failure(
        self,
        mock_run: Mock,
        sample_video_path: Path,
    ) -> None:
        """Test handling of FFmpeg failure during compression."""

        def run_side_effect(cmd, *args, **kwargs):
            if "ffprobe" in cmd[0]:
                return Mock(returncode=0, stdout="600.0", stderr="")
            else:
                raise subprocess.CalledProcessError(
                    returncode=1,
                    cmd=["ffmpeg"],
                    stderr="FFmpeg compression error",
                )

        mock_run.side_effect = run_side_effect

        with pytest.raises(ConversionError, match="FFmpeg compression failed"):
            Splitter.compress_to_size(sample_video_path, target_size_gb=2.0)

    @patch("subprocess.run")
    def test_compress_no_output_file(
        self,
        mock_run: Mock,
        sample_video_path: Path,
    ) -> None:
        """Test error when compression doesn't create output file."""

        def run_side_effect(cmd, *args, **kwargs):
            if "ffprobe" in cmd[0]:
                return Mock(returncode=0, stdout="600.0", stderr="")
            else:
                # Don't create output file
                return Mock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = run_side_effect

        with pytest.raises(ConversionError, match="output file not found"):
            Splitter.compress_to_size(sample_video_path, target_size_gb=2.0)


class TestHandleSizeExceed:
    """Test suite for handle_size_exceed method."""

    def test_handle_size_not_exceeded(self, sample_video_path: Path) -> None:
        """Test when file size is within limit."""
        # File is small
        result = Splitter.handle_size_exceed(
            input_path=sample_video_path,
            max_size_gb=10.0,
            action=OnSizeExceed.SPLIT,
        )

        assert len(result) == 1
        assert result[0] == sample_video_path

    @patch.object(Splitter, "split_video")
    def test_handle_size_exceed_split_action(
        self,
        mock_split: Mock,
        sample_video_path: Path,
        temp_dir: Path,
    ) -> None:
        """Test split action when size exceeded."""
        # Make file appear large
        with patch.object(Splitter, "get_file_size_gb", return_value=5.0):
            part1 = temp_dir / "part1.mp4"
            part2 = temp_dir / "part2.mp4"
            mock_split.return_value = [part1, part2]

            result = Splitter.handle_size_exceed(
                input_path=sample_video_path,
                max_size_gb=2.0,
                action=OnSizeExceed.SPLIT,
                output_dir=temp_dir,
            )

            assert result == [part1, part2]
            mock_split.assert_called_once_with(sample_video_path, 2.0, temp_dir)

    @patch.object(Splitter, "compress_to_size")
    def test_handle_size_exceed_compress_action(
        self,
        mock_compress: Mock,
        sample_video_path: Path,
        temp_dir: Path,
    ) -> None:
        """Test compress action when size exceeded."""
        # Make file appear large
        with patch.object(Splitter, "get_file_size_gb", return_value=5.0):
            compressed = temp_dir / "sample_video_compressed.mp4"
            mock_compress.return_value = compressed

            result = Splitter.handle_size_exceed(
                input_path=sample_video_path,
                max_size_gb=2.0,
                action=OnSizeExceed.COMPRESS,
                output_dir=temp_dir,
            )

            assert result == [compressed]
            mock_compress.assert_called_once()

    def test_handle_size_exceed_warn_action(self, sample_video_path: Path) -> None:
        """Test warn action when size exceeded."""
        # Make file appear large
        with patch.object(Splitter, "get_file_size_gb", return_value=5.0):
            result = Splitter.handle_size_exceed(
                input_path=sample_video_path,
                max_size_gb=2.0,
                action=OnSizeExceed.WARN,
            )

            # Should return original file despite size
            assert result == [sample_video_path]

    def test_handle_size_exceed_skip_action(self, sample_video_path: Path) -> None:
        """Test skip action when size exceeded."""
        # Make file appear large
        with patch.object(Splitter, "get_file_size_gb", return_value=5.0):
            result = Splitter.handle_size_exceed(
                input_path=sample_video_path,
                max_size_gb=2.0,
                action=OnSizeExceed.SKIP,
            )

            # Should return empty list
            assert result == []
