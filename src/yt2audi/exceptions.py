"""Custom exceptions for YT2Audi."""


class YT2AudiError(Exception):
    """Base exception for all YT2Audi errors."""

    pass


class ConfigError(YT2AudiError):
    """Configuration validation or loading error."""

    pass


class DownloadError(YT2AudiError):
    """Video download failed."""

    pass


class ConversionError(YT2AudiError):
    """Video conversion failed."""

    pass


class TransferError(YT2AudiError):
    """File transfer to USB/network failed."""

    pass


class GPUDetectionError(YT2AudiError):
    """GPU detection or encoder selection failed."""

    pass
