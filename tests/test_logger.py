"""Unit tests for logging setup using pytest."""

import logging
import pytest
from unittest.mock import patch
from app.infra import setup_logging
from app.infra.config import Config


class TestLoggingSetup:
    """Test logging configuration."""

    def test_setup_logging_returns_logger(self):
        """setup_logging() should return a configured logger."""
        logger = setup_logging(level="INFO")
        assert logger is not None
        assert isinstance(logger, logging.Logger)

    def test_setup_logging_uses_config_log_level(self):
        """setup_logging() should use Config.LOG_LEVEL by default."""
        logger = setup_logging()
        assert logger.level == logging.getLevelName(Config.LOG_LEVEL)

    def test_setup_logging_accepts_custom_level(self):
        """setup_logging() should accept custom log level."""
        logger = setup_logging(level="DEBUG")
        assert logger.level == logging.DEBUG

    def test_setup_logging_creates_stream_handler(self):
        """setup_logging() should add StreamHandler for console output."""
        logger = setup_logging()
        handlers = logger.handlers
        assert len(handlers) > 0
        assert any(isinstance(h, logging.StreamHandler) for h in handlers)

    def test_setup_logging_applies_correct_format(self):
        """setup_logging() should apply the correct log format."""
        logger = setup_logging()
        handler = logger.handlers[0]
        assert handler.formatter is not None
        # Check format contains expected placeholders
        format_string = handler.formatter._fmt
        assert "%(asctime)s" in format_string
        assert "%(name)s" in format_string
        assert "%(levelname)s" in format_string
        assert "%(message)s" in format_string

    def test_setup_logging_can_log_messages(self):
        """setup_logging() should produce a working logger."""
        logger = setup_logging(level="INFO")
        try:
            logger.info("Test message")
            logger.warning("Warning message")
            logger.error("Error message")
        except Exception as e:
            pytest.fail(f"Logger failed to log: {e}")

    def test_setup_logging_is_importable(self):
        """setup_logging should be importable from app.infra."""
        from app.infra import setup_logging as imported_setup
        assert imported_setup is not None
        assert callable(imported_setup)

    def test_setup_logging_removes_duplicate_handlers(self):
        """Multiple calls to setup_logging() should not create duplicate handlers."""
        setup_logging(level="INFO")
        initial_count = len(logging.getLogger().handlers)
        setup_logging(level="INFO")
        final_count = len(logging.getLogger().handlers)
        assert final_count == initial_count
