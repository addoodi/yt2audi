"""Unit tests for logging configuration."""

from unittest.mock import patch, MagicMock
from yt2audi.utils.logging import configure_logging, get_logger
from yt2audi.models.profile import LoggingConfig, LogLevel, LogFormat

class TestLogging:
    """Test suite for logging utilities."""

    @patch("yt2audi.config.expand_path")
    @patch("logging.basicConfig")
    @patch("structlog.configure")
    def test_configure_logging_console(self, mock_structlog, mock_logging, mock_expand, tmp_path):
        """Test console logging configuration."""
        mock_expand.return_value = tmp_path / "test.log"
        config = LoggingConfig(
            level=LogLevel.DEBUG,
            format=LogFormat.CONSOLE,
            log_file="test.log"
        )
        
        configure_logging(config)
        
        mock_logging.assert_called_once()
        mock_structlog.assert_called_once()
        # Verify processors (checking if console renderer is used)
        args, kwargs = mock_structlog.call_args
        processors = kwargs["processors"]
        assert any("ConsoleRenderer" in str(p) for p in processors)

    @patch("yt2audi.config.expand_path")
    @patch("logging.basicConfig")
    @patch("structlog.configure")
    def test_configure_logging_json(self, mock_structlog, mock_logging, mock_expand, tmp_path):
        """Test JSON logging configuration."""
        mock_expand.return_value = tmp_path / "test.log"
        config = LoggingConfig(
            level=LogLevel.INFO,
            format=LogFormat.JSON,
            log_file="test.log"
        )
        
        configure_logging(config)
        
        args, kwargs = mock_structlog.call_args
        processors = kwargs["processors"]
        assert any("JSONRenderer" in str(p) for p in processors)

    def test_get_logger(self):
        """Test get_logger returns a structlog logger."""
        logger = get_logger("test")
        assert logger is not None
