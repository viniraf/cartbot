"""Unit tests for Config loader using pytest."""

import os
import pytest
from unittest.mock import patch
from app.infra import Config


class TestConfigLoading:
    """Test configuration loading from environment variables."""

    def test_config_loads_telegram_token(self):
        """Config should load TELEGRAM_TOKEN from environment."""
        assert Config.TELEGRAM_TOKEN is not None
        assert isinstance(Config.TELEGRAM_TOKEN, str)
        assert len(Config.TELEGRAM_TOKEN) > 0

    def test_config_loads_database_path(self):
        """Config should load DATABASE_PATH with correct default."""
        assert Config.DATABASE_PATH == "data/cartbot.db"

    def test_config_loads_log_level(self):
        """Config should load LOG_LEVEL with correct default."""
        assert Config.LOG_LEVEL == "INFO"

    def test_config_validate_succeeds_with_token(self):
        """Config.validate() should not raise error when TELEGRAM_TOKEN is set."""
        try:
            Config.validate()
        except ValueError:
            pytest.fail("Config.validate() raised ValueError unexpectedly")

    def test_config_validate_fails_without_token(self):
        """Config.validate() should raise ValueError when TELEGRAM_TOKEN is missing."""
        with patch.object(Config, 'TELEGRAM_TOKEN', None):
            with pytest.raises(ValueError) as exc_info:
                Config.validate()
            assert "TELEGRAM_TOKEN is required" in str(exc_info.value)

    def test_config_is_importable_from_infra(self):
        """Config should be importable from app.infra module."""
        from app.infra import Config as ImportedConfig
        assert ImportedConfig is not None
        assert hasattr(ImportedConfig, 'TELEGRAM_TOKEN')
        assert hasattr(ImportedConfig, 'DATABASE_PATH')
        assert hasattr(ImportedConfig, 'LOG_LEVEL')
        assert hasattr(ImportedConfig, 'validate')

    def test_config_attributes_are_class_attributes(self):
        """Config values should be accessible as class attributes."""
        # Can access without instantiating
        assert hasattr(Config, 'TELEGRAM_TOKEN')
        assert hasattr(Config, 'DATABASE_PATH')
        assert hasattr(Config, 'LOG_LEVEL')
