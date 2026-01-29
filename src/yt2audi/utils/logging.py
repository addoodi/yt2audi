"""Logging configuration using structlog."""

import logging
import sys
from pathlib import Path

import structlog

from yt2audi.models.profile import LogFormat, LogLevel, LoggingConfig


def configure_logging(config: LoggingConfig) -> None:
    """Configure structured logging.

    Args:
        config: Logging configuration

    Sets up structlog with:
    - JSON output for production (easy parsing)
    - Console output for development (human-readable)
    - Log rotation
    - Appropriate log levels
    """
    # Expand log file path
    from yt2audi.config import expand_path

    log_file = expand_path(config.log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, config.level.value),
    )

    # Select processors based on format
    if config.format == LogFormat.JSON:
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ]
    else:  # CONSOLE
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, config.level.value)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)
