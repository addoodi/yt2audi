"""Default configuration values."""

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


def get_default_profile() -> Profile:
    """Get the default Audi Q5 MMI profile.

    Returns:
        Default Profile instance
    """
    return Profile(
        profile=ProfileMeta(
            name="Audi Q5 MMI (Default)",
            description="Default profile optimized for Audi Q5 MMI/MIB2/3 systems",
            version="1.0.0",
        ),
        video=VideoConfig(),
        audio=AudioConfig(),
        subtitles=SubtitleConfig(),
        output=OutputConfig(),
        transfer=TransferConfig(),
        download=DownloadConfig(),
        logging=LoggingConfig(),
    )
