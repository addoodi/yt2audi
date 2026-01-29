"""Pydantic models for profile configuration."""

from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class EncoderType(str, Enum):
    """Video encoder types."""

    NVENC_H264 = "h264_nvenc"
    AMF_H264 = "h264_amf"
    QSV_H264 = "h264_qsv"
    LIBX264 = "libx264"


class OnSizeExceed(str, Enum):
    """Actions to take when file exceeds max size."""

    SPLIT = "split"
    COMPRESS = "compress"
    WARN = "warn"
    SKIP = "skip"


class LogLevel(str, Enum):
    """Logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class LogFormat(str, Enum):
    """Log output formats."""

    JSON = "json"
    CONSOLE = "console"


class ProfileMeta(BaseModel):
    """Profile metadata."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    version: str = Field(default="1.0.0", pattern=r"^\d+\.\d+\.\d+$")


class VideoConfig(BaseModel):
    """Video encoding configuration."""

    # Resolution constraints
    max_width: int = Field(default=720, ge=1, le=3840)
    max_height: int = Field(default=540, ge=1, le=2160)
    maintain_aspect_ratio: bool = Field(default=True)

    # Codec settings
    codec: Literal["h264", "h265", "av1"] = Field(default="h264")
    profile: Literal["baseline", "main", "high"] = Field(default="main")
    level: str = Field(default="4.0", pattern=r"^\d+\.\d+$")
    pixel_format: str = Field(default="yuv420p")

    # Quality settings
    max_bitrate_mbps: str | float = Field(default="auto")
    max_fps: int = Field(default=25, ge=1, le=120)
    quality_cq: int = Field(default=24, ge=0, le=51)

    # Encoder preference (ordered fallback)
    encoder_priority: list[EncoderType] = Field(
        default=[
            EncoderType.NVENC_H264,
            EncoderType.AMF_H264,
            EncoderType.QSV_H264,
            EncoderType.LIBX264,
        ]
    )

    # Advanced FFmpeg options
    extra_video_args: list[str] = Field(default_factory=list)

    @field_validator("max_bitrate_mbps")
    @classmethod
    def validate_bitrate(cls, v: str | float) -> str | float:
        """Validate bitrate is either 'auto' or a positive number."""
        if isinstance(v, str):
            if v != "auto":
                raise ValueError("Bitrate must be 'auto' or a number")
        elif isinstance(v, (int, float)):
            if v <= 0:
                raise ValueError("Bitrate must be positive")
        return v


class AudioConfig(BaseModel):
    """Audio encoding configuration."""

    codec: Literal["aac", "mp3", "opus"] = Field(default="aac")
    bitrate_kbps: int = Field(default=128, ge=32, le=320)
    sample_rate: int = Field(default=44100, ge=8000, le=48000)
    channels: int = Field(default=2, ge=1, le=8)
    extra_audio_args: list[str] = Field(default_factory=list)


class SubtitleConfig(BaseModel):
    """Subtitle configuration."""

    embed: bool = Field(default=True)
    languages: list[str] = Field(default_factory=lambda: ["en", "ar"])
    auto_generate: bool = Field(default=False)
    burn_in: bool = Field(default=False)

    @field_validator("languages")
    @classmethod
    def validate_languages(cls, v: list[str]) -> list[str]:
        """Validate language codes are 2-3 characters."""
        for lang in v:
            if not (2 <= len(lang) <= 3):
                raise ValueError(f"Invalid language code: {lang}")
        return v


class OutputConfig(BaseModel):
    """Output file configuration."""

    container: Literal["mp4", "mkv", "avi"] = Field(default="mp4")
    faststart: bool = Field(default=True)
    output_dir: str = Field(default="./output")
    filename_template: str = Field(default="{title}_{id}.{ext}")

    # FAT32 file size handling
    max_file_size_gb: float = Field(default=3.9, ge=0.1, le=100.0)
    on_size_exceed: OnSizeExceed = Field(default=OnSizeExceed.SPLIT)

    # Split settings
    split_part_template: str = Field(default="{stem}_part{num:03d}.{ext}")

    # Compress settings
    target_bitrate_reduction: float = Field(default=0.8, ge=0.1, le=1.0)


class TransferConfig(BaseModel):
    """File transfer configuration."""

    # USB auto-copy
    usb_auto_copy: bool = Field(default=False)
    usb_mount_path: str = Field(default="")
    usb_subdir: str = Field(default="Videos")

    # Network transfer
    network_copy: bool = Field(default=False)
    network_path: str = Field(default="")
    network_subdir: str = Field(default="")

    # Transfer options
    verify_checksum: bool = Field(default=True)
    delete_after_transfer: bool = Field(default=False)


class DownloadConfig(BaseModel):
    """Download configuration."""

    # yt-dlp settings
    format_preference: str = Field(
        default="bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
    )
    download_archive: str = Field(default="~/.config/yt2audi/archive.txt")
    rate_limit_mbps: float | None = Field(default=None, ge=0.1)
    retries: int = Field(default=3, ge=0, le=10)
    fragment_retries: int = Field(default=10, ge=0, le=50)

    # Playlist settings
    playlist_start: int = Field(default=1, ge=1)
    playlist_end: int | None = Field(default=None, ge=1)
    playlist_reverse: bool = Field(default=False)


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: LogLevel = Field(default=LogLevel.INFO)
    format: LogFormat = Field(default=LogFormat.JSON)
    log_file: str = Field(default="~/.config/yt2audi/logs/yt2audi.log")
    rotation_size_mb: int = Field(default=10, ge=1, le=1000)
    rotation_count: int = Field(default=5, ge=1, le=100)


class Profile(BaseModel):
    """Complete profile configuration."""

    profile: ProfileMeta
    video: VideoConfig
    audio: AudioConfig
    subtitles: SubtitleConfig
    output: OutputConfig
    transfer: TransferConfig
    download: DownloadConfig
    logging: LoggingConfig

    @classmethod
    def from_toml_file(cls, path: Path) -> "Profile":
        """Load and validate profile from TOML file.

        Args:
            path: Path to TOML file

        Returns:
            Validated Profile instance

        Raises:
            ConfigError: If file doesn't exist or is invalid
        """
        from yt2audi.exceptions import ConfigError

        if not path.exists():
            raise ConfigError(f"Profile file not found: {path}")

        try:
            import tomli

            with open(path, "rb") as f:
                data = tomli.load(f)
            return cls(**data)
        except Exception as e:
            raise ConfigError(f"Failed to load profile from {path}: {e}") from e

    def to_toml_file(self, path: Path) -> None:
        """Write profile to TOML file.

        Args:
            path: Destination path for TOML file

        Raises:
            ConfigError: If write fails
        """
        from yt2audi.exceptions import ConfigError

        try:
            import tomli_w

            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "wb") as f:
                tomli_w.dump(self.model_dump(), f)
        except Exception as e:
            raise ConfigError(f"Failed to write profile to {path}: {e}") from e


class AppConfig(BaseModel):
    """Application-level configuration."""

    default_profile: str = Field(default="audi_q5_mmi")
    concurrent_downloads: int = Field(default=2, ge=1, le=10)
    concurrent_conversions: int = Field(default=2, ge=1, le=10)
    temp_dir: str = Field(default="")

    # Update settings
    check_on_startup: bool = Field(default=True)
    ytdlp_auto_update: bool = Field(default=False)
    app_auto_update: bool = Field(default=False)

    # UI settings
    theme: Literal["light", "dark", "auto"] = Field(default="dark")
    show_notifications: bool = Field(default=True)
    minimize_to_tray: bool = Field(default=False)
