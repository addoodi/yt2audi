"""Shared pytest fixtures for YT2Audi tests."""

import tempfile
from pathlib import Path
from typing import Generator

import pytest

from yt2audi.models.profile import (
    AudioConfig,
    DownloadConfig,
    LoggingConfig,
    OutputConfig,
    Profile,
    ProfileMeta,
    SubtitleConfig,
    TransferConfig,
    VideoConfig,
)


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files.

    Yields:
        Path to temporary directory that is cleaned up after test.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_video_path(temp_dir: Path) -> Path:
    """Create a sample video file for testing.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Path to a fake video file
    """
    video_path = temp_dir / "sample_video.mp4"
    # Create a small fake video file
    video_path.write_bytes(b"fake video data")
    return video_path


@pytest.fixture
def sample_profile() -> Profile:
    """Create a sample Audi Q5 profile for testing.

    Returns:
        A valid Profile instance with default Audi Q5 settings
    """
    return Profile(
        profile=ProfileMeta(
            name="Test Audi Q5",
            description="Test profile for Audi Q5",
            version="1.0.0",
        ),
        video=VideoConfig(
            max_width=720,
            max_height=576,
            maintain_aspect_ratio=True,
            codec="h264",
            profile="main",
            level="4.0",
            pixel_format="yuv420p",
            max_bitrate_mbps=2.0,
            max_fps=25,
            quality_cq=24,
            encoder_priority=["h264_nvenc", "h264_amf", "h264_qsv", "libx264"],
            extra_video_args=[],
        ),
        audio=AudioConfig(
            codec="aac",
            bitrate_kbps=128,
            sample_rate=44100,
            channels=2,
            extra_audio_args=[],
        ),
        subtitles=SubtitleConfig(
            embed=True,
            languages=["en"],
            auto_generate=False,
            burn_in=False,
        ),
        output=OutputConfig(
            container="mp4",
            faststart=True,
            output_dir="./output",
            filename_template="{title}_{id}.{ext}",
            max_file_size_gb=3.9,
            on_size_exceed="split",
            split_part_template="{stem}_part{num:03d}.{ext}",
            target_bitrate_reduction=0.8,
        ),
        transfer=TransferConfig(
            usb_auto_copy=False,
            usb_mount_path="",
            usb_subdir="",
            network_copy=False,
            network_path="",
            network_subdir="",
            verify_checksum=True,
            delete_after_transfer=False,
        ),
        download=DownloadConfig(
            format_preference="bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            download_archive="",
            rate_limit_mbps=None,
            retries=3,
            fragment_retries=10,
            playlist_start=1,
            playlist_end=None,
            playlist_reverse=False,
        ),
        logging=LoggingConfig(
            level="INFO",
            format="json",
            log_file="",
            rotation_size_mb=10,
            rotation_count=5,
        ),
    )


@pytest.fixture
def minimal_profile() -> Profile:
    """Create a minimal valid profile for testing.

    Returns:
        A Profile with minimal valid settings
    """
    return Profile(
        profile=ProfileMeta(
            name="Minimal Test Profile",
            description="Minimal profile for testing",
            version="1.0.0",
        ),
        video=VideoConfig(
            max_width=1280,
            max_height=720,
            maintain_aspect_ratio=True,
            codec="h264",
            profile="main",
            level="4.0",
            pixel_format="yuv420p",
            max_bitrate_mbps=5.0,
            max_fps=30,
            quality_cq=23,
            encoder_priority=["libx264"],
            extra_video_args=[],
        ),
        audio=AudioConfig(
            codec="aac",
            bitrate_kbps=128,
            sample_rate=44100,
            channels=2,
            extra_audio_args=[],
        ),
        subtitles=SubtitleConfig(
            embed=False,
            languages=[],
            auto_generate=False,
            burn_in=False,
        ),
        output=OutputConfig(
            container="mp4",
            faststart=True,
            output_dir="./output",
            filename_template="{title}.{ext}",
            max_file_size_gb=10.0,
            on_size_exceed="warn",
            split_part_template="{stem}_part{num:03d}.{ext}",
            target_bitrate_reduction=0.8,
        ),
        transfer=TransferConfig(
            usb_auto_copy=False,
            usb_mount_path="",
            usb_subdir="",
            network_copy=False,
            network_path="",
            network_subdir="",
            verify_checksum=False,
            delete_after_transfer=False,
        ),
        download=DownloadConfig(
            format_preference="best",
            download_archive="",
            rate_limit_mbps=None,
            retries=3,
            fragment_retries=10,
            playlist_start=1,
            playlist_end=None,
            playlist_reverse=False,
        ),
        logging=LoggingConfig(
            level="INFO",
            format="json",
            log_file="",
            rotation_size_mb=10,
            rotation_count=5,
        ),
    )


@pytest.fixture
def sample_youtube_url() -> str:
    """Return a sample YouTube URL for testing.

    Returns:
        A valid YouTube URL string
    """
    return "https://www.youtube.com/watch?v=jNQXAC9IVRw"


@pytest.fixture
def sample_playlist_url() -> str:
    """Return a sample YouTube playlist URL for testing.

    Returns:
        A valid YouTube playlist URL string
    """
    return "https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"


@pytest.fixture
def sample_urls_file(temp_dir: Path) -> Path:
    """Create a sample URLs file for batch testing.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Path to a file containing test URLs
    """
    urls_file = temp_dir / "urls.txt"
    urls_file.write_text(
        "https://www.youtube.com/watch?v=jNQXAC9IVRw\n"
        "https://www.youtube.com/watch?v=aqz-KE-bpKQ\n"
    )
    return urls_file
