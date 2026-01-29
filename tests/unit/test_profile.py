"""Unit tests for Profile and related Pydantic models."""

import pytest
from pydantic import ValidationError

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


class TestVideoConfig:
    """Test suite for VideoConfig model."""

    def test_valid_video_config(self) -> None:
        """Test creating a valid VideoConfig."""
        config = VideoConfig(
            max_width=1920,
            max_height=1080,
            maintain_aspect_ratio=True,
            codec="h264",
            profile="high",
            level="4.1",
            pixel_format="yuv420p",
            max_bitrate_mbps=5.0,
            max_fps=60,
            quality_cq=23,
            encoder_priority=["h264_nvenc", "libx264"],
            extra_video_args=[],
        )
        assert config.max_width == 1920
        assert config.max_height == 1080
        assert config.codec == "h264"

    def test_max_width_must_be_positive(self) -> None:
        """Test that max_width must be > 0."""
        with pytest.raises(ValidationError) as exc_info:
            VideoConfig(
                max_width=0,  # Invalid
                max_height=1080,
                maintain_aspect_ratio=True,
                codec="h264",
                profile="main",
                level="4.0",
                pixel_format="yuv420p",
                max_bitrate_mbps=2.0,
                max_fps=30,
                quality_cq=24,
                encoder_priority=["libx264"],
                extra_video_args=[],
            )
        assert "max_width" in str(exc_info.value)

    def test_max_height_must_be_positive(self) -> None:
        """Test that max_height must be > 0."""
        with pytest.raises(ValidationError) as exc_info:
            VideoConfig(
                max_width=1920,
                max_height=-1,  # Invalid
                maintain_aspect_ratio=True,
                codec="h264",
                profile="main",
                level="4.0",
                pixel_format="yuv420p",
                max_bitrate_mbps=2.0,
                max_fps=30,
                quality_cq=24,
                encoder_priority=["libx264"],
                extra_video_args=[],
            )
        assert "max_height" in str(exc_info.value)

    def test_quality_cq_range(self) -> None:
        """Test that quality_cq is within valid range (0-51)."""
        # Valid range
        config = VideoConfig(
            max_width=1920,
            max_height=1080,
            maintain_aspect_ratio=True,
            codec="h264",
            profile="main",
            level="4.0",
            pixel_format="yuv420p",
            max_bitrate_mbps=2.0,
            max_fps=30,
            quality_cq=0,  # Min valid
            encoder_priority=["libx264"],
            extra_video_args=[],
        )
        assert config.quality_cq == 0

        config.quality_cq = 51  # Max valid
        assert config.quality_cq == 51

        # Invalid: too high
        with pytest.raises(ValidationError):
            VideoConfig(
                max_width=1920,
                max_height=1080,
                maintain_aspect_ratio=True,
                codec="h264",
                profile="main",
                level="4.0",
                pixel_format="yuv420p",
                max_bitrate_mbps=2.0,
                max_fps=30,
                quality_cq=52,  # Invalid
                encoder_priority=["libx264"],
                extra_video_args=[],
            )


class TestAudioConfig:
    """Test suite for AudioConfig model."""

    def test_valid_audio_config(self) -> None:
        """Test creating a valid AudioConfig."""
        config = AudioConfig(
            codec="aac",
            bitrate_kbps=192,
            sample_rate=48000,
            channels=2,
            extra_audio_args=[],
        )
        assert config.codec == "aac"
        assert config.bitrate_kbps == 192
        assert config.sample_rate == 48000
        assert config.channels == 2

    def test_bitrate_must_be_positive(self) -> None:
        """Test that bitrate_kbps must be > 0."""
        with pytest.raises(ValidationError):
            AudioConfig(
                codec="aac",
                bitrate_kbps=0,  # Invalid
                sample_rate=44100,
                channels=2,
                extra_audio_args=[],
            )

    def test_channels_must_be_positive(self) -> None:
        """Test that channels must be >= 1."""
        with pytest.raises(ValidationError):
            AudioConfig(
                codec="aac",
                bitrate_kbps=128,
                sample_rate=44100,
                channels=0,  # Invalid
                extra_audio_args=[],
            )


class TestOutputConfig:
    """Test suite for OutputConfig model."""

    def test_valid_output_config(self) -> None:
        """Test creating a valid OutputConfig."""
        config = OutputConfig(
            container="mp4",
            faststart=True,
            output_dir="./output",
            filename_template="{title}_{id}.{ext}",
            max_file_size_gb=3.9,
            on_size_exceed="split",
            split_part_template="{stem}_part{num:03d}.{ext}",
            target_bitrate_reduction=0.8,
        )
        assert config.container == "mp4"
        assert config.max_file_size_gb == 3.9
        assert config.on_size_exceed == "split"

    def test_max_file_size_must_be_positive(self) -> None:
        """Test that max_file_size_gb must be > 0."""
        with pytest.raises(ValidationError):
            OutputConfig(
                container="mp4",
                faststart=True,
                output_dir="./output",
                filename_template="{title}.{ext}",
                max_file_size_gb=0,  # Invalid
                on_size_exceed="split",
                split_part_template="{stem}_part{num:03d}.{ext}",
                target_bitrate_reduction=0.8,
            )

    def test_on_size_exceed_validation(self) -> None:
        """Test that on_size_exceed only accepts valid values."""
        # Valid values
        for action in ["split", "compress", "warn", "skip"]:
            config = OutputConfig(
                container="mp4",
                faststart=True,
                output_dir="./output",
                filename_template="{title}.{ext}",
                max_file_size_gb=3.9,
                on_size_exceed=action,
                split_part_template="{stem}_part{num:03d}.{ext}",
                target_bitrate_reduction=0.8,
            )
            assert config.on_size_exceed == action

    def test_target_bitrate_reduction_range(self) -> None:
        """Test that target_bitrate_reduction is between 0 and 1."""
        # Valid
        config = OutputConfig(
            container="mp4",
            faststart=True,
            output_dir="./output",
            filename_template="{title}.{ext}",
            max_file_size_gb=3.9,
            on_size_exceed="compress",
            split_part_template="{stem}_part{num:03d}.{ext}",
            target_bitrate_reduction=0.5,
        )
        assert config.target_bitrate_reduction == 0.5

        # Invalid: > 1
        with pytest.raises(ValidationError):
            OutputConfig(
                container="mp4",
                faststart=True,
                output_dir="./output",
                filename_template="{title}.{ext}",
                max_file_size_gb=3.9,
                on_size_exceed="compress",
                split_part_template="{stem}_part{num:03d}.{ext}",
                target_bitrate_reduction=1.5,  # Invalid
            )


class TestProfile:
    """Test suite for complete Profile model."""

    def test_valid_profile_from_fixture(self, sample_profile: Profile) -> None:
        """Test that fixture profile is valid."""
        assert sample_profile.profile.name == "Test Audi Q5"
        assert sample_profile.video.max_width == 720
        assert sample_profile.video.max_height == 576
        assert sample_profile.audio.bitrate_kbps == 128
        assert sample_profile.output.max_file_size_gb == 3.9

    def test_profile_with_minimal_config(self, minimal_profile: Profile) -> None:
        """Test profile with minimal configuration."""
        assert minimal_profile.profile.name == "Minimal Test Profile"
        assert minimal_profile.video.encoder_priority == ["libx264"]
        assert minimal_profile.subtitles.embed is False

    def test_profile_serialization(self, sample_profile: Profile) -> None:
        """Test that profile can be serialized to dict."""
        profile_dict = sample_profile.model_dump()
        assert "profile" in profile_dict
        assert "video" in profile_dict
        assert "audio" in profile_dict
        assert profile_dict["video"]["max_width"] == 720

    def test_profile_from_dict(self, sample_profile: Profile) -> None:
        """Test creating profile from dictionary."""
        profile_dict = sample_profile.model_dump()
        new_profile = Profile(**profile_dict)
        assert new_profile.profile.name == sample_profile.profile.name
        assert new_profile.video.max_width == sample_profile.video.max_width


class TestDownloadConfig:
    """Test suite for DownloadConfig model."""

    def test_valid_download_config(self) -> None:
        """Test creating a valid DownloadConfig."""
        config = DownloadConfig(
            format_preference="best",
            download_archive="~/.config/yt2audi/archive.txt",
            rate_limit_mbps=10.0,
            retries=3,
            fragment_retries=10,
            playlist_start=1,
            playlist_end=None,
            playlist_reverse=False,
        )
        assert config.retries == 3
        assert config.rate_limit_mbps == 10.0

    def test_retries_must_be_positive(self) -> None:
        """Test that retries must be >= 0."""
        with pytest.raises(ValidationError):
            DownloadConfig(
                format_preference="best",
                download_archive=None,
                rate_limit_mbps=None,
                retries=-1,  # Invalid
                fragment_retries=10,
                playlist_start=1,
                playlist_end=None,
                playlist_reverse=False,
            )

    def test_playlist_start_must_be_positive(self) -> None:
        """Test that playlist_start must be >= 1."""
        with pytest.raises(ValidationError):
            DownloadConfig(
                format_preference="best",
                download_archive=None,
                rate_limit_mbps=None,
                retries=3,
                fragment_retries=10,
                playlist_start=0,  # Invalid
                playlist_end=None,
                playlist_reverse=False,
            )
