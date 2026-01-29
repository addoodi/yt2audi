"""YT2Audi - YouTube downloader and converter for Audi MMI systems."""

__version__ = "2.0.0"
__author__ = "AAlmana"
__license__ = "MIT"

from yt2audi.exceptions import (
    YT2AudiError,
    ConfigError,
    DownloadError,
    ConversionError,
    TransferError,
    GPUDetectionError,
)

__all__ = [
    "__version__",
    "__author__",
    "__license__",
    "YT2AudiError",
    "ConfigError",
    "DownloadError",
    "ConversionError",
    "TransferError",
    "GPUDetectionError",
]
